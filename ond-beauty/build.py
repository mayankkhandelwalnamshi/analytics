"""Build the OND Beauty dashboard HTML.

Usage:
    python3 ond-beauty/build.py [bq_result.json ...]

Each bq_result.json is the raw BigQuery `jobs.query` response of sql/daily_beauty_cube.sql
for one date window (rows: d, r). They are merged into data/cube_raw.json ({date: packed rows};
each record is "c,brand,category,sub_category,gmv,units,mkd,np,rev,pc1,ppc1").
data/lfl.json maps each OND 2026 date to its [LY, LLY] like-for-like date (sql/lfl_mapping.sql).

The cube is packed as columnar binary (int32 metrics, uint16 date/combo, uint8 country),
gzip-compressed and base64-embedded into template.html -> dist/ond_beauty_dashboard.html.

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
FIELDS = ["gmv", "u", "mkd", "np", "rev", "pc1", "ppc1"]


def merge(paths):
    cube_path = DATA / "cube_raw.json"
    days = json.loads(cube_path.read_text()) if cube_path.exists() else {}
    for p in paths:
        raw = json.loads(pathlib.Path(p).read_text())
        for r in raw["rows"]:
            d, s = [c["v"] for c in r["f"]]
            days[d] = s
    cube_path.write_text(json.dumps(days, separators=(",", ":")))


def pack():
    days = json.loads((DATA / "cube_raw.json").read_text())
    dates = sorted(days)
    combo_idx = {}
    cols = [[] for _ in range(3 + len(FIELDS))]  # d, c, k, metrics...
    for di, d in enumerate(dates):
        for rec in days[d].split(";"):
            v = rec.split(",")
            key = (v[1], v[2], v[3])
            if key not in combo_idx:
                combo_idx[key] = len(combo_idx)
            cols[0].append(di)
            cols[1].append(int(v[0]))
            cols[2].append(combo_idx[key])
            for j in range(len(FIELDS)):
                cols[3 + j].append(int(round(float(v[4 + j]))))
    combos = list(combo_idx)
    n = len(cols[0])
    buf = b"".join(struct.pack(f"<{n}i", *cols[3 + j]) for j in range(len(FIELDS)))
    buf += struct.pack(f"<{n}H", *cols[0]) + struct.pack(f"<{n}H", *cols[2]) + struct.pack(f"<{n}B", *cols[1])
    names = {key: sorted({c[i] for c in combos}) for i, key in enumerate(["brand", "cat", "sub"])}
    idx = {key: {v: i for i, v in enumerate(names[key])} for key in names}
    meta = {
        "fields": FIELDS,
        "n": n,
        "dates": dates,
        "names": names,
        "combos": [[idx["brand"][b], idx["cat"][c], idx["sub"][s]] for b, c, s in combos],
        "lfl": lfl_map(),
        "refreshed": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    blob = base64.b64encode(gzip.compress(buf, 9)).decode()
    return meta, blob


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
    return {"metric": "gmv", "dates": dates, "brand": brands, "cat": cats, "rows": flat}


def build():
    meta, blob = pack()
    targets = pack_targets()
    html = (ROOT / "template.html").read_text()
    html = html.replace("/*__META__*/null", json.dumps(meta, separators=(",", ":")))
    html = html.replace("/*__TARGETS__*/null", json.dumps(targets, separators=(",", ":")))
    html = html.replace("__BLOB__", blob)
    out = ROOT / "dist" / "ond_beauty_dashboard.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"wrote {out} ({len(html) // 1024} KB, {meta['n']} rows, {len(meta['combos'])} combos)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--targets" in args:
        i = args.index("--targets")
        raw = json.loads(pathlib.Path(args[i + 1]).read_text())
        (DATA / "targets_raw.json").write_text(json.dumps(
            {r["f"][0]["v"]: r["f"][1]["v"] for r in raw["rows"]}, separators=(",", ":")))
        del args[i:i + 2]
    if args:
        merge(args)
    build()
