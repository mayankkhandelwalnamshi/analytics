# OND Beauty Dashboard

Interactive HTML dashboard for Beauty during OND 2026 (from 1 Oct), compared with LY and LLY.

- `sql/daily_beauty_cube.sql (one run per window), sql/targets_beauty.sql, sql/lfl_mapping.sql` – daily Beauty metrics by country (billing project `noonprd-nm-analytics-ai`)
- `data/daily.json` – query output in compact form
- `data/targets.json` – daily targets per metric and region (empty for now)
- `template.html` – dashboard page; `build.py` injects the data and writes `dist/ond_beauty_dashboard.html`

## Refresh

1. Run `sql/daily_beauty_cube.sql (one run per window), sql/targets_beauty.sql, sql/lfl_mapping.sql` and save the raw BigQuery JSON result.
2. `python3 ond-beauty/build.py <result.json>`
3. Republish `dist/ond_beauty_dashboard.html`.

## Tabs

1. **Daily trend** – GMV, ASP, Units, MKD %, PC1 %, Prov. PC1 % day on day vs LY / LLY (/ Target), for Overall, KSA and UAE.
