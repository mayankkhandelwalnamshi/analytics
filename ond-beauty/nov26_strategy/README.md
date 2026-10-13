# Beauty · November '26 strategy doc (backing numbers)

Numbers behind the "Beauty — November '26 Strategy" doc (as of 12 Oct 2026). Goals: Nov '26 GMV +25% vs Nov '25, year-end retail stock ≤ 10 weeks of Dec '25 sales.

- `queries.sql` – the BigQuery queries (billing project `noonprd-nm-analytics-ai`); results were pasted into the scripts below.
- `plan.py` – top 15 brands, stock + open POs at 80% fill, year-end WoC scenarios, brand health table, GMV per 1K impressions.
- `daily.py` – Nov '24 / Nov '25 daily GMV, units, impressions, glance views: UCR vs traffic.
- `peaks_margin.py` – first-half share, event vs shoulder days, PC1 / markdown history, Nov multiples.

Definitions: Beauty = item_d `business_unit = 'beauty'`, no samples & GWP; sales on Namshi marketplaces with `gmv_inc_vat > 0`.
Retail stock = primary, live Namshi retail listings (partner 3001) in SA + AE. WoC = units / (Dec '25 retail units / 31 × 7).
