"""Extract a paper (PDF or DOCX) into an article folder.

  python3 extract.py <paper.pdf|paper.docx> <article_dir>

Writes:
  <article_dir>/source.md   plain text; tables as "a | b | c" rows; PDF pages marked "<!-- page N -->"
  <article_dir>/media/      embedded figures (image1.png, image2.png, ...)
Quotes in orbit.json must be copied from source.md.
"""
import sys
import zipfile
from pathlib import Path


def from_docx(src, out):
    import docx
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    d = docx.Document(src)
    blocks = []
    for el in d.element.body.iterchildren():
        if el.tag == qn("w:p"):
            t = Paragraph(el, d).text.strip()
            if t:
                blocks.append(t)
        elif el.tag == qn("w:tbl"):
            rows = ["[TABLE]"]
            for r in Table(el, d).rows:
                cells, seen = [], set()
                for c in r.cells:
                    if id(c._tc) in seen:  # horizontally merged cell repeats the same _tc
                        continue
                    seen.add(id(c._tc))
                    cells.append(c.text.strip().replace("\n", " "))
                rows.append(" | ".join(cells))
            rows.append("[/TABLE]")
            blocks.append("\n".join(rows))
    (out / "source.md").write_text("\n\n".join(blocks))

    media = out / "media"
    media.mkdir(exist_ok=True)
    n = 0
    with zipfile.ZipFile(src) as z:
        for name in sorted(z.namelist()):
            if name.startswith("word/media/"):
                n += 1
                (media / Path(name).name).write_bytes(z.read(name))
    return n


def from_pdf(src, out):
    import fitz

    doc = fitz.open(src)
    parts = []
    media = out / "media"
    media.mkdir(exist_ok=True)
    n = 0
    for i, page in enumerate(doc, 1):
        parts.append(f"<!-- page {i} -->\n{page.get_text('text').strip()}")
        for img in page.get_images(full=True):
            pix = fitz.Pixmap(doc, img[0])
            if pix.width < 300 or pix.height < 150:  # skip logos and glyphs
                continue
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            n += 1
            pix.save(str(media / f"p{i:02d}-image{n}.png"))
    (out / "source.md").write_text("\n\n".join(parts))
    return n


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower()
    if ext == ".docx":
        n = from_docx(src, out)
    elif ext == ".pdf":
        n = from_pdf(src, out)
    else:
        sys.exit(f"unsupported file type: {ext} (use .pdf or .docx)")
    words = len((out / "source.md").read_text().split())
    print(f"source.md: {words} words · media: {n} images · {out}")


if __name__ == "__main__":
    main()
