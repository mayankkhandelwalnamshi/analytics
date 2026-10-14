"""Beauty · November '26 Strategy — pageless web page (Beauty Pulse / Nov Flashback look).

python3 ond-beauty/nov26_strategy/page/build_page.py  ->  ond-beauty/dist/nov26_strategy.html

All figures as of 12 Oct 2026; the queries and calculations live in ../ (queries.sql, *.py).
Charts are inline SVG coloured through CSS tokens, so they follow the viewer's light / dark theme.
"""
import html
import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent.parent / "dist" / "nov26_strategy.html"
H = json.load(open(HERE / "health.json"))

E = html.escape
MINUS = "−"


def pct(v, d=0, sign=True):
    if v is None:
        return "–"
    s = f"{abs(v) * 100:.{d}f}%"
    if round(abs(v) * 100, d) == 0:
        return "0%"
    return (("+" if v > 0 else MINUS) + s) if sign else s


def K(v):
    return f"{v / 1e6:.2f}M" if v >= 1e6 else f"{round(v / 1e3)}K"


# ---------------------------------------------------------------- SVG helpers
def svg(w, h, body, label):
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{E(label)}" class="chart" '
            f'preserveAspectRatio="xMidYMid meet">{body}</svg>')


def t(x, y, s, cls="lab", anchor="start", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" {extra}>{E(str(s))}</text>'


def rect(x, y, w, h, cls, rx=2, title=None):
    tt = f"<title>{E(title)}</title>" if title else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" rx="{rx}" class="{cls}">{tt}</rect>'


# ---------------------------------------------------------------- 1. monthly GMV
G = {2024: [6855585, 6926332, 12706844, 9111608, 8670958, 8723815, 7095023, 8278112, 7948656, 8777059, 17785925, 8898392],
     2025: [7745502, 6926861, 18676633, 7980590, 10107349, 8709243, 8290997, 10014889, 8842244, 8044470, 16440910, 8798689],
     2026: [5862235, 6216703, 11487996, 6288631, 8241744, 5976895, 6236584, 6166883, 6374596]}
OCT_PACE, NOV_TGT, OCT_TGT = 8132734, 20551138, 8623116


def chart_monthly():
    W, Hh, L, R, y0, B, mx = 760, 330, 52, 670, 30, 290, 22e6
    x = lambda m: L + (m - 1) * (R - L) / 11
    y = lambda v: B - v / mx * (B - y0)
    step = (R - L) / 11
    b = [rect(x(11) - step / 2, y0 - 6, step, B - y0 + 6, "band", 0),
         t(x(11), y0 - 12, "NOVEMBER", "eyebrow-s", "middle")]
    for v in (0, 5e6, 10e6, 15e6, 20e6):
        b.append(f'<line x1="{L}" x2="{R}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>')
        b.append(t(L - 8, y(v) + 4, "0" if v == 0 else f"{int(v / 1e6)}M", "axis", "end"))
    for i, mn in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()):
        b.append(t(x(i + 1), B + 18, mn, "axis", "middle"))
    for yr, cls in ((2024, "ly2"), (2025, "ly"), (2026, "ty")):
        pts = " ".join(f"{x(i + 1):.1f},{y(v):.1f}" for i, v in enumerate(G[yr]))
        b.append(f'<polyline points="{pts}" class="line {cls}"/>')
        for i, v in enumerate(G[yr]):
            b.append(f'<circle cx="{x(i + 1):.1f}" cy="{y(v):.1f}" r="{3.5 if yr == 2026 else 2.5}" class="dot {cls}"><title>{yr} {i + 1:02d}: AED {v / 1e6:.1f}M</title></circle>')
    b.append(f'<path d="M{x(9):.1f},{y(G[2026][-1]):.1f} L{x(10):.1f},{y(OCT_PACE):.1f} L{x(11):.1f},{y(NOV_TGT):.1f}" class="line ty dash"/>')
    b.append(f'<circle cx="{x(10):.1f}" cy="{y(OCT_PACE):.1f}" r="4" class="hollow"><title>Oct at 1–12 Oct pace: AED 8.1M</title></circle>')
    b.append(f'<line x1="{x(10) - 9:.1f}" x2="{x(10) + 9:.1f}" y1="{y(OCT_TGT):.1f}" y2="{y(OCT_TGT):.1f}" class="tick-ty"><title>Oct target: AED 8.6M</title></line>')
    b.append(f'<circle cx="{x(11):.1f}" cy="{y(NOV_TGT):.1f}" r="7" class="target"><title>Nov target: AED 20.6M</title></circle>')
    b.append(t(x(11) - 12, y(NOV_TGT) + 5, "Target 20.6M", "val-ty", "end"))
    b.append(t(x(11) + step / 2 + 6, y(G[2024][10]) + 4, "Nov '24 17.8M", "lab"))
    b.append(t(x(11) + step / 2 + 6, y(G[2025][10]) + 14, "Nov '25 16.4M", "lab"))
    b.append(t(x(9) + 4, y(G[2026][-1]) + 18, "2026", "val-ty"))
    b.append(t(x(10) + 6, y(OCT_PACE) + 30, "Oct pace 8.1M", "lab"))
    b.append(t(x(10) + 6, y(OCT_PACE) + 44, "Oct target 8.6M", "lab-ty"))
    b.append(t(x(12) + 6, y(G[2025][11]) + 14, "2025", "lab"))
    b.append(t(x(12) + 6, y(G[2024][11]) - 4, "2024", "lab"))
    return svg(W, Hh, "".join(b), "Beauty GMV by month 2024 to 2026 with the November 2026 target")


# ---------------------------------------------------------------- 2. November cohorts
COH = [('MS', '1–6', 6, 2239163, 6, 1854805, 6, 2277057, 0), ('Pre 11.11', '7–10', 4, 2851377, 4, 1975823, 4, 2675615, 1),
       ('11.11', '11', 1, 989146, 1, 913169, 1, 1060315, 1), ('Post 11.11', '12–14', 3, 1586836, 3, 1633586, 3, 1798851, 1),
       ('BAU', '15–19', 5, 2079289, 7, 2418156, 6, 1965714, 0), ('BF week', '20–24', 5, 3334409, 5, 2306274, 5, 3126401, 1),
       ('Pre BF', '25–26', 2, 1979216, 2, 1523664, 2, 1945516, 1), ('Black Friday', '27', 1, 1512952, 1, 1320009, 1, 1577290, 1),
       ('Post BF', '28–30', 3, 1213538, 1, 2495534, 2, 4124379, 1)]


def chart_cohorts():
    W, Hh, L, R, y0, B, mx = 760, 360, 8, 752, 26, 262, 1.75e6
    band = (R - L) / len(COH)
    bw = 17
    y = lambda v: B - v / mx * (B - y0)
    b = []
    for i, (n, d, days, lly, lld, ly, lyd, tg, ev) in enumerate(COH):
        cx = L + i * band + band / 2
        if ev:
            b.append(rect(L + i * band + 2, y0 - 16, band - 4, B - y0 + 16, "band", 0))
        for k, (v, cls, lab, tot, dd) in enumerate(((lly / lld, "b-ly2", "Nov '24", lly, lld), (ly / lyd, "b-ly", "Nov '25", ly, lyd), (tg / days, "b-ty", "Nov '26 target", tg, days))):
            bx = cx - 1.5 * bw - 2 + k * (bw + 2)
            b.append(rect(bx, y(v), bw, B - y(v), cls, 2, f"{n} {lab}: AED {K(v)} a day, AED {K(tot)} in total"))
        b.append(t(cx + bw + 1, y(tg / days) - 6, K(tg / days), "val-ty", "middle"))
        b.append(t(cx, B + 16, n, "name-ty" if ev else "name", "middle"))
        b.append(t(cx, B + 31, f"{d} Nov", "axis", "middle"))
        b.append(t(cx, B + 49, K(tg), "val", "middle"))
        g = (tg / days) / (ly / lyd) - 1
        b.append(t(cx, B + 65, f"{pct(g)}/day", "neg" if g < 0 else "axis", "middle"))
    b.append(f'<line x1="{L}" x2="{R}" y1="{B}" y2="{B}" class="axisline"/>')
    return svg(W, Hh, "".join(b), "November GMV per day by cohort, Nov 2024, Nov 2025 and Nov 2026 target")


# ---------------------------------------------------------------- 3. year-end stock
STOCK = [("End 2024", "actual", 399915, 20.9, "h"), ("End 2025", "actual", 393278, 20.4, "h"),
         ("Last-4-week trend", "retail GMV −30%", 241727, 12.5, "s"), ("October trend", "retail GMV −11%", 165601, 8.6, "s"),
         ("Nov at target", "ASP 65 · Dec −10%", 116806, 6.0, "s")]
CAP = 193089


def chart_stock():
    W, Hh, L, R, y0, B, mx = 760, 300, 10, 750, 24, 236, 420000
    band = (R - L) / len(STOCK)
    bw = band * 0.52
    y = lambda v: B - v / mx * (B - y0)
    b = []
    for i, (n, sub, u, w, kind) in enumerate(STOCK):
        cx = L + i * band + band / 2
        cls = "b-hist" if kind == "h" else ("b-bad" if u > CAP else "b-good")
        b.append(rect(cx - bw / 2, y(u), bw, B - y(u), cls, 3, f"{n}: {round(u / 1000)}K units, {w} weeks"))
        b.append(t(cx, y(u) - 8, f"{round(u / 1000)}K", "val", "middle"))
        b.append(t(cx, y(u) + 18, f"{w} wks", "in-bar", "middle"))
        b.append(t(cx, B + 18, n, "name", "middle"))
        b.append(t(cx, B + 33, sub, "axis", "middle"))
    b.append(f'<line x1="{L}" x2="{R}" y1="{y(CAP):.1f}" y2="{y(CAP):.1f}" class="ref"/>')
    b.append(t(R, y(CAP) - 6, "Cap: 10 WoC = 193K", "lab", "end"))
    b.append(f'<line x1="{L + 2 * band:.1f}" x2="{L + 2 * band:.1f}" y1="{y0}" y2="{B + 36}" class="grid"/>')
    b.append(t(L + 2 * band + 8, y0 + 6, "2026 PROJECTIONS", "eyebrow-s"))
    b.append(f'<line x1="{L}" x2="{R}" y1="{B}" y2="{B}" class="axisline"/>')
    return svg(W, Hh, "".join(b), "Year-end retail units by scenario against the 193K cap")


# ---------------------------------------------------------------- 4. risk map
NM = {'kiko_milano': 'KIKO Milano', 'charlotte_tilbury': 'Charlotte Tilbury', 'kerastase': 'Kérastase', 'mac_cosmetics': 'MAC',
      'nyx_professional_makeup': 'NYX', 'kylie_cosmetics': 'Kylie Cosmetics', 'elizabeth_arden': 'Elizabeth Arden',
      'loreal_professionnel': "L'Oréal Professionnel", 'make_up_for_ever': 'Make Up For Ever', 'estee_lauder': 'Estée Lauder',
      'lancome': 'Lancôme', 'armani': 'Armani', 'maybelline_new_york': 'Maybelline', 'anastasia_beverly_hills': 'Anastasia Beverly Hills',
      'clinique': 'Clinique', 'clara': 'Clara', 'louzan': 'Louzan', 'laverne': 'Laverne', 'bath_body_works': 'Bath & Body Works', 'h_m': 'H&M'}
JO = {'kiko_milano': 1603312, 'charlotte_tilbury': 1579030, 'kerastase': 1172953, 'mac_cosmetics': 1100407, 'nyx_professional_makeup': 1056639,
      'kylie_cosmetics': 746363, 'elizabeth_arden': 708164, 'loreal_professionnel': 517536, 'make_up_for_ever': 509084, 'estee_lauder': 454944,
      'lancome': 435324, 'armani': 413094, 'maybelline_new_york': 393497, 'anastasia_beverly_hills': 317618, 'clinique': 311673}
SIDE = {'kerastase': 'l', 'mac_cosmetics': 'l', 'maybelline_new_york': 'l', 'kylie_cosmetics': 'b'}


def bucket(d):
    if d['bm'] == 'mp':
        return 'stable'
    if d['jo_gmv'] <= -0.25 and d['woc'] >= 20:
        return 'high'
    if d['jo_gmv'] >= -0.12 and d['ucr'] >= -0.10 and d['woc'] < 20:
        return 'stable'
    return 'mid'


BLABEL = {'stable': 'Stable', 'mid': 'Mid risk', 'high': 'High risk'}


def chart_risk():
    W, Hh, L, R, y0, B = 760, 330, 46, 740, 16, 286
    xmin, xmax, ymax = -60, 20, 35
    cx = lambda v: L + (v - xmin) / (xmax - xmin) * (R - L)
    cy = lambda v: B - v / ymax * (B - y0)
    b = []
    for v in (-60, -40, -20, 0, 20):
        b.append(f'<line x1="{cx(v):.1f}" x2="{cx(v):.1f}" y1="{y0}" y2="{B}" class="{"axisline" if v == 0 else "grid"}"/>')
        b.append(t(cx(v), B + 16, f"{'+' if v > 0 else (MINUS if v < 0 else '')}{abs(v)}%", "axis", "middle"))
    for v in (0, 10, 20, 30):
        b.append(f'<line x1="{L}" x2="{R}" y1="{cy(v):.1f}" y2="{cy(v):.1f}" class="grid"/>')
        b.append(t(L - 8, cy(v) + 4, v, "axis", "end"))
    b.append(f'<rect x="{L}" y="{y0}" width="{cx(-25) - L:.1f}" height="{cy(20) - y0:.1f}" class="zone-bad"/>')
    b.append(f'<line x1="{L}" x2="{R}" y1="{cy(20):.1f}" y2="{cy(20):.1f}" class="ref"/>')
    b.append(f'<line x1="{cx(-25):.1f}" x2="{cx(-25):.1f}" y1="{y0}" y2="{B}" class="ref"/>')
    b.append(t(L + 8, y0 + 14, "HIGH-RISK ZONE", "eyebrow-bad"))
    b.append(t(R, cy(20) - 6, "20 weeks", "lab", "end"))
    b.append(t((L + R) / 2, B + 36, "GMV 1 Jul – 12 Oct vs LY", "axis", "middle"))
    b.append(t(L - 40, y0 - 2, "WoC", "axis"))
    for d in [d for d in H if d['bm'] == 'retail']:
        g, w, r = d['jo_gmv'] * 100, d['woc'], math.sqrt(JO[d['brand']] / 1e6) * 10
        bk = bucket(d)
        b.append(f'<circle cx="{cx(g):.1f}" cy="{cy(w):.1f}" r="{r:.1f}" class="bub {bk}"><title>{E(NM[d["brand"]])}: {pct(d["jo_gmv"])} GMV since July, {w:.1f} weeks of cover</title></circle>')
        s = SIDE.get(d['brand'], 'r')
        if s == 'b':
            b.append(t(cx(g), cy(w) + r + 13, NM[d['brand']], "name", "middle"))
        else:
            b.append(t(cx(g) + (-1 if s == 'l' else 1) * (r + 4), cy(w) + 4, NM[d['brand']], "name", "end" if s == 'l' else "start"))
    return svg(W, Hh, "".join(b), "Retail focus brands: GMV vs LY since July against weeks of cover")


# ---------------------------------------------------------------- 5. event windows
WIN = [("Singles window", "8–12 Nov · 5 days", 4277273, 3182390), ("Black Friday window", "27–30 Nov · 4 days", 4705706, 4795171),
       ("Shoulder days", "other 21 days", 8802946, 8463350)]


def chart_windows():
    W, Hh, L, R, rh, bh, mx = 760, 228, 190, 650, 74, 20, 9.5e6
    w = lambda v: v / mx * (R - L)
    b = []
    for i, (n, d, a, c) in enumerate(WIN):
        yy = 8 + i * rh
        b.append(t(L - 14, yy + 18, n, "name", "end"))
        b.append(t(L - 14, yy + 34, d, "axis", "end"))
        b.append(rect(L, yy, w(a), bh, "b-ly2", 2, f"{n} Nov 2024: AED {a / 1e6:.2f}M"))
        b.append(t(L + w(a) + 6, yy + 15, f"{a / 1e6:.2f}M", "lab"))
        b.append(rect(L, yy + bh + 4, w(c), bh, "b-ty", 2, f"{n} Nov 2025: AED {c / 1e6:.2f}M"))
        b.append(t(L + w(c) + 6, yy + bh + 19, f"{c / 1e6:.2f}M", "val"))
        ch = c / a - 1
        b.append(t(R + 100, yy + 30, pct(ch), "big-neg" if ch < -0.1 else "big", "end"))
    return svg(W, Hh, "".join(b), "November GMV by window, 2024 vs 2025")


# ---------------------------------------------------------------- 6. impressions share
SH = [('Clara', 429580, 1561884), ("L'Oréal Professionnel", 353265, 2489178), ('Kérastase', 962796, 7190803), ('Elizabeth Arden', 186762, 2460243),
      ('Lancôme', 246751, 3805413), ('Charlotte Tilbury', 1336512, 21071983), ('SKIN1004', 352923, 6110718), ('Estée Lauder', 398494, 7424315),
      ('Kylie Cosmetics', 360683, 8092817), ('MAC', 829669, 18957086), ('Clinique', 242433, 6260474), ('Make Up For Ever', 521336, 14156218),
      ('Maybelline', 536816, 16948373), ('KIKO Milano', 1233982, 42575283), ('NYX', 1437628, 56414253)]
TG, TI = 16440911, 406544422


def chart_share():
    L, Wd, rh, mx = 170, 430, 28, 0.14
    Hh = 30 + len(SH) * rh + 10
    x = lambda v: L + v / mx * Wd
    b = [t(752, 14, "AED per 1K impr.", "axis", "end")]
    for i, (n, g, im) in enumerate(SH):
        yy = 26 + i * rh
        sg, si, gpk = g / TG, im / TI, g / im * 1000
        b.append(t(L - 10, yy + 12, n, "name", "end"))
        b.append(rect(L, yy, x(sg) - L, 9, "b-ty", 2, f"{n}: {sg * 100:.1f}% of GMV"))
        b.append(rect(L, yy + 11, x(si) - L, 9, "b-ly", 2, f"{n}: {si * 100:.1f}% of impressions"))
        b.append(t(max(x(sg), x(si)) + 6, yy + 14, f"{sg * 100:.1f}% / {si * 100:.1f}%", "lab"))
        b.append(t(752, yy + 14, round(gpk), "val-ty" if gpk >= 40 else "lab", "end"))
    b.append(t(752, 26 + len(SH) * rh + 6, "Beauty avg 40", "axis", "end"))
    return svg(760, Hh, "".join(b), "Share of GMV vs share of impressions, Nov 2025")


# ---------------------------------------------------------------- 7. UCR and sets
def chart_pairs(groups, fmt, mx, under=None, label=""):
    W, Hh, L, R, y0, B = 760, 250 if under else 230, 10, 750, 22, 184
    gw = (R - L) / len(groups)
    bw = 72
    y = lambda v: B - v / mx * (B - y0)
    b = []
    for gi, (name, sub, vals) in enumerate(groups):
        c = L + gi * gw + gw / 2
        for k, (yr, v, extra) in enumerate(vals):
            bx = c - bw - 4 + k * (bw + 8)
            b.append(rect(bx, y(v), bw, B - y(v), "b-ty" if k == 1 else "b-ly", 3, f"{name} {yr}: {fmt(v)}"))
            b.append(t(bx + bw / 2, y(v) - 7, fmt(v), "val", "middle"))
            if under:
                b.append(t(bx + bw / 2, B + 16, extra, under(extra), "middle"))
            else:
                b.append(t(bx + bw / 2, B + 16, extra, "axis", "middle"))
        b.append(t(c, B + 36, name, "name", "middle"))
        if sub:
            b.append(t(c, B + 52, sub, "axis", "middle"))
    b.append(f'<line x1="{L}" x2="{R}" y1="{B}" y2="{B}" class="axisline"/>')
    return svg(W, Hh, "".join(b), label)


def chart_ucr():
    G2 = [("Quietest 10 days", None, [("2024", 2.34, "8.1M/day"), ("2025", 2.51, "7.9M/day")]),
          ("Middle 10 days", None, [("2024", 2.88, "11.5M/day"), ("2025", 2.82, "12.9M/day")]),
          ("Busiest 10 days", None, [("2024", 3.76, "18.5M/day"), ("2025", 3.72, "19.9M/day")])]
    return chart_pairs(G2, lambda v: f"{v:.2f}%", 4.2, None, "UCR by daily traffic level, November 2024 and 2025")


def chart_sets():
    G3 = [("Gift sets", "13% → 9% of Nov GMV", [("2024", 3.35, "PC1 +20.1%"), ("2025", 2.00, "PC1 +16.9%")]),
          ("Launches (<120 days)", "12% → 7% of Nov GMV", [("2024", 3.00, "PC1 +15.8%"), ("2025", 2.21, "PC1 +24.0%")]),
          ("Core range", "75% → 83% of Nov GMV", [("2024", 1.95, "PC1 +1.3%"), ("2025", 1.96, f"PC1 {MINUS}10.4%")])]
    return chart_pairs(G3, lambda v: f"{v:.1f}x", 3.8, lambda s: "neg" if (MINUS in s or "+1.3" in s) else "pos",
                       "November daily GMV as a multiple of Sep–Oct, and PC1, by segment")


# ---------------------------------------------------------------- tables
def tbl(head, rows, cls=""):
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def chip(bk):
    return f'<span class="chip {bk}">{BLABEL[bk]}</span>'


def sg(v, d=0):
    s = pct(v, d)
    return f'<span class="{"neg" if v is not None and v < -0.0005 else ""}">{s}</span>'


def pp(v):
    if v is None:
        return "–"
    return f'<span class="{"neg" if v < 0 else ""}">{"+" if v >= 0 else MINUS}{abs(v):.1f}pp</span>'


def pcv(v):
    return "–" if v is None else f"{v:.1f}%"


retail = [d for d in H if d['bm'] == 'retail']
mp = [d for d in H if d['bm'] == 'mp']
share = {k: sum(JO[d['brand']] for d in retail if bucket(d) == k) / sum(JO.values()) for k in BLABEL}

retail_rows = [[f"<b>{E(NM[d['brand']])}</b>", chip(bucket(d)), f"{d['ytd'] / 1e6:.2f}", sg(d['ytd_yoy']), f"{d['oct'] / 1e3:.0f}", sg(d['oct_yoy']),
                pcv(d['pc1']), pp(d['pc1_pp']), pcv(d['pc1o']), pp(d['pc1o_pp']), pcv(d['mkd25']), pcv(d['mkd24']),
                f"{d['woc']:.1f}", f"{d['fwoc']:.1f}", f"{d['rv'] / 1e6:.2f}", f"{d['fwd_rv'] / 1e6:.2f}"] for d in retail]
mp_rows = [[f"<b>{E(NM[d['brand']])}</b>", chip(bucket(d)), f"{d['ytd'] / 1e6:.2f}", sg(d['ytd_yoy']), f"{d['oct'] / 1e3:.0f}", sg(d['oct_yoy']),
            pcv(d['pc1']), pp(d['pc1_pp']), pcv(d['pc1o']), pp(d['pc1o_pp']), pcv(d['mkd25']), pcv(d['mkd24'])] for d in mp]
funnel_rows = [[f"<b>{E(NM[d['brand']])}</b>", chip(bucket(d)),
                sg(d['jo_gmv']) if d['jo_gmv'] is not None else '<span class="muted">new in 2026</span>',
                sg(d['imps']), sg(d['ctr']), sg(d['ucr']), f"{d['woc']:.1f}" if d['bm'] == 'retail' else "–"] for d in H]

TILES = [("Nov '26 GMV target", "AED 20.6M", "+25% vs Nov '25 (16.4M)", "hero"), ("Retail GMV target", "AED 17.9M", "+18% vs LY (15.2M) · 87% of target", "hero"),
         ("MP GMV target", "AED 2.7M", "+117% vs LY (1.2M) · 13% of target", "hero"),
         ("Impressions needed", "≈ 593M", "+46% vs LY (407M)", ""), ("Retail impressions", "≈ 499M", "+35% vs LY (369M) · 84%", ""),
         ("MP impressions", "≈ 93M", "+151% vs LY (37M) · 16%", ""),
         ("Year-end retail stock", "≤ 193K units", "10 WoC · LY closed 393K (20.4 wks)", ""), ("Stock available for Q4", "503K units", "AED 53.2M retail · 31.5M cost", ""),
         ("PC1 before rebates", "≈ +5%", f"LY {MINUS}5.2% · LLY +5.6%", "")]
tiles = "".join(f'<div class="tile {c}"><div class="tl">{E(a)}</div><div class="tv">{E(b)}</div><div class="ts">{E(s)}</div></div>' for a, b, s, c in TILES)

SECTIONS = [("target", "Target"), ("brands", "Focus brands"), ("stock", "Stock"), ("health", "Brand health"), ("themes", "Themes & asks"),
            ("learnings", "Learnings"), ("open", "Open items")]
nav = "".join(f'<a href="#{k}">{v}</a>' for k, v in SECTIONS)

CSS = """
/* Layout: one long scroll, 1080px reading column, sticky section rail; Beauty Pulse plum carries all emphasis. */
:root{
  --bg:#fbf9fa; --paper:#ffffff; --ink:#19151a; --ink2:#57505a; --muted:#8a838c; --line:#e6e1e7;
  --plum:#8a2a5c; --plum-soft:#f4e6ee; --plum-band:rgba(138,42,92,.07);
  --grey:#c3bec6; --grey2:#e2dfe4; --good:#1f7a3a; --good-f:rgba(31,122,58,.55); --bad:#b3261e; --bad-f:rgba(179,38,30,.55); --warn:#b26a00; --warn-f:rgba(214,145,22,.6);
  --zone:rgba(179,38,30,.05);
  --f-display:"Bricolage Grotesque", "Segoe UI", system-ui, sans-serif; --f-body:"IBM Plex Sans", "Segoe UI", system-ui, sans-serif; --f-data:"IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#141015; --paper:#1c171d; --ink:#f2edf2; --ink2:#c9c1ca; --muted:#9a929c; --line:#342c35;
  --plum:#d57aa8; --plum-soft:#3a2230; --plum-band:rgba(213,122,168,.10);
  --grey:#6d6670; --grey2:#4a444c; --good:#5cc27f; --good-f:rgba(92,194,127,.55); --bad:#ff7b72; --bad-f:rgba(255,123,114,.55); --warn:#f0b44c; --warn-f:rgba(240,180,76,.6);
  --zone:rgba(255,123,114,.07); color-scheme:dark }}
:root[data-theme="dark"]{
  --bg:#141015; --paper:#1c171d; --ink:#f2edf2; --ink2:#c9c1ca; --muted:#9a929c; --line:#342c35;
  --plum:#d57aa8; --plum-soft:#3a2230; --plum-band:rgba(213,122,168,.10);
  --grey:#6d6670; --grey2:#4a444c; --good:#5cc27f; --good-f:rgba(92,194,127,.55); --bad:#ff7b72; --bad-f:rgba(255,123,114,.55); --warn:#f0b44c; --warn-f:rgba(240,180,76,.6);
  --zone:rgba(255,123,114,.07); color-scheme:dark }
*{box-sizing:border-box}
body{background:var(--bg); color:var(--ink); font-family:var(--f-body); font-size:15px; line-height:1.55; padding-inline:16px}
.wrap{max-width:1080px; margin:0 auto; padding-block:40px 80px}
.rule{width:72px; height:3px; background:var(--plum); margin-bottom:28px}
.eyebrow{font:600 12px/1 var(--f-body); letter-spacing:.14em; text-transform:uppercase; color:var(--plum)}
h1{font:700 clamp(32px,5vw,52px)/1.05 var(--f-display); letter-spacing:-.02em; margin:12px 0 10px; text-wrap:balance}
.lede{color:var(--ink2); max-width:68ch; font-size:16px}
.meta{color:var(--muted); font-size:13px; margin-top:10px; font-family:var(--f-data)}
nav{position:sticky; top:env(safe-area-inset-top,0px); z-index:5; background:var(--bg); border-bottom:1px solid var(--line);
    display:flex; gap:4px 18px; flex-wrap:wrap; padding-block:10px; margin-block:28px 8px}
nav a{color:var(--ink2); text-decoration:none; font-size:13px; font-weight:500}
nav a:hover, nav a:focus-visible{color:var(--plum); outline:none; text-decoration:underline; text-underline-offset:4px}
section{padding-top:44px; scroll-margin-top:56px}
h2{font:700 26px/1.2 var(--f-display); color:var(--plum); margin:6px 0 6px; letter-spacing:-.01em; text-wrap:balance}
h2 .n{font-family:var(--f-data); font-weight:500; font-size:15px; color:var(--muted); margin-right:10px; vertical-align:3px}
h3{font:600 16px/1.3 var(--f-display); margin:28px 0 8px; text-wrap:balance}
p{max-width:72ch; margin:8px 0}
.kick{font-size:17px; color:var(--ink); max-width:70ch}
.tiles{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:22px}
.tile{background:var(--paper); border:1px solid var(--line); border-radius:10px; padding:16px 18px; min-width:0}
.tile.hero{background:var(--plum-soft); border-color:transparent}
.tl{font-size:12px; color:var(--ink2); letter-spacing:.02em}
.tv{font:700 30px/1.15 var(--f-display); margin:6px 0 4px; letter-spacing:-.01em; font-variant-numeric:tabular-nums}
.tile.hero .tv{color:var(--plum)}
.ts{font-size:12.5px; color:var(--muted)}
.fig{background:var(--paper); border:1px solid var(--line); border-radius:12px; padding:18px 18px 12px; margin-top:16px; overflow-x:auto}
.fig h4{font:600 15px/1.35 var(--f-display); margin:0 0 4px}
.fig .sub{color:var(--muted); font-size:12.5px; margin:0 0 10px}
.legend{display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; color:var(--ink2); margin-bottom:6px}
.legend i{display:inline-block; width:11px; height:11px; border-radius:2px; margin-right:6px; vertical-align:-1px}
.src{color:var(--muted); font-size:11.5px; margin-top:8px; font-family:var(--f-data)}
.chart{width:100%; min-width:620px; height:auto; display:block; font-family:var(--f-body)}
.grid{stroke:var(--line); stroke-width:1} .axisline{stroke:var(--grey); stroke-width:1}
.ref{stroke:var(--muted); stroke-width:1.5; stroke-dasharray:6 4}
.band{fill:var(--plum-band)} .zone-bad{fill:var(--zone)}
.line{fill:none; stroke-width:2} .line.ty{stroke:var(--plum); stroke-width:2.8} .line.ly{stroke:var(--grey)} .line.ly2{stroke:var(--grey2)} .dash{stroke-dasharray:5 4}
.dot.ty{fill:var(--plum)} .dot.ly{fill:var(--grey)} .dot.ly2{fill:var(--grey2)}
.hollow{fill:var(--paper); stroke:var(--plum); stroke-width:2} .target{fill:var(--plum-soft); stroke:var(--plum); stroke-width:2.5}
.tick-ty{stroke:var(--plum); stroke-width:3}
.b-ty{fill:var(--plum)} .b-ly{fill:var(--grey)} .b-ly2{fill:var(--grey2)} .b-hist{fill:var(--grey)} .b-good{fill:var(--good-f)} .b-bad{fill:var(--bad-f)}
.bub{stroke-width:1.2} .bub.stable{fill:var(--good-f); stroke:var(--good)} .bub.mid{fill:var(--warn-f); stroke:var(--warn)} .bub.high{fill:var(--bad-f); stroke:var(--bad)}
text{font-size:12px} .axis{fill:var(--muted)} .lab{fill:var(--ink2)} .lab-ty{fill:var(--plum)} .name{fill:var(--ink); font-weight:600}
.name-ty{fill:var(--plum); font-weight:700} .val{fill:var(--ink); font-weight:600} .val-ty{fill:var(--plum); font-weight:700}
.in-bar{fill:var(--ink); font-size:11.5px} .neg{fill:var(--bad); color:var(--bad)} .pos{fill:var(--good); font-weight:600}
.big{fill:var(--ink); font:700 17px var(--f-display)} .big-neg{fill:var(--bad); font:700 17px var(--f-display)}
.eyebrow-s{fill:var(--plum); font-size:10.5px; font-weight:700; letter-spacing:.12em} .eyebrow-bad{fill:var(--bad); font-size:10.5px; font-weight:700; letter-spacing:.12em}
.tw{overflow-x:auto; margin-top:14px; border:1px solid var(--line); border-radius:10px; background:var(--paper)}
table{border-collapse:collapse; width:100%; font-size:13px; font-variant-numeric:tabular-nums}
th{text-align:left; font-weight:600; font-size:11.5px; letter-spacing:.03em; color:var(--ink2); background:var(--plum-soft); padding:9px 10px; border-bottom:2px solid var(--plum); white-space:nowrap}
td{padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top}
table.num td:first-child{white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
table.num td:nth-child(n+3){text-align:right; white-space:nowrap} table.num th:nth-child(n+3){text-align:right}
td .neg{color:var(--bad)} .muted{color:var(--muted)}
.chip{display:inline-block; font-size:11.5px; font-weight:600; padding:2px 9px; border-radius:999px; white-space:nowrap}
.chip.stable{background:var(--good-f); color:var(--ink)} .chip.mid{background:var(--warn-f); color:var(--ink)} .chip.high{background:var(--bad-f); color:var(--ink)}
.cols{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px}
.card{background:var(--paper); border:1px solid var(--line); border-radius:10px; padding:16px 18px; min-width:0}
.card h4{margin:0 0 6px; font:600 14px var(--f-display)}
.brandlist{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px}
.brandlist span{font-size:12.5px; padding:3px 10px; border-radius:999px; border:1px solid var(--line); background:var(--bg)}
.brandlist span.lead{border-color:var(--plum); color:var(--plum); font-weight:600}
.bar3{display:flex; height:10px; border-radius:999px; overflow:hidden; margin:10px 0 6px; max-width:520px}
.bar3 i{display:block} .k{display:flex; gap:16px; flex-wrap:wrap; font-size:12.5px; color:var(--ink2)}
ul.tight{padding-left:18px; margin:8px 0} ul.tight li{margin:6px 0; max-width:72ch}
.learn{display:grid; grid-template-columns:44px minmax(0,1fr); gap:4px 14px; margin-top:28px}
.learn .num{font:700 30px/1 var(--f-display); color:var(--plum)}
.learn h3{margin:2px 0 4px}
.note{font-size:12.5px; color:var(--muted); max-width:90ch}
.checks li{list-style:none; margin:6px 0} .checks{padding-left:0} .checks li::before{content:"○"; color:var(--plum); margin-right:10px}
footer{margin-top:56px; padding-top:16px; border-top:1px solid var(--line); color:var(--muted); font-size:12px; display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap}
@media (max-width:760px){ .tiles{grid-template-columns:repeat(2,minmax(0,1fr))} .cols{grid-template-columns:1fr} .tv{font-size:24px} }
@media (max-width:460px){ .tiles{grid-template-columns:1fr} }
@media (prefers-reduced-motion:no-preference){ html{scroll-behavior:smooth} }
"""


def fig(title, sub, body, src, legend=None):
    lg = ""
    if legend:
        lg = '<div class="legend">' + "".join(f'<span><i style="background:var({c})"></i>{E(n)}</span>' for n, c in legend) + "</div>"
    return f'<div class="fig"><h4>{E(title)}</h4><p class="sub">{E(sub)}</p>{lg}{body}<div class="src">{E(src)}</div></div>'


agenda = tbl(["TY agenda", "What it takes", "Where we start"], [
    ["<b>November GMV +25% vs LY</b><br><span class='muted'>AED 20.6M</span>", "AED 685K a day vs 548K LY. About 593M impressions (+46%): 499M retail, 93M MP.", f"1–12 Oct is {MINUS}7% YoY. Retail UCR has been 26% below LY since July."],
    ["<b>Close 2026 under 10 WoC</b><br><span class='muted'>≤ 193K retail units</span>", "Sell 310K retail units from 13 Oct to 31 Dec.", "503K units available. Plan case closes at 117K (6.0 WoC); the risk is stock-outs."],
    ["<b>Protect the bottom line</b>", "Markdown at 40% or less. Push gift sets and launches (17–24% PC1).", f"Nov '25 PC1 was {MINUS}5.2% before rebates at 44% markdown."],
    ["<b>Win the event windows</b>", "Hero singles first half, then Black Friday. Keep the shoulders alive.", "Singles fell 26% LY; Black Friday held (+2%)."]])

margin = tbl(["Margin line", "Nov '24", "Nov '25", "Nov '26 commitment"], [
    ["Markdown, % of full price", "35.4%", "43.7%", "40% or less"],
    ["<b>PC1 before rebates</b>", "+5.6%", f"<span class='neg'>{MINUS}5.2%</span>", "<b>Back to about +5%</b>"],
    ["Rebates, % of revenue (LY only)", "no data", "15.5% (AED 2.36M)", "<span class='muted'>not used for TY</span>"],
    ["PC1 incl. rebates (LY only)", "–", "+10.3%", "<span class='muted'>not used for TY</span>"],
    ["EBITDA", "–", "–", "No worse than BP (assumption to insert)"]])

buckets = tbl(["Bucket", "Rule (1 Jul – 12 Oct vs LY)", "Brands", "Support required"], [
    [chip('stable'), f"GMV within {MINUS}12%, UCR not down more than 10%, WoC under 20", "Kylie Cosmetics, Armani, Lancôme · MP: all top 5", "Visibility. These brands convert well, so extra impressions turn into extra GMV."],
    [chip('mid'), "Between Stable and High", "KIKO Milano, Charlotte Tilbury, Kérastase, Elizabeth Arden, L'Oréal Professionnel, Estée Lauder, Anastasia Beverly Hills", "Impressions, plus extra promo funding from category."],
    [chip('high'), "GMV down 25%+ and WoC 20+", "NYX, MAC, Maybelline, Make Up For Ever, Clinique", "Impressions, category-led promo funding and flash sales, cross-selling with Fashion and Sports."]])

themes = tbl(["Theme", "Evidence", "Ask"], [
    ["<b>Win Singles, then Black Friday</b>", f"Singles {MINUS}26% LY: AED 1.1M of the 1.35M decline. Black Friday +2%.", "Hero singles in the first half, then Black Friday."],
    ["<b>Impressions plan</b>", "About 593M needed (+46%): retail 499M, MP 93M.", "BP / non-BP split based on conversion."],
    ["<b>Peaks and shoulders</b>", "9 event days ≈ 21 shoulder days ≈ AED 8–9M each.", "Own offers and visibility for pre- and post-event days."],
    ["<b>Gift sets</b>", f"Set PC1 17–20% vs core {MINUS}10% to +1%.", "Push to 100% sell-through."],
    ["<b>DM and CRM</b>", "Retargeting between peaks.", "Ring-fenced budget (amount TBC)."],
    ["<b>GCC</b>", f"Other GCC is 4% of Nov and {MINUS}70% YTD. KSA {MINUS}AED 1.3M vs Nov '24.", "Focus recovery on KSA."]])

funnel = tbl(["", "Retail", "MP", "Total"], [
    ["Nov '26 GMV target", "AED 17.9M", "AED 2.7M", "AED 20.6M"],
    ["Nov '25: CTR / UCR / ASP", "2.39% / 3.23% / AED 53.3", "2.00% / 2.76% / AED 60.2", ""],
    ["Jul–Oct TY vs LY: CTR / UCR / ASP", f"+2% / <span class='neg'>{MINUS}26%</span> / +8%", f"<span class='neg'>{MINUS}18%</span> / +23% / <span class='neg'>{MINUS}21%</span>", ""],
    ["Nov '26 at 70/30: CTR / UCR / ASP", "2.42% / 2.64% / AED 56.2", "1.74% / 3.19% / AED 51.4", ""],
    ["GMV per 1K impressions", "AED 41.2 → 35.8", "AED 33.2 → 28.7", "AED 40.4 → 34.9"],
    ["<b>Impressions needed</b>", "<b>≈ 499M (+35%)</b>", "<b>≈ 93M (+151%)</b>", "<b>≈ 593M (+46%)</b>"],
    ["Range: LY conversion → full Jul–Oct trend", "434–538M", "81–101M", "515–640M"]], "num")

owners = tbl(["Team", "Ask", "By"], [
    ["<b>Brand Partnerships</b>", "Lock November funding before any event markdown: no funding, no markdown. Secure gift sets and launches for Mid- and High-risk brands.", "25 Oct"],
    ["<b>Onsite</b>", "Plan about 593M impressions (499M retail, 93M MP). Front-load Pre 11.11 and BF week, and weight to brands above AED 40 per 1K.", "28 Oct"],
    ["<b>Category / Trading</b>", "Hero singles in the first half. Markdown at 40% or less. Category-led promo and flash sales for the five High-risk brands.", "31 Oct"],
    ["<b>CRM / DM</b>", "Retargeting plan for the shoulder days between peaks.", "28 Oct"],
    ["<b>Planning / Supply</b>", "Track PO landing (91% due before 1 Nov). Watch December cover on NYX and Make Up For Ever.", "1 Nov"],
    ["<b>Finance</b>", "EBITDA BP assumption for November.", "25 Oct"]])

RET15 = ["KIKO Milano", "Charlotte Tilbury", "Kérastase", "MAC", "NYX", "Kylie Cosmetics", "Elizabeth Arden", "L'Oréal Professionnel", "Make Up For Ever",
         "Estée Lauder", "Lancôme", "Armani", "Maybelline", "Anastasia Beverly Hills", "Clinique"]
MP5 = ["Clara", "Louzan", "Laverne", "Bath & Body Works", "H&M"]
bl = lambda xs: "".join(f'<span class="{"lead" if i < 3 else ""}">{E(n)}</span>' for i, n in enumerate(xs))

bar3 = (f'<div class="bar3"><i style="width:{share["high"] * 100:.0f}%;background:var(--bad-f)"></i><i style="width:{share["mid"] * 100:.0f}%;background:var(--warn-f)"></i>'
        f'<i style="width:{share["stable"] * 100:.0f}%;background:var(--good-f)"></i></div>'
        f'<div class="k"><span>High risk {share["high"] * 100:.0f}%</span><span>Mid risk {share["mid"] * 100:.0f}%</span><span>Stable {share["stable"] * 100:.0f}%</span><span class="muted">of top-15 retail GMV since 1 Jul</span></div>')

LY_LEG = [("Nov '24", "--grey2"), ("Nov '25", "--grey")]

page = f"""<title>Beauty November '26 Strategy</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header>
  <div class="rule"></div>
  <div class="eyebrow">Beauty Pulse · Strategy</div>
  <h1>Beauty · November '26 Strategy</h1>
  <p class="lede">Grow November GMV 25% on last year and close 2026 under 10 weeks of cover. Built on the November 2024 and 2025 flashback, this year's trends to 12 October, and the stock and open POs on hand.</p>
  <div class="meta">As of 12 Oct 2026 · Namshi marketplaces, Beauty, excl. samples &amp; GWP</div>
</header>
<nav aria-label="Sections">{nav}</nav>

<section id="summary">
  <div class="eyebrow">Summary</div>
  <div class="tiles">{tiles}</div>
  {agenda}
</section>

<section id="target">
  <h2><span class="n">01</span>Target: +25% GMV and a protected bottom line</h2>
  <p class="kick"><b>AED 20.6M in November:</b> +25% on Nov '25 and +16% on Nov '24. It's a stretch: November must reach 3.2x September's daily GMV (LY 1.9x, LLY 2.2x). The trend is improving, from {MINUS}28% YoY in September to {MINUS}7% for 1–12 October.</p>
  {fig("The Nov '26 target of AED 20.6M is 16% above the Nov '24 peak", "Beauty GMV by month, AED. 2026 is running 28% below 2025 to September.", chart_monthly(), "sales_metrics · Jan 2024 – 12 Oct 2026 · Oct target from the planning table", [("2026 and plan", "--plum"), ("2025", "--grey"), ("2024", "--grey2")])}
  {fig("Biggest lifts needed in Pre 11.11 and Black Friday week, +35% per day vs LY", "GMV per day by November cohort. Shaded: event cohorts. Under each cohort: Nov '26 total and per-day change vs Nov '25.", chart_cohorts(), "Official November targets aren't loaded yet (October's are, AED 8.6M). AED 20.6M is split on the last two Novembers' daily pattern.", LY_LEG + [("Nov '26 target", "--plum")])}
  <h3>Margin commitment</h3>
  {margin}
</section>

<section id="brands">
  <h2><span class="n">02</span>Focus brands</h2>
  <p class="kick">Ranked by GMV from 1 Jul to 12 Oct 2026. Together they are <b>63% of Beauty GMV</b>.</p>
  <div class="cols">
    <div class="card"><h4>Retail · top 15 = 63% of retail GMV</h4><div class="brandlist">{bl(RET15)}</div></div>
    <div class="card"><h4>MP · top 5 = 62% of MP GMV</h4><div class="brandlist">{bl(MP5)}</div><p class="note">Clara alone is 37% of MP GMV. Benefit is excluded (discontinued).</p></div>
  </div>
</section>

<section id="stock">
  <h2><span class="n">03</span>Stock: enough to hit the target, and the 10-week cap is within reach</h2>
  {fig("We close under the 193K cap if retail holds October's trend or hits the November target", "Year-end retail units. 2026 = 503K available, minus retail sales from 13 Oct to 31 Dec. Red: over the cap.", chart_stock(), "psku_sku_mapped and stock_summary_history, 12 Oct · POs ETA before 31 Dec at 80% fill · WoC vs Dec '25 retail units (19.3K a week)")}
  <ul class="tight">
    <li><b>503K retail units available</b> (262K on hand + 241K from POs at 80% fill) = <b>AED 53.2M</b> at retail, 3.0x November's retail need. 91% of PO units land before 1 Nov.</li>
    <li><b>Plan case: sell 275K retail units in November and close the year at 117K (6.0 WoC).</b> AED 17.9M retail at ASP AED 65. October is running at AED 97; ASP fell 27% from October to November in 2024 and 36% in 2025, which points to 62–71. Rest of October at the 7–13 Oct run-rate of 1.8K units a day: 35K units. December at −10% vs LY: 77K units. Range: 103K at ASP 62 to 140K at ASP 71. At last November's ASP of 53.3 it would take 336K units and close at 56K.</li>
    <li><b>The risk is running out of stock, not overstock.</b> NYX and Make Up For Ever cover their November need only 1.1x.</li>
  </ul>
  <p class="note">Method: retail GMV only. Sales from 13 Oct to 31 Dec = LY retail GMV × TY trend ÷ TY retail ASP; Plan case: 13–31 Oct = 7–13 Oct retail units per day × 19; November = retail target ÷ ASP 65; December −10% vs LY units (387K units 13 Oct – 31 Dec). PO SKUs with no live price are valued at cost × 1.35.</p>
</section>

<section id="health">
  <h2><span class="n">04</span>Brand health and risk buckets</h2>
  <p class="kick"><b>{share["high"] * 100:.0f}% of top-15 retail GMV sits in High-risk brands.</b> Buckets are set on post-July trends vs LY and current weeks of cover.</p>
  {bar3}
  {buckets}
  {fig("High-risk brands are 25–50% behind LY since July and sit on 20+ weeks of cover", "Retail top 15. GMV since July vs LY (x) and current WoC on last-45-day sales (y). Bubble size = GMV since July.", chart_risk(), "sales_metrics, psku_sku_mapped · 1 Jul – 12 Oct 2026 vs 2025", [("Stable", "--good-f"), ("Mid risk", "--warn-f"), ("High risk", "--bad-f")])}
  <h3>Retail · top 15</h3>
  {tbl(["Brand", "Bucket", "YTD GMV (M)", "YoY", "Oct GMV (K)", "YoY", "YTD PC1", "YoY", "Oct PC1", "YoY", "Nov '25 MKD", "Nov '24 MKD", "WoC now", "Fwd WoC", "Retail value now (M)", "Fwd retail value (M)"], retail_rows, "num")}
  <h3>MP · top 5</h3>
  {tbl(["Brand", "Bucket", "YTD GMV (M)", "YoY", "Oct GMV (K)", "YoY", "YTD PC1", "YoY", "Oct PC1", "YoY", "Nov '25 MKD", "Nov '24 MKD"], mp_rows, "num")}
  <h3>Post-July funnel vs LY: the evidence behind each bucket</h3>
  {tbl(["Brand", "Bucket", "GMV", "Impressions", "CTR", "UCR", "WoC now"], funnel_rows, "num")}
  <p class="note">YTD = 1 Jan – 12 Oct; Oct = 1–12 Oct. PC1 is before rebates (pc1_gross / rev_gross); YoY in points. MKD = markdown as a share of full price. WoC now = stock on 12 Oct ÷ average weekly retail units over the last 45 days; Fwd WoC adds 80% of open POs. Louzan, Laverne and Bath &amp; Body Works are new in 2026.</p>
</section>

<section id="themes">
  <h2><span class="n">05</span>Key themes and asks</h2>
  {fig("Most of last year's decline came from the Singles window. Black Friday held.", "Beauty GMV by November window, AED.", chart_windows(), "sales_metrics · 1–30 Nov 2024 and 2025", [("Nov 2024", "--grey2"), ("Nov 2025", "--plum")])}
  {themes}
  <h3>Impressions needed, by retail and MP</h3>
  <p>Each segment's Nov '25 funnel, adjusted 70% by its own Jul–Oct trend vs LY and 30% unchanged. Retail's gap is conversion; MP's is CTR and ASP. Getting retail UCR back to LY would bring the total close to 515M.</p>
  {funnel}
  {fig("The best converters get less traffic than their GMV share", "Nov '25, top brands, sorted by GMV per 1K impressions. Plum = share of GMV, grey = share of impressions.", chart_share(), "sales_metrics, onsite_measures · 1–30 Nov 2025")}
</section>

<section id="learnings">
  <h2><span class="n">06</span>What Nov '24 and Nov '25 taught us</h2>
  <div class="learn"><div class="num">1</div><div><h3>UCR rises on heavy-traffic days</h3><p>Traffic and conversion grow together: correlation 0.78–0.79 in both years.</p>
  {fig("Busiest days convert at about 3.7% vs 2.3–2.5% on the quietest", "November days split into thirds by Beauty impressions. UCR = units / product views.", chart_ucr(), "onsite_measures, sales_metrics · 1–30 Nov", [("Nov 2024", "--grey"), ("Nov 2025", "--plum")])}</div></div>
  <div class="learn"><div class="num">2</div><div><h3>Traffic isn't going where it converts best</h3><p>GMV per 1K impressions: Kérastase AED 134, Charlotte Tilbury AED 63, La Roche-Posay AED 62, vs a Beauty average of AED 40.</p></div></div>
  <div class="learn"><div class="num">3</div><div><h3>Sets and launches are November's margin heroes</h3><p>In 2025, set GMV fell 34% and launch GMV fell 42%. A strong line-up is the cheapest way to protect PC1.</p>
  {fig("Sets and launches carry November margin; they grew fastest in 2024, not 2025", "Bars: November daily GMV as a multiple of Sep–Oct. Below: November PC1 before rebates.", chart_sets(), "sales_metrics, item_d · sets = gift_sets, launches = live < 120 days", [("Nov 2024", "--grey"), ("Nov 2025", "--plum")])}</div></div>
  <div class="learn"><div class="num">4</div><div><h3>Deeper markdown did not buy growth</h3><p>Markdown went from 35% to 44%, GMV fell 8%, and PC1 before rebates went from +5.6% to {MINUS}5.2%. Rebates (AED 2.36M) lifted LY to +10.3%, but half went to NYX and Maybelline; Charlotte Tilbury and Kylie had none. <b>No event markdown without agreed brand funding.</b></p></div></div>
</section>

<section id="open">
  <h2><span class="n">07</span>Open items</h2>
  <ul class="checks">
    <li>Official November daily targets in the planning table (Planning)</li>
    <li>EBITDA BP assumption for November (Finance)</li>
    <li>Share of promo funded by each brand, TY / LY / LLY (Brand Partnerships)</li>
    <li>BP vs non-BP brand list, to split the 593M impressions (Onsite)</li>
    <li>DM and CRM budget amount (Marketing)</li>
  </ul>
</section>

<footer><span>Beauty Pulse · November '26 Strategy</span><span>Sources: sales_metrics, onsite_measures, psku_sku_mapped, stock_summary_history, po_expected_received_union, rebate_income · as of 12 Oct 2026</span></footer>
</div>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(OUT, len(page))
