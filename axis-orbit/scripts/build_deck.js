// Build an Axis ORbits PowerPoint deck from out/deck/deck-data.json (written by deck_data.py).
//
//   node build_deck.js <article_dir>
//
// Writes out/deck/<slug>.pptx (raw, before finish_deck.py adds theme, transitions and animations)
// and out/deck/anim.json (which named shapes animate, in which order, with which effect).
// Every number comes from deck-data.json, which comes from the locked metrics in orbit.json.

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const article = path.resolve(process.argv[2]);
const D = JSON.parse(fs.readFileSync(path.join(article, "out/deck/deck-data.json"), "utf8"));

// Brand tokens (references/design-tokens.json). Hex without '#', as pptxgenjs requires.
const K = {
  healthygreen: "39B54A", freshgreen: "8DC63F", trustturquoise: "00A79D", seafoam: "74C7A7",
  strengthblue: "003C4C", balanceblue: "00596D", darkgreen: "277E33", link: "00857D",
  text: "000607", faded: "545A66", border: "E1E5E8", alt: "F2F3F5", white: "FFFFFF",
};
const hex = (name) => K[name] || name;
const W = 13.333, M = 0.6, CW = W - 2 * M; // LAYOUT_WIDE, margins, content width
const FONT_CHART = "+mn-lt"; // theme body font (Open Sans) for chart text

const num = (s) => { const m = String(s).replace(/−/g, "-").replace(/,/g, "").match(/-?\d+(?:\.\d+)?/); return m ? parseFloat(m[0]) : 0; };
const decimals = (s) => ((String(s).match(/\.(\d+)/) || [, ""])[1]).length;
const unitOf = (s) => String(s).replace(/^[−\-+]?[\d,]*\.?\d+/, "");
// Number format that prints each value exactly as the paper does (same decimals, same unit).
const fmtCode = (values) => {
  const ds = values.map(decimals), u = unitOf(values[0]).replace(/"/g, "");
  const base = Math.min(...ds) === Math.max(...ds) ? (ds[0] ? "0." + "0".repeat(ds[0]) : "0") : "General";
  return base + (u ? `"${u}"` : "");
};

async function iconPng(name, color, px = 256) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="${px}" height="${px}" fill="none" stroke="#${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${D.icons[name]}</svg>`;
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = D.title;
pres.subject = D.paper_title;
pres.author = "Axis ORbits draft";
pres.theme = { headFontFace: "Open Sans", bodyFontFace: "Open Sans" };

// ---------- Layouts (one per frame; footer, wordmark and slide number live here) ----------
function footer(dark) {
  const fg = dark ? K.white : K.strengthblue, muted = dark ? "9FB7BE" : K.faded;
  return [
    { text: { text: "Axis", options: { x: M, y: 6.92, w: 0.5, h: 0.3, fontSize: 12, bold: true, color: fg, margin: 0, valign: "middle" } } },
    { rect: { x: M + 0.5, y: 6.94, w: 0.74, h: 0.26, fill: { color: dark ? K.white : K.strengthblue }, rectRadius: 0.13 } },
    { text: { text: "ORbits", options: { x: M + 0.5, y: 6.94, w: 0.74, h: 0.26, fontSize: 10, italic: true, bold: true, color: dark ? K.strengthblue : K.white, align: "center", valign: "middle", margin: 0 } } },
    { text: { text: "Draft for internal review · not an official Advita publication", options: { x: M + 1.45, y: 6.92, w: 8, h: 0.3, fontSize: 9, color: muted, margin: 0, valign: "middle" } } },
  ];
}
function layout(name, dark, withTitle) {
  const objects = footer(dark);
  objects.push({ placeholder: { options: { name: "eyebrow", type: "body", x: M, y: 0.42, w: CW, h: 0.34, fontSize: 12, bold: true, charSpacing: 2, color: dark ? K.freshgreen : K.healthygreen, align: "left", margin: 0, valign: "top" }, text: "" } });
  if (withTitle) objects.push({ placeholder: { options: { name: "title", type: "title", x: M, y: 0.76, w: CW, h: 0.8, fontSize: 30, bold: true, color: dark ? K.white : K.strengthblue, align: "left", margin: 0, valign: "top" }, text: "" } });
  pres.defineSlideMaster({
    title: name, background: { color: dark ? K.strengthblue : K.white }, objects,
    slideNumber: { x: W - M - 0.6, y: 6.92, w: 0.6, h: 0.3, fontSize: 9, color: dark ? "9FB7BE" : K.faded, align: "right" },
  });
}
layout("AXIS_LIGHT", false, true);
layout("AXIS_DARK", true, true);
layout("AXIS_COVER", true, false);
layout("AXIS_STATEMENT", false, false);

// ---------- helpers ----------
const ANIM = [];
let slideNo = 0, steps = null, nameSeq = 0;
function newSlide(master) {
  slideNo++; steps = []; ANIM.push({ slide: slideNo, steps });
  return pres.addSlide({ masterName: master });
}
function nm(base) { nameSeq++; return `${base}-${nameSeq}`; }
function step(...items) { steps.push(items.filter(Boolean)); }
const fade = (name) => ({ name, effect: "fade" });
const up = (name) => ({ name, effect: "wipeUp" });
const right = (name) => ({ name, effect: "wipeRight" });

function text(slide, str, o) {
  const name = nm(o.name || "text");
  slide.addText(str, { isTextBox: true, margin: 0, valign: "top", align: "left", fit: "none", ...o, objectName: name });
  return name;
}
// pptxgenjs does not name placeholder shapes, so finish_deck.py finds them by placeholder type.
function ph(slide, phName, str) {
  slide.addText(str, { placeholder: phName, align: "left" });
  return `ph:${phName}`;
}
async function iconCircle(slide, icon, x, y, d, circleColor, iconColor) {
  const name = nm("icon");
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: circleColor }, line: { color: circleColor }, objectName: name + "-c" });
  slide.addImage({ data: await iconPng(icon, iconColor), x: x + d * 0.22, y: y + d * 0.22, w: d * 0.56, h: d * 0.56, objectName: name });
  return [name + "-c", name];
}
const label = (s) => String(s).replace(/\n/g, " ");

// ---------- slide types ----------
const S = {};

S.title = async () => {
  const s = newSlide("AXIS_COVER");
  s.addNotes(`${D.content.study_question}\n\n${D.content.story.join("\n\n")}`);
  const eb = ph(s, "eyebrow", ["Axis ORbits", ...D.tags].join(" · ").toUpperCase());
  const t = text(s, D.title, { name: "cover-title", x: M, y: 1.2, w: 7.5, h: 2.7, fontSize: 38, bold: true, color: K.white });
  const sub = text(s, D.paper_title, { name: "cover-sub", x: M, y: 4.05, w: 7.5, h: 1.0, fontSize: 14, color: K.white, transparency: 20 });
  const au = text(s, D.authors, { name: "cover-authors", x: M, y: 5.1, w: 7.5, h: 0.7, fontSize: 11, color: K.white, transparency: 35 });
  const pill = nm("cover-note");
  s.addText(D.note, { isTextBox: true, x: M, y: 6.0, w: Math.min(0.09 * D.note.length + 0.6, 7.5), h: 0.36, shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.18, fill: { color: K.balanceblue }, fontSize: 10, bold: true, color: K.white, align: "center", valign: "middle", margin: 0, objectName: pill });
  step(fade(eb), fade(t)); step(fade(sub), fade(au), fade(pill));
  const counters = D.sidebar.filter((c) => c.type === "counter").slice(0, 3);
  const h = 1.5, gap = 0.25, y0 = 1.2;
  counters.forEach((c, i) => {
    const y = y0 + i * (h + gap), card = nm("hero-card");
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.75, y, w: W - M - 8.75, h, rectRadius: 0.15, fill: { color: K.balanceblue }, line: { color: K.balanceblue }, objectName: card });
    const runs = [];
    if (c.pre) runs.push({ text: c.pre + " ", options: { fontSize: 16, bold: true, color: K.white } });
    runs.push({ text: c.value, options: { fontSize: 36, bold: true, color: hex(c.color || "freshgreen") } });
    const v = text(s, runs, { name: "hero-value", x: 9.0, y: y + 0.12, w: W - M - 9.25, h: 0.7, valign: "middle" });
    const cap = text(s, c.caption, { name: "hero-cap", x: 9.0, y: y + 0.82, w: W - M - 9.25, h: 0.6, fontSize: 11, color: K.white });
    step(fade(card), fade(v), fade(cap));
  });
};

S.question = async () => {
  const s = newSlide("AXIS_STATEMENT");
  s.addNotes(D.content.story.join("\n\n"));
  const eb = ph(s, "eyebrow", "STUDY QUESTION");
  const q = text(s, D.content.study_question, { name: "question", x: M, y: 0.95, w: 11.4, h: 2.3, fontSize: 36, bold: true, color: K.strengthblue });
  const st = text(s, D.content.story[0], { name: "story", x: M, y: 3.55, w: 9.6, h: 1.9, fontSize: 18, color: K.text, lineSpacingMultiple: 1.15 });
  step(fade(eb), fade(q)); step(fade(st));
  let x = M; const pills = [];
  for (const t of D.tags) {
    const w = 0.11 * t.length + 0.6, n = nm("tag");
    s.addText(t.toUpperCase(), { isTextBox: true, x, y: 5.9, w, h: 0.38, shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.19, fill: { color: K.healthygreen }, fontSize: 10, bold: true, charSpacing: 1, color: K.strengthblue, align: "center", valign: "middle", margin: 0, objectName: n });
    pills.push(fade(n)); x += w + 0.15;
  }
  step(...pills);
};

S.population = async (cfg) => {
  const P = D.population, s = newSlide("AXIS_DARK");
  s.addNotes(D.content.story[1] || "");
  const eb = ph(s, "eyebrow", P.eyebrow.toUpperCase());
  const t = ph(s, "title", cfg.title || "Who was studied");
  step(fade(eb), fade(t));
  const icons = cfg.icons || ["patient", "volume", "chart-up"];
  const [c0, i0] = await iconCircle(s, icons[0], M, 2.0, 0.8, K.balanceblue, K.freshgreen);
  const big = text(s, P.big.value, { name: "pop-big", x: M, y: 2.95, w: 6.4, h: 1.5, fontSize: 96, bold: true, color: K.freshgreen, valign: "middle" });
  const cap = text(s, P.big.caption, { name: "pop-cap", x: M, y: 4.5, w: 6.4, h: 0.6, fontSize: 22, bold: true, color: K.white });
  step(fade(c0), fade(i0), fade(big), fade(cap));
  for (const [i, sm] of P.small.entries()) {
    const y = 2.0 + i * 2.0;
    const [c, ic] = await iconCircle(s, icons[i + 1] || "check", 7.6, y, 0.8, K.balanceblue, K.freshgreen);
    const v = text(s, sm.value, { name: "pop-small", x: 8.65, y: y - 0.1, w: W - M - 8.65, h: 0.9, fontSize: 48, bold: true, color: sm.accent ? K.freshgreen : K.white, valign: "middle" });
    const cp = text(s, sm.caption, { name: "pop-small-cap", x: 8.65, y: y + 0.8, w: W - M - 8.65, h: 0.7, fontSize: 14, color: K.white, transparency: 10 });
    step(fade(c), fade(ic), fade(v), fade(cp));
  }
  if (D.topic) {
    const tp = text(s, D.topic, { name: "pop-topic", x: M, y: 5.9, w: 6.4, h: 0.4, fontSize: 13, color: K.white, transparency: 35 });
    step(fade(tp));
  }
};

S.figure = async (cfg) => {
  const s = newSlide("AXIS_LIGHT"), IL = D.icon_list, F = D.figure;
  s.addNotes(F ? F.caption : "");
  const eb = ph(s, "eyebrow", (cfg.eyebrow || "Methods").toUpperCase());
  const t = ph(s, "title", cfg.title || (IL && IL.title) || "What was measured");
  step(fade(eb), fade(t));
  const listX = F ? 8.35 : M, listW = F ? W - M - 8.35 : CW;
  if (F) {
    const meta = await sharp(F.path).metadata(), fw = 7.4, fh = fw * meta.height / meta.width;
    const img = nm("figure");
    s.addImage({ path: F.path, x: M, y: 1.85, w: fw, h: fh, altText: F.alt, objectName: img });
    const cap = text(s, F.caption, { name: "figure-cap", x: M, y: 1.85 + fh + 0.15, w: fw, h: 1.0, fontSize: 11, color: K.faded });
    step(fade(img), fade(cap));
  }
  if (IL) {
    const cols = F ? 1 : 2, rows = Math.ceil(IL.items.length / cols), rh = Math.min(0.66, 4.6 / rows);
    const items = [];
    for (const [i, it] of IL.items.entries()) {
      const col = Math.floor(i / rows), x = listX + col * (listW / cols), y = 1.85 + (i % rows) * rh;
      const [c, ic] = await iconCircle(s, it.icon, x, y + 0.04, 0.44, "E8F5EA", K.healthygreen);
      const l = text(s, [{ text: it.label, options: { bold: true, color: K.strengthblue, breakLine: true } }, { text: it.detail || "", options: { bold: true, color: K.link } }],
        { name: "factor", x: x + 0.58, y, w: listW / cols - 0.65, h: rh - 0.04, fontSize: 12, valign: "middle" });
      items.push(fade(c), fade(ic), fade(l));
    }
    step(...items);
  }
};

S.visual = async (cfg) => {
  const v = D.visuals[cfg.visual];
  if (!v) throw new Error(`deck: unknown visual ${cfg.visual}`);
  await VIS[v.type](v, cfg);
};

const VIS = {};

VIS.bars = async (v, cfg) => {
  const s = newSlide("AXIS_LIGHT");
  s.addNotes(v.subtitle || "");
  const eb = ph(s, "eyebrow", (cfg.eyebrow || "Results").toUpperCase());
  const t = ph(s, "title", cfg.title || v.title);
  step(fade(eb), fade(t));
  const hl = v.highlight_from ?? v.rows.length;
  const ch = nm("chart");
  s.addChart(pres.charts.BAR, [{ name: v.title, labels: v.rows.map((r) => r.label), values: v.rows.map((r) => num(r.value)) }], {
    x: M, y: 1.75, w: 8.5, h: 4.55, barDir: "col", barGapWidthPct: 45,
    chartColors: v.rows.map((_, i) => (i >= hl ? K.freshgreen : K.seafoam)),
    valAxisMaxVal: v.y_max, valAxisMinVal: 0, valAxisMajorUnit: (v.grid && v.grid[0]) || undefined,
    valAxisLabelFormatCode: `0"${v.unit || ""}"`, valAxisLabelColor: K.faded, valAxisLabelFontSize: 11, valAxisLabelFontFace: FONT_CHART,
    catAxisLabelColor: K.faded, catAxisLabelFontSize: 11, catAxisLabelFontFace: FONT_CHART,
    valGridLine: { color: K.border, size: 0.75 }, catGridLine: { style: "none" }, valAxisLineShow: false,
    showCatAxisTitle: !!v.x_label, catAxisTitle: v.x_label || "", catAxisTitleFontSize: 11, catAxisTitleColor: K.faded, catAxisTitleFontFace: FONT_CHART,
    showLegend: false, showTitle: false, showValue: false, objectName: ch,
  });
  step(up(ch));
  (v.callouts || []).forEach((c, i) => {
    const y = 2.0 + i * 1.7;
    const val = text(s, c.text, { name: "callout", x: 9.6, y, w: W - M - 9.6, h: 0.8, fontSize: 40, bold: true, color: i === (v.callouts.length - 1) ? K.healthygreen : K.strengthblue, valign: "middle" });
    const sub = text(s, c.sub || "", { name: "callout-sub", x: 9.6, y: y + 0.8, w: W - M - 9.6, h: 0.5, fontSize: 14, color: K.faded });
    step(fade(val), fade(sub));
  });
  for (const [i, sd] of (cfg.side || []).entries()) {
    const n = text(s, sd, { name: "side", x: 9.6, y: 2.0 + (v.callouts || []).length * 1.7 + i * 0.6, w: W - M - 9.6, h: 0.55, fontSize: 13, color: K.text });
    step(fade(n));
  }
  if (v.subtitle) { const c = text(s, v.subtitle, { name: "chart-caption", x: M, y: 6.38, w: 8.5, h: 0.35, fontSize: 11, color: K.faded }); step(fade(c)); }
};

VIS.zones = async (v, cfg) => {
  const s = newSlide("AXIS_LIGHT");
  s.addNotes(v.subtitle || "");
  const eb = ph(s, "eyebrow", (cfg.eyebrow || "Results").toUpperCase());
  const t = ph(s, "title", cfg.title || v.title);
  step(fade(eb), fade(t));
  const [d0, d1] = v.domain || [0, 1], X0 = M + 0.5, X1 = W - M - 0.2, sx = (x) => X0 + (X1 - X0) * (x - d0) / (d1 - d0);
  const base = 5.0, hmax = 2.3;
  const band = [];
  for (const z of v.zones) {
    const n = nm("band"); band.push(right(n));
    s.addShape(pres.shapes.RECTANGLE, { x: sx(z.from), y: base + 0.04, w: sx(z.to) - sx(z.from), h: 0.2, fill: { color: hex(z.color) }, line: { color: hex(z.color), width: 0 }, objectName: n });
  }
  const ticks = (v.ticks || []).map((tk) => text(s, tk === 1 ? "1.0" : String(tk), { name: "tick", x: sx(tk) - 0.3, y: base + 0.3, w: 0.6, h: 0.3, fontSize: 12, bold: true, color: K.strengthblue, align: "center" }));
  const tkSorted = [...(v.ticks || [d0, d1])].sort((a, b) => a - b), mid = (d0 + d1) / 2;
  const gap = tkSorted.map((a, i) => [a, tkSorted[i + 1]]).find(([a, b]) => b !== undefined && a <= mid && mid <= b) || [d0, d1];
  const ax = v.axis_label ? text(s, v.axis_label, { name: "axis", x: sx(gap[0]) + 0.35, y: base + 0.3, w: sx(gap[1]) - sx(gap[0]) - 0.7, h: 0.3, fontSize: 11, color: K.faded, align: "center" }) : null;
  step(...band, ...ticks.map(fade), ax && fade(ax));
  for (const z of v.zones) {
    const cx = (sx(z.from) + sx(z.to)) / 2, col = hex(z.color), h = Math.max(hmax * num(z.value) / v.scale_max, 0.05);
    const zl = text(s, z.label.toUpperCase(), { name: "zone-label", x: cx - 1.6, y: 1.85, w: 3.2, h: 0.35, fontSize: 13, bold: true, charSpacing: 1, color: col, align: "center" });
    const bar = nm("zone-bar");
    s.addShape(pres.shapes.RECTANGLE, { x: cx - 0.55, y: base - h, w: 1.1, h, fill: { color: col }, line: { color: col, width: 0 }, objectName: bar });
    const val = text(s, z.value, { name: "zone-value", x: cx - 1.4, y: base - h - 0.72, w: 2.8, h: 0.65, fontSize: 32, bold: true, color: K.strengthblue, align: "center", valign: "bottom" });
    const st = text(s, [
      { text: z.stats?.[0] || "", options: { fontSize: 16, bold: true, color: z.accent ? K.trustturquoise : K.strengthblue, breakLine: true } },
      { text: z.stats?.[1] || "", options: { fontSize: 12, color: K.faded } },
    ], { name: "zone-stats", x: cx - 1.6, y: base + 0.75, w: 3.2, h: 0.8, align: "center" });
    step(fade(zl), up(bar), fade(val), fade(st));
  }
};

VIS.hbars = async (v, cfg) => {
  const dark = (cfg.theme || v.theme || "dark") !== "light";
  const s = newSlide(dark ? "AXIS_DARK" : "AXIS_LIGHT");
  s.addNotes(v.subtitle || "");
  const fg = dark ? K.white : K.strengthblue;
  const eb = ph(s, "eyebrow", (cfg.eyebrow || v.eyebrow || "Results").toUpperCase());
  const t = ph(s, "title", cfg.title || v.title);
  step(fade(eb), fade(t));
  const rows = v.rows, n = rows.length, cx = M, cy = 1.7, cw = 9.6, chh = 3.9, L = { x: 0.37, y: 0.03, w: 0.55, h: 0.88 };
  const colorOf = (c) => (dark && c === "strengthblue" ? K.white : hex(c || "trustturquoise"));
  const ch = nm("chart");
  s.addChart(pres.charts.BAR, [{ name: v.title, labels: rows.map((r) => label(r.label)), values: rows.map((r) => num(r.value)) }], {
    x: cx, y: cy, w: cw, h: chh, barDir: "bar", barGapWidthPct: 55, layout: L,
    chartColors: rows.map((r) => colorOf(r.color)), catAxisOrientation: "maxMin",
    valAxisMaxVal: v.x_max, valAxisMinVal: 0, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    catAxisLabelColor: fg, catAxisLabelFontSize: 13, catAxisLabelFontFace: FONT_CHART, catAxisLineShow: false,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: fg, dataLabelFontSize: 16, dataLabelFontBold: true, dataLabelFontFace: FONT_CHART,
    dataLabelFormatCode: fmtCode(rows.map((r) => r.value)), showLegend: false, showTitle: false, objectName: ch,
  });
  step(right(ch));
  const changes = [];
  if (rows.some((r) => r.change)) {
    const hx = cx + cw + 0.15;
    changes.push(fade(text(s, "Change in odds", { name: "change-head", x: hx, y: cy + chh * L.y - 0.32, w: 2.2, h: 0.3, fontSize: 11, bold: true, color: dark ? K.seafoam : K.faded })));
    rows.forEach((r, i) => {
      if (!r.change) return;
      const yc = cy + chh * (L.y + L.h * (i + 0.5) / n);
      changes.push(fade(text(s, r.change, { name: "change", x: hx, y: yc - 0.2, w: 2.2, h: 0.4, fontSize: 18, bold: true, color: dark ? K.seafoam : K.trustturquoise, valign: "middle" })));
    });
  }
  step(...changes);
  if (v.punch) {
    const p = text(s, [
      { text: (v.punch.pre || "") + " ", options: { color: fg } },
      { text: v.punch.value, options: { color: dark ? K.freshgreen : K.healthygreen } },
      { text: " " + (v.punch.post || ""), options: { color: fg } },
    ], { name: "punch", x: M, y: 5.85, w: CW, h: 0.7, fontSize: 28, bold: true, valign: "middle" });
    step(fade(p));
  }
};

async function columns(v, cfg, items, colors, calloutObj) {
  const s = newSlide("AXIS_LIGHT");
  s.addNotes(v.subtitle || "");
  const eb = ph(s, "eyebrow", (cfg.eyebrow || "Results").toUpperCase());
  const t = ph(s, "title", cfg.title || v.title);
  step(fade(eb), fade(t));
  const ch = nm("chart"), w = calloutObj ? 8.6 : CW;
  s.addChart(pres.charts.BAR, [{ name: v.title, labels: items.map((x) => label(x.label)), values: items.map((x) => num(x.value)) }], {
    x: M, y: 1.75, w, h: 4.6, barDir: "col", barGapWidthPct: 80, chartColors: colors,
    valAxisMinVal: 0, valAxisMaxVal: v.scale_max || undefined, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    catAxisLabelColor: K.strengthblue, catAxisLabelFontSize: 14, catAxisLabelFontFace: FONT_CHART,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: K.strengthblue, dataLabelFontSize: 24, dataLabelFontBold: true, dataLabelFontFace: FONT_CHART,
    dataLabelFormatCode: fmtCode(items.map((x) => x.value)), showLegend: false, showTitle: false, objectName: ch,
  });
  step(up(ch));
  if (calloutObj) {
    const val = text(s, calloutObj.value, { name: "callout", x: 9.6, y: 2.3, w: W - M - 9.6, h: 1.1, fontSize: 54, bold: true, color: K.trustturquoise, valign: "middle" });
    const cap = text(s, calloutObj.caption, { name: "callout-sub", x: 9.6, y: 3.45, w: W - M - 9.6, h: 0.8, fontSize: 15, color: K.faded });
    step(fade(val), fade(cap));
  }
}
VIS.vs = (v, cfg) => columns(v, { ...cfg, title: cfg.title || v.outcome || v.title }, [v.a, v.b], [K.healthygreen, K.trustturquoise]);
VIS.steps = (v, cfg) => columns(v, cfg, v.steps, v.steps.map((_, i) => [K.seafoam, K.trustturquoise, K.strengthblue, K.strengthblue][Math.min(i, 3)]), v.callout);

S.findings = async (cfg) => {
  const s = newSlide("AXIS_LIGHT");
  s.addNotes(D.content.key_findings.map((f) => `${f.label}: ${f.text}`).join("\n"));
  const eb = ph(s, "eyebrow", (cfg.eyebrow || "Results").toUpperCase());
  const t = ph(s, "title", cfg.title || "Key findings");
  step(fade(eb), fade(t));
  const kf = D.content.key_findings, rh = Math.min(1.0, 4.85 / kf.length);
  for (const [i, f] of kf.entries()) {
    const y = 1.8 + i * rh;
    const [c, ic] = await iconCircle(s, "check", M, y + 0.05, 0.46, "E8F5EA", K.healthygreen);
    const tx = text(s, [{ text: f.label + ": ", options: { bold: true, color: K.strengthblue } }, { text: f.text, options: { color: K.text } }],
      { name: "finding", x: M + 0.7, y, w: CW - 0.7, h: rh - 0.08, fontSize: 15, valign: "top", lineSpacingMultiple: 1.05 });
    step(fade(c), fade(ic), fade(tx));
  }
};

S.context = async (cfg) => {
  const s = newSlide("AXIS_LIGHT");
  s.addNotes(`${D.content.clinical_context}\n\nLimitations: ${D.content.limitations}`);
  const eb = ph(s, "eyebrow", (cfg.eyebrow || "Clinical context").toUpperCase());
  const t = ph(s, "title", cfg.title || "What this means for surgeons");
  step(fade(eb), fade(t));
  const cx = text(s, D.content.clinical_context, { name: "context", x: M, y: 1.85, w: 7.3, h: 4.3, fontSize: 20, color: K.strengthblue, lineSpacingMultiple: 1.2 });
  step(fade(cx));
  const card = nm("limits-card");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.3, y: 1.85, w: W - M - 8.3, h: 2.9, rectRadius: 0.15, fill: { color: K.alt }, line: { color: K.alt }, objectName: card });
  const lt = text(s, [{ text: "Limitations", options: { bold: true, fontSize: 16, color: K.strengthblue, breakLine: true } }, { text: " ", options: { fontSize: 8, breakLine: true } }, { text: D.content.limitations, options: { fontSize: 14, color: K.text } }],
    { name: "limits", x: 8.6, y: 2.15, w: W - M - 8.9, h: 2.4 });
  step(fade(card), fade(lt));
};

S.reference = async (cfg) => {
  const s = newSlide("AXIS_DARK");
  s.addNotes(D.content.reference);
  const eb = ph(s, "eyebrow", "REFERENCE FOR THIS STUDY");
  const t = ph(s, "title", cfg.title || "Read the full study");
  step(fade(eb), fade(t));
  const pt = text(s, D.paper_title, { name: "ref-title", x: M, y: 1.85, w: 11.5, h: 1.3, fontSize: 24, bold: true, color: K.white });
  const ref = text(s, D.content.reference, { name: "ref", x: M, y: 3.3, w: 11.5, h: 1.3, fontSize: 13, color: K.white, transparency: 25 });
  step(fade(pt), fade(ref));
  const cl = text(s, "The Advita multicenter Axis research group efforts make these generalizable findings possible.", { name: "closing", x: M, y: 5.2, w: 11.5, h: 0.8, fontSize: 18, bold: true, color: K.freshgreen });
  step(fade(cl));
};

(async () => {
  for (const cfg of D.slides) {
    if (!S[cfg.type]) throw new Error(`deck: unknown slide type ${cfg.type}`);
    await S[cfg.type](cfg);
  }
  const raw = path.join(article, "out/deck", `${D.slug}.raw.pptx`);
  await pres.writeFile({ fileName: raw });
  fs.writeFileSync(path.join(article, "out/deck/anim.json"), JSON.stringify({ mode: D.animation, slides: ANIM }, null, 1));
  console.log(`deck: ${raw} · ${slideNo} slides`);
})().catch((e) => { console.error(e.message); process.exit(1); });
