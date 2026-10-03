"""Render share cards from orbit.json.

  python3 render_cards.py <article_dir>

Writes out/page/share-1200x630.png (link preview) and out/page/share-1080.png (square, one number).
"""
import sys
from html import escape

from playwright.sync_api import sync_playwright

import visuals as V
from common import load, resolve

HEAD = """<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap">
<style>
*{box-sizing:border-box;margin:0}
body{width:%dpx;height:%dpx;overflow:hidden;font-family:"Open Sans",Arial,sans-serif;color:#003C4C;background:%s}
.mark{display:flex;align-items:center;gap:10px;font-size:30px}
.mark .a{font-weight:700;letter-spacing:-.02em}
.mark .o{background:#003C4C;color:#fff;font-weight:600;font-style:italic;font-size:20px;padding:2px 14px;border-radius:99px}
.dark .mark .o{background:#fff;color:#003C4C}
.eyebrow{font-size:17px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#39B54A}
.foot{font-size:14px;color:#545a66}
svg{width:100%%;height:auto;display:block}
</style>"""


def main():
    article, orbit, M = load(sys.argv[1])
    R = resolve({k: v for k, v in orbit.items() if k != "metrics"}, M)
    cards = R["cards"]
    vis = {v["id"]: v for v in R.get("visuals", [])}
    w = cards["wide"]
    panel = ""
    if w.get("visual"):
        v = vis[w["visual"]]
        panel = f"""<div style="background:#f2f3f5;padding:48px 40px;display:flex;flex-direction:column;justify-content:center">
    <div style="font-size:22px;font-weight:700;margin-bottom:6px">{escape(w.get('visual_title', v['title']))}</div>
    <div class="foot" style="margin-bottom:18px">{escape(w.get('visual_subtitle', ''))}</div>
    {V.render(v, orbit.get('tables', {}))}</div>"""
    wide = HEAD % (1200, 630, "#fff") + f"""
<div style="display:grid;grid-template-columns:{'1.05fr 1fr' if panel else '1fr'};height:630px">
  <div style="padding:56px 48px 48px 64px;display:flex;flex-direction:column;justify-content:space-between">
    <div class="mark"><span class="a">Axis</span><span class="o">ORbits</span></div>
    <div><div class="eyebrow" style="margin-bottom:18px">{escape(w['eyebrow'])}</div>
      <div style="font-size:42px;font-weight:600;line-height:1.15;letter-spacing:-.02em">{escape(R['title'])}</div></div>
    <div class="foot">{escape(w['foot'])}</div>
  </div>{panel}
</div>"""
    s = cards["square"]
    square = HEAD % (1080, 1080, "#003C4C") + f"""
<div class="dark" style="height:1080px;padding:72px 80px;display:flex;flex-direction:column;justify-content:space-between;color:#fff">
  <div class="mark"><span class="a">Axis</span><span class="o">ORbits</span></div>
  <div>
    <div class="eyebrow" style="color:#8DC63F;margin-bottom:20px">{escape(s['eyebrow'])}</div>
    <div style="font-size:{230 if len(s['value']) <= 6 else 170}px;font-weight:700;line-height:1;letter-spacing:-.03em;color:var(--c,#00A79D)">{escape(s['value'])}</div>
    <div style="font-size:44px;font-weight:600;line-height:1.2;margin-top:18px;max-width:880px">{escape(s['caption'])}</div>
  </div>
  <div class="foot" style="color:rgba(255,255,255,.6)">{escape(s['foot'])}</div>
</div>"""
    out = article / "out" / "page"
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for name, html, size in (("share-1200x630.png", wide, (1200, 630)), ("share-1080.png", square, (1080, 1080))):
            pg = b.new_page(viewport={"width": size[0], "height": size[1]})
            pg.set_content(html, wait_until="networkidle")
            pg.evaluate("document.fonts.ready.then(() => true)")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(out / name))
            pg.close()
        b.close()
    print(f"cards: {out}/share-1200x630.png, share-1080.png")


if __name__ == "__main__":
    main()
