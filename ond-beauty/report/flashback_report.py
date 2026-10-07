"""Beauty Pulse · Nov Flashback PDF report.

python3 ond-beauty/report/flashback_report.py  ->  ond-beauty/dist/data/nov_flashback_report.pdf

A detailed LY / LLY November flashback built from the same data as the dashboard's Nov Flashback tab (build.pack_flashback,
data/flashback_daily.json) plus the retail stock / units sets (data/assort_raw.json, data/retail_raw.json) for the WoC plan.
TY agenda: November GMV +25% vs LY, retail WoC under 10 weeks at the end of November.
"""
import datetime as D
import io
import json
import math
import pathlib
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "dist" / "data" / "nov_flashback_report.pdf"
WOC_CAP = 10

# ---------- look ----------
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("DV", FONT))
pdfmetrics.registerFont(TTFont("DVB", FONTB))
ACC = "#8a2a5c"; ACC_SOFT = "#f4e6ee"; GOOD = "#006300"; BAD = "#b3261e"; WARN = "#8a5300"; MUTED = "#8a838c"; INK = "#19151a"; INK2 = "#57505a"; LINE = "#e6e1e7"; FLAT = "#eeebef"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": "#c9c2ca", "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})
S = {
    "h1": ParagraphStyle("h1", fontName="DVB", fontSize=17, leading=21, textColor=colors.HexColor(INK), spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="DVB", fontSize=12.5, leading=16, textColor=colors.HexColor(ACC), spaceBefore=6, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="DVB", fontSize=10, leading=13, textColor=colors.HexColor(INK), spaceBefore=4, spaceAfter=2),
    "p": ParagraphStyle("p", fontName="DV", fontSize=8.6, leading=12, textColor=colors.HexColor(INK)),
    "small": ParagraphStyle("small", fontName="DV", fontSize=7.4, leading=10, textColor=colors.HexColor(INK2)),
    "b": ParagraphStyle("b", fontName="DV", fontSize=8.6, leading=12, textColor=colors.HexColor(INK), leftIndent=10, bulletIndent=2, spaceAfter=2),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=7.2, leading=9, textColor=colors.HexColor(INK)),
    "cellb": ParagraphStyle("cellb", fontName="DVB", fontSize=7.2, leading=9, textColor=colors.HexColor(INK)),
}
W, H = landscape(A4)
CW = W - 28 * mm


def P(t, st="p"):
    return Paragraph(t, S[st])


def bullets(items, st="b"):
    return [Paragraph(t, S[st], bulletText="•") for t in items]


def K(v):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "–"
    a = abs(v)
    if a >= 1e9: return f"{v / 1e9:.2f}B"
    if a >= 1e6: return f"{v / 1e6:.{0 if a >= 1e8 else 1 if a >= 1e7 else 2}f}M"
    if a >= 1e3: return f"{v / 1e3:.{0 if a >= 1e5 else 1}f}K"
    return f"{v:.0f}"


def pc(v, d=0):
    if v is None or not math.isfinite(v): return "–"
    return ("+" if v > 0 else "−" if v < 0 else "±") + f"{abs(v) * 100:.{d}f}%"


def pp(v):
    if v is None or not math.isfinite(v): return "–"
    return ("+" if v > 0 else "−" if v < 0 else "±") + f"{abs(v) * 100:.1f}pp"


def pct(v, d=1):
    return "–" if v is None or not math.isfinite(v) else f"{v * 100:.{d}f}%"


def col(v, inv=False):
    if v is None or not math.isfinite(v) or abs(v) < 1e-9: return INK
    return GOOD if (v > 0) != inv else BAD


def cp(v, d=0, inv=False):
    return f'<font color="{col(v, inv)}">{pc(v, d)}</font>'


def nm(k):
    t = k.replace("_", " ")
    return t.title() if "_" in k or t.islower() and " " not in t and len(t) > 3 and k not in CATS else t


def table(rows, widths, head=1, zebra=True, align_right_from=1, bold_last=False, extra=None):
    data = [[c if isinstance(c, Paragraph) else Paragraph(str(c), S["cellb" if r < head else "cell"]) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=head)
    st = [("FONT", (0, 0), (-1, -1), "DV", 7.2), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("LINEBELOW", (0, head - 1), (-1, head - 1), 0.8, colors.HexColor(ACC)),
          ("LINEBELOW", (0, head), (-1, -1), 0.3, colors.HexColor(LINE)),
          ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if zebra:
        for r in range(head, len(rows)):
            if (r - head) % 2: st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#faf8fa")))
    if bold_last:
        st.append(("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), colors.HexColor(FLAT)))
    if extra: st += extra
    t.setStyle(TableStyle(st))
    return t


def fig_img(fig, w):
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=200, bbox_inches="tight"); plt.close(fig); buf.seek(0)
    from reportlab.lib.utils import ImageReader
    ir = ImageReader(buf); iw, ih = ir.getSize()
    buf.seek(0)
    return Image(buf, width=w, height=w * ih / iw)


# ---------- data ----------
FB = build.pack_flashback()
YRS = FB["years"]                     # [2024, 2025, 2026]
PER = FB["periods"]; WIN = [p["p"] for p in PER]; U = FB["uplift"]
DAYS = FB["days"]
SHORT = {"MS": "MS", "Pre 11.11": "Pre 11.11", "11.11 Day": "11.11", "Post 11.11": "Post 11.11", "BAU 2": "BAU week",
         "Black Friday Week": "YF Week", "Black Friday Pre": "Pre YF", "Black Friday": "YF", "Black Friday Post": "YF Post"}
EVENT = lambda c: not (c.startswith("MS") or c.startswith("BAU"))
TYD = {p["p"]: (D.date.fromisoformat(p["ty"][1]) - D.date.fromisoformat(p["ty"][0])).days + 1 for p in PER}


def fsum(r, yi, ps):
    o = [0.0] * 6; d = 0
    for p in ps:
        for i in range(6): o[i] += r["v"][yi][p][i]
        d += DAYS[yi][p]
    return o, d


def stat(r, yi, ps):
    a, d = fsum(r, yi, ps); s, sd = fsum(r, yi, [0])
    g, im = a[0], a[5]; gpd = g / d if d else None; ipd = im / d if d else None
    sg = s[0] / sd if sd else 0; si = s[5] / sd if sd else 0
    mk = a[2] / a[3] if a[3] > 0 else None; smk = s[2] / s[3] if s[3] > 0 else None
    o = dict(g=g, u=a[1], gv=a[4], im=im, d=d, gpd=gpd, ipd=ipd, mk=mk, smk=smk, sgpd=sg, sipd=si,
             spG=(gpd / sg - 1) if sg >= 300 and gpd is not None else None, spI=(ipd / si - 1) if si >= 5000 and ipd is not None else None,
             gpi=g / im if im > 0 else None, sgpi=s[0] / s[5] if s[5] > 0 else None,
             ucr=a[1] / a[4] if a[4] else None, ctr=a[4] / im if im else None, asp=g / a[1] if a[1] else None)
    o["dMk"] = (mk - smk) if mk is not None and smk is not None else None
    o["drv"] = driver(o)
    return o


def driver(o):
    if o["spG"] is None or not o["g"]: return None
    if abs(o["spG"]) < 0.1: return "Neutral"
    if o["spG"] < 0: return "Declined"
    G = math.log1p(o["spG"]); I = math.log1p(o["spI"]) if o["spI"] is not None and o["spI"] > -1 else 0
    mk = (o["dMk"] or 0) >= 0.03
    if I / G >= 0.6: return "Imps + markdown" if mk else "Impressions-led"
    return "Markdown-led" if mk else "Organic"


ALL = FB["lv"]["all"][0]
CATS = {r["k"] for r in FB["lv"]["cat"]} | {x for r in FB["lv"]["sub"] for x in r["k"].split("|")}
S26 = fsum(ALL, 2, [0])[0]; GPI26 = S26[0] / S26[5]; IPD26 = S26[5] / DAYS[2][0]


def lift(o):
    return min(3, max(0.3, o["gpi"] / o["sgpi"])) if o["gpi"] and o["sgpi"] else None


def plan(r, ps, parent=None, lv=None):
    """2026: target = LY GMV × uplift; impressions = target ÷ (today's GMV per impression × average LY / LLY lift)."""
    own = fsum(r, 2, [0])[0]; cur = own
    if (own[5] < 2e5 or own[1] < 30) and parent: cur = fsum(parent, 2, [0])[0]
    gpi = cur[0] / cur[5] if cur[5] > 0 and cur[0] > 0 else None
    ra = FB["realloc"].get(r["k"]) if lv == "brand" else None; gone = bool(ra and ra.get("gone"))
    tgt = need = lo = hi = 0
    for p in ps:
        o1, o0 = stat(r, 1, [p]), stat(r, 0, [p]); t = 0 if gone else o1["g"] * U + (ra["add"][p] * U if ra else 0)
        l1 = lift(o1) or lift(o0) or 1; l0 = lift(o0) or l1
        tgt += t
        if gpi: need += t / (gpi * (l1 + l0) / 2); lo += t / (gpi * max(l1, l0)); hi += t / (gpi * min(l1, l0))
    ly = stat(r, 1, ps)
    return dict(gone=gone, tgt=tgt, need=need if gpi else None, lo=lo, hi=hi, lyim=ly["im"], vs=(need / ly["im"] - 1) if gpi and ly["im"] else None)


# daily
DAILY = {r["d"]: r for r in json.loads((DATA / "flashback_daily.json").read_text())}


def month_days(y, m):
    return sorted(d for d in DAILY if d.startswith(f"{y}-{m:02d}"))


def dagg(ds):
    o = dict(g=0, u=0, gv=0, im=0, mkd=0, np=0, n=0)
    for d in ds:
        r = DAILY.get(d)
        if not r: continue
        o["g"] += r["g"]; o["u"] += r["u"]; o["gv"] += r["gv"]; o["im"] += r["im"]; o["mkd"] += r["mkd"]; o["np"] += r["np"]; o["n"] += 1
    o["gpd"] = o["g"] / o["n"] if o["n"] else None; o["ipd"] = o["im"] / o["n"] if o["n"] else None; o["mk"] = o["mkd"] / o["np"] if o["np"] else None
    return o


# ---------- retail stock / WoC ----------
RET = json.loads((DATA / "retail_raw.json").read_text()); AS = json.loads((DATA / "assort_raw.json").read_text())


def drange(a, b):
    d = D.date.fromisoformat(a); e = D.date.fromisoformat(b); o = []
    while d <= e: o.append(d.isoformat()); d += D.timedelta(1)
    return o


def runits(ds, key):
    u = defaultdict(float); c = defaultdict(float)
    for d in ds:
        for r in RET.get(d, "").split(";"):
            if not r: continue
            x = r.split(",")
            if x[0] not in ("0", "1"): continue
            k = key(x); u[k] += float(x[6]); c[k] += float(x[7])
    return u, c


def rstock(d, key):
    o = defaultdict(float)
    for r in AS[d].split(";"):
        x = r.split(","); o[key(x)] += float(x[8])
    return o


STOCK_DAY = max(d for d in AS if d.startswith("2026"))
SD = D.date.fromisoformat(STOCK_DAY)
L30 = drange((SD - D.timedelta(29)).isoformat(), STOCK_DAY)
MTD_TY = drange("2026-10-01", STOCK_DAY); MTD_LY = drange("2025-10-01", (SD.replace(year=2025)).isoformat())
L30_LY = drange((SD.replace(year=2025) - D.timedelta(29)).isoformat(), SD.replace(year=2025).isoformat())
REST_LY = drange((SD.replace(year=2025) + D.timedelta(1)).isoformat(), "2025-10-31")
NOV_LY = drange("2025-11-01", "2025-11-30"); NOV_LLY = drange("2024-11-01", "2024-11-30")


def woc_table(key):
    st = rstock(STOCK_DAY, key); u30, _ = runits(L30, key); tym, _ = runits(L30, key); lym, _ = runits(L30_LY, key)
    rest, _ = runits(REST_LY, key); nov, novc = runits(NOV_LY, key)
    stly = rstock("2025-11-30", key); stlly = rstock("2024-11-30", key); novll, _ = runits(NOV_LLY, key)
    out = {}
    for k in set(st) | set(nov):
        trend = (tym[k] / lym[k]) if lym[k] >= 50 else 1.0
        trend = min(1.5, max(0.5, trend))
        s_rest = rest[k] * trend; s_nov = nov[k] * U; wk = s_nov / 30 * 7
        end0 = st[k] - s_rest - s_nov                          # end-Nov stock with no inbound
        need_min = max(0.0, -end0)                             # inbound so the plan does not stock out
        cap = WOC_CAP * wk                                     # end-Nov stock at WoC 10
        out[k] = dict(stock=st[k], u30=u30[k], woc=(st[k] / (u30[k] / 30 * 7)) if u30[k] else None, trend=trend,
                      s_rest=s_rest, s_nov=s_nov, end0=end0, need_min=need_min, cap=cap, otb_max=max(0.0, cap - end0),
                      cpu=(novc[k] / nov[k]) if nov[k] else None,
                      ly_end_woc=(stly[k] / (nov[k] / 30 * 7)) if nov[k] else None, lly_end_woc=(stlly[k] / (novll[k] / 30 * 7)) if novll[k] else None,
                      ly_nov=nov[k])
    return out


WOC_ALL = woc_table(lambda x: "all")["all"]
WOC_CAT = woc_table(lambda x: x[2])
WOC_BR = woc_table(lambda x: x[1])
WOC_C = woc_table(lambda x: "KSA" if x[0] == "0" else "UAE")


# ---------- charts ----------
def chart_nov(y):
    key = "llyd" if y == YRS[0] else "lyd"
    coh = {}
    for p in PER:
        for d in p[key]: coh[d] = p
    days = month_days(y, 11); sep = dagg(month_days(y, 9)); octo = dagg(month_days(y, 10))
    mx = max(max(DAILY[d]["g"] for d in month_days(yy, 11)) for yy in YRS[:2]) * 1.12
    fig, (ax, axm) = plt.subplots(2, 1, figsize=(11, 3.6), gridspec_kw={"height_ratios": [5, 0.9]}, sharex=True)
    i = 0
    while i < len(days):
        P = coh.get(days[i]); j = i
        while j + 1 < len(days) and coh.get(days[j + 1]) is P: j += 1
        if P:
            ev = EVENT(P["cohort"])
            ax.add_patch(Rectangle((i + 0.55, 0), j - i + 0.9, mx, color=ACC_SOFT if ev else FLAT, alpha=0.8 if ev else 0.6, lw=0))
            narrow = (j - i) < 2; k_ = sum(1 for q in range(i) if coh.get(days[q]) is not coh.get(days[q - 1] if q else None)) if narrow else 0
            ax.text((i + j) / 2 + 1, mx * (0.965 if not narrow or k_ % 2 == 0 else 1.035), SHORT[P["cohort"]], ha="center", va="top", fontsize=7.5,
                    color=ACC if ev else INK2, fontweight="bold" if ev else "normal")
        i = j + 1
    xs = list(range(1, len(days) + 1))
    cols_ = [ACC if coh.get(d) and EVENT(coh[d]["cohort"]) else "#b9b2bb" for d in days]
    ax.bar(xs, [DAILY[d]["g"] for d in days], color=cols_, width=0.72, zorder=3)
    ax.axhline(sep["gpd"], color=INK2, ls=(0, (5, 4)), lw=1, zorder=4); ax.axhline(octo["gpd"], color=INK2, ls=(0, (1, 2)), lw=1, zorder=4)
    ax.text(len(days) + 0.9, sep["gpd"], f"Sept {K(sep['gpd'])}", va="bottom" if sep["gpd"] >= octo["gpd"] else "top", fontsize=7, color=INK2)
    ax.text(len(days) + 0.9, octo["gpd"], f"Oct {K(octo['gpd'])}", va="top" if sep["gpd"] >= octo["gpd"] else "bottom", fontsize=7, color=INK2)
    ax.set_ylim(0, mx); ax.set_xlim(0.4, len(days) + 3.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: K(v)))
    ax.set_title(f"{'LY' if y == YRS[1] else 'LLY'} · November {y} · Beauty GMV per day", loc="left", fontsize=10, fontweight="bold", color=INK)
    mks = [DAILY[d]["mkd"] / DAILY[d]["np"] for d in days]
    axm.imshow([mks], aspect="auto", cmap="YlOrBr", vmin=0.1, vmax=0.65, extent=(0.5, len(days) + 0.5, 0, 1))
    for k, v in enumerate(mks): axm.text(k + 1, 0.5, f"{v * 100:.0f}", ha="center", va="center", fontsize=6.5, color="white" if v > 0.42 else INK)
    axm.set_yticks([0.5]); axm.set_yticklabels(["MKD %"]); axm.set_xticks(xs[::2] + ([xs[-1]] if len(xs) % 2 == 0 else []))
    for sp in ("left", "bottom"): axm.spines[sp].set_visible(False)
    fig.tight_layout()
    return fig


def chart_scatter():
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    for y, c, a in ((YRS[0], "#b9b2bb", 0.9), (YRS[1], ACC, 0.9)):
        sep = dagg(month_days(y, 9)); gpi0 = sep["g"] / sep["im"]
        xs = [DAILY[d]["im"] / sep["ipd"] for d in month_days(y, 11)]; ys = [DAILY[d]["g"] / DAILY[d]["im"] / gpi0 - 1 for d in month_days(y, 11)]
        ax.scatter(xs, ys, s=26, color=c, alpha=a, label=f"Nov {y}", edgecolor="white", lw=0.6, zorder=3)
    ax.axhline(0, color=INK2, ls=(0, (5, 4)), lw=1)
    ax.set_xlabel("Impressions per day vs that year's September (×)"); ax.set_ylabel("GMV per impression vs September")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: pc(v)))
    ax.legend(frameon=False, fontsize=8); ax.grid(axis="y", color=LINE, lw=0.6)
    fig.tight_layout(); return fig


def chart_cohort_bars():
    labels = [SHORT[p["cohort"]] for p in PER]; x = range(len(PER))
    g0 = [stat(ALL, 0, [p["p"]])["gpd"] for p in PER]; g1 = [stat(ALL, 1, [p["p"]])["gpd"] for p in PER]
    m0 = [stat(ALL, 0, [p["p"]])["mk"] for p in PER]; m1 = [stat(ALL, 1, [p["p"]])["mk"] for p in PER]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 2.9))
    w = 0.38
    a1.bar([i - w / 2 for i in x], g0, w, color="#b9b2bb", label=str(YRS[0])); a1.bar([i + w / 2 for i in x], g1, w, color=ACC, label=str(YRS[1]))
    a1.set_xticks(list(x)); a1.set_xticklabels(labels, rotation=30, ha="right"); a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: K(v)))
    a1.set_title("GMV per day by cohort", loc="left", fontsize=9.5, fontweight="bold"); a1.legend(frameon=False, fontsize=7.5); a1.grid(axis="y", color=LINE, lw=0.6)
    a2.bar([i - w / 2 for i in x], [v * 100 for v in m0], w, color="#b9b2bb", label=str(YRS[0])); a2.bar([i + w / 2 for i in x], [v * 100 for v in m1], w, color=WARN, label=str(YRS[1]))
    a2.set_xticks(list(x)); a2.set_xticklabels(labels, rotation=30, ha="right"); a2.set_title("Markdown % by cohort", loc="left", fontsize=9.5, fontweight="bold")
    a2.legend(frameon=False, fontsize=7.5); a2.grid(axis="y", color=LINE, lw=0.6)
    fig.tight_layout(); return fig


def chart_brand(r):
    fig, ax = plt.subplots(figsize=(5.4, 1.55))
    v0 = [stat(r, 0, [p])["gpd"] or 0 for p in WIN]; v1 = [stat(r, 1, [p])["gpd"] or 0 for p in WIN]
    x = range(len(WIN)); w = 0.4
    ax.bar([i - w / 2 for i in x], v0, w, color="#b9b2bb", label=str(YRS[0])); ax.bar([i + w / 2 for i in x], v1, w, color=ACC, label=str(YRS[1]))
    ax.set_xticks(list(x)); ax.set_xticklabels([SHORT[p["cohort"]] for p in PER], fontsize=6.2, rotation=25, ha="right")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: K(v))); ax.tick_params(axis="y", labelsize=6.5)
    ax.legend(frameon=False, fontsize=6.5, loc="upper left"); ax.grid(axis="y", color=LINE, lw=0.5)
    fig.tight_layout(); return fig


def chart_woc():
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    labels = ["LLY end Nov", "LY end Nov", "TY now (6 Oct)", "TY end Nov\n(no inbound)"]
    end0w = WOC_ALL["end0"] / (WOC_ALL["s_nov"] / 30 * 7)
    vals = [WOC_ALL["lly_end_woc"], WOC_ALL["ly_end_woc"], WOC_ALL["woc"], end0w]
    cs = ["#b9b2bb", "#b9b2bb", ACC, BAD if end0w < 0 else ACC]
    ax.bar(labels, vals, color=cs, width=0.6)
    for i, v in enumerate(vals): ax.text(i, v + (0.6 if v >= 0 else -1.6), f"{v:.1f} wk", ha="center", fontsize=8, fontweight="bold")
    ax.axhline(WOC_CAP, color=GOOD, ls=(0, (5, 4)), lw=1.2); ax.text(3.45, WOC_CAP + 0.4, f"cap {WOC_CAP} wk", ha="right", fontsize=7.5, color=GOOD)
    ax.axhline(0, color=INK2, lw=0.8); ax.set_ylabel("weeks of cover"); ax.grid(axis="y", color=LINE, lw=0.5)
    fig.tight_layout(); return fig


# ---------- content ----------
RA = sorted(((k, sum(v["add"])) for k, v in FB["realloc"].items() if not v.get("gone")), key=lambda t: -t[1]); RA_T = sum(v for _, v in RA) or 1


def build_story():
    st = []
    o0, o1 = stat(ALL, 0, WIN), stat(ALL, 1, WIN); pl = plan(ALL, WIN)
    sep25, sep24, oct25, oct24 = dagg(month_days(2025, 9)), dagg(month_days(2024, 9)), dagg(month_days(2025, 10)), dagg(month_days(2024, 10))
    per = [(p, stat(ALL, 0, [p["p"]]), stat(ALL, 1, [p["p"]])) for p in PER]
    worst = sorted(per, key=lambda t: (t[2]["gpd"] / t[1]["gpd"] - 1))[:3]
    best = max(per, key=lambda t: (t[2]["gpd"] / t[1]["gpd"] - 1))
    f = lambda yy: dict(ctr=yy[4] / yy[5], ucr=yy[1] / yy[4], asp=yy[0] / yy[1], gpk=yy[0] / yy[5] * 1000)
    fun = {y: f(fsum(ALL, i, [0])[0]) for i, y in enumerate(YRS)}
    W_ = WOC_ALL; wk_nov = W_["s_nov"] / 30 * 7

    # cover
    st += [Spacer(1, 30 * mm), P("Beauty · November Flashback", "h1"),
           P(f"LY ({YRS[1]}) and LLY ({YRS[0]}) November, cohort by cohort, against each year's September and October, and what it means for November 2026.", "p"),
           Spacer(1, 6 * mm)]
    agenda = table([["TY agenda", "What it takes", "Where we start"],
                    [P("<b>November GMV +25% vs LY</b>", "cell"), P(f"{K(pl['tgt'])} GMV ({K(pl['tgt'] / 30)}/day) vs LY {K(o1['g'])}. About <b>{K(pl['need'])} impressions</b> ({pc(pl['vs'])} vs LY) at today's conversion with LY/LLY event lift.", "cell"),
                     P(f"Oct MTD is running −5% vs LY; Sept 2026 GMV per 1K impressions is {fun[2026]['gpk']:.1f} AED vs {fun[2025]['gpk']:.1f} LY (UCR {pct(fun[2026]['ucr'], 2)} vs {pct(fun[2025]['ucr'], 2)}).", "cell")],
                    [P(f"<b>Retail WoC under {WOC_CAP} weeks at end of November</b>", "cell"),
                     P(f"End-Nov stock at most {K(W_['cap'])} units ({WOC_CAP} weeks of the planned Nov run-rate, {K(wk_nov)} units/week).", "cell"),
                     P(f"Live retail stock {K(W_['stock'])} units on {D.date.fromisoformat(STOCK_DAY):%-d %b} = {W_['woc']:.1f} weeks of cover on the last 30 days. LY ended November at {W_['ly_end_woc']:.1f} weeks, LLY at {W_['lly_end_woc']:.1f}.", "cell")]],
                   [55 * mm, 105 * mm, CW - 160 * mm], zebra=False)
    st += [agenda, Spacer(1, 8 * mm), P(f"Generated {D.datetime.utcnow():%-d %b %Y %H:%M} UTC from the Beauty Pulse data. Full calendar November in every year; per-day figures so periods of different length compare fairly. Scope: Namshi marketplaces, GMV incl. VAT above zero, Beauty, no samples &amp; GWP.", "small"), PageBreak()]

    # executive summary
    st += [P("Executive summary", "h2")]
    ex = [
        f"<b>November {YRS[1]} vs {YRS[0]}:</b> GMV {K(o1['g'])} vs {K(o0['g'])} ({cp(o1['g'] / o0['g'] - 1)}), per day {K(o1['gpd'])} vs {K(o0['gpd'])}. Impressions {cp(o1['im'] / o0['im'] - 1)}, markdown {pct(o1['mk'])} vs {pct(o0['mk'])} ({pp(o1['mk'] - o0['mk'])}). LY bought less GMV with more traffic and deeper discounts.",
        f"<b>Lift over September fell:</b> November GMV per day was {pc(o0['spG'])} vs September in {YRS[0]} but only {pc(o1['spG'])} in {YRS[1]}; GMV per impression ran {pc(o0['gpi'] / o0['sgpi'] - 1)} vs September in {YRS[0]} and {pc(o1['gpi'] / o1['sgpi'] - 1)} in {YRS[1]}.",
        "<b>Where LY lost the most (GMV per day vs LLY):</b> " + "; ".join(f"{SHORT[p['cohort']]} {pc(b['gpd'] / a['gpd'] - 1)} (imps {pc(b['ipd'] / a['ipd'] - 1)}, MKD {pp(b['mk'] - a['mk'])})" for p, a, b in worst) + ".",
        f"<b>Best cohort YoY:</b> {SHORT[best[0]['cohort']]} {pc(best[2]['gpd'] / best[1]['gpd'] - 1)} on impressions {pc(best[2]['ipd'] / best[1]['ipd'] - 1)} and markdown {pp(best[2]['mk'] - best[1]['mk'])}.",
        f"<b>Conversion, not traffic, is the gap.</b> UCR rises on event days (event traffic buys more units), but CTR slips and markdown cuts ASP. On in-between days pushed with impressions (BAU week, YF Week) GMV per impression fell to 67–75% of September; peak days (11.11, Pre YF, YF, YF Post) held ~90%+.",
        f"<b>2026 GMV plan:</b> {K(pl['tgt'])} (+25% vs LY). At Sept 2026 conversion ({fun[2026]['gpk']:.1f} AED / 1K imps) and the average LY/LLY event lift, November needs about <b>{K(pl['need'])} impressions ({pc(pl['vs'])} vs LY)</b>; range {K(pl['lo'])}–{K(pl['hi'])} (LLY-like to LY-like conversion).",
        f"<b>Stock is the binding constraint, not the WoC cap.</b> Retail units are running {pc(W_['trend'] - 1)} vs LY over the last 30 days and live retail stock is {K(W_['stock'])} units ({pc(W_['stock'] / rstock('2025-10-06', lambda x: 'a')['a'] - 1)} vs the same day LY). Selling the plan (≈{K(W_['s_rest'])} units to 31 Oct + {K(W_['s_nov'])} in November) needs at least <b>{K(W_['need_min'])} units of inbound</b> before the end of November just not to run out; ending at LY's {W_['ly_end_woc']:.1f} weeks needs ≈{K(W_['need_min'] + W_['ly_end_woc'] * wk_nov)}; the {WOC_CAP}-week cap allows up to {K(W_['otb_max'])}.",
        "<b>Replicate:</b> LLY's Singles depth on the right brands, the post-Singles extension (NYX, L'Oréal, Maybelline), YF → YF Post continuity (Kerastase, Kiko, ABH).  <b>Fix:</b> early Singles (Pre 11.11) and YF Week conversion, markdown that did not pay (Elizabeth Arden, Dyson, Philips, Medicube), and brands that are down 50–70% coming into OND (NYX, Kerastase, MUFE, La Roche-Posay, Vichy).",
    ]
    st += bullets(ex)
    st += [Spacer(1, 4 * mm), table([["", f"LLY {YRS[0]}", f"LY {YRS[1]}", "LY vs LLY", "2026 plan"],
                                     ["November GMV", K(o0["g"]), K(o1["g"]), cp(o1["g"] / o0["g"] - 1), K(pl["tgt"])],
                                     ["GMV per day", K(o0["gpd"]), K(o1["gpd"]), cp(o1["gpd"] / o0["gpd"] - 1), K(pl["tgt"] / 30)],
                                     ["GMV per day vs Sept", pc(o0["spG"]), pc(o1["spG"]), "", ""],
                                     ["GMV per day vs Oct", pc(o0["gpd"] / oct24["gpd"] - 1), pc(o1["gpd"] / oct25["gpd"] - 1), "", ""],
                                     ["Impressions", K(o0["im"]), K(o1["im"]), cp(o1["im"] / o0["im"] - 1), K(pl["need"])],
                                     ["Markdown %", pct(o0["mk"]), pct(o1["mk"]), pp(o1["mk"] - o0["mk"]), ""],
                                     ["CTR / UCR / ASP (Nov)", f"{pct(o0['ctr'], 2)} / {pct(o0['ucr'], 2)} / {o0['asp']:.0f}", f"{pct(o1['ctr'], 2)} / {pct(o1['ucr'], 2)} / {o1['asp']:.0f}", "", ""],
                                     ["Retail WoC end of Nov", f"{W_['lly_end_woc']:.1f} wk", f"{W_['ly_end_woc']:.1f} wk", "", f"< {WOC_CAP} wk"]],
                                    [60 * mm, 35 * mm, 35 * mm, 30 * mm, 35 * mm]), PageBreak()]

    # November at a glance
    st += [P("1 · November at a glance", "h2"),
           P(f"Every November day; shaded bands are the cohort periods (event cohorts in colour), dashed lines that year's September and October GMV per day, the strip underneath the day's markdown %. Both charts share one scale.", "small"),
           fig_img(chart_nov(YRS[0]), CW * 0.86), fig_img(chart_nov(YRS[1]), CW * 0.86), PageBreak()]
    # cohort scorecard
    st += [P("2 · Cohort scorecard", "h2"), P("Per-day figures. Uplift = cohort GMV (or impressions) per day vs the same year's September / October per day; YoY = LY vs LLY on the like-for-like cohort dates.", "small")]
    rows = [["Cohort", "Dates LLY · LY", f"GMV/day '{str(YRS[0])[2:]}", f"GMV/day '{str(YRS[1])[2:]}", "YoY", "GMV vs Sept '24", "'25", "GMV vs Oct '24", "'25",
             "Imps vs Sept '24", "'25", "Imps vs Oct '24", "'25", "Imps YoY", "MKD '24", "MKD '25", "MKD YoY", "Driver '25"]]
    for p, a, b in per:
        ln = lambda o, yy: dagg(p["llyd" if yy == YRS[0] else "lyd"])
        d0, d1 = ln(a, YRS[0]), ln(b, YRS[1])
        rows.append([P(f"<b>{SHORT[p['cohort']]}</b>", "cell"), P(f"{p['lly'][0][5:]}…{p['lly'][1][5:]} · {p['ly'][0][5:]}…{p['ly'][1][5:]}", "cell"),
                     K(d0["gpd"]), K(d1["gpd"]), cp(d1["gpd"] / d0["gpd"] - 1), cp(d0["gpd"] / sep24["gpd"] - 1), cp(d1["gpd"] / sep25["gpd"] - 1), cp(d0["gpd"] / oct24["gpd"] - 1), cp(d1["gpd"] / oct25["gpd"] - 1),
                     cp(d0["ipd"] / sep24["ipd"] - 1), cp(d1["ipd"] / sep25["ipd"] - 1), cp(d0["ipd"] / oct24["ipd"] - 1), cp(d1["ipd"] / oct25["ipd"] - 1), cp(d1["ipd"] / d0["ipd"] - 1),
                     pct(d0["mk"]), pct(d1["mk"]), f'<font color="{col(d1["mk"] - d0["mk"], True)}">{pp(d1["mk"] - d0["mk"])}</font>', b["drv"] or "–"])
    n0, n1 = dagg(month_days(YRS[0], 11)), dagg(month_days(YRS[1], 11))
    rows.append(["November", "", K(n0["gpd"]), K(n1["gpd"]), cp(n1["gpd"] / n0["gpd"] - 1), cp(n0["gpd"] / sep24["gpd"] - 1), cp(n1["gpd"] / sep25["gpd"] - 1), cp(n0["gpd"] / oct24["gpd"] - 1), cp(n1["gpd"] / oct25["gpd"] - 1),
                 cp(n0["ipd"] / sep24["ipd"] - 1), cp(n1["ipd"] / sep25["ipd"] - 1), cp(n0["ipd"] / oct24["ipd"] - 1), cp(n1["ipd"] / oct25["ipd"] - 1), cp(n1["ipd"] / n0["ipd"] - 1), pct(n0["mk"]), pct(n1["mk"]), pp(n1["mk"] - n0["mk"]), o1["drv"] or ""])
    cw = [18 * mm, 30 * mm] + [13.6 * mm] * 15 + [22 * mm]
    st += [table(rows, cw, bold_last=True), Spacer(1, 3 * mm), fig_img(chart_cohort_bars(), CW * 0.8), PageBreak()]
    st += [P("What the cohorts say", "h3")] + bullets([
        f"{SHORT[p['cohort']]}: LY {K(b['gpd'])}/day vs LLY {K(a['gpd'])} ({cp(b['gpd'] / a['gpd'] - 1)}); impressions {pc(b['ipd'] / a['ipd'] - 1)}, markdown {pct(b['mk'])} vs {pct(a['mk'])}. "
        + ("More markdown did not buy the GMV back." if (b["mk"] - a["mk"]) > 0.03 and b["gpd"] < a["gpd"] else "Visibility was the gap." if b["ipd"] < a["ipd"] * 0.95 and b["gpd"] < a["gpd"] else "Held or grew." if b["gpd"] >= a["gpd"] else "Conversion was the gap.")
        for p, a, b in per]) + [Spacer(1, 4 * mm)]

    # traffic & conversion
    st += [P("3 · Traffic, conversion and markdown", "h2")]
    buckets = [(0, 1.5, "under 1.5×"), (1.5, 2.5, "1.5–2.5×"), (2.5, 3.5, "2.5–3.5×"), (3.5, 99, "3.5× +")]
    brows = [["Imps/day vs Sept", "Days '24", "CTR", "UCR", "ASP", "Yield vs Sept", "MKD", "Days '25", "CTR", "UCR", "ASP", "Yield vs Sept", "MKD"]]
    for lo, hi, lab in buckets:
        row = [lab]
        for y in YRS[:2]:
            sep = dagg(month_days(y, 9)); ds = [d for d in month_days(y, 11) if lo <= DAILY[d]["im"] / sep["ipd"] < hi]; a = dagg(ds)
            row += ([str(a["n"]), pct(a["gv"] / a["im"], 2), pct(a["u"] / a["gv"], 2), f"{a['g'] / a['u']:.0f}", cp(a["g"] / a["im"] / (sep["g"] / sep["im"]) - 1), pct(a["mk"], 0)] if a["n"] else ["0"] + ["–"] * 5)
        brows.append(row)
    left = [table(brows, [24 * mm] + [11.5 * mm] * 12), Spacer(1, 2 * mm),
            table([["Funnel (September)", "CTR", "UCR", "ASP", "AED / 1K imps"]] + [[f"Sept {y}", pct(fun[y]["ctr"], 2), pct(fun[y]["ucr"], 2), f"{fun[y]['asp']:.0f}", f"{fun[y]['gpk']:.1f}"] for y in YRS], [40 * mm, 22 * mm, 22 * mm, 22 * mm, 30 * mm])]
    st += [Table([[left, fig_img(chart_scatter(), 105 * mm)]], colWidths=[CW - 110 * mm, 110 * mm], style=[("VALIGN", (0, 0), (-1, -1), "TOP")])]
    st += [P("Reading", "h3")] + bullets([
        "<b>UCR does not fall when impressions rise — it rises.</b> On 3.5×+ days UCR was ~3.7–4.5% vs 2.3–2.5% in September: event traffic arrives with deals and buys more units.",
        "<b>What falls is CTR and ASP.</b> CTR slips a little as impressions widen, and deeper markdown pulls ASP down, so GMV per impression can drop while UCR climbs.",
        f"<b>LY's problem was the 1.5–3.5× days:</b> {YRS[1]} converted those at −18% to −28% vs September at 37–51% markdown, where {YRS[0]} ran +17% to +24% at 38%. Those are the BAU week after Singles and YF Week — impressions and markdown without a peak-day reason to buy.",
        f"<b>Today's funnel is weaker than LY's:</b> Sept 2026 UCR {pct(fun[2026]['ucr'], 2)} vs {pct(fun[2025]['ucr'], 2)}, GMV per 1K impressions {fun[2026]['gpk']:.1f} vs {fun[2025]['gpk']:.1f} AED. Every conversion point recovered lowers the impressions ask directly.",
        "<b>Markdown:</b> LY ran 8pp more markdown across November than LLY and still sold 8% less per day; the extra depth showed up as lower ASP, not more GMV. Keep depth for the peak days and the brands where it paid (see brand pages)."]) + [PageBreak()]

    # country / category / sub-category / brand
    def lv_table(lv, rows_, title, n=None, show_cat=False):
        out = [[title] + (["Category"] if show_cat else []) + [f"Nov GMV '{str(YRS[0])[2:]}", f"Nov GMV '{str(YRS[1])[2:]}", "YoY", "vs Sept '24", "vs Sept '25", "Imps vs Sept '25", "MKD '24", "MKD '25", "Driver '25", "2026 target", "Imps needed", "vs LY imps"]]
        for r in [x for x in rows_ if not x["k"].startswith("(")][:n or None]:
            a, b = stat(r, 0, WIN), stat(r, 1, WIN)
            par = None if lv in ("all",) else ALL if lv in ("country", "cat") else next((x for x in FB["lv"]["cat"] if x["k"] == (r["k"].split("|")[0] if lv == "sub" else r.get("cat"))), ALL)
            pl_ = plan(r, WIN, par, lv)
            name = " › ".join(nm(x) for x in r["k"].split("|")) if lv == "sub" else nm(r["k"])
            out.append([P(f"<b>{name}</b>", "cell")] + ([nm(r.get("cat") or "")] if show_cat else []) + [K(a["g"]), K(b["g"]), cp(b["g"] / a["g"] - 1) if a["g"] else "new", pc(a["spG"]), pc(b["spG"]), pc(b["spI"]), pct(a["mk"]), pct(b["mk"]), b["drv"] or "–"] + (["discontinued", "–", "–"] if pl_["gone"] else [K(pl_["tgt"]), K(pl_["need"]), pc(pl_["vs"])]))
        return out
    lw = [44 * mm, 19 * mm, 19 * mm, 15 * mm, 17 * mm, 17 * mm, 19 * mm, 15 * mm, 15 * mm, 28 * mm, 19 * mm, 19 * mm, 17 * mm]
    st += [P("4 · Country and category", "h2"), table(lv_table("country", FB["lv"]["country"], "Country"), lw), Spacer(1, 3 * mm),
           table(lv_table("cat", FB["lv"]["cat"], "Category"), lw)]
    cats = [(r, stat(r, 0, WIN), stat(r, 1, WIN)) for r in FB["lv"]["cat"] if not r["k"].startswith("(")]
    st += [P("Reading", "h3")] + bullets([f"<b>{nm(r['k'])}</b>: LY {K(b['g'])} vs LLY {K(a['g'])} ({cp(b['g'] / a['g'] - 1)}), lift over Sept {pc(a['spG'])} → {pc(b['spG'])}, markdown {pct(a['mk'])} → {pct(b['mk'])}." for r, a, b in cats[:6]])
    st += [PageBreak(), P("Sub-categories (top 20 by LY November GMV)", "h3"), table(lv_table("sub", FB["lv"]["sub"], "Sub-category", 20), lw), PageBreak()]
    bw = [36 * mm, 22 * mm, 17 * mm, 17 * mm, 13 * mm, 15 * mm, 15 * mm, 17 * mm, 13 * mm, 13 * mm, 26 * mm, 17 * mm, 17 * mm, 15 * mm]
    st += [P("5 · Brands (top 40 by LY November GMV)", "h2"), table(lv_table("brand", FB["lv"]["brand"], "Brand", 40, True), bw), PageBreak()]
    br = [(r, stat(r, 0, WIN), stat(r, 1, WIN)) for r in FB["lv"]["brand"] if not r["k"].startswith("(")]
    top = [x for x in br if x[2]["g"] >= 20000]
    grow = sorted([x for x in top if x[1]["g"] > 0], key=lambda x: -(x[2]["g"] - x[1]["g"]))[:10]
    fall = sorted([x for x in br if x[1]["g"] >= 50000], key=lambda x: (x[2]["g"] - x[1]["g"]))[:10]
    org = sorted([x for x in top if (x[2]["spG"] or 0) >= 0.3 and (x[2]["dMk"] if x[2]["dMk"] is not None else 1) < 0.05], key=lambda x: -x[2]["g"])[:8]
    nopay = sorted([x for x in top if (x[2]["dMk"] or 0) >= 0.1 and (x[2]["spG"] if x[2]["spG"] is not None else 1) < 0.1], key=lambda x: -x[2]["g"])[:8]
    st += [P("Brand winners and losers", "h3")] + bullets([
        "<b>Biggest GMV gains LY vs LLY:</b> " + ", ".join(f"{nm(r['k'])} +{K(b['g'] - a['g'])} ({pc(b['g'] / a['g'] - 1)})" for r, a, b in grow),
        "<b>Biggest GMV losses LY vs LLY:</b> " + ", ".join(f"{nm(r['k'])} −{K(a['g'] - b['g'])} ({pc(b['g'] / a['g'] - 1)})" for r, a, b in fall),
        "<b>Grew 30%+ vs September without extra markdown (organic):</b> " + (", ".join(f"{nm(r['k'])} {pc(b['spG'])} at {pct(b['mk'])}" for r, a, b in org) or "none"),
        "<b>Markdown did not pay (MKD +10pp vs Sept, GMV/day up under 10%):</b> " + (", ".join(f"{nm(r['k'])} {pct(b['mk'])} ({pp(b['dMk'])}), GMV {pc(b['spG'])}" for r, a, b in nopay) or "none")])

    # learnings
    st += [P("6 · Learnings — replicate, fix, missed", "h2")]
    good = [f"<b>{SHORT[p['cohort']]}</b> LY: GMV/day {pc(b['spG'])} vs Sept at {pct(b['mk'])} markdown, impressions {pc(b['spI'])} ({b['drv']})." for p, a, b in sorted(per, key=lambda t: -(t[2]['spG'] or 0))[:3]]
    bad = [f"<b>{SHORT[p['cohort']]}</b>: LY GMV/day {pc(b['gpd'] / a['gpd'] - 1)} vs LLY ({K(b['gpd'])} vs {K(a['gpd'])}), markdown {pct(b['mk'])} vs {pct(a['mk'])}, impressions/day {pc(b['ipd'] / a['ipd'] - 1)}." for p, a, b in worst]
    st += [P("What worked LY — replicate", "h3")] + bullets(good) + [P("What did not work — improve", "h3")] + bullets(bad)
    lost = sorted([x for x in br if x[1]["g"] >= 20000 and (x[1]["spG"] or 0) >= 0.5 and x[2]["spG"] is not None and x[2]["spG"] < 0.1], key=lambda x: -x[1]["g"])[:10]
    st += [P("Missed vs LLY", "h3")] + bullets(["Spiked in LLY but not in LY: " + (", ".join(f"{nm(r['k'])} LLY {pc(a['spG'])} → LY {pc(b['spG'])}" for r, a, b in lost) or "none")]) + [PageBreak()]

    # plan
    st += [P("7 · 2026 plan — GMV +25% vs LY", "h2"),
           P(f"Target per cohort = LY GMV × {U}. Impressions needed = target ÷ (Sept 2026 GMV per impression {GPI26 * 1000:.1f} AED/1K × the cohort's lift over September, average of LY and LLY); range = the better year's lift to the weaker year's. Sept 2026 runs {K(IPD26)} impressions a day.", "small")]
    prow = [["Cohort (2026 dates)", "LY GMV", "Target GMV", "Target/day", "LY imps/day", "LY yield vs Sept", "LLY yield vs Sept", "Imps/day needed", "Range/day", "× Sept-26 imps/day", "vs LY imps"]]
    T = dict(t=0, n=0, lo=0, hi=0, ly=0, lyg=0)
    for p in PER:
        a, b = stat(ALL, 0, [p["p"]]), stat(ALL, 1, [p["p"]]); pl_ = plan(ALL, [p["p"]]); ty = TYD[p["p"]]
        for k_, v in (("t", pl_["tgt"]), ("n", pl_["need"]), ("lo", pl_["lo"]), ("hi", pl_["hi"]), ("ly", b["im"]), ("lyg", b["g"])): T[k_] += v
        prow.append([P(f"<b>{SHORT[p['cohort']]}</b> {p['ty'][0][5:]}…{p['ty'][1][5:]}", "cell"), K(b["g"]), K(pl_["tgt"]), K(pl_["tgt"] / ty), K(b["ipd"]), cp(b["gpi"] / b["sgpi"] - 1), cp(a["gpi"] / a["sgpi"] - 1),
                     K(pl_["need"] / ty), f"{K(pl_['lo'] / ty)}–{K(pl_['hi'] / ty)}", f"×{pl_['need'] / ty / IPD26:.1f}", pc(pl_["vs"])])
    prow.append(["November", K(T["lyg"]), K(T["t"]), K(T["t"] / 30), K(T["ly"] / 30), "", "", K(T["n"] / 30), f"{K(T['lo'] / 30)}–{K(T['hi'] / 30)}", f"×{T['n'] / 30 / IPD26:.1f}", pc(T["n"] / T["ly"] - 1)])
    st += [table(prow, [40 * mm, 20 * mm, 22 * mm, 20 * mm, 22 * mm, 22 * mm, 22 * mm, 24 * mm, 30 * mm, 24 * mm, 18 * mm], bold_last=True)]
    st += [P("Plan calls", "h3")] + bullets([
        f"<b>Ask onsite for ≈{K(T['n'])} November impressions ({pc(T['n'] / T['ly'] - 1)} vs LY)</b>, weighted to 11.11, Pre YF, YF and YF Post where an impression earned 30%+ more than in the BAU week.",
        "<b>BAU week (15–19 Nov) is the most expensive GMV of the month</b> (GMV per impression at 67–83% of September in both years): fix its offer or accept less growth there and over-deliver on the peaks.",
        "<b>Pre 11.11 and YF Week</b> lost 31% vs LLY: start the Singles and YF offers on day 1 of those windows with visibility, not just on the peak day.",
        "<b>Conversion work is worth more than traffic:</b> recovering Sept 2026 UCR to LY's level alone would cut the impressions ask by about a quarter.",
        "<b>Discontinued Benefit Cosmetics:</b> its target is handed to same-type brands in its sub-categories, pro rata to their LY GMV — " + ", ".join(f"{nm(k)} {v / RA_T:.0%}" for k, v in RA[:5]) + " and the rest spread; totals unchanged."]) + [PageBreak()]

    # WoC plan
    st += [P(f"8 · Inventory — WoC under {WOC_CAP} weeks at end of November", "h2"),
           P(f"Retail only (Namshi retail, partner 3001), KSA + UAE warehouses. WoC = live retail stock ÷ (retail units shipped in the last 30 days ÷ 30 × 7), as on the dashboard. Plan sales: rest of October at the last-30-day unit trend vs LY ({pc(W_['trend'] - 1)}), November = LY November units × {U}. Stock as of {D.date.fromisoformat(STOCK_DAY):%-d %b %Y}.", "small")]
    wrow = [["", "Units", "Note"],
            ["Live retail stock now", K(W_["stock"]), f"{W_['woc']:.1f} weeks on the last 30 days"],
            ["Plan sales to 31 Oct", K(W_["s_rest"]), f"LY {K(W_['s_rest'] / W_['trend'])} × trend {W_['trend']:.2f}"],
            ["Plan sales in November", K(W_["s_nov"]), f"LY {K(W_['ly_nov'])} × {U} → {K(wk_nov)} units/week"],
            ["End-Nov stock with no inbound", K(W_["end0"]), "negative = the plan cannot be sold from today's stock"],
            ["Minimum inbound to sell the plan", K(W_["need_min"]), f"≈{K(W_['need_min'] * (W_['cpu'] or 0))} AED at LY Nov unit cost" if W_["cpu"] else ""],
            [f"Inbound to end at LY's {W_['ly_end_woc']:.1f} wk", K(W_["need_min"] + W_["ly_end_woc"] * wk_nov), ""],
            [f"Maximum inbound at the {WOC_CAP}-week cap", K(W_["otb_max"]), f"end-Nov stock ≤ {K(W_['cap'])} units"]]
    st += [Table([[table(wrow, [62 * mm, 26 * mm, 70 * mm]), fig_img(chart_woc(), 100 * mm)]], colWidths=[CW - 104 * mm, 104 * mm], style=[("VALIGN", (0, 0), (-1, -1), "TOP")])]
    st += bullets([
        f"<b>The {WOC_CAP}-week cap is not the risk; running short is.</b> WoC at the end of November is measured on November's peak sales, so even {WOC_CAP} weeks there is ~{K(W_['cap'])} units — far more than December sells. LY and LLY both closed November at ~6.6–6.7 weeks.",
        f"<b>Recommended landing band: 6–8 weeks</b> at end of November (LY/LLY level, under the cap, without a December hangover): inbound ≈{K(W_['need_min'] + 6 * wk_nov)}–{K(W_['need_min'] + 8 * wk_nov)} units between now and end of November, front-loaded before Pre 11.11 and YF Week.",
        "<b>Category and brand split below:</b> 'Min inbound' = units needed not to run out at plan; 'Max inbound' = most that keeps the end-Nov WoC under the cap. Brands with negative 'end with no inbound' need POs now; brands already over the cap at end-Nov without any inbound need sell-through, not buying."])
    crow = [["Category", "Stock now", "WoC now", "LY end-Nov WoC", "Plan Nov units", "End-Nov stock, no inbound", "End-Nov WoC, no inbound", "Min inbound", "Max inbound (≤10 wk)"]]
    for k, w in [t for t in sorted(WOC_CAT.items(), key=lambda t: -t[1]["s_nov"]) if t[1]["s_nov"] >= 100 and not t[0].startswith("(")][:12]:
        e = w["end0"] / (w["s_nov"] / 30 * 7) if w["s_nov"] else None
        crow.append([P(f"<b>{nm(k)}</b>", "cell"), K(w["stock"]), "–" if w["woc"] is None else f"{w['woc']:.1f}", "–" if w["ly_end_woc"] is None else f"{w['ly_end_woc']:.1f}", K(w["s_nov"]), f'<font color="{BAD if w["end0"] < 0 else INK}">{K(w["end0"])}</font>',
                     "–" if e is None else f'<font color="{BAD if e < 4 else WARN if e > WOC_CAP else INK}">{e:.1f}</font>', K(w["need_min"]), K(w["otb_max"])])
    st += [P("By category", "h3"), table(crow, [40 * mm, 22 * mm, 18 * mm, 24 * mm, 24 * mm, 32 * mm, 30 * mm, 24 * mm, 30 * mm]), PageBreak()]
    brow = [["Retail brand", "Stock now", "WoC now", "LY end-Nov WoC", "Trend vs LY (last 30d)", "Plan Nov units", "End-Nov stock, no inbound", "End-Nov WoC, no inbound", "Min inbound", "Max inbound (≤10 wk)", "Call"]]
    for k, w in [t for t in sorted(WOC_BR.items(), key=lambda t: -t[1]["s_nov"]) if t[0] not in FB["realloc"] or not FB["realloc"][t[0]].get("gone")][:30]:
        e = w["end0"] / (w["s_nov"] / 30 * 7) if w["s_nov"] else None
        call = "PO now — plan exceeds stock" if w["end0"] < 0 else "Over cap — push sell-through" if e is not None and e > WOC_CAP else "Top up to 6–8 wk" if e is not None and e < 6 else "Covered"
        brow.append([P(f"<b>{nm(k)}</b>", "cell"), K(w["stock"]), "–" if w["woc"] is None else f"{w['woc']:.1f}", "–" if w["ly_end_woc"] is None else f"{w['ly_end_woc']:.1f}", pc(w["trend"] - 1), K(w["s_nov"]),
                     f'<font color="{BAD if w["end0"] < 0 else INK}">{K(w["end0"])}</font>', "–" if e is None else f"{e:.1f}", K(w["need_min"]), K(w["otb_max"]), call])
    st += [P("By retail brand (top 30 by planned November units)", "h3"), table(brow, [36 * mm, 18 * mm, 15 * mm, 20 * mm, 22 * mm, 20 * mm, 28 * mm, 24 * mm, 20 * mm, 26 * mm, 40 * mm]), PageBreak()]

    # top 20 retail brands
    st += [P("9 · Top 20 retail brands — LY and LLY November", "h2")]
    for i, r in enumerate(FB["retail"]):
        a, b = stat(r, 0, WIN), stat(r, 1, WIN); n = r.get("note") or {}; w = WOC_BR.get(r["k"])
        s26 = fsum(r, 2, [0])[0]; s25 = fsum(r, 1, [0])
        m = table([["", f"LY '{str(YRS[1])[2:]}", f"LLY '{str(YRS[0])[2:]}"],
                   ["Nov GMV", K(b["g"]), K(a["g"])], ["GMV/day vs Sept", pc(b["spG"]), pc(a["spG"])], ["Impressions vs Sept", pc(b["spI"]), pc(a["spI"])],
                   ["Markdown", pct(b["mk"]), pct(a["mk"])], ["UCR · ASP", f"{pct(b['ucr'], 2)} · {b['asp'] or 0:.0f}", f"{pct(a['ucr'], 2)} · {a['asp'] or 0:.0f}"], ["Driver", b["drv"] or "–", a["drv"] or "–"]],
                  [30 * mm, 22 * mm, 22 * mm])
        side = [P(f"#{i + 1} {nm(r['k']).title()} <font size=8 color='{INK2}'>· {nm(r.get('cat') or '')} · retail · LY vs LLY {cp(b['g'] / a['g'] - 1) if a['g'] else 'new'}</font>", "h3"),
                Table([[m, fig_img(chart_brand(r), 98 * mm)]], colWidths=[78 * mm, 100 * mm], style=[("VALIGN", (0, 0), (-1, -1), "TOP")]),
                P(f"Sept 2026: {K(s26[0] / 30)}/day vs {K(s25[0][0] / s25[1])} in Sept {YRS[1]} ({pc((s26[0] / 30) / (s25[0][0] / s25[1]) - 1) if s25[0][0] else '–'})"
                  + (f" · stock {K(w['stock'])} units, WoC now {w['woc']:.1f} wk, plan Nov {K(w['s_nov'])} units, end-Nov with no inbound {K(w['end0'])}" if w and w["woc"] is not None else ""), "small")]
        txt = []
        if n.get("worked"): txt += [P("<font color='%s'><b>What worked</b></font>" % GOOD, "small")] + bullets(n["worked"])
        if n.get("missed"): txt += [P("<font color='%s'><b>Where we missed GMV</b></font>" % BAD, "small")] + bullets(n["missed"])
        if n.get("do"): txt += [P("<font color='%s'><b>2026 focus</b></font>" % ACC, "small")] + bullets(n["do"])
        st += [KeepTogether([Table([[side, txt]], colWidths=[180 * mm, CW - 180 * mm], style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(LINE)), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])])]
    st += [PageBreak()]

    # buyers ref
    KEY = [("11.11 Day", "Singles"), ("Post 11.11", "Post Singles"), ("Black Friday Pre", "Pre YF"), ("Black Friday", "YF")]
    kp = [(next(p for p in PER if p["cohort"] == c), n_) for c, n_ in KEY]
    head = ["Brand", "Category", "Sept MKD LY · LLY"] + [f"{n_} MKD ask (LY) · LLY" for _, n_ in kp] + [f"{n_} GMV '25 / '24 vs Sept" for _, n_ in kp]
    rows = [head]
    for r in [x for x in FB["lv"]["brand"] if not x["k"].startswith("(")][:40]:
        s1, s0 = stat(r, 1, [0]), stat(r, 0, [0])
        row = [P(f"<b>{nm(r['k'])}</b>", "cell"), nm(r.get("cat") or ""), f"{pct(s1['smk'])} · {pct(s0['smk'])}"]
        for p, _ in kp:
            a, b = stat(r, 0, [p["p"]]), stat(r, 1, [p["p"]]); row.append(P(f"<b>{pct(b['mk'] if b['mk'] is not None else a['mk'])}</b> · {pct(a['mk'])}", "cell"))
        for p, _ in kp:
            a, b = stat(r, 0, [p["p"]]), stat(r, 1, [p["p"]]); row.append(P(f"{cp(b['spG'])} / {cp(a['spG'])}", "cell"))
        rows.append(row)
    st += [P("10 · Buyers reference — key periods", "h2"), P("Bold = the markdown % the brand ran LY in that period: the bare minimum to ask the brand to fund in 2026 (LLY after the dot). GMV = per day vs that year's September.", "small"),
           table(rows, [30 * mm, 22 * mm, 22 * mm] + [24 * mm] * 4 + [26 * mm] * 4), PageBreak()]

    # method
    st += [P("Method and definitions", "h2")] + bullets([
        "Periods: the LFL cohorts of the 2026 dates 1–30 Nov (MS, Pre 11.11, 11.11, Post 11.11, BAU week, YF Week, Pre YF, YF, YF Post). LY / LLY use the like-for-like dates; days the mapping skips (20 Nov LY, 20–21 Nov LLY) count in the BAU week and days outside November are left out, so every total is calendar November.",
        "Per-day figures throughout, so periods of different length compare fairly. Uplift vs September / October = the period's per-day value vs that month's per-day value in the same year.",
        "What drove it: Impressions-led = impressions explain 60%+ of the GMV lift and markdown rose under 3pp; Markdown-led = markdown up 3pp+ and impressions explain under 60%; Imps + markdown = both; Organic = GMV up 10%+ without either; Neutral = within ±10%; Declined = 10%+ below September.",
        "Impressions needed = target ÷ (Sept 2026 GMV per impression × the period's lift over September, average of LY and LLY; lifts kept within 0.3–3×). Rows with too little Sept 2026 traffic use their category's rates.",
        "GMV incl. VAT, all item statuses; MKD % = markdown ÷ normal price; CTR = glance views ÷ impressions (search + non-search, all platforms); UCR = units ÷ glance views; ASP = GMV ÷ units.",
        f"WoC (retail, units) = live Namshi retail stock in the KSA + UAE warehouses ÷ (retail units shipped from them in the last 30 days ÷ 30 × 7). Plan sales: rest of October = LY units × the brand's / category's last-30-day unit trend vs the same 30 days LY (kept within 0.5–1.5×), November = LY November units × {U} (units assumed to grow with GMV).",
        "Discontinued Benefit Cosmetics stays in all history; its 2026 target is handed to same-type brands in its sub-categories."])
    return st


def on_page(c, doc):
    c.saveState(); c.setFont("DV", 7); c.setFillColor(colors.HexColor(MUTED))
    c.drawString(14 * mm, 8 * mm, "Beauty Pulse · November Flashback")
    c.drawRightString(W - 14 * mm, 8 * mm, f"{doc.page}")
    c.setStrokeColor(colors.HexColor(ACC)); c.setLineWidth(2); c.line(14 * mm, H - 9 * mm, 40 * mm, H - 9 * mm)
    c.restoreState()


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm, topMargin=13 * mm, bottomMargin=13 * mm,
                            title="Beauty November Flashback", author="Beauty Pulse")
    doc.build(build_story(), onFirstPage=on_page, onLaterPages=on_page)
    print("wrote", OUT, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
