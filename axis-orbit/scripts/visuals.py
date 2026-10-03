"""SVG component library for Axis ORbits. Input: a visual spec with placeholders already resolved.

Types: zones, bars, hbars, vs, steps (see references/visual-library.md).
Rules: one linear scale per chart, brand tokens only, no red/orange, no gradients, no shadows.
"""
from html import escape

from common import color, num

FAINT = "#e1e5e8"
FADED = "#545a66"
BLUE = "#003C4C"
FONT = "'Open Sans', Arial, sans-serif"


def _svg(w, h, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{escape(label)}" font-family="{FONT}">{body}</svg>'
    )


def _t(x, y, s, size=13, weight=400, fill=BLUE, anchor="middle", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{escape(str(s))}</text>'


def zones(v):
    """A 0-1 (or domain) score ruler split into zones; a bar per zone for one rate, on one scale."""
    d0, d1 = v.get("domain", [0, 1])
    x0, x1 = 40, 720
    sx = lambda s: x0 + (x1 - x0) * (s - d0) / (d1 - d0)
    base, hmax, smax = 236, 150, v["scale_max"]
    unit = v.get("unit", "%")
    out = []
    for g in v.get("grid", []):
        y = base - hmax * g / smax
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{FAINT}"/>')
        out.append(_t(x0 - 8, y + 4, f"{g:g}{unit}", 11, fill=FADED, anchor="end"))
    if v.get("bar_label"):
        out.append(_t(x0 - 30, base - hmax - 18, v["bar_label"], 11, fill=FADED, anchor="start"))
    for z in v["zones"]:
        col = color(z["color"])
        cx = (sx(z["from"]) + sx(z["to"])) / 2
        h = hmax * num(z["value"]) / smax
        out.append(_t(cx, 22, z["label"].upper(), 13, 700, col, extra=' letter-spacing="1"'))
        out.append(f'<rect x="{cx - 34:.1f}" y="{base - max(h, 2):.1f}" width="68" height="{max(h, 2):.1f}" rx="3" fill="{col}"/>')
        out.append(_t(cx, base - max(h, 2) - 10, z["value"], 28, 700))
        out.append(f'<rect x="{sx(z["from"]):.1f}" y="{base + 6}" width="{sx(z["to"]) - sx(z["from"]):.1f}" height="16" fill="{col}"/>')
        for i, st in enumerate(z.get("stats", [])[:2]):
            out.append(_t(cx, base + 84 + 22 * i, st, 15 if i == 0 else 13, 600 if i == 0 else 400, BLUE if i == 0 else FADED))
    for tk in v.get("ticks", []):
        out.append(f'<line x1="{sx(tk):.1f}" x2="{sx(tk):.1f}" y1="{base + 4}" y2="{base + 30}" stroke="{BLUE}" stroke-width="1.5"/>')
        out.append(_t(sx(tk), base + 46, f"{tk:g}" if tk not in (0, 1) else ("0" if tk == 0 else "1.0"), 13, 600))
    if v.get("axis_label"):
        tk = sorted(v.get("ticks", [d0, d1]))
        centre = (d0 + d1) / 2
        a, b = next(((x, y) for x, y in zip(tk, tk[1:]) if x <= centre <= y), (d0, d1))
        out.append(_t((sx(a) + sx(b)) / 2, base + 46, v["axis_label"], 12, fill=FADED))
    return _svg(760, 350, "".join(out), v.get("title", "Score zones"))


def bars(v, rows, dark=False):
    """Vertical columns from a table; one linear scale 0..y_max."""
    fg = "#ffffff" if dark else BLUE
    muted = "rgba(255,255,255,.55)" if dark else FADED
    grid = "rgba(255,255,255,.12)" if dark else FAINT
    unit = v.get("unit", "%")
    x0, x1, base, top, ymax = 34, 350, 190, 20, v["y_max"]
    n = len(rows)
    step = (x1 - x0) / n
    bw = step * 0.62
    hl = v.get("highlight_from", n)
    show = set(v.get("label_every", [r["label"] for r in rows]))
    out = []
    for g in v.get("grid", []):
        y = base - (base - top) * g / ymax
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{grid}"/>')
        out.append(_t(x0 - 6, y + 4, f"{g:g}{unit}", 10, fill=muted, anchor="end"))
    for i, r in enumerate(rows):
        bh = max((base - top) * num(r["value"]) / ymax, 1.5)
        x = x0 + i * step + (step - bw) / 2
        hot = i >= hl
        out.append(f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" fill="{color("freshgreen") if hot else color("seafoam")}" fill-opacity="{1 if hot else .55}"/>')
        if r["label"] in show:
            out.append(_t(x + bw / 2, base + 16, r["label"], 10, fill=muted))
    last = rows[-1]
    ly = base - (base - top) * num(last["value"]) / ymax
    out.append(_t(x0 + (n - 1) * step + step / 2 - 8, ly + 2, f"{last['value']}{unit}", 13, 700, fg, anchor="end"))
    if v.get("x_label"):
        out.append(_t((x0 + x1) / 2, base + 34, v["x_label"], 10, fill=muted))
    return _svg(360, 230, "".join(out), v.get("title", "Bar chart"))


def hbars(v):
    """Horizontal bars on one scale 0..x_max, label left, value and optional change right."""
    rows = v["rows"]
    bx, rh, y0 = 250, 52, 30
    unit_px = 400 / v["x_max"]
    out = []
    bottom = y0 + rh * len(rows)
    for g in [0] + list(v.get("grid", [])):
        x = bx + unit_px * g
        if g:
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y0 - 10}" y2="{bottom - 8}" stroke="{FAINT}"/>')
        out.append(_t(x, bottom + 10, f"{g:g}", 11, fill=FADED))
    out.append(f'<line x1="{bx}" x2="{bx}" y1="{y0 - 10}" y2="{bottom - 8}" stroke="{BLUE}"/>')
    for i, r in enumerate(rows):
        y = y0 + i * rh
        lines = r["label"].split("\n")
        for j, ln in enumerate(lines):
            out.append(_t(0, y + (22 if len(lines) == 1 else 12 + 18 * j), ln, 14, 600, anchor="start"))
        w = unit_px * num(r["value"])
        out.append(f'<rect x="{bx}" y="{y + 4}" width="{w:.1f}" height="24" rx="3" fill="{color(r.get("color", "trustturquoise"))}"/>')
        out.append(_t(bx + w + 8, y + 22, r["value"], 16, 700, anchor="start"))
        if r.get("change"):
            out.append(_t(bx + w + 14 + 9 * len(r["value"]), y + 22, r["change"], 14, 600, color("trustturquoise"), anchor="start"))
    if v.get("x_label"):
        out.append(_t(bx + 200, bottom + 30, v["x_label"], 12, fill=FADED))
    return _svg(760, bottom + 40, "".join(out), v.get("title", "Comparison"))


def vs(v):
    """Two arms, one outcome: two columns on one scale, A in healthygreen, B in trustturquoise."""
    a, b = v["a"], v["b"]
    smax = v.get("scale_max") or max(num(a["value"]), num(b["value"])) * 1.15
    base, hmax = 250, 170
    out = []
    for i, (arm, col, cx) in enumerate(((a, "healthygreen", 230), (b, "trustturquoise", 530))):
        h = max(hmax * num(arm["value"]) / smax, 2)
        out.append(f'<rect x="{cx - 60}" y="{base - h:.1f}" width="120" height="{h:.1f}" rx="4" fill="{color(col)}"/>')
        out.append(_t(cx, base - h - 14, arm["value"], 40, 700))
        for j, ln in enumerate(arm["label"].split("\n")):
            out.append(_t(cx, base + 30 + 20 * j, ln, 16, 700))
    out.append(f'<line x1="80" x2="680" y1="{base}" y2="{base}" stroke="{BLUE}"/>')
    out.append(_t(380, base - 60, "vs", 22, 700, FADED))
    if v.get("outcome"):
        out.append(_t(380, 26, v["outcome"].upper(), 14, 700, color("healthygreen"), extra=' letter-spacing="1"'))
    return _svg(760, 310, "".join(out), v.get("title", "Comparison"))


def steps(v):
    """Accumulating risk: one column per step on one scale, plus an optional reported callout."""
    st = v["steps"]
    smax = v.get("scale_max") or max(num(s["value"]) for s in st) * (1.45 if v.get("callout") else 1.15)
    base, hmax = 250, 180
    gap = 600 / len(st)
    out = [f'<line x1="60" x2="700" y1="{base}" y2="{base}" stroke="{BLUE}"/>']
    shades = ["seafoam", "trustturquoise", "strengthblue", "strengthblue"]
    for i, s in enumerate(st):
        cx = 80 + gap * i + gap / 2
        h = max(hmax * num(s["value"]) / smax, 2)
        out.append(f'<rect x="{cx - 50:.1f}" y="{base - h:.1f}" width="100" height="{h:.1f}" rx="4" fill="{color(shades[min(i, 3)])}"/>')
        out.append(_t(cx, base - h - 12, s["value"], 30, 700))
        for j, ln in enumerate(s["label"].split("\n")):
            out.append(_t(cx, base + 26 + 18 * j, ln, 14, 600))
    if v.get("callout"):
        out.append(_t(700, 30, v["callout"]["value"], 34, 700, color("trustturquoise"), anchor="end"))
        out.append(_t(700, 52, v["callout"]["caption"], 13, fill=FADED, anchor="end"))
    return _svg(760, 310, "".join(out), v.get("title", "Accumulating risk"))


ICONS = {
    # 32x32 grid, stroke 2, round caps, currentColor, geometric only
    "elongation": '<ellipse cx="16" cy="18" rx="13" ry="5"/><path d="M5 8h22M5 8l3-2.5M5 8l3 2.5M27 8l-3-2.5M27 8l-3 2.5"/>',
    "flatness": '<rect x="3" y="15" width="26" height="8" rx="4"/><path d="M16 4v8M16 12l-2.5-3M16 12l2.5-3"/>',
    "volume": '<path d="M16 4l11 6v12l-11 6-11-6V10z"/><path d="M5 10l11 6 11-6M16 16v12"/>',
    "axis": '<ellipse cx="16" cy="16" rx="12" ry="7" stroke-dasharray="3 3"/><path d="M2 16h28M2 12v8M30 12v8"/>',
    "surface": '<rect x="4" y="4" width="24" height="24" rx="5"/><circle cx="16" cy="16" r="6"/>',
    "score": '<path d="M4 23a12 12 0 0 1 24 0"/><path d="M16 23l6-8"/><circle cx="16" cy="23" r="2"/>',
    "patient": '<circle cx="16" cy="9" r="5"/><path d="M6 28c0-6 4.5-10 10-10s10 4 10 10"/>',
    "clock": '<circle cx="16" cy="16" r="12"/><path d="M16 9v7l5 3"/>',
    "chart-up": '<path d="M4 26h24M7 21l6-6 5 4 8-9"/><path d="M21 10h5v5"/>',
    "chart-down": '<path d="M4 26h24M7 10l6 6 5-4 8 9"/><path d="M21 21h5v-5"/>',
    "check": '<circle cx="16" cy="16" r="12"/><path d="M10 16.5l4 4 8-9"/>',
    "zero": '<circle cx="16" cy="16" r="12"/><path d="M8 24L24 8"/>',
    "rom-arc": '<path d="M6 26A20 20 0 0 1 26 6"/><path d="M6 26h4M6 26v-4"/><circle cx="26" cy="6" r="2"/>',
    "navigation": '<circle cx="16" cy="16" r="12"/><path d="M16 4v4M16 24v4M4 16h4M24 16h4"/><circle cx="16" cy="16" r="3"/>',
    "repair": '<path d="M6 10c6 0 6 12 12 12M14 10c6 0 6 12 12 12"/><path d="M4 16h24" stroke-dasharray="2 3"/>',
}


def icon(name, size=32):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="{size}" height="{size}" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'
    )


def render(v, tables, dark=False):
    t = v["type"]
    if t == "zones":
        return zones(v)
    if t == "bars":
        return bars(v, tables[v["table"]]["rows"], dark=dark)
    if t == "hbars":
        return hbars(v)
    if t == "vs":
        return vs(v)
    if t == "steps":
        return steps(v)
    raise ValueError(f"unknown visual type {t}")
