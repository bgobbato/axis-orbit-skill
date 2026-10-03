# Visual library and orbit.json schema

A full working example is `references/orbit-example.json` (instability risk score paper). Copy its shape.

## Budget per article

- Sidebar: 2–4 cards (`counter` or `chart`).
- In-flow visuals: 1–3, each placed `after` a section: `story`, `key_findings`, `clinical_context` or `limitations`.
- Video: 2–3 visual scenes, plus the fixed title, population and citation scenes. Total about 25–35 s.
- Hero numbers (`hero_metric_ids`): 3 at most.

## Decision rule: result type → visual

Go down the list and take the first that fits the paper's main result.

| Paper reports | Visual | Notes |
|---|---|---|
| Two arms compared on one outcome | `vs` | Arm of interest is `a` (healthygreen). Comparator is `b` (trustturquoise). |
| A score or measure with cut-offs that sort patients into tiers | `zones` | One bar per tier on one rate scale. Stats line 1 bold (odds ratio), line 2 muted (share of patients). |
| Risk climbing as factors are added (rate per combination) | `steps` | 2–4 steps. `callout` only for a ratio the paper reports. Never compute the ratio from the steps. |
| A rate across many ordered groups (table) | `bars` | Uses a `tables` entry; every row has its own quote. Also works as a dark sidebar chart. |
| Several cohorts on one effect measure (OR, HR, score) | `hbars` | Optional `change` per row, only if the paper prints it. |
| One headline rate or count | sidebar `counter` | freshgreen for rates, trustturquoise for ratios (`x`). |
| Zero events | sidebar `counter` with value `0` | Caption "Cases of …" + n and time point. |
| Qualitative factors or named measures | `icon_list` | 3–8 items, geometric icons, `detail` copied from one list quote. |

## Visual specs

All string fields may use `{metric_id}` placeholders. Numeric layout fields (`domain`, `ticks`, `scale_max`, `grid`, `x_max`, `y_max`, `from`, `to`) are plain numbers.

```json
{"id": "threshold", "type": "zones", "after": "key_findings",
 "title": "...", "subtitle": "...",
 "domain": [0, 1], "ticks": [0, 0.3, 0.6, 1], "scale_max": 6, "grid": [2, 4, 6], "unit": "%",
 "bar_label": "Instability rate", "axis_label": "Instability risk score",
 "zones": [{"label": "Low risk", "from": 0, "to": 0.3, "color": "freshgreen", "value": "{low_rate}",
            "stats": ["Odds ratio {low_or}", "{low_share} of patients"], "accent": false}]}

{"id": "accumulation", "type": "bars", "table": "accumulation", "title": "...", "subtitle": "...",
 "y_max": 18, "grid": [5, 10, 15], "unit": "%", "highlight_from": 5, "label_every": ["0", "5", "10", "13+"],
 "x_label": "Number of risk factors"}

{"id": "modifiable", "type": "hbars", "title": "...", "x_max": 10, "grid": [2, 4, 6, 8, 10], "x_label": "...",
 "rows": [{"label": "+ Subscapularis repair\n+ GPS navigation", "value": "{t5_gps_subscap}", "change": "{c_gps_subscap}", "color": "trustturquoise"}]}

{"id": "notching", "type": "vs", "title": "...", "outcome": "Scapular notching",
 "a": {"label": "Augmented\nbaseplate", "value": "{notch_aug}"}, "b": {"label": "Bone graft", "value": "{notch_graft}"}}

{"id": "stacked", "type": "steps", "title": "...",
 "steps": [{"label": "Female", "value": "{fx_female}"}, {"label": "Female + RA", "value": "{fx_female_ra}"}],
 "callout": {"value": "{fx_or_all3}x", "caption": "with all three risk factors"}}
```

Pick `scale_max` / `x_max` / `y_max` just above the largest value so bars use the space. One scale per chart, starting at zero.

## Colors

| Token | Use |
|---|---|
| healthygreen `#39B54A` | structure, badges, arm of interest, "best" row |
| freshgreen `#8DC63F` | headline numbers on dark cards, low tier, highlighted bars |
| trustturquoise `#00A79D` | ratios, comparator, middle tier, change labels |
| seafoam `#74C7A7` | muted bars (below highlight) |
| strengthblue `#003C4C` | high tier, card backgrounds, headings |

Never red, never orange/yellow, no gradients, no shadows on charts.

## Icons

Fixed geometric set in `scripts/visuals.py` (`ICONS`): elongation, flatness, volume, axis, surface, score, patient, clock, chart-up, chart-down, check, zero, rom-arc, navigation, repair. 32×32 grid, stroke 2, round caps, `currentColor`, no fill. If none fits, add one new icon that follows the same rules and list it in the final report so a designer can review it. Never draw anatomy, never use image models, never use stock art.

## Where each visual appears

| Visual | Page (SVG) | Video scene | Deck slide |
|---|---|---|---|
| `zones` | yes | yes | shapes to scale (see `deck.md`) |
| `bars` | yes, also dark sidebar card | yes, with callouts | native column chart + callouts |
| `hbars` | yes | yes, dark, with punch | native bar chart + change column + punch |
| `vs` | yes | yes | native column chart |
| `steps` | yes | yes | native column chart + callout |

## Video overrides

`video.scenes` lists visual ids. `video.overrides.<id>` replaces fields for the video only (shorter titles, `foot` with the source table, `callouts` for `bars`: `[{"row": 13, "text": "{rate_13rf}", "sub": "with 13 or more"}]`, `punch` for `hbars`: `{"pre": "Up to", "value": "{x}", "post": "lower odds"}`, `theme: "light"` for a light `hbars` scene).

## Anti-slop checklist (check the contact sheet and page screenshot)

- Every number visible traces to the evidence table.
- One accent per scene; backgrounds only white or strengthblue.
- Motion: fades and slides ≤ 0.4 s ease-out, count-ups 2 s, bar growth 0.6–0.8 s. No bounce, zoom, particles, glow, 3D, blur.
- Silent video, all text on screen, citation scene last.
- No text smaller than 1.8vmin in the video; nothing clipped or overlapping.
- No AI images, no stock photos, no generated anatomy. Only paper figures and the geometric icon set.
