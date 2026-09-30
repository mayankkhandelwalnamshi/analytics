"""Build the OND Beauty dashboard HTML.

Usage:
    python3 ond-beauty/build.py [bigquery_result.json]

If a BigQuery JSON result (the raw `jobs.query` response of sql/daily_beauty.sql)
is passed, it is converted into data/daily.json first. Then data/daily.json and
data/targets.json are injected into template.html -> dist/ond_beauty_dashboard.html.

targets.json shape (only metrics/regions that have a target):
    {"gmv": {"KSA": {"2026-10-01": 150000, ...}, "UAE": {...}, "ALL": {...}}}
"""
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"


def convert(raw_path):
    raw = json.loads(pathlib.Path(raw_path).read_text())
    fields = [f["name"] for f in raw["schema"]["fields"]]
    days = {}
    for r in raw["rows"]:
        v = [c["v"] for c in r["f"]]
        days.setdefault(v[0], {})[v[1]] = [float(x) if x is not None else 0 for x in v[2:]]
    (DATA / "daily.json").write_text(
        json.dumps({"fields": fields[2:], "days": days}, separators=(",", ":"))
    )


def build():
    daily = json.loads((DATA / "daily.json").read_text())
    daily["refreshed"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    targets = json.loads((DATA / "targets.json").read_text())
    html = (ROOT / "template.html").read_text()
    html = html.replace("/*__DATA__*/null", json.dumps(daily, separators=(",", ":")))
    html = html.replace("/*__TARGETS__*/null", json.dumps(targets, separators=(",", ":")))
    out = ROOT / "dist" / "ond_beauty_dashboard.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"wrote {out} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        convert(sys.argv[1])
    build()
