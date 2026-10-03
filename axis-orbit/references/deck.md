# PowerPoint deck

The skill builds a `.pptx` from the same `orbit.json` as the page and the video. Same design system, same locked numbers, same visuals, now as editable slides with native PowerPoint animations.

Output: `articles/<slug>/out/deck/<slug>.pptx`, plus `out/deck/preview.jpg` (contact sheet) and `out/deck/preview/slide-N.jpg`.

## Pipeline

```
orbit.json
  │ deck_data.py      resolve {metric_id} placeholders, attach table rows, pick the slide list → out/deck/deck-data.json
  │ build_deck.js     pptxgenjs: layouts, slides, native charts, icons, speaker notes → <slug>.raw.pptx + anim.json
  │ finish_deck.py    brand theme colors, fade transitions, entrance animations (<p:timing>) → <slug>.pptx
  │ preview_deck.py   LibreOffice → PDF → JPGs + contact sheet (visual QA; also shown in the page media kit)
```

`run_all.py` runs all four after `validate.py`. Use `--no-deck` to skip them.

Requirements: Node 18+ and `npm install` in the skill folder (installs `pptxgenjs` and `sharp`). LibreOffice is optional and only used for the preview.

## The `deck` block in orbit.json

```json
"deck": {
  "animation": "auto",
  "slides": [
    {"type": "title"},
    {"type": "question"},
    {"type": "population", "title": "Who was studied", "icons": ["patient", "volume", "chart-up"]},
    {"type": "figure", "eyebrow": "Methods", "title": "The seven radiomic risk factors"},
    {"type": "visual", "visual": "accumulation", "eyebrow": "Results"},
    {"type": "visual", "visual": "threshold", "eyebrow": "Results"},
    {"type": "visual", "visual": "modifiable"},
    {"type": "findings", "title": "Key findings"},
    {"type": "context", "title": "What this means for surgeons"},
    {"type": "reference", "title": "Read the full study"}
  ]
}
```

If `deck` is missing, `deck_data.py` builds this same sequence from what the orbit contains (it skips `population` without `video.population`, `figure` without `figure`/`icon_list`, and uses `video.scenes` for the visual slides). All strings may use `{metric_id}` placeholders and are checked by `validate.py` like every other field.

`animation`: `"auto"` plays each slide's build by itself after the slide appears (good for a kiosk, a recorded talk or a shared file). `"click"` makes each step wait for a click (good for a live talk).

## Slide types

| Type | Layout | Content | Build order |
|---|---|---|---|
| `title` | dark cover | eyebrow (`Axis ORbits · tags`), page title, paper title, authors, draft pill; up to 3 sidebar `counter` cards on the right | title → paper/authors → each card |
| `question` | light statement | "Study question" eyebrow, the question at 36 pt, first Story paragraph, tag pills | question → story → pills |
| `population` | dark | `video.population`: big number with icon, two smaller stats with icons, topic line | big stat → each small stat → topic |
| `figure` | light | paper figure (left) with caption, `icon_list` (right). Without a figure the list spans two columns | figure → list |
| `visual` | depends on visual type | one visual from `visuals[]`, see below | header → chart → labels |
| `findings` | light | each Key Finding as a row: green check icon, bold label, text | one row at a time |
| `context` | light | Clinical Context (20 pt) and a Limitations card | context → card |
| `reference` | dark | paper title, full reference, closing line | title → reference → closing line |

Optional fields on any slide: `eyebrow`, `title`. `population` also takes `icons` (3 names from the icon set). `visual` slides take `side` (extra one-line notes next to a `bars` chart).

Speaker notes are filled automatically: The Story on the title and question slides, the figure caption, the visual subtitle, all Key Findings, Clinical Context with Limitations, and the full reference.

## Visual types on slides

| Visual | Slide | How it is drawn | Animation |
|---|---|---|---|
| `bars` | light | **native column chart** (editable data), per-bar colors (seafoam below `highlight_from`, freshgreen from it), gridlines, axis title; `callouts` from `video.overrides.<id>.callouts` as big numbers on the right | chart wipes up, then each callout fades in |
| `zones` | light | **shapes** drawn to scale: score band split at the cut-offs, one bar per zone on one rate scale, tick labels, stats under each zone. A chart cannot place bars on an uneven score axis, so this one is shapes | band wipes right, then zone by zone: label, bar wipes up, value, stats |
| `hbars` | dark (or `"theme": "light"`) | **native bar chart**, rows top to bottom, data labels in the paper's decimals, a "Change in odds" column aligned to the rows, `punch` line | chart wipes right, change column, punch |
| `vs` | light | **native column chart**, arm A healthygreen, arm B trustturquoise, data labels | chart wipes up |
| `steps` | light | **native column chart** in rising shades, data labels, reported `callout` on the right | chart wipes up, callout |

For `hbars` the slide uses the video override (shorter title, eyebrow, `punch`, rows) when there is one.

Data labels print each value exactly as the paper does: `build_deck.js` writes a number format with the same decimals and unit (for example `0.00` for 9.08, 3.74; `General"%"` when decimals differ, such as 0.2%, 1.17%, 5.7%).

## Design system on slides

- Canvas 13.333 × 7.5 in (16:9 wide). Margins 0.6 in.
- Font: Open Sans (theme heading and body font). Chart text uses the theme font too (`+mn-lt`).
- Colors are the Advita tokens. `finish_deck.py` also writes them into the Office theme (`accent1` healthygreen, `accent2` freshgreen, `accent3` trustturquoise, `accent4` seafoam, `accent5` balanceblue, `accent6` darkgreen, `dk2` strengthblue, `lt2` #F2F3F5) so anything added in PowerPoint picks the brand palette.
- Four layouts: `AXIS_COVER` (dark, no title), `AXIS_STATEMENT` (light, no title), `AXIS_LIGHT` and `AXIS_DARK` (eyebrow + title placeholders). Every layout carries the footer: "Axis ORbits" wordmark, draft note, slide number.
- Eyebrow: 12 pt bold, letter-spaced caps, healthygreen (freshgreen on dark). Title: 30 pt bold, strengthblue (white on dark), left aligned.
- Big numbers 36–96 pt bold. Body 14–20 pt. Captions 11–12 pt `#545A66`.
- Icons: the same geometric set as the page (`scripts/visuals.py` `ICONS`), rasterized by `sharp`, inside a tinted circle (`#E8F5EA` on light, balanceblue on dark).
- Same bans as the page: no red or orange, no gradients, no accent bars under titles, no stock or AI images.

## Animations

pptxgenjs cannot write animations, so `build_deck.js` names every animated shape and records the build order in `anim.json`; `finish_deck.py` then writes standard PowerPoint XML into each slide:

- Slide transition: Fade, medium.
- Entrance effects (PowerPoint presets, editable in the Animation pane):

| Effect in anim.json | PowerPoint preset | Duration |
|---|---|---|
| `fade` | Fade | 0.45 s |
| `wipeUp` | Wipe, From Bottom | 0.75 s |
| `wipeRight` | Wipe, From Left | 0.75 s |

- Auto mode: steps start 0.55 s apart, items inside a step 0.07 s apart, all "With Previous" from slide start.
- Click mode: each step is one click; items inside a step run together.
- Placeholders (eyebrow, title) are found by placeholder type, because pptxgenjs does not name them.

PowerPoint has no number count-up, so numbers fade in instead of counting. LibreOffice previews do not play animations; check them in PowerPoint (Slide Show, or the Animation pane).

To add an effect: add a row to `EFFECTS` in `finish_deck.py` (preset id, subtype, filter, duration) and use its name in `build_deck.js`.

## Extending

- **New slide type:** add `S.<type> = async (cfg) => { … }` in `build_deck.js`. Start it with `newSlide(<layout>)`, place shapes with `text()`, `iconCircle()` or `addChart`, and call `step(...)` in build order. Add it to the table above and, if it should appear by default, to `default_slides()` in `deck_data.py`.
- **New visual type:** add the SVG in `visuals.py` (page), the scene in `templates/video.html` (video) and `VIS.<type>` in `build_deck.js` (deck). Document it in `visual-library.md` and here.
- Keep every number coming from `deck-data.json`; never type one into the builder.

## QA

1. `python3 scripts/preview_deck.py articles/<slug>` and look at `out/deck/preview.jpg`: text overflow, overlaps, labels that do not match the evidence table, titles at different heights.
2. If the Anthropic `pptx` skill is available, run its `scripts/office/validate.py` on the deck (needs Python 3.10+ with `defusedxml` and `lxml`).
3. Open the deck in PowerPoint once and play two slides to check the animations.
4. LibreOffice replaces Open Sans when the font is not installed, so the preview can show odd spacing and serif digits. Install Open Sans (Google Fonts) for a faithful preview. Users who open the deck without Open Sans see a substitute font.
