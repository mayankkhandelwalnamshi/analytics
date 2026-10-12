const pptxgen = require("pptxgenjs");
const fs = require("fs");
const SK = "/root/.claude/skills/synced/cfb3e858-e963-4cfd-92e6-3623d7ec76ec_de2eebe3-e3f5-4ae2-b254-f5013fbcc9a6/pptx";
const { applyTheme } = require(SK + "/scripts/apply_theme.js");
const D = JSON.parse(fs.readFileSync("deck_data.json", "utf8"));
const CUT = D.cuts;

// ---------- theme ----------
const INK = "33373E", GREY = "6B7079", LIME = "B6ED2F", TYC = "7FA91E", LYC = "C9A0AE",
      RED = "C0392B", GRN = "2E7D32", AMB = "B26A00", CARD = "F6F7F2", LINE = "E3E5E8", WHITE = "FFFFFF";
const THEME = { name: "Namshi Beauty", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: INK, lt1: WHITE, dk2: "1F2226", lt2: CARD, accent1: TYC, accent2: LYC, accent3: LIME,
            accent4: RED, accent5: GRN, accent6: AMB, hlink: "2F6EBA", folHlink: "7F7F7F" } };
const pres = new pptxgen();
pres.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 }); pres.layout = "WIDE";
pres.theme = { headFontFace: "Calibri", bodyFontFace: "Calibri" };
pres.title = "Beauty performance review: September 2026";
const C = pres.SchemeColor;
const FOOT = "Namshi Beauty  |  September 2026 vs September 2025  |  Source: BigQuery sales_metrics + onsite_measures";

pres.defineSlideMaster({ title: "COVER", background: { color: INK },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 2.1, w: 8.5, h: 1.3, fontSize: 44, bold: true, color: WHITE, align: "left", valign: "bottom", margin: 0 }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 3.55, w: 8.5, h: 0.6, fontSize: 18, color: LIME, align: "left", margin: 0 }, text: "" } }] });
pres.defineSlideMaster({ title: "SECTION", background: { color: INK },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 2.8, w: 11.5, h: 1.2, fontSize: 40, bold: true, color: WHITE, margin: 0 }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 4.0, w: 11.5, h: 0.8, fontSize: 18, color: LIME, margin: 0 }, text: "" } }] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: WHITE }, margin: [0.5, 0.5, 0.6, 0.5],
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 24, bold: true, color: INK, align: "left", valign: "top", margin: 0 }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 1.27, w: 12.1, h: 0.4, fontSize: 13, italic: true, color: GREY, align: "left", margin: 0 }, text: "" } },
            { text: { text: FOOT, options: { x: 0.6, y: 7.05, w: 10.5, h: 0.3, fontSize: 9, color: "9AA0A8", margin: 0 } } }],
  slideNumber: { x: 12.3, y: 7.05, w: 0.5, h: 0.3, fontSize: 9, color: "9AA0A8", align: "right" } });

// ---------- helpers ----------
const M = v => (v / 1e6).toFixed(2) + "M", K = v => Math.round(v / 1e3).toLocaleString("en-US") + "K";
const N = v => Math.round(v).toLocaleString("en-US");
const MN = s => s.replace("-", "\u2212");
const pc = v => MN((v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%");
const pp = v => MN((v >= 0 ? "+" : "") + (v * 100).toFixed(2) + "\u00a0pp");
const pp1 = v => MN((v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "\u00a0pp");
const col = v => v >= 0 ? GRN : RED;
const g = (cut, per) => CUT[cut][per];
const yo = (cut, per, k) => g(cut, per).ty[k] / g(cut, per).ly[k] - 1;
const dl = (cut, per, k) => g(cut, per).ty[k] - g(cut, per).ly[k];
const PERS = ["1-18 Sep", "19-25 Sep", "26-30 Sep"], PLAB = { "1-18 Sep": "1–18 Sep", "19-25 Sep": "19–25 Sep", "26-30 Sep": "26–30 Sep", "Sept": "Full Sept" };
let sec = "";
function content(title, sub) { const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: sec });
  s.addText(title, { placeholder: "title" }); if (sub) s.addText(sub, { placeholder: "body" }); return s; }
function tx(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, margin: 0, fontSize: 14, color: INK, valign: "top" }, o)); }
function card(s, x, y, w, h, name) { s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: CARD }, line: { color: LINE, width: 1 }, objectName: name }); }
function legend(s, x, y) { s.addShape(pres.ShapeType.rect, { x, y: y + 0.07, w: 0.22, h: 0.16, fill: { color: TYC }, line: { type: "none" } });
  tx(s, "TY 2026", { x: x + 0.3, y, w: 0.9, h: 0.3, fontSize: 11, color: GREY });
  s.addShape(pres.ShapeType.rect, { x: x + 1.2, y: y + 0.07, w: 0.22, h: 0.16, fill: { color: LYC }, line: { type: "none" } });
  tx(s, "LY 2025", { x: x + 1.5, y, w: 0.9, h: 0.3, fontSize: 11, color: GREY }); }
const chartBase = () => ({ catAxisLabelColor: GREY, valAxisLabelColor: GREY, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, valGridLine: { color: "E6E6E6", size: 0.5 }, catGridLine: { style: "none" },
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, dataLabelColor: INK, titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: INK, legendFontFace: "+mn-lt" });
function hc(t, al) { return { text: t, options: { bold: true, color: WHITE, fill: { color: INK }, align: al || "center", valign: "middle", fontSize: 11 } }; }
function c(t, o) { return { text: t, options: Object.assign({ color: INK, align: "right", valign: "middle", fontSize: 11 }, o || {}) }; }
const dcell = (v, f, fill) => c(f(v), { color: col(v), bold: true, fill: fill ? { color: fill } : undefined });
const mcell = (v, fill) => c(pp1(v), { color: AMB, bold: true, fill: fill ? { color: fill } : undefined });

const O = g("Overall", "Sept");
// ================= 1. COVER =================
sec = "Cover"; pres.addSection({ title: sec });
{ const s = pres.addSlide({ masterName: "COVER", sectionTitle: sec });
  s.addText("Beauty performance review", { placeholder: "title" });
  s.addText("September 2026 vs LY  ·  October MTD to follow", { placeholder: "body" });
  const k = [[M(O.ty.gmv) + " AED", "GMV", pc(yo("Overall", "Sept", "gmv")) + " vs LY"], [(O.ty.ucr * 100).toFixed(2) + "%", "UCR (units ÷ GVs)", pp(dl("Overall", "Sept", "ucr")) + " vs LY"],
             [(O.ty.gv / 1e6).toFixed(2) + "M", "Glance views", pc(yo("Overall", "Sept", "gv")) + " vs LY"], [(O.ty.mkd * 100).toFixed(1) + "%", "Markdown", pp1(dl("Overall", "Sept", "mkd")) + " vs LY"]];
  k.forEach((r, i) => { const x = 0.7 + i * 2.9;
    tx(s, r[0], { x, y: 5.2, w: 2.7, h: 0.6, fontSize: 30, bold: true, color: WHITE });
    tx(s, r[1], { x, y: 5.8, w: 2.7, h: 0.3, fontSize: 12, color: "C8CCD2" });
    tx(s, r[2], { x, y: 6.1, w: 2.7, h: 0.3, fontSize: 13, bold: true, color: i == 3 ? "F5C26B" : "FF9AA2" }); });
  tx(s, "namshi beauty", { x: 9.6, y: 0.6, w: 3.2, h: 0.5, fontSize: 22, bold: true, color: LIME, align: "right" });
  s.addNotes("Scope: Namshi marketplaces (namshi, namshi_v2), Beauty business unit, samples & GWP excluded, GMV incl. VAT. LY = same calendar dates in 2025.");
}

// ================= 2. EXEC SUMMARY =================
sec = "September 2026"; pres.addSection({ title: sec });
{ const s = content("September GMV fell 28% vs LY; weaker conversion explains most of the gap",
    "GMV bridge, LY to TY (AED): GMV = glance views × conversion (units per GV) × ASP");
  // waterfall drawn with shapes
  const d = O.drv, L = O.ly.gmv, T = O.ty.gmv;
  const steps = [["LY Sept", L, 0, INK], ["Traffic\n(GVs)", d.traffic, 1], ["Conversion\n(UCR)", d.conv, 1], ["Price\n(ASP)", d.price, 1], ["TY Sept", T, 0, TYC]];
  const x0 = 0.8, base = 6.25, top = 2.1, maxV = 9.5e6, sc = (base - top) / maxV, bw = 0.85, gap = 0.35;
  s.addShape(pres.ShapeType.line, { x: x0 - 0.1, y: base, w: 5 * (bw + gap), h: 0, line: { color: "BBBBBB", width: 1 } });
  let run = L;
  steps.forEach((st, i) => { const x = x0 + i * (bw + gap); let y, h, clr, lab;
    if (st[2] === 0) { h = st[1] * sc; y = base - h; clr = st[3]; lab = M(st[1]); }
    else { const a = run, b = run + st[1]; y = base - Math.max(a, b) * sc; h = Math.abs(st[1]) * sc; clr = st[1] < 0 ? RED : GRN; lab = (st[1] < 0 ? "−" : "+") + M(Math.abs(st[1])); run = b; }
    s.addShape(pres.ShapeType.rect, { x, y, w: bw, h: Math.max(h, 0.02), fill: { color: clr }, line: { type: "none" }, objectName: "bridge " + i });
    tx(s, lab, { x: x - 0.2, y: y - 0.32, w: bw + 0.4, h: 0.28, fontSize: 12, bold: true, align: "center", color: st[2] === 0 ? INK : clr });
    tx(s, st[0], { x: x - 0.2, y: base + 0.08, w: bw + 0.4, h: 0.5, fontSize: 11, align: "center", color: GREY }); });
  // key messages
  const R = g("Retail", "Sept"), P = g("MP", "Sept"), oth = g("Other GCC", "Sept");
  const msgs = [
    ["Conversion is the main drag", `UCR fell to ${(O.ty.ucr*100).toFixed(2)}% from ${(O.ly.ucr*100).toFixed(2)}%, worth −${M(-d.conv)} AED. GVs ${pc(yo("Overall","Sept","gv"))}, ASP ${pc(yo("Overall","Sept","asp"))}.`],
    ["Retail down, marketplace up", `Retail ${pc(yo("Retail","Sept","gmv"))} (${M(R.ty.gmv)} vs ${M(R.ly.gmv)}); MP ${pc(yo("MP","Sept","gmv"))}, now ${(P.ty.gmv/O.ty.gmv*100).toFixed(0)}% of GMV vs ${(P.ly.gmv/O.ly.gmv*100).toFixed(0)}% LY.`],
    ["More discount, fewer sales", `Markdown ${(O.ty.mkd*100).toFixed(1)}% vs ${(O.ly.mkd*100).toFixed(1)}%, but the increase sits in MP (${(P.ty.mkd*100).toFixed(0)}%); retail markdown was lower than LY (${(R.ty.mkd*100).toFixed(1)}% vs ${(R.ly.mkd*100).toFixed(1)}%).`],
    ["Gap widest on 19–25 Sep", `GMV ${pc(yo("Overall","19-25 Sep","gmv"))}: LY ran pre-Beauty Week and National Day offers (markdown ${(g("Overall","19-25 Sep").ly.mkd*100).toFixed(0)}% vs ${(g("Overall","19-25 Sep").ty.mkd*100).toFixed(0)}% TY).`],
  ];
  msgs.forEach((m, i) => { const y = 1.85 + i * 1.25;
    s.addShape(pres.ShapeType.ellipse, { x: 7.1, y: y + 0.02, w: 0.42, h: 0.42, fill: { color: LIME }, line: { type: "none" } });
    tx(s, String(i + 1), { x: 7.1, y: y + 0.02, w: 0.42, h: 0.42, fontSize: 14, bold: true, align: "center", valign: "middle" });
    tx(s, m[0], { x: 7.7, y, w: 5.0, h: 0.32, fontSize: 15, bold: true });
    tx(s, m[1], { x: 7.7, y: y + 0.35, w: 5.0, h: 0.8, fontSize: 12.5, color: "41464E" }); });
  s.addNotes("Bridge uses a log-mean (LMDI) split of the GMV change into traffic (glance views), conversion (units per GV) and price (ASP); the three bars add up to the total change.");
}

// ================= 3. OVERALL SCORECARD =================
{ const s = content("Overall: traffic held up better than sales; conversion and units fell hardest",
    "Beauty, full September (1–30 Sep), TY 2026 vs LY 2025 same dates");
  const tile = (x, y, w, lab, ty, ly, d, dcol, sub) => { card(s, x, y, w, 1.75, lab);
    tx(s, lab, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.3, fontSize: 13, bold: true, color: GREY });
    tx(s, ty, { x: x + 0.2, y: y + 0.48, w: w - 0.4, h: 0.55, fontSize: 28, bold: true });
    tx(s, [{ text: d, options: { bold: true, color: dcol } }, { text: "   LY " + ly, options: { color: GREY } }], { x: x + 0.2, y: y + 1.12, w: w - 0.4, h: 0.3, fontSize: 13 });
    if (sub) tx(s, sub, { x: x + 0.2, y: y + 1.42, w: w - 0.4, h: 0.25, fontSize: 10, color: GREY }); };
  const o = O.ty, l = O.ly;
  // row 1: outcome
  tile(0.6, 1.8, 3.9, "GMV (AED)", M(o.gmv), M(l.gmv), pc(o.gmv / l.gmv - 1), col(o.gmv - l.gmv), "Units " + N(o.units) + " (" + pc(o.units / l.units - 1) + ")");
  tile(4.7, 1.8, 3.9, "ASP (AED)", o.asp.toFixed(1), l.asp.toFixed(1), pc(o.asp / l.asp - 1), col(o.asp - l.asp), "GMV ÷ units");
  tile(8.8, 1.8, 3.9, "Markdown %", (o.mkd * 100).toFixed(1) + "%", (l.mkd * 100).toFixed(1) + "%", pp1(o.mkd - l.mkd), AMB, "Markdown ÷ normal price");
  // row 2: funnel
  tx(s, "Traffic and conversion funnel", { x: 0.6, y: 3.85, w: 6, h: 0.3, fontSize: 14, bold: true });
  const fw = 2.75, fx = [0.6, 3.75, 6.9, 10.05];
  tile(fx[0], 4.25, fw, "Impressions", (o.imp / 1e6).toFixed(1) + "M", (l.imp / 1e6).toFixed(1) + "M", pc(o.imp / l.imp - 1), col(o.imp - l.imp), "Search + non-search");
  tile(fx[1], 4.25, fw, "CTR", (o.ctr * 100).toFixed(2) + "%", (l.ctr * 100).toFixed(2) + "%", pp(o.ctr - l.ctr), col(o.ctr - l.ctr), "GVs ÷ impressions");
  tile(fx[2], 4.25, fw, "Glance views (GVs)", (o.gv / 1e6).toFixed(2) + "M", (l.gv / 1e6).toFixed(2) + "M", pc(o.gv / l.gv - 1), col(o.gv - l.gv), "Product page views");
  tile(fx[3], 4.25, fw, "UCR", (o.ucr * 100).toFixed(2) + "%", (l.ucr * 100).toFixed(2) + "%", pp(o.ucr - l.ucr), col(o.ucr - l.ucr), "Units ÷ GVs");
  [0, 1, 2].forEach(i => s.addShape(pres.ShapeType.rightArrow, { x: fx[i] + fw + 0.08, y: 4.95, w: 0.24, h: 0.3, fill: { color: "C5C9CF" }, line: { type: "none" } }));
  tx(s, [{ text: "Read: ", options: { bold: true } }, { text: `views fell only ${((1-o.gv/l.gv)*100).toFixed(1)}% and CTR improved, but each view converted ${((1-o.ucr/l.ucr)*100).toFixed(0)}% less often (UCR ${(o.ucr*100).toFixed(2)}% vs ${(l.ucr*100).toFixed(2)}%), so units fell ${((1-o.units/l.units)*100).toFixed(1)}%. A higher ASP (${pc(o.asp/l.asp-1)}) softened the GMV drop.` }],
     { x: 0.6, y: 6.25, w: 12.1, h: 0.6, fontSize: 13, color: "41464E" });
}

// ================= 4. BY COUNTRY =================
{ const s = content("By country: UAE and KSA down about a quarter; Other GCC fell 72% as traffic dropped by 61%",
    "Full September, TY 2026 vs LY 2025. Value metrics show % change; CTR, UCR and markdown show percentage-point (pp) change");
  const rows = ["UAE", "KSA", "Kuwait", "Qatar", "Bahrain", "Oman", "Overall"];
  const H = [hc("Country", "left"), hc("GMV TY"), hc("vs LY"), hc("Share"), hc("ASP TY"), hc("vs LY"), hc("Impr. vs LY"), hc("CTR TY"), hc("vs LY"), hc("GVs vs LY"), hc("UCR TY"), hc("vs LY"), hc("MKD TY"), hc("vs LY")];
  const body = rows.map((r, i) => { const t = g(r, "Sept").ty, l = g(r, "Sept").ly, f = r === "Overall" ? "FFF6D6" : (i % 2 ? "F7F8FA" : undefined), b = r === "Overall";
    const o = x => Object.assign({ bold: b }, f ? { fill: { color: f } } : {});
    return [c(r, Object.assign(o(), { align: "left", bold: true })), c(M(t.gmv), o()), dcell(t.gmv / l.gmv - 1, pc, f), c((t.gmv / O.ty.gmv * 100).toFixed(0) + "%", o()),
      c(t.asp.toFixed(0), o()), dcell(t.asp / l.asp - 1, pc, f), dcell(t.imp / l.imp - 1, pc, f), c((t.ctr * 100).toFixed(2) + "%", o()), dcell(t.ctr - l.ctr, pp, f),
      dcell(t.gv / l.gv - 1, pc, f), c((t.ucr * 100).toFixed(2) + "%", o()), dcell(t.ucr - l.ucr, pp, f), c((t.mkd * 100).toFixed(1) + "%", o()), mcell(t.mkd - l.mkd, f)]; });
  s.addTable([H].concat(body), { x: 0.6, y: 1.8, w: 12.1, colW: [1.25, 0.95, 0.85, 0.7, 0.75, 0.8, 0.9, 0.8, 0.85, 0.9, 0.8, 0.85, 0.8, 0.9], rowH: 0.42,
    fontFace: "Calibri", border: { type: "solid", pt: 0.5, color: LINE } });
  const u = g("UAE", "Sept"), k = g("KSA", "Sept"), og = g("Other GCC", "Sept");
  const bl = [[`UAE ${pc(yo("UAE","Sept","gmv"))}: `, `GVs grew ${pc(u.ty.gv/u.ly.gv-1)} and CTR improved, but UCR fell ${pp(u.ty.ucr-u.ly.ucr)}. This is a conversion problem, not a traffic one.`],
              [`KSA ${pc(yo("KSA","Sept","gmv"))}: `, `fewer views (${pc(k.ty.gv/k.ly.gv-1)}) and lower UCR (${pp(k.ty.ucr-k.ly.ucr)}); ASP up ${pc(k.ty.asp/k.ly.asp-1)}.`],
              [`Other GCC ${pc(yo("Other GCC","Sept","gmv"))}: `, `GVs ${pc(og.ty.gv/og.ly.gv-1)} and UCR halved; now ${(og.ty.gmv/O.ty.gmv*100).toFixed(0)}% of GMV vs ${(og.ly.gmv/O.ly.gmv*100).toFixed(0)}% LY.`]];
  bl.forEach((b, i) => tx(s, [{ text: b[0], options: { bold: true } }, { text: b[1] }], { x: 0.6, y: 5.45 + i * 0.45, w: 12.1, h: 0.4, fontSize: 13, color: "41464E" }));
}

// ================= 5. RETAIL vs MP =================
{ const s = content("By business model: retail fell 37% while marketplace grew 67% on heavier discounting",
    "Full September, TY 2026 vs LY 2025");
  s.addChart(pres.ChartType.bar, [{ name: "TY 2026", labels: ["Retail", "Marketplace"], values: ["Retail", "MP"].map(k => +(g(k, "Sept").ty.gmv / 1e6).toFixed(2)) },
                                   { name: "LY 2025", labels: ["Retail", "Marketplace"], values: ["Retail", "MP"].map(k => +(g(k, "Sept").ly.gmv / 1e6).toFixed(2)) }],
    Object.assign(chartBase(), { x: 0.6, y: 1.75, w: 4.6, h: 4.6, barDir: "col", barGrouping: "clustered", chartColors: [TYC, LYC], showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: '0.00"M"', valAxisHidden: true, valGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: GREY,
      showTitle: true, title: "GMV (AED M)" }));
  const mets = [["GMV (AED)", "gmv", M, "pct"], ["Units", "units", N, "pct"], ["ASP (AED)", "asp", v => v.toFixed(1), "pct"], ["Impressions", "imp", v => (v / 1e6).toFixed(1) + "M", "pct"],
                ["CTR", "ctr", v => (v * 100).toFixed(2) + "%", "pp"], ["GVs", "gv", v => (v / 1e6).toFixed(2) + "M", "pct"], ["UCR", "ucr", v => (v * 100).toFixed(2) + "%", "pp"], ["Markdown %", "mkd", v => (v * 100).toFixed(1) + "%", "mk"]];
  const H = [hc("Metric", "left"), hc("Retail TY"), hc("Retail LY"), hc("vs LY"), hc("MP TY"), hc("MP LY"), hc("vs LY")];
  const body = mets.map((m, i) => { const f = i % 2 ? "F7F8FA" : undefined, o = f ? { fill: { color: f } } : {}; const r = [c(m[0], Object.assign({ align: "left", bold: true }, o))];
    ["Retail", "MP"].forEach(k => { const t = g(k, "Sept").ty[m[1]], l = g(k, "Sept").ly[m[1]];
      r.push(c(m[2](t), o), c(m[2](l), Object.assign({ color: GREY }, o)), m[3] === "pct" ? dcell(t / l - 1, pc, f) : m[3] === "pp" ? dcell(t - l, pp, f) : mcell(t - l, f)); }); return r; });
  s.addTable([H].concat(body), { x: 5.6, y: 1.8, w: 7.1, colW: [1.4, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95], rowH: 0.4, fontFace: "Calibri", border: { type: "solid", pt: 0.5, color: LINE } });
  const R = g("Retail", "Sept"), P = g("MP", "Sept");
  tx(s, [{ text: "Retail: ", options: { bold: true } }, { text: `units ${pc(R.ty.units/R.ly.units-1)}, GVs ${pc(R.ty.gv/R.ly.gv-1)} and UCR ${pp(R.ty.ucr-R.ly.ucr)}, with markdown below LY (${(R.ty.mkd*100).toFixed(1)}% vs ${(R.ly.mkd*100).toFixed(1)}%).` , options: { breakLine: true } },
          { text: "Marketplace: ", options: { bold: true } }, { text: `GVs ${pc(P.ty.gv/P.ly.gv-1)} and UCR ${pp(P.ty.ucr-P.ly.ucr)} at ${(P.ty.mkd*100).toFixed(0)}% markdown; share of GMV ${(P.ty.gmv/O.ty.gmv*100).toFixed(0)}% vs ${(P.ly.gmv/O.ly.gmv*100).toFixed(0)}% LY.` }],
     { x: 5.6, y: 5.55, w: 7.1, h: 1.0, fontSize: 13, color: "41464E", paraSpaceAfter: 6 });
}

// ================= 6. PERIOD VIEW =================
{ const s = content("By period: the gap was widest on 19–25 Sep, when LY ran pre-Beauty Week and National Day offers",
    "GMV per day (AED K), TY 2026 vs LY 2025 on the same calendar dates. Periods: 1–18 Sep (BAU), 19–25 Sep (pre-Beauty Week), 26–30 Sep (Beauty Week)");
  s.addChart(pres.ChartType.bar, [{ name: "TY 2026", labels: PERS.map(p => PLAB[p]), values: PERS.map(p => Math.round(g("Overall", p).ty.gmv / g("Overall", p).ty.days / 1e3)) },
                                   { name: "LY 2025", labels: PERS.map(p => PLAB[p]), values: PERS.map(p => Math.round(g("Overall", p).ly.gmv / g("Overall", p).ly.days / 1e3)) }],
    Object.assign(chartBase(), { x: 0.6, y: 1.85, w: 4.9, h: 4.4, barDir: "col", barGrouping: "clustered", chartColors: [TYC, LYC], showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: '#,##0"K"', valAxisHidden: true, valGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: GREY, showTitle: true, title: "GMV per day (AED K)" }));
  const H = [hc("Metric", "left")].concat(PERS.map(p => hc(PLAB[p]))).concat([hc("Full Sept")]);
  const P4 = PERS.concat(["Sept"]);
  const mrow = (lab, fty, fd) => [c(lab, { align: "left", bold: true })].concat(P4.map(p => { const t = g("Overall", p).ty, l = g("Overall", p).ly;
    return { text: [{ text: fty(t, l), options: { color: INK } }, { text: "\n" + fd(t, l)[0], options: { color: fd(t, l)[1], bold: true, fontSize: 10 } }], options: { align: "right", valign: "middle", fontSize: 11 } }; }));
  const body = [
    mrow("GMV (AED)", t => M(t.gmv), (t, l) => [pc(t.gmv / l.gmv - 1), col(t.gmv - l.gmv)]),
    mrow("ASP (AED)", t => t.asp.toFixed(0), (t, l) => [pc(t.asp / l.asp - 1), col(t.asp - l.asp)]),
    mrow("Impressions", t => (t.imp / 1e6).toFixed(1) + "M", (t, l) => [pc(t.imp / l.imp - 1), col(t.imp - l.imp)]),
    mrow("CTR", t => (t.ctr * 100).toFixed(2) + "%", (t, l) => [pp(t.ctr - l.ctr), col(t.ctr - l.ctr)]),
    mrow("GVs", t => (t.gv / 1e6).toFixed(2) + "M", (t, l) => [pc(t.gv / l.gv - 1), col(t.gv - l.gv)]),
    mrow("UCR", t => (t.ucr * 100).toFixed(2) + "%", (t, l) => [pp(t.ucr - l.ucr), col(t.ucr - l.ucr)]),
    mrow("Markdown %", t => (t.mkd * 100).toFixed(1) + "%", (t, l) => [pp1(t.mkd - l.mkd), AMB]) ];
  s.addTable([H].concat(body), { x: 5.9, y: 1.85, w: 6.8, colW: [1.4, 1.35, 1.35, 1.35, 1.35], rowH: 0.56, fontFace: "Calibri", border: { type: "solid", pt: 0.5, color: LINE } });
  tx(s, "Each cell: TY value, with change vs LY below (% for values, pp for rates)", { x: 5.9, y: 6.45, w: 6.8, h: 0.3, fontSize: 10, italic: true, color: GREY });
}

// ================= 7. DAILY CORRELATION =================
{ const s = content("Daily view: sales follow traffic and conversion; the extra early-Sept markdown did not lift them",
    "Daily, 1–30 Sep, TY 2026 vs LY 2025 (same dates). Dotted guides mark the three periods: 1–18 | 19–25 | 26–30 Sep");
  const days = Array.from({ length: 30 }, (_, i) => String(i + 1));
  const dv = (y, f) => days.map(d => f(D.daily[y + "|" + d]));
  const series = (f) => [{ name: "TY 2026", labels: days, values: dv("2026", f) }, { name: "LY 2025", labels: days, values: dv("2025", f) }];
  const panels = [["GMV (AED K)", a => Math.round(a[0] / 1e3), "#,##0"], ["Markdown %", a => +(a[2] / a[3] * 100).toFixed(1), "0"],
                  ["Glance views (K)", a => Math.round(a[5] / 1e3), "#,##0"], ["UCR % (units ÷ GVs)", a => +(a[1] / a[5] * 100).toFixed(2), "0.0"]];
  panels.forEach((p, i) => { const x = 0.6 + (i % 2) * 6.15, y = 1.75 + Math.floor(i / 2) * 2.62, w = 5.95, h = 2.5;
    s.addChart(pres.ChartType.line, series(p[1]), Object.assign(chartBase(), { x, y, w, h, chartColors: [TYC, LYC], lineSize: 2, lineDataSymbol: "none",
      showTitle: true, title: p[0], showLegend: i === 0, legendPos: "t", legendFontSize: 10, legendColor: GREY, valAxisLabelFormatCode: p[2], catAxisLabelFontSize: 9,
      catAxisLabelFrequency: 1, valAxisLabelFontSize: 9, layout: { x: 0.09, y: 0.2, w: 0.88, h: 0.62 } }));
    const pl = x + 0.09 * w, pw = 0.88 * w; [18, 25].forEach(dd => s.addShape(pres.ShapeType.line, { x: pl + pw * (dd / 30), y: y + 0.2 * h, w: 0, h: 0.62 * h, line: { color: "9AA0A8", width: 0.75, dashType: "dash" } })); });
  s.addNotes("Markdown % = markdown discount ÷ normal price. UCR = units ÷ glance views. In 1–18 Sep markdown ran at 21–27% TY vs 9–18% LY while UCR stayed below LY every day.");
}

// ================= 8. DRIVERS BY PERIOD =================
{ const s = content("Drivers: conversion is the biggest drag in every period; traffic adds to it from 19 Sep",
    "Change in GMV vs LY (AED K) split into traffic (GVs), conversion (UCR) and price (ASP); the three add up to the total change");
  const P4 = PERS.concat(["Sept"]), lab = P4.map(p => PLAB[p]);
  s.addChart(pres.ChartType.bar, [
      { name: "Traffic (GVs)", labels: lab, values: P4.map(p => Math.round(g("Overall", p).drv.traffic / 1e3)) },
      { name: "Conversion (UCR)", labels: lab, values: P4.map(p => Math.round(g("Overall", p).drv.conv / 1e3)) },
      { name: "Price (ASP)", labels: lab, values: P4.map(p => Math.round(g("Overall", p).drv.price / 1e3)) }],
    Object.assign(chartBase(), { x: 0.6, y: 1.8, w: 7.0, h: 4.9, barDir: "col", barGrouping: "clustered", chartColors: ["5B8DB8", RED, TYC], showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: '#,##0', showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: GREY, valAxisLabelFormatCode: "#,##0", showTitle: true, title: "GMV change vs LY by driver (AED K)" }));
  const H = [hc("Period", "left"), hc("GMV vs LY"), hc("GVs"), hc("UCR"), hc("ASP"), hc("MKD")];
  const body = P4.map((p, i) => { const t = g("Overall", p).ty, l = g("Overall", p).ly, f = p === "Sept" ? "FFF6D6" : undefined;
    return [c(PLAB[p], { align: "left", bold: true, fill: f ? { color: f } : undefined }), dcell(t.gmv / l.gmv - 1, pc, f), dcell(t.gv / l.gv - 1, pc, f), dcell(t.ucr - l.ucr, pp, f), dcell(t.asp / l.asp - 1, pc, f), mcell(t.mkd - l.mkd, f)]; });
  s.addTable([H].concat(body), { x: 7.85, y: 1.85, w: 4.85, colW: [0.95, 0.8, 0.75, 0.8, 0.75, 0.8], rowH: 0.42, fontFace: "Calibri", fontSize: 10, border: { type: "solid", pt: 0.5, color: LINE } });
  const p1 = g("Overall", "1-18 Sep"), p2 = g("Overall", "19-25 Sep"), p3 = g("Overall", "26-30 Sep");
  const notes = [["1–18 Sep: ", `traffic flat, markdown +${((p1.ty.mkd-p1.ly.mkd)*100).toFixed(0)} pp, yet UCR ${pp(p1.ty.ucr-p1.ly.ucr)}. Discount did not convert.`],
                 ["19–25 Sep: ", `LY markdown was ${((p2.ly.mkd-p2.ty.mkd)*100).toFixed(0)} pp deeper; GVs ${pc(p2.ty.gv/p2.ly.gv-1)} and UCR ${pp(p2.ty.ucr-p2.ly.ucr)}.`],
                 ["26–30 Sep: ", `similar markdown to LY, but GVs ${pc(p3.ty.gv/p3.ly.gv-1)} and UCR ${pp(p3.ty.ucr-p3.ly.ucr)}; ASP ${pc(p3.ty.asp/p3.ly.asp-1)} offsets part.`]];
  notes.forEach((n, i) => tx(s, [{ text: n[0], options: { bold: true } }, { text: n[1] }], { x: 7.85, y: 4.3 + i * 0.8, w: 4.85, h: 0.75, fontSize: 12, color: "41464E" }));
}

// ================= 9. PERIOD x CUT HEAT TABLE =================
{ const s = content("Period by country and business model: retail drives the decline in every period; MP grows throughout",
    "GMV % change vs LY with the matching markdown (pp), GVs (%) and UCR (pp) change, per period");
  const cuts = ["UAE", "KSA", "Other GCC", "Retail", "MP", "Overall"];
  const H1 = [hc("", "left")].concat(PERS.flatMap(p => [{ text: PLAB[p], options: { bold: true, color: WHITE, fill: { color: INK }, align: "center", colspan: 4, fontSize: 11 } }]));
  const H2 = [hc("Cut", "left")].concat(PERS.flatMap(() => ["GMV", "MKD", "GVs", "UCR"].map(t => ({ text: t, options: { bold: true, color: INK, fill: { color: "E9ECEF" }, align: "center", fontSize: 10 } }))));
  const heat = v => v <= -0.4 ? "F4C7C3" : v <= -0.15 ? "FBE3E1" : v >= 0.15 ? "D7EDD9" : undefined;
  const body = cuts.map(k => [c(k, { align: "left", bold: true, fill: k === "Overall" ? { color: "FFF6D6" } : undefined })].concat(PERS.flatMap(p => { const t = g(k, p).ty, l = g(k, p).ly, gv = t.gmv / l.gmv - 1;
    return [c(pc(gv), { bold: true, color: col(gv), fill: heat(gv) ? { color: heat(gv) } : undefined }), c(pp1(t.mkd - l.mkd), { color: AMB }), c(pc(t.gv / l.gv - 1), { color: col(t.gv - l.gv) }), c(pp(t.ucr - l.ucr), { color: col(t.ucr - l.ucr) })]; })));
  s.addTable([H1, H2].concat(body), { x: 0.6, y: 1.85, w: 12.1, colW: [1.3].concat(Array(12).fill(0.9)), rowH: 0.42, fontFace: "Calibri", fontSize: 10.5, border: { type: "solid", pt: 0.5, color: LINE } });
  const R2 = g("Retail", "19-25 Sep");
  tx(s, [{ text: "How to read: ", options: { bold: true } }, { text: "GMV cells are shaded red below −15% and dark red below −40%, green above +15%. MKD = markdown % change in pp (amber: more or less discount, not good or bad by itself)." , options: { breakLine: true } },
          { text: "Takeaway: ", options: { bold: true } }, { text: `retail on 19–25 Sep fell ${((1-R2.ty.gmv/R2.ly.gmv)*100).toFixed(1)}% with ${((R2.ly.mkd-R2.ty.mkd)*100).toFixed(0)} pp less markdown than LY; MP grew 60–70% in every period at roughly 40% markdown.` }],
     { x: 0.6, y: 5.3, w: 12.1, h: 1.2, fontSize: 13, color: "41464E", paraSpaceAfter: 6 });
}

// ================= 10. NOTES =================
sec = "Notes"; pres.addSection({ title: sec });
{ const s = content("Definitions, dates and sources", "How every number in this deck is built");
  const items = [
    ["Scope", "Namshi marketplaces (namshi, namshi_v2), Beauty business unit, lines with GMV above zero, samples & GWP excluded. GMV includes VAT and all item statuses."],
    ["Periods", "TY = 1–30 Sep 2026, LY = 1–30 Sep 2025 (same calendar dates). Split into 1–18, 19–25 and 26–30 Sep so the three periods add up to the month. LY Beauty Week began 25 Sep and LY National Day (23 Sep) falls in 19–25."],
    ["Metrics", "ASP = GMV ÷ units. Impressions = search + non-search. CTR = GVs ÷ impressions. UCR = units ÷ GVs. Markdown % = markdown discount ÷ normal price. Per-day values used where periods differ in length."],
    ["Drivers", "GMV change split with a log-mean (LMDI) method into traffic (GVs), conversion (UCR) and price (ASP); the parts add up to the total."],
    ["Sources", "BigQuery: noonbinamshi.custom_views.sales_metrics (sales, markdown), noonbinamshi.onsite_v1.onsite_measures (impressions, GVs), custom_views.item_d (Beauty scope, business model). Pulled 12 Oct 2026."],
    ["Next", "October MTD section to be added with the same structure."]];
  items.forEach((it, i) => { const y = 1.8 + i * 0.85;
    s.addShape(pres.ShapeType.ellipse, { x: 0.6, y: y + 0.05, w: 0.3, h: 0.3, fill: { color: LIME }, line: { type: "none" } });
    tx(s, it[0], { x: 1.1, y, w: 1.6, h: 0.4, fontSize: 14, bold: true });
    tx(s, it[1], { x: 2.8, y, w: 9.9, h: 0.8, fontSize: 13, color: "41464E" }); });
}

(async () => { await pres.writeFile({ fileName: "Beauty_Sept_2026_Review.pptx" }); await applyTheme("Beauty_Sept_2026_Review.pptx", THEME); console.log("ok"); })();
