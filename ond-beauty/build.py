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
        "oosDates": sorted(raw["oos_raw.json"]),
        "ageDates": sorted(raw["age_raw.json"]),
        "platform": json.loads((DATA / "platform.json").read_text()),   # sql/platform_gmv.sql
        "refreshed": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    bufs["orders"] = buf
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
    # top retail SKUs (sql/top_skus.sql): plain JSON, loaded when the Top SKU tab opens
    (out.parent / "data" / "skus.txt").write_text((DATA / "top_skus.json").read_text())
    print("data files:", {n: f"{len(gzip.compress(b, 6)) // 1024} KB" for n, b in bufs.items()})
    print(f"wrote {out} ({len(html) // 1024} KB, {[x['n'] for x in meta['sets']]} rows, {len(meta['combos'])} combos)")


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
