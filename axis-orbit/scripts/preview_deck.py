"""Render the finished deck to images for visual QA (LibreOffice + pdftoppm).

  python3 preview_deck.py <article_dir>

Writes out/deck/preview/slide-N.jpg, out/deck/preview.jpg (contact sheet) and
out/page/deck-preview.jpg (shown in the page's media kit). Skips with a warning if LibreOffice is missing.
LibreOffice does not play animations and substitutes Open Sans if it is not installed, so check
text fit with some slack and check animations in PowerPoint itself.
"""
import glob
import shutil
import subprocess
import sys

from common import load

SOFFICE = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def main():
    article, orbit, _ = load(sys.argv[1])
    deck = article / "out" / "deck" / f"{orbit['slug']}.pptx"
    prev = article / "out" / "deck" / "preview"
    if not shutil.which(SOFFICE) and not __import__("os").path.exists(SOFFICE):
        print("WARN LibreOffice not found; skipped deck preview")
        return
    shutil.rmtree(prev, ignore_errors=True)
    prev.mkdir(parents=True)
    subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(prev), str(deck)], check=True, capture_output=True)
    subprocess.run(["pdftoppm", "-jpeg", "-r", "90", str(prev / f"{orbit['slug']}.pdf"), str(prev / "slide")], check=True)
    from PIL import Image

    ims = [Image.open(f) for f in sorted(glob.glob(str(prev / "slide-*.jpg")))]
    tw = 640
    th = int(ims[0].height * tw / ims[0].width)
    cols, gap = 2, 12
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols - 1) * gap, rows * th + (rows - 1) * gap), "#e1e5e8")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th)), ((i % cols) * (tw + gap), (i // cols) * (th + gap)))
    sheet.save(article / "out" / "deck" / "preview.jpg", quality=85)
    (article / "out" / "page").mkdir(parents=True, exist_ok=True)
    sheet.save(article / "out" / "page" / "deck-preview.jpg", quality=82)
    print(f"deck preview: {article / 'out' / 'deck' / 'preview.jpg'} · {len(ims)} slides")


if __name__ == "__main__":
    main()
