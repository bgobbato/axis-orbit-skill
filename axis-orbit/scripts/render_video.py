"""Render the ORbit animation frame by frame (Playwright) and encode with ffmpeg.

  python3 render_video.py <article_dir> --sample   # contact sheets in out/video/ for review
  python3 render_video.py <article_dir>            # out/page/orbit-video-16x9.mp4, -1x1.mp4, video-poster.jpg
"""
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap

from playwright.sync_api import sync_playwright

from common import SKILL, load, resolve

FPS = 30
VARIANTS = {"16x9": (1920, 1080), "1x1": (1080, 1080)}


def scene_data(orbit, R):
    vid = R["video"]
    lines = vid.get("question_lines") or textwrap.wrap(R["content"]["study_question"], 44)
    assert " ".join(lines) == R["content"]["study_question"], "video.question_lines must join to content.study_question exactly"
    scenes = [{"type": "title", "lines": lines, "tags": R["tags"][:2], "foot": vid.get("topic", "")}]
    if vid.get("population"):
        scenes.append({"type": "population", **vid["population"]})
    vis = {v["id"]: v for v in R.get("visuals", [])}
    for vid_id in vid["scenes"]:
        v = dict(vis[vid_id])
        v.update(vid.get("overrides", {}).get(vid_id, {}))
        if v["type"] == "bars":
            v["rows"] = [{"label": r["label"], "value": r["value"]} for r in orbit["tables"][v["table"]]["rows"]]
        scenes.append(v)
    scenes.append({"type": "citation", "paper_title": R["paper_title"], "authors": R["authors"], "note": vid.get("note", "Draft for internal review")})
    return {"scenes": scenes}


def open_page(pw, html_path, size):
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": size[0], "height": size[1]})
    pg.goto(html_path.resolve().as_uri() + "?capture", wait_until="networkidle")
    pg.evaluate("window.READY")
    pg.wait_for_timeout(300)
    return b, pg


def main():
    article, orbit, M = load(sys.argv[1])
    R = resolve({k: v for k, v in orbit.items() if k not in ("metrics",)}, M)
    data = scene_data(orbit, R)
    out = article / "out"
    (out / "video").mkdir(parents=True, exist_ok=True)
    (out / "page").mkdir(parents=True, exist_ok=True)
    html_path = out / "video" / "video.html"
    html_path.write_text((SKILL / "templates" / "video.html").read_text().replace("/*DATA*/null", json.dumps(data)))

    with sync_playwright() as pw:
        if "--sample" in sys.argv:
            from PIL import Image

            for name, size in VARIANTS.items():
                b, pg = open_page(pw, html_path, size)
                shots = []
                for s0, s1 in pg.evaluate("window.SCENES"):
                    pg.evaluate(f"renderAt({s1 - 0.5})")
                    shots.append(Image.open(__import__("io").BytesIO(pg.screenshot())))
                b.close()
                cols = 2 if name == "16x9" else 3
                scale = 0.4 if name == "16x9" else 0.33
                tw, th = int(size[0] * scale), int(size[1] * scale)
                rows = (len(shots) + cols - 1) // cols
                sheet = Image.new("RGB", (cols * tw + 10 * (cols - 1), rows * th + 10 * (rows - 1)), "#888")
                for i, im in enumerate(shots):
                    sheet.paste(im.resize((tw, th)), ((i % cols) * (tw + 10), (i // cols) * (th + 10)))
                sheet.save(out / "video" / f"sheet-{name}.png")
            print(f"contact sheets: {out / 'video'}/sheet-16x9.png, sheet-1x1.png")
            return
        for name, size in VARIANTS.items():
            tmp = tempfile.mkdtemp()
            b, pg = open_page(pw, html_path, size)
            dur = pg.evaluate("window.DURATION")
            scenes = pg.evaluate("window.SCENES")
            poster_t = scenes[len(scenes) // 2][1] - 0.5  # end of a middle visual scene, all numbers settled
            for i in range(int(dur * FPS)):
                pg.evaluate(f"renderAt({i / FPS})")
                pg.screenshot(path=f"{tmp}/f{i:05d}.jpg", type="jpeg", quality=95)
            b.close()
            mp4 = out / "page" / f"orbit-video-{name}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%05d.jpg",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", "-movflags", "+faststart", str(mp4),
            ], check=True)
            if name == "16x9":
                shutil.copy(f"{tmp}/f{int(poster_t * FPS):05d}.jpg", out / "page" / "video-poster.jpg")
            shutil.rmtree(tmp)
            print(f"video: {mp4.name} · {dur:.1f} s · {mp4.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
