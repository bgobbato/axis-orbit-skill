---
name: axis-orbit
description: Turn a scientific paper or manuscript (PDF or DOCX) from the Advita Axis shoulder research group into an Axis ORbits draft — summary page (Study Question, The Story, Key Findings, Clinical Context, Limitations, Reference), on-brand SVG visuals, share cards and a short silent animated video, with every number locked to a verbatim quote — then publish it as a private artifact for review. Use when the user gives a paper and asks for an ORbit, an Axis summary, the "página, mídias e vídeo", or runs /axis-orbit.
---

# Axis ORbit

Input: one paper (`.pdf` or `.docx`). Output: a draft ORbit in `articles/<slug>/out/page/` plus a private artifact link. All output text is in **English**, even when the user writes in Portuguese. Talk to the user in their language.

Paths below are relative to this skill folder (`.claude/skills/axis-orbit/`). Article folders live in the project at `articles/<slug>/`.

## Steps

### 1. Extract

```bash
python3 .claude/skills/axis-orbit/scripts/extract.py "<paper path>" articles/<slug>
```

`<slug>` is short kebab-case from the topic (e.g. `instability-risk-score`). This writes `source.md` (text, tables as `a | b | c` rows, PDF pages as `<!-- page N -->`) and `media/` (figures). Read all of `source.md`. Look at the figures in `media/`.

### 2. Write `articles/<slug>/orbit.json`

Read first: `references/orbit-example.json` (full working example), `references/writing-guide.md`, `references/visual-library.md`.

Order matters:
1. **`metrics` first.** For every number you will show anywhere, add `{"id", "value", "kind", "section", "quote"}`. `quote` is copied character for character from `source.md` and contains `value`. `section` is the paper section, table, or `p. N` for PDFs. Never compute a number. If the paper prints a change (for example `-58.8%`), make it its own metric.
2. **`tables`** for chart series with many rows (one quote per row).
3. **`content`** with `{metric_id}` placeholders for every result number. Cut-offs that define the study go in `definitions`.
4. **Visuals** by the decision rule in `references/visual-library.md`; `sidebar` (2–4 cards); optional `figure` (a real paper figure from `media/`) and `icon_list`.
5. **`video`** (question lines, population scene, 2–3 visual scenes, overrides) and **`cards`** (wide link preview, square single number).

### 3. Validate (hard gate)

```bash
python3 .claude/skills/axis-orbit/scripts/validate.py articles/<slug>
```

Fix every FAIL by correcting the quote or the placeholder, never by loosening the check. Read WARN lines and fix the text length if it reads too long or too thin.

### 4. Build and review

```bash
python3 .claude/skills/axis-orbit/scripts/run_all.py articles/<slug> --no-video
python3 .claude/skills/axis-orbit/scripts/render_video.py articles/<slug> --sample
```

Look at: a full-page screenshot of `out/page/index.html` (Playwright, 1280 wide), `out/page/share-*.png`, and `out/video/sheet-16x9.png` and `sheet-1x1.png`. Check against the anti-slop list in `references/visual-library.md`: overlaps, clipped text, numbers that do not match, scales that do not start at zero. Fix `orbit.json` (or a script, if it is a real bug) and rebuild once.

### 5. Render the video

```bash
python3 .claude/skills/axis-orbit/scripts/render_video.py articles/<slug>
```

About 1 minute. Writes `out/page/orbit-video-16x9.mp4`, `orbit-video-1x1.mp4`, `video-poster.jpg`.

### 6. Review notes for the authors

While locking numbers you will see places where the paper disagrees with itself (abstract vs results vs tables, typos in thresholds, wrong figure numbers, denominators that do not add up). Write them to `articles/<slug>/review-notes.md` as tables: where, issue, suggested fix. Use the values as printed on the page; do not "fix" numbers in the ORbit.

### 7. Publish the draft

Publish `articles/<slug>/out/page/index.html` with the Artifact tool, icon `chart`, a one-sentence description, and `files`:

```json
{"figure.jpg": "articles/<slug>/out/page/figure.jpg",
 "orbit-video-16x9.mp4": "articles/<slug>/out/page/orbit-video-16x9.mp4",
 "orbit-video-1x1.mp4": "articles/<slug>/out/page/orbit-video-1x1.mp4",
 "share-1200x630.png": "articles/<slug>/out/page/share-1200x630.png",
 "share-1080.png": "articles/<slug>/out/page/share-1080.png",
 "video-poster.jpg": "articles/<slug>/out/page/video-poster.jpg"}
```

Leave out `figure.jpg` when there is no figure. On a later change, publish the same file path again to keep the URL.

### 8. Report

Tell the user: the link; what is on the page; that all N numbers passed the evidence check; the main items in `review-notes.md`; any new icon you added; and that the link is private until they share it. Ask them to review before anything goes to Advita's site.

## Rules

- The page is a **draft**. Keep the "Draft preview · not an official Advita publication" ribbon. Do not use the Advita logo or claim publication.
- Never publish to advita.com or WordPress. Medical Affairs and Regulatory approve first.
- Never invent, round, convert or derive a number. If the result you want is not printed in the paper, do not show it.
- No AI-generated images, stock art or drawn anatomy. Only paper figures, charts from data, and the geometric icon set.
- Brand colors only (`references/design-tokens.json`). No red, no orange.
- Unpublished manuscripts are confidential: keep artifacts private and say so.
