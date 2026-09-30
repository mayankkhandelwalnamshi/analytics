"""Build the OND Beauty dashboard HTML.

Usage:
    python3 ond-beauty/build.py [bq_result.json ...]

Each bq_result.json is the raw BigQuery `jobs.query` response of sql/daily_beauty_cube.sql
for one date window (rows: d, r). They are merged into data/cube_raw.json ({date: packed rows}).
data/combos.json holds the [brand, category, sub_category] list; row k = combo index k.

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
    combos = json.loads((DATA / "combos.json").read_text())
    dates = sorted(days)
    cols = [[] for _ in range(3 + len(FIELDS))]  # d, c, k, metrics...
    for di, d in enumerate(dates):
        for rec in days[d].split(";"):
            v = rec.split(",")
            cols[0].append(di)
            cols[1].append(int(v[0]))
            cols[2].append(int(v[1]))
            for j in range(len(FIELDS)):
                cols[3 + j].append(int(round(float(v[2 + j]))))
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
        "refreshed": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    blob = base64.b64encode(gzip.compress(buf, 9)).decode()
    return meta, blob


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
