# Beauty · November '26 strategy doc (backing numbers)

Numbers behind the "Beauty — November '26 Strategy" doc (as of 12 Oct 2026). Goals: Nov '26 GMV +25% vs Nov '25, year-end retail stock ≤ 10 weeks of Dec '25 sales.

- `queries.sql` – the BigQuery queries (billing project `noonprd-nm-analytics-ai`); results were pasted into the scripts below.
- `plan.py` – top 15 brands, stock + open POs at 80% fill, year-end WoC scenarios, brand health table, GMV per 1K impressions.
- `daily.py` – Nov '24 / Nov '25 daily GMV, units, impressions, glance views: UCR vs traffic.
- `peaks_margin.py` – first-half share, event vs shoulder days, PC1 / markdown history, Nov multiples.
- `rebates.py` – PC1 before / incl. rebates by brand for Nov '25 (LY only; TY stays before rebates).

Definitions: Beauty = item_d `business_unit = 'beauty'`, no samples & GWP; sales on Namshi marketplaces with `gmv_inc_vat > 0`.
Retail stock = primary, live Namshi retail listings (partner 3001) in SA + AE. WoC = units / (Dec '25 retail units / 31 × 7).
- `impressions_funnel.py` – impressions needed for AED 20.6M: Nov '25 funnel (CTR, UCR, ASP) adjusted by TY vs LY trends (1–12 Oct and Jul–Sep). Base ≈ 565M, range 508–647M.
- `woc_retail.py` – year-end WoC from retail GMV only: LY retail GMV × TY trend ÷ TY retail ASP → units; plan case = AED 20.6M × 86% retail share in November.
- `impressions_funnel_bm.py` – impressions needed by retail (AED 18.5M) and MP (AED 2.1M): each segment's Nov '25 CTR / UCR / ASP × (70% Jul–Oct TY-vs-LY trend + 30% no change). Base ≈ 517M + 72M = 588M, range 511–635M.
- `nov_cohort_targets.py` – Nov '26 target split by cohort (Nov target not yet in the planning table; Oct target AED 8.62M is).
