"""Resolve orbit.json into the data file the PowerPoint builder reads.

  python3 deck_data.py <article_dir>

Writes <article_dir>/out/deck/deck-data.json: every {metric_id} replaced by its locked value,
table rows attached to bar visuals, icon SVGs, figure path, and the slide list (orbit.deck.slides,
or a default sequence built from what the orbit contains).
"""
import json
import sys

import visuals as V
from common import load, resolve


def default_slides(R):
    slides = [{"type": "title"}, {"type": "question"}]
    if R.get("video", {}).get("population"):
        slides.append({"type": "population"})
    if R.get("figure") or R.get("icon_list"):
        slides.append({"type": "figure"})
    order = R.get("video", {}).get("scenes") or [v["id"] for v in R.get("visuals", [])]
    slides += [{"type": "visual", "visual": vid} for vid in order]
    slides += [{"type": "findings"}, {"type": "context"}, {"type": "reference"}]
    return slides


def main():
    article, orbit, M = load(sys.argv[1])
    R = resolve({k: v for k, v in orbit.items() if k != "metrics"}, M)
    out = article / "out" / "deck"
    out.mkdir(parents=True, exist_ok=True)

    visuals = {}
    for v in R.get("visuals", []):
        v = dict(v)
        v.update(R.get("video", {}).get("overrides", {}).get(v["id"], {}) if v["type"] == "hbars" else {})
        if v["type"] == "bars":
            v["rows"] = [{"label": r["label"], "value": r["value"]} for r in orbit["tables"][v["table"]]["rows"]]
            v["callouts"] = R.get("video", {}).get("overrides", {}).get(v["id"], {}).get("callouts", [])
        visuals[v["id"]] = v

    figure = None
    if R.get("figure"):
        fig = article / "out" / "page" / "figure.jpg"
        figure = {**R["figure"], "path": str(fig if fig.exists() else article / R["figure"]["file"])}

    deck = R.get("deck", {})
    data = {
        "slug": R["slug"],
        "title": R["title"],
        "paper_title": R["paper_title"],
        "authors": R["authors"],
        "tags": R["tags"],
        "content": R["content"],
        "population": R.get("video", {}).get("population"),
        "topic": R.get("video", {}).get("topic", ""),
        "note": R.get("video", {}).get("note", "Draft for internal review"),
        "square": R.get("cards", {}).get("square"),
        "figure": figure,
        "icon_list": R.get("icon_list"),
        "sidebar": R.get("sidebar", []),
        "visuals": visuals,
        "slides": deck.get("slides") or default_slides(R),
        "animation": deck.get("animation", "auto"),
        "icons": {name: V.ICONS[name] for name in V.ICONS},
        "output": str(out / f"{R['slug']}.pptx"),
    }
    (out / "deck-data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(f"deck data: {out / 'deck-data.json'} · {len(data['slides'])} slides")


if __name__ == "__main__":
    main()
