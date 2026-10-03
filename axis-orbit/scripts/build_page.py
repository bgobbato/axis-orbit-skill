"""Build the ORbit page and standalone SVGs from orbit.json.

  python3 build_page.py <article_dir>

Writes <article_dir>/out/page/index.html, out/page/figure.jpg, out/svg/*.svg
"""
import datetime
import re
import sys
from html import escape

import visuals as V
from common import SKILL, load, resolve


def split_value(v):
    m = re.match(r"^([−\-+]?[\d,]*\.?\d+)(.*)$", v.strip())
    return (m.group(1), m.group(2)) if m else (v, "")


def counter_card(c):
    num, unit = split_value(c["value"])
    pre = f'<p class="card-pre">{escape(c["pre"])}</p>' if c.get("pre") else ""
    return f"""
      <div class="card">{pre}
        <p class="counter" style="color:var(--{c.get('color', 'freshgreen')})"><span class="count" data-final="{escape(num)}">{escape(num)}</span><span class="unit">{escape(unit)}</span></p>
        <p class="card-cap">{escape(c['caption'])}</p>
      </div>"""


def main():
    article, orbit, M = load(sys.argv[1])
    R = resolve({k: v for k, v in orbit.items() if k not in ("metrics", "tables")}, M)
    tables = orbit.get("tables", {})
    C = R["content"]
    out = article / "out"
    (out / "page").mkdir(parents=True, exist_ok=True)
    (out / "svg").mkdir(parents=True, exist_ok=True)

    svgs = {}
    for v in R.get("visuals", []):
        svgs[v["id"]] = V.render(v, tables)
        (out / "svg" / f"{v['id']}.svg").write_text(svgs[v["id"]])
        if v["type"] == "bars":
            (out / "svg" / f"{v['id']}-dark.svg").write_text(V.render(v, tables, dark=True))
    used_icons = {it["icon"] for it in (R.get("icon_list") or {}).get("items", [])}
    for name in used_icons:
        (out / "svg" / f"icon-{name}.svg").write_text(V.icon(name).replace('width="32" height="32" ', ""))

    def vis_block(after):
        html = ""
        for v in R.get("visuals", []):
            if v.get("after") == after:
                html += f"""
    <section class="vis" aria-labelledby="t-{v['id']}">
      <h3 id="t-{v['id']}">{escape(v['title'])}</h3>
      <p class="sub">{escape(v.get('subtitle', ''))}</p>
      {svgs[v['id']]}
    </section>"""
        return html

    figure = ""
    if R.get("figure"):
        from PIL import Image

        f = R["figure"]
        im = Image.open(article / f["file"]).convert("RGB")
        im.save(out / "page" / "figure.jpg", quality=82, optimize=True)
        figure = f"""
    <figure>
      <img src="figure.jpg" alt="{escape(f['alt'])}" width="{im.width}" height="{im.height}">
      <figcaption>{escape(f['caption'])}</figcaption>
    </figure>"""

    icon_list = ""
    if R.get("icon_list"):
        il = R["icon_list"]
        items = "".join(
            f'<li><span class="ico">{V.icon(it["icon"], 30)}</span><span><b>{escape(it["label"])}</b><span class="thr">{escape(it.get("detail", ""))}</span></span></li>'
            for it in il["items"]
        )
        icon_list = f'<ul class="radiomic" aria-label="{escape(il.get("title", "Key factors"))}">{items}</ul>'

    sidebar = ""
    for c in R["sidebar"]:
        if c["type"] == "counter":
            sidebar += counter_card(c)
        elif c["type"] == "chart":
            v = next(x for x in R["visuals"] if x["id"] == c["visual"])
            sidebar += f"""
      <div class="card">
        <p class="card-title">{escape(c['title'])}</p>
        <div class="chart">{V.render(v, tables, dark=True)}</div>
        <p class="card-cap small">{escape(c['caption'])}</p>
      </div>"""

    story = "".join(f"<p>{escape(p)}</p>" for p in C["story"])
    findings = "".join(f"<li><strong>{escape(f['label'])}:</strong> {escape(f['text'])}</li>" for f in C["key_findings"])
    tags = "".join(f'<span class="badge">{escape(t)}</span>' for t in R["tags"])
    evidence = "".join(
        f"<tr><td class='num'>{escape(m['value'])}</td><td>{escape(m['section'])}</td><td class='q'>“{escape(m['quote'])}”</td></tr>"
        for m in orbit["metrics"]
    )
    n_rows = sum(len(t["rows"]) for t in tables.values())
    today = datetime.date.today().strftime("%B %-d, %Y")
    svg_list = "".join(f"<code>{p.name}</code>" for p in sorted((out / "svg").glob("*.svg")))
    wide_preview = svgs.get((R.get("cards") or {}).get("wide_visual", ""), "")

    css = (SKILL / "templates" / "page.css").read_text()
    page = f"""<title>{escape(R.get('page_name', R['title']))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap">
<style>
{css}
</style>

<div class="ribbon"><div class="wrap">
  <span><b>Draft preview</b>&nbsp; Built in the Axis ORbits format for internal medical and regulatory review. Not an official Advita publication.</span>
  <span>Generated from <code>orbit.json</code> · {len(orbit['metrics'])} numbers locked to the source</span>
</div></div>

<header class="top wrap">
  <span class="back">Return to Axis ORbits</span>
  <div class="wordmark" aria-label="Axis ORbits"><span class="axis">Axis</span><span class="orbits">ORbits</span></div>
  <p class="date">Draft prepared on {today} · not yet published</p>
  <h1>{escape(R['title'])}</h1>
  <div class="badges">{tags}</div>
  <hr class="rule">
</header>

<div class="wrap grid">
  <main>
    <h2>Study Question</h2>
    <p class="lead">{escape(C['study_question'])}</p>

    <h2>The Story</h2>
    {story}{figure}
    {icon_list}{vis_block('story')}

    <h2>Key Findings</h2>
    <ul class="findings">{findings}</ul>
    {vis_block('key_findings')}

    <h2>Clinical Context</h2>
    <p>{escape(C['clinical_context'])}</p>
    {vis_block('clinical_context')}

    <h2>Limitations</h2>
    <p>{escape(C['limitations'])}</p>
    {vis_block('limitations')}

    <div class="video">
      <video controls muted playsinline preload="metadata" poster="video-poster.jpg" src="orbit-video-16x9.mp4" aria-label="Animated summary of the key results, no sound"></video>
    </div>

    <p class="ref"><strong>Reference for this study:</strong> {escape(C['reference'])}</p>
    <p class="closing">The Advita multicenter Axis research group efforts make these generalizable findings possible.</p>
  </main>

  <aside aria-label="Key metrics"><div class="stick">{sidebar}
  </div></aside>
</div>

<section class="kit"><div class="wrap">
  <h2>Media kit</h2>
  <p class="intro">Everything below is generated from the same locked data file as the article. Nothing here is drawn by an image model: charts are plotted to scale from the source tables, and icons come from a fixed geometric set.</p>
  <div class="kit-grid">
    <div class="tile">
      <video controls muted playsinline preload="metadata" poster="share-1080.png" src="orbit-video-1x1.mp4" aria-label="Square animated summary, no sound"></video>
      <h4>Animated summary · 1080 × 1080</h4>
      <p>Square cut for LinkedIn and Instagram feeds. Silent, all text on screen. The 16:9 cut is in the article above.</p>
    </div>
    <div class="tile">
      <img src="share-1200x630.png" alt="Link preview card" width="1200" height="630">
      <h4>Share card · 1200 × 630</h4>
      <p>Link preview for LinkedIn, X and email.</p>
    </div>
    <div class="tile">
      <img src="share-1080.png" alt="Square card with the key result" width="1080" height="1080">
      <h4>Square card · 1080 × 1080</h4>
      <p>Single-number post for social feeds and slides.</p>
    </div>
    <div class="tile">
      <div class="chart">{wide_preview}</div>
      <h4>Standalone SVGs</h4>
      <p>Each visual is also exported as its own SVG for slides and posters.</p>
      <div class="svgs">{svg_list}</div>
    </div>
  </div>

  <div class="evidence">
    <h2>Evidence check <span class="ok">All {len(orbit['metrics'])} pass</span></h2>
    <p class="intro">Each number on this page and in the video, next to the exact sentence it comes from in the source. A script fails the build if any quote is missing from the source or any value is missing from its quote. {n_rows} table rows used in charts are checked the same way.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Value</th><th>Where</th><th>Source text</th></tr></thead>
      <tbody>{evidence}</tbody>
    </table></div>
  </div>
</div></section>

<footer><div class="wrap">Draft for internal review · Axis ORbits format · source: “{escape(orbit['paper_title'])}”</div></footer>

<script>
{(SKILL / "templates" / "page.js").read_text()}
</script>
"""
    (out / "page" / "index.html").write_text(page)
    print(f"page: {out / 'page' / 'index.html'} · {len(list((out / 'svg').glob('*.svg')))} SVGs")


if __name__ == "__main__":
    main()
