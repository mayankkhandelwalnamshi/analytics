"""Build the OND Beauty dashboard HTML.

Usage:
    python3 ond-beauty/build.py [bq_result.json ...]

Usage with traffic: python3 ond-beauty/build.py [sales_result.json ...] --traffic [traffic_result.json ...]

Each bq_result.json is the raw BigQuery `jobs.query` response of sql/daily_beauty_cube.sql
(or sql/daily_traffic_cube.sql after --traffic, merged into data/traffic_raw.json)
for one date window (rows: d, r). They are merged into data/cube_raw.json ({date: packed rows};
each record is "c,brand,category,sub_category,gmv,units,mkd,np,rev,pc1,ppc1").
data/lfl.json maps each OND 2026 date to its [LY, LLY] like-for-like date (sql/lfl_mapping.sql).

Each dataset is packed as columnar binary (int32 metrics, uint16 date/combo, uint8 country), gzip-compressed and
written to dist/data/<set>.txt (base64); template.html -> dist/ond_beauty_dashboard.html fetches them. Publish the page
with the dist/data/*.txt files alongside it.

data/ssku_raw.json holds sql/mtd_ssku.sql for the current month to date ({period, from, to, align: "lfl", rows: ["v|..."],
info: {supplier_sku: [brand, cat, sub, bm, season, title]}}); it becomes dist/data/ssku.txt for the MTD tab's Supplier SKU cut.
Re-run it with the month's dates on every refresh, or the cut only covers the old period.

data/targets_raw.json is the result of sql/targets_beauty.sql ({date: "c,brand,category,gmv;..."}):
daily GMV targets by country x brand x category. Pass a raw BigQuery result with --targets to refresh it.
"""
import base64
import datetime
import gzip
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
SALES_FIELDS = ["gmv", "u", "mkd", "np", "rev", "pc1", "ppc1"]
TRAFFIC_FIELDS = ["gv", "atc", "si", "nsi", "asi", "ansi"]
OOS_FIELDS = ["oos"]
KEY = ["brand", "cat", "sub", "bm", "season"]          # product combo key (sql/*.sql)
START = "2026-10-01"
ATTRS = ["btype", "bgroup", "poc"]                      # brand attributes (sql/brand_attributes.sql)
# (name, raw file, fields, traffic level or None). Traffic has two levels, see sql/daily_traffic_cube.sql.
SETS = [("sales", "cube_raw.json", SALES_FIELDS, None),
        ("trafA", "traffic_raw.json", TRAFFIC_FIELDS, "0"),
        ("trafB", "traffic_raw.json", TRAFFIC_FIELDS, "1"),
        ("oos", "oos_raw.json", OOS_FIELDS, None),
        ("asrt", "assort_raw.json", ["la", "cb", "st", "nw"], None),   # supplier SKUs; Overall = KSA + UAE (sql/daily_assortment.sql)
        ("inv", "inv_raw.json", ["cv", "rv"], None),             # inventory value at cost / retail (sql/daily_inventory_value.sql)
        ("rs", "retail_raw.json", ["ur30", "cg30"], None),       # retail units / COGS per day from 1 Sep (sql/daily_retail_cogs.sql);
                                                                 # the page turns them into trailing 30-day sums for WoC
        ("age", "age_raw.json", ["ag0", "ag1", "ag2", "ag3", "ag4"], None)]   # cost value by ageing band, TY (sql/daily_inventory_ageing.sql)


def fold_small_oos(recs, threshold=10):
    """OOS rows under 10 AED of loss (about a third of rows, ~2% of the loss) are folded into '(other brands)'
    within their country / category / sub-category / business model / season, so totals stay exact."""
    out = {}
    for rec in recs:
        v = rec.split(",")
        if abs(float(v[6])) < threshold:
            v[1] = "(other brands)"
        k = tuple(v[:6])
        out[k] = out.get(k, 0.0) + float(v[6])
    return [",".join(k) + f",{val:.0f}" for k, val in out.items() if round(val) != 0]


def merge(paths, target="cube_raw.json"):
    cube_path = DATA / target
    days = json.loads(cube_path.read_text()) if cube_path.exists() else {}
    for p in paths:
        raw = json.loads(pathlib.Path(p).read_text())
        for r in raw["rows"]:
            d, s = [c["v"] for c in r["f"]]
            days[d] = s
    cube_path.write_text(json.dumps(days, separators=(",", ":")))


def pack():
    """All sets share one date list and one product-combo list (brand, category, sub-category, business model, season).
    Each set is stored as columns: int32 per field (as 4 byte planes), then uint16 date, uint16 combo, uint8 country."""
    raw = {f: json.loads((DATA / f).read_text()) for f in {s[1] for s in SETS}}
    dates = sorted(set().union(*raw.values()))
    di = {d: i for i, d in enumerate(dates)}
    combo_idx = {}
    bufs, sizes = {}, []
    for name, f, fields, lvl in SETS:
        buf = b""
        cols = [[] for _ in range(3 + len(fields))]  # d, c, k, metrics...
        for d in sorted(raw[f]):
            recs = raw[f][d].split(";")
            if name == "oos":
                recs = fold_small_oos(recs)
            if name == "asrt":
                recs = [r for r in recs if not r.startswith("2,")]   # Overall = KSA + UAE (sum), the union rows are not used
            for rec in recs:
                v = rec.split(",")
                if lvl is not None:
                    if v[0] != lvl:
                        continue
                    v = v[1:]
                key = tuple(v[1:6])
                if key not in combo_idx:
                    combo_idx[key] = len(combo_idx)
                cols[0].append(di[d])
                cols[1].append(int(v[0]))
                cols[2].append(combo_idx[key])
                for j in range(len(fields)):
                    cols[3 + j].append(int(round(float(v[6 + j]))))
        n = len(cols[0])
        for j in range(len(fields)):
            col = struct.pack(f"<{n}i", *cols[3 + j])
            buf += b"".join(col[k::4] for k in range(4))  # byte planes: compresses ~20% better
        buf += struct.pack(f"<{n}H", *cols[0]) + struct.pack(f"<{n}H", *cols[2]) + struct.pack(f"<{n}B", *cols[1])
        bufs[name] = buf
        sizes.append(n)
    # distinct orders, one block per level (see sql/daily_orders.sql): int32 count, uint16 date, uint16 key, uint8 country
    orders = json.loads((DATA / "orders_raw.json").read_text())
    levels = [[] for _ in range(7)]
    for d in sorted(orders):
        for rec in orders[d].split(";"):
            l, c, k, n = rec.split(",")
            l = int(l)
            if l == 4:
                continue  # brand x category x ... level: too large; mixed filters are estimated on the page
            levels[l].append((di[d], int(c), k, int(n)))
    # supplier-SKU month-to-date rows for the MTD tab (sql/mtd_ssku.sql): their combos join the shared combo list
    ss_raw = json.loads((DATA / "ssku_raw.json").read_text())
    ss_names = sorted(ss_raw["info"])
    ss_i = {v: i for i, v in enumerate(ss_names)}
    for v in ss_raw["info"].values():
        combo_idx.setdefault(tuple(v[:5]), len(combo_idx))
    combos = list(combo_idx)
    assert len(combos) < 65536
    names = {key: sorted({c[i] for c in combos}) for i, key in enumerate(KEY)}
    idx = {key: {v: i for i, v in enumerate(names[key])} for key in names}
    pairs = sorted({tuple(r[2].split("|")) for r in levels[2]})
    pair_idx = {p: i for i, p in enumerate(pairs)}
    keyof = [
        lambda k: 0,
        lambda k: idx["cat"][k],
        lambda k: pair_idx[tuple(k.split("|"))],
        lambda k: idx["brand"][k],
        None,
        lambda k: idx["bm"][k],
        lambda k: idx["season"][k],
    ]
    buf = b""
    for l, rows in enumerate(levels):
        n = len(rows)
        buf += struct.pack(f"<{n}i", *[r[3] for r in rows]) + struct.pack(f"<{n}H", *[r[0] for r in rows])
        buf += struct.pack(f"<{n}H", *[keyof[l](r[2]) for r in rows]) + struct.pack(f"<{n}B", *[r[1] for r in rows])
        buf += b"\0" * (-len(buf) % 4)
    # brand attributes: per brand index -> [type, group, poc] index, -1 for the '*' / '(other brands)' placeholders
    battr_raw = json.loads((DATA / "brand_attrs.json").read_text())
    attr_names = {a: sorted({v[i] for v in battr_raw.values()} | {"unassigned"}) for i, a in enumerate(ATTRS)}
    battr = []
    for b in names["brand"]:
        if b in ("*", "(other brands)"):
            battr.append([-1, -1, -1])
        else:
            vals = battr_raw.get(b, ["unassigned"] * 3)
            battr.append([attr_names[a].index(vals[i]) for i, a in enumerate(ATTRS)])
    names.update(attr_names)
    meta = {
        "ord": [len(rows) for rows in levels],
        "pairs": [[idx["cat"][c], idx["sub"][s]] for c, s in pairs],
        "sets": [{"name": name, "fields": fields, "n": n} for (name, _, fields, _), n in zip(SETS, sizes)],
        "dates": dates,
        "names": names,
        "battr": battr,
        "combos": [[idx[k][v] for k, v in zip(KEY, c)] for c in combos],
        "lfl": lfl_map(),
        "cohort": json.loads((DATA / "lfl_cohort.json").read_text()),   # TY date -> LFL cohort (sql/lfl_cohort.sql)
        "oosDates": sorted(raw["oos_raw.json"]),
        "ageDates": sorted(raw["age_raw.json"]),
        "platform": json.loads((DATA / "platform.json").read_text()),   # sql/platform_gmv.sql
        "refreshed": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    bufs["orders"] = buf
    # supplier SKUs: JSON, fetched when the MTD tab is cut by supplier SKU
    flat = []
    for r in ss_raw["rows"]:
        _, c, ss, *ys = r.split("|")
        flat += [int(c), ss_i[ss]] + [int(round(float(x))) for y in ys for x in y.split(",")]
    bufs["ssku"] = json.dumps({"names": ss_names, "titles": [ss_raw["info"][n][5] for n in ss_names],
                               "k": [combo_idx[tuple(ss_raw["info"][n][:5])] for n in ss_names],
                               "fields": ["gmv", "u", "mkd", "np", "rev", "pc1", "ppc1", "gv", "atc", "si", "nsi"], "rows": flat},
                              separators=(",", ":")).encode()
    meta["ssku"] = {"from": ss_raw["from"], "to": ss_raw["to"], "align": ss_raw["align"], "n": len(ss_raw["rows"])}
    return meta, bufs


def lfl_map():
    """TY date -> [LY, LLY]. A mapped date in the wrong year (the table has a few) falls back to the same calendar date."""
    raw = json.loads((DATA / "lfl.json").read_text())
    out = {}
    for d, (ly, lly) in raw.items():
        y = int(d[:4])
        ly = ly if int(ly[:4]) == y - 1 else f"{y - 1}{d[4:]}"
        lly = lly if int(lly[:4]) == y - 2 else f"{y - 2}{d[4:]}"
        out[d] = [ly, lly]
    return out


def pack_targets():
    days = json.loads((DATA / "targets_raw.json").read_text())
    recs = [(d, *r.split(",")) for d in sorted(days) for r in days[d].split(";")]
    dates = sorted(days)
    brands = sorted({r[2] for r in recs})
    cats = sorted({r[3] for r in recs})
    bi = {v: i for i, v in enumerate(brands)}
    ci = {v: i for i, v in enumerate(cats)}
    di = {v: i for i, v in enumerate(dates)}
    flat = []
    for d, c, b, cat, g in recs:
        flat += [di[d], int(c), bi[b], ci[cat], int(round(float(g)))]
    return {"metric": "gmv", "dates": dates, "brand": brands, "cat": cats, "rows": flat, "bm": target_bm(brands)}


def target_bm(brands):
    """Targets are at brand level; each brand is given the business model (retail / mp) with most of its GMV
    (latest year first, then all history) so the Business model filter can use them."""
    cube = json.loads((DATA / "cube_raw.json").read_text())
    gmv = [{}, {}]
    for d, s in cube.items():
        for rec in s.split(";"):
            v = rec.split(",")
            for g in gmv[:1 + (d >= START)]:
                g.setdefault(v[1], {}).setdefault(v[4], 0.0)
                g[v[1]][v[4]] += float(v[6])
    fallback = json.loads((DATA / "target_bm_fallback.json").read_text())   # no sales yet: by item_d SKUs (sql/target_brand_bm.sql)
    out = []
    for br in brands:
        m = gmv[1].get(br) or gmv[0].get(br)
        out.append(max(m, key=m.get) if m else fallback.get(br))
    return out


def build():
    meta, bufs = pack()
    targets = pack_targets()
    html = (ROOT / "template.html").read_text()
    html = html.replace("/*__META__*/null", json.dumps(meta, separators=(",", ":")))
    html = html.replace("/*__TARGETS__*/null", json.dumps(targets, separators=(",", ":")))
    out = ROOT / "dist" / "ond_beauty_dashboard.html"
    (out.parent / "data").mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    # data files are published next to the page and fetched by it (data/<set>.bin, gzip)
    # base64 text, because the artifact host serves text but not raw binary files
    for old in (out.parent / "data").glob("*.bin"):
        old.unlink()
    for name, b in bufs.items():
        (out.parent / "data" / f"{name}.txt").write_text(base64.b64encode(gzip.compress(b, 9)).decode())
    # retail SKUs at risk (sql/risk_skus.sql): plain JSON, loaded when the Risk SKUs tab opens
    (out.parent / "data" / "risk.txt").write_text((DATA / "risk_skus.json").read_text())
    # Nov Flashback + Buyers ref (sql/flashback.sql): plain JSON, loaded when either tab opens
    if (DATA / "flashback_raw.json").exists():
        (out.parent / "data" / "fb.txt").write_text(json.dumps(pack_flashback(), separators=(",", ":")))
    print("data files:", {n: f"{len(gzip.compress(b, 6)) // 1024} KB" for n, b in bufs.items()})
    print(f"wrote {out} ({len(html) // 1024} KB, {[x['n'] for x in meta['sets']]} rows, {len(meta['combos'])} combos)")


FB_YEARS = (2024, 2025, 2026)   # 2026 = September baseline only (current conversion)
FB_REALLOC = {"benefit_cosmetics"}   # discontinued brands: history stays, their 2026 target moves to like-for-like brands
FB_MIN = 5000                  # brands / categories / sub-categories under this LY + LLY window GMV fold into "(other)"


def pack_flashback():
    """data/flashback_raw.json ({"Y|p|days|c": "brand,cat,sub,gmv,u,mkd,np,gv,si,nsi;..."}, period 0 = September)
    -> per level (overall, country, category, sub-category, brand) and entity: v[year][period] = [gmv, u, mkd, np, gv, imp]."""
    raw = json.loads((DATA / "flashback_raw.json").read_text())
    periods = json.loads((DATA / "flashback_periods.json").read_text())
    n_p = len(periods) + 1
    days = {y: [0] * n_p for y in FB_YEARS}
    recs = []
    for k, v in raw.items():
        y, p, d, c = map(int, k.split("|"))
        days[y][p] = d
        for r in v.split(";"):
            x = r.split(",")
            recs.append((y, p, c, x[0], x[1], x[2], [float(t) for t in x[3:6]] + [float(x[6]), float(x[7]), float(x[8]) + float(x[9])]))
    # window GMV (LY + LLY, periods 1..n) decides who gets a row of their own
    win = {"cat": {}, "sub": {}, "brand": {}}
    for y, p, c, b, cat, sub, m in recs:
        if y < 2026 and p > 0:
            for lv, key in (("cat", cat), ("sub", cat + "|" + sub), ("brand", b)):
                win[lv][key] = win[lv].get(key, 0) + m[0]
    keep = {lv: {k for k, g in w.items() if g >= FB_MIN and k not in ("(other brands)", "(none)", "(none)|(none)")} for lv, w in win.items()}
    brand_cat = {}
    for y, p, c, b, cat, sub, m in recs:
        if y == 2025 and p > 0 and b in keep["brand"]:
            brand_cat.setdefault(b, {})[cat] = brand_cat.get(b, {}).get(cat, 0) + m[0]
    levels = {lv: {} for lv in ("all", "country", "cat", "sub", "brand")}
    yi = {y: i for i, y in enumerate(FB_YEARS)}

    def add(lv, key, y, p, m):
        e = levels[lv].setdefault(key, [[[0] * 6 for _ in range(n_p)] for _ in FB_YEARS])
        cell = e[yi[y]][p]
        for i in range(6):
            cell[i] += m[i]

    for y, p, c, b, cat, sub, m in recs:
        add("all", "Beauty", y, p, m)
        add("country", ["KSA", "UAE", "Other GCC"][c], y, p, m)
        add("cat", cat if cat in keep["cat"] else "(other)", y, p, m)
        add("sub", cat + "|" + sub if cat + "|" + sub in keep["sub"] else "(other)|(other)", y, p, m)
        add("brand", b if b in keep["brand"] else "(other brands)", y, p, m)
    out = {}
    for lv, ents in levels.items():
        rows = []
        for key, v in ents.items():
            row = {"k": key, "v": [[[round(t) for t in cell] for cell in yr] for yr in v]}
            if lv == "brand" and key in brand_cat:
                row["cat"] = max(brand_cat[key], key=brand_cat[key].get)
            rows.append(row)
        # LY window GMV, largest first; the "(other …)" bucket last
        rows.sort(key=lambda r: (r["k"].startswith("(other"), -sum(cell[0] for cell in r["v"][1][1:])))
        out[lv] = rows
    # top retail brands (sql/flashback_retail.sql: retail business model only) + hand-written learnings per brand
    retail = []
    if (DATA / "flashback_retail_raw.json").exists():
        rraw = json.loads((DATA / "flashback_retail_raw.json").read_text())
        ents = {}
        for k, v in rraw.items():
            y, p, d = map(int, k.split("|"))
            if days[y][p] != d:
                raise SystemExit(f"flashback_retail_raw {k}: {d} days, flashback_raw has {days[y][p]}")
            for r in v.split(";"):
                x = r.split(",")
                e = ents.setdefault(x[0], [[[0] * 6 for _ in range(n_p)] for _ in FB_YEARS])
                e[yi[y]][p] = [round(float(t)) for t in x[1:7]]
        notes = json.loads((DATA / "flashback_notes.json").read_text()) if (DATA / "flashback_notes.json").exists() else {}
        top = sorted((b for b in ents if b != "(none)"), key=lambda b: -sum(c[0] for c in ents[b][1][1:]))[:20]
        cat_of = {r["k"]: r.get("cat") for r in out["brand"]}
        retail = [{"k": b, "cat": cat_of.get(b), "v": ents[b], "note": notes.get(b)} for b in top]
    # daily Beauty totals (Sept + Nov, LY / LLY) for the impressions vs conversion check: [date, gmv, units, mkd, np→mkd%, gv, imps]
    daily = []
    if (DATA / "flashback_daily.json").exists():
        daily = [[r["d"], round(r["g"]), round(r["u"]), round(r["mk"], 4), round(r["gv"]), round(r["im"])]
                 for r in json.loads((DATA / "flashback_daily.json").read_text()) if r["d"][5:7] in ("09", "11")]
    # discontinued brands: their LY GMV in each period and sub-category is handed to the brands of the same brand type
    # (prestige / masstige) in that sub-category, in proportion to those brands' LY GMV there (whole November when they
    # had none in the period; any brand type when no same-type brand sells there). Category, sub-category and brand-type
    # targets stay the same; only the brand split changes. realloc[brand] = extra LY GMV per period, {"from": ...}.
    btype = {k: v[0] for k, v in json.loads((DATA / "brand_attrs.json").read_text()).items()}
    ly_sub = {}
    for y, p, c, b, cat, sub, m in recs:
        if y == FB_YEARS[1] and p > 0:
            ly_sub.setdefault((cat, sub), {}).setdefault(b, [0.0] * n_p)[p] += m[0]
    realloc = {}
    for gone in sorted(FB_REALLOC):
        for (cat, sub), bs in ly_sub.items():
            src = bs.get(gone)
            if not src:
                continue
            others = {b: v for b, v in bs.items() if b not in FB_REALLOC and not b.startswith("(")}
            same = {b: v for b, v in others.items() if btype.get(b) == btype.get(gone)} or others
            for p in range(1, n_p):
                if not src[p]:
                    continue
                w = {b: v[p] for b, v in same.items() if v[p] > 0} or {b: sum(v[1:]) for b, v in same.items() if sum(v[1:]) > 0}
                tot = sum(w.values())
                for b, wv in w.items():
                    e = realloc.setdefault(b, {"add": [0.0] * n_p, "from": []})
                    e["add"][p] += src[p] * wv / tot
                    if gone not in e["from"]:
                        e["from"].append(gone)
        realloc[gone] = {"gone": True}
    for e in realloc.values():
        if "add" in e:
            e["add"] = [round(v) for v in e["add"]]
    return {"realloc": realloc, "daily": daily, "retail": retail, "periods": [{"p": p["p"], "cohort": p["cohort"].replace("_", " "), "ty": [p["ty"][0], p["ty"][-1]],
                         "ly": [p["ly"][0], p["ly"][-1]], "lly": [p["lly"][0], p["lly"][-1]]} for p in periods],
            "years": list(FB_YEARS), "days": [days[y] for y in FB_YEARS], "lv": out, "uplift": 1.25}


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--targets" in args:
        i = args.index("--targets")
        raw = json.loads(pathlib.Path(args[i + 1]).read_text())
        (DATA / "targets_raw.json").write_text(json.dumps(
            {r["f"][0]["v"]: r["f"][1]["v"] for r in raw["rows"]}, separators=(",", ":")))
        del args[i:i + 2]
    if "--traffic" in args:
        i = args.index("--traffic")
        merge(args[i + 1:], "traffic_raw.json")
        args = args[:i]
    if args:
        merge(args)
    build()
