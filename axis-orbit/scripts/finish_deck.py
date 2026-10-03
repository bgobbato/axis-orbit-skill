"""Finish the deck: brand theme colors, fade transitions and native PowerPoint entrance animations.

  python3 finish_deck.py <article_dir>

Reads out/deck/<slug>.raw.pptx and out/deck/anim.json, writes out/deck/<slug>.pptx.
pptxgenjs cannot write animations, so this adds <p:transition> and <p:timing> to each slide.

Animation modes (orbit.json -> deck.animation):
  "auto"  each slide plays its build by itself after the slide appears (like the video)
  "click" each step waits for a click (for a live talk)
"""
import json
import re
import sys
import zipfile

from common import load

THEME_COLORS = {  # Advita brand -> Office theme slots, so new shapes in PowerPoint use the brand palette
    "dk1": "000607", "lt1": "FFFFFF", "dk2": "003C4C", "lt2": "F2F3F5",
    "accent1": "39B54A", "accent2": "8DC63F", "accent3": "00A79D", "accent4": "74C7A7",
    "accent5": "00596D", "accent6": "277E33", "hlink": "00857D", "folHlink": "003C4C",
}
EFFECTS = {  # name -> (presetID, presetSubtype, filter, duration ms)
    "fade": (10, 0, "fade", 450),
    "wipeUp": (22, 4, "wipe(up)", 750),      # Wipe, from bottom
    "wipeRight": (22, 8, "wipe(right)", 750),  # Wipe, from left
}
STEP_GAP_MS = 550   # auto mode: time between steps
ITEM_GAP_MS = 70    # stagger inside one step


def theme_xml(xml):
    def slot(m):
        name = m.group(1)
        return f"<a:{name}><a:srgbClr val=\"{THEME_COLORS[name]}\"/></a:{name}>" if name in THEME_COLORS else m.group(0)

    xml = re.sub(r"<a:(dk1|lt1|dk2|lt2|accent\d|hlink|folHlink)>.*?</a:\1>", slot, xml, flags=re.S)
    return re.sub(r'<a:clrScheme name="[^"]*"', '<a:clrScheme name="Advita Axis"', xml)


class Ids:
    def __init__(self):
        self.n = 2

    def next(self):
        self.n += 1
        return self.n


def effect(ids, spid, kind, delay, node):
    preset, sub, flt, dur = EFFECTS[kind]
    a, b, c = ids.next(), ids.next(), ids.next()
    return (
        f'<p:par><p:cTn id="{a}" presetID="{preset}" presetClass="entr" presetSubtype="{sub}" fill="hold" grpId="0" nodeType="{node}">'
        f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>'
        f'<p:set><p:cBhvr><p:cTn id="{b}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
        f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
        f'<p:to><p:strVal val="visible"/></p:to></p:set>'
        f'<p:animEffect transition="in" filter="{flt}"><p:cBhvr><p:cTn id="{c}" dur="{dur}"/>'
        f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
        f"</p:childTnLst></p:cTn></p:par>"
    )


def group(ids, effects_xml, auto):
    outer, inner = ids.next(), ids.next()
    start = '<p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>' if auto else '<p:cond delay="indefinite"/>'
    return (
        f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst>{start}</p:stCondLst><p:childTnLst>'
        f'<p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        f"{effects_xml}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>"
    )


def shape_index(xml):
    """name -> (id, kind) where kind is sp | graphicFrame | pic."""
    out = {}
    for m in re.finditer(r'<p:sp><p:nvSpPr><p:cNvPr id="(\d+)"[^>]*>.*?</p:cNvPr>.*?<p:ph([^>]*)/>', xml, flags=re.S):
        typ = re.search(r'type="(\w+)"', m.group(2))
        if typ and m.group(0).count("<p:sp>") == 1:
            out[{"title": "ph:title", "body": "ph:eyebrow"}.get(typ.group(1), "ph:" + typ.group(1))] = (m.group(1), "sp")
    for kind in ("sp", "graphicFrame", "pic"):
        for m in re.finditer(rf"<p:{kind}>\s*<p:nv\w+Pr>\s*<p:cNvPr id=\"(\d+)\" name=\"([^\"]+)\"", xml):
            out[m.group(2)] = (m.group(1), kind)
    return out


def timing(xml, steps, auto):
    idx = shape_index(xml)
    ids = Ids()
    groups, builds, seen = [], [], set()
    missing = []
    flat_auto = []
    for si, st in enumerate(steps):
        effs = []
        for j, item in enumerate(st):
            if item["name"] not in idx:
                missing.append(item["name"])
                continue
            spid, kind = idx[item["name"]]
            if auto:
                delay, node = si * STEP_GAP_MS + j * ITEM_GAP_MS, "withEffect" if flat_auto or j else "afterEffect"
                flat_auto.append(effect(ids, spid, item["effect"], delay, node))
            else:
                delay, node = j * ITEM_GAP_MS, "clickEffect" if j == 0 else "withEffect"
                effs.append(effect(ids, spid, item["effect"], delay, node))
            if spid not in seen:
                seen.add(spid)
                if kind == "sp":
                    builds.append(f'<p:bldP spid="{spid}" grpId="0" animBg="1"/>')
                elif kind == "graphicFrame":
                    builds.append(f'<p:bldGraphic spid="{spid}" grpId="0"><p:bldAsOne/></p:bldGraphic>')
        if effs:
            groups.append(group(ids, "".join(effs), auto=False))
    if auto and flat_auto:
        groups = [group(ids, "".join(flat_auto), auto=True)]
    if not groups:
        return "", missing
    xml_t = (
        '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        + "".join(groups)
        + "</p:childTnLst></p:cTn>"
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        "</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>"
        + (f"<p:bldLst>{''.join(builds)}</p:bldLst>" if builds else "")
        + "</p:timing>"
    )
    return xml_t, missing


def main():
    article, orbit, _ = load(sys.argv[1])
    deck_dir = article / "out" / "deck"
    slug = orbit["slug"]
    anim = json.loads((deck_dir / "anim.json").read_text())
    auto = anim["mode"] != "click"
    by_slide = {a["slide"]: a["steps"] for a in anim["slides"]}
    raw, final = deck_dir / f"{slug}.raw.pptx", deck_dir / f"{slug}.pptx"
    warnings, n_effects = [], 0
    with zipfile.ZipFile(raw) as zin, zipfile.ZipFile(final, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            m = re.match(r"ppt/slides/slide(\d+)\.xml$", item.filename)
            if m:
                xml = data.decode("utf8")
                t, missing = timing(xml, by_slide.get(int(m.group(1)), []), auto)
                warnings += [f"slide {m.group(1)}: no shape named {x}" for x in missing]
                n_effects += t.count("presetClass=")
                insert = '<p:transition spd="med"><p:fade/></p:transition>' + t
                xml = xml.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + insert, 1) if "</p:clrMapOvr>" in xml else xml.replace("</p:sld>", insert + "</p:sld>", 1)
                data = xml.encode("utf8")
            elif re.match(r"ppt/theme/theme\d+\.xml$", item.filename):
                data = theme_xml(data.decode("utf8")).encode("utf8")
            zout.writestr(item, data)
    raw.unlink()
    for w in warnings:
        print("WARN", w)
    print(f"deck: {final} · {len(by_slide)} slides · {n_effects} animations ({'auto' if auto else 'on click'})")


if __name__ == "__main__":
    main()
