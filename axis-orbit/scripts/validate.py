"""Hard gate: every number shown anywhere must be locked to a verbatim quote in source.md.

  python3 validate.py <article_dir>

FAIL (exit 1) when:
  - a metric quote, table-row quote or list quote is not in source.md
  - a value is not inside its own quote
  - a {placeholder} has no matching metric
  - a bare number appears in displayed text without being a placeholder or a listed definition
  - structural limits are broken (hero metrics, sidebar cards, key findings)
WARN (exit 0) when text lengths drift from the writing guide.
"""
import re
import sys

from common import PLACEHOLDER, load

# Keys whose values are layout, not displayed claims.
STRUCTURAL = {
    "type", "id", "after", "table", "color", "icon", "file", "domain", "from", "to", "scale_max",
    "x_max", "y_max", "grid", "ticks", "highlight_from", "label_every", "width", "lines",
    "duration", "visual", "accent", "ref_rows", "callout_rows",
}
SKIP_TOP = {"slug", "status", "source", "paper_title", "authors", "metrics", "tables", "definitions", "hero_metric_ids"}
NUMBER = re.compile(r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?!D\b)")
FIG_REF = re.compile(r"\b(?:Figure|Fig\.|Table)\s+\d+", re.I)


def norm(s):
    s = s.replace(" ", " ").replace(" ", " ").replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"\s+", " ", s).strip()


def tight(s):
    return norm(s).replace(" ", "").replace("³", "3").replace("²", "2").lower()


def bare_value(v):
    return norm(v).rstrip("%").rstrip("x").lstrip("+")


def walk(obj, path=()):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            yield from walk(x, path + (i,))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, path + (k,))


def main():
    article, orbit, metrics = load(sys.argv[1])
    src_file = article / orbit["source"].get("text", "source.md")
    text = norm(src_file.read_text())
    text_tight = tight(text)
    errors, warns = [], []

    for m in orbit["metrics"]:
        q = norm(m["quote"])
        if q not in text:
            errors.append(f"metric '{m['id']}': quote not in {src_file.name}: “{m['quote'][:70]}”")
        if bare_value(m["value"]) not in q:
            errors.append(f"metric '{m['id']}': value {m['value']} not inside its quote")

    for tid, t in orbit.get("tables", {}).items():
        for r in t["rows"]:
            q = norm(r["quote"])
            if q not in text:
                errors.append(f"table '{tid}' row '{r['label']}': quote not in source")
            if bare_value(r["value"]) not in q:
                errors.append(f"table '{tid}' row '{r['label']}': value {r['value']} not inside its quote")

    il = orbit.get("icon_list")
    if il:
        if tight(il["quote"]) not in text_tight:
            errors.append("icon_list: quote not in source")
        for it in il["items"]:
            if it.get("detail") and tight(it["detail"]) not in tight(il["quote"]):
                errors.append(f"icon_list item '{it['label']}': detail '{it['detail']}' not in the list quote")

    allowed = set(orbit.get("definitions", []))
    for path, s in walk({k: v for k, v in orbit.items() if k not in SKIP_TOP}):
        if any(p in STRUCTURAL for p in path if isinstance(p, str)):
            continue
        if path[:2] == ("content", "reference") or path[:1] == ("icon_list",) and path[-1] in ("detail", "quote"):
            continue
        for ph in PLACEHOLDER.findall(s):
            if ph not in metrics:
                errors.append(f"{'.'.join(map(str, path))}: unknown placeholder {{{ph}}}")
        bare = FIG_REF.sub("", PLACEHOLDER.sub("", s))
        for n in NUMBER.findall(bare):
            if n not in allowed:
                errors.append(f"{'.'.join(map(str, path))}: bare number '{n}' (use a metric placeholder, or add it to definitions if it is a cut-off) in “{s[:60]}”")

    if len(orbit.get("hero_metric_ids", [])) > 3:
        errors.append("hero_metric_ids: more than 3")
    for h in orbit.get("hero_metric_ids", []):
        if h not in metrics:
            errors.append(f"hero_metric_ids: unknown metric {h}")
    if not 2 <= len(orbit.get("sidebar", [])) <= 4:
        errors.append("sidebar: needs 2 to 4 cards")
    c = orbit["content"]
    if not 3 <= len(c["key_findings"]) <= 6:
        errors.append("key_findings: needs 3 to 6 bullets")
    if not c["study_question"].strip().endswith("?"):
        errors.append("study_question: must be one question ending with '?'")
    visual_ids = {v["id"] for v in orbit.get("visuals", [])}
    for card in orbit.get("sidebar", []):
        if card.get("visual") and card["visual"] not in visual_ids:
            errors.append(f"sidebar: unknown visual {card['visual']}")
    for sc in orbit.get("video", {}).get("scenes", []):
        if sc not in visual_ids:
            errors.append(f"video.scenes: unknown visual {sc}")
    for v in orbit.get("visuals", []):
        if v.get("table") and v["table"] not in orbit.get("tables", {}):
            errors.append(f"visual {v['id']}: unknown table {v['table']}")

    words = lambda s: len(s.split())
    story = sum(words(p) for p in c["story"])
    for label, n, lo, hi in (
        ("study_question", words(c["study_question"]), 10, 20),
        ("story", story, 70, 140),
        ("clinical_context", words(c["clinical_context"]), 35, 70),
        ("limitations", words(c["limitations"]), 20, 45),
    ):
        if not lo <= n <= hi:
            warns.append(f"{label}: {n} words (guide {lo}-{hi})")
    for f in c["key_findings"]:
        if not 12 <= words(f["text"]) <= 45:
            warns.append(f"key finding '{f['label']}': {words(f['text'])} words (guide 12-45)")

    for w in warns:
        print("WARN", w)
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    rows = sum(len(t["rows"]) for t in orbit.get("tables", {}).values())
    print(f"OK: {len(orbit['metrics'])} metrics and {rows} table rows locked to {src_file.name}")


if __name__ == "__main__":
    main()
