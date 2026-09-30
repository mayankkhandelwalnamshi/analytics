"""Build the OND Beauty dashboard HTML.

Usage:
    python3 ond-beauty/build.py [bq_result.json ...]

Each bq_result.json is the raw BigQuery `jobs.query` response of sql/daily_beauty_cube.sql
for one date window (rows: d, r). They are merged into data/cube_raw.json ({date: packed rows}).
data/combos.json holds the [brand, category, sub_category] list; row k = combo index k.

The cube is packed as columnar binary (int32 metrics, uint16 date/combo, uint8 country),
gzip-compressed and base64-embedded into template.html -> dist/ond_beauty_dashboard.html.

targets.json shape (only metrics/regions that have a target; unfiltered Beauty only):
    {"gmv": {"KSA": {"2026-10-01": 150000, ...}, "UAE": {...}, "ALL": {...}}}
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


def build():
    meta, blob = pack()
    targets = json.loads((DATA / "targets.json").read_text())
    html = (ROOT / "template.html").read_text()
    html = html.replace("/*__META__*/null", json.dumps(meta, separators=(",", ":")))
    html = html.replace("/*__TARGETS__*/null", json.dumps(targets, separators=(",", ":")))
    html = html.replace("__BLOB__", blob)
    out = ROOT / "dist" / "ond_beauty_dashboard.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"wrote {out} ({len(html) // 1024} KB, {meta['n']} rows, {len(meta['combos'])} combos)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        merge(sys.argv[1:])
    build()
