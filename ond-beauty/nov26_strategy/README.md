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
- `impressions_funnel_bm.py` – impressions needed by retail (AED 17.9M) and MP (AED 2.7M), MP share 13%: each segment's Nov '25 CTR / UCR / ASP × (70% Jul–Oct TY-vs-LY trend + 30% no change). Base ≈ 499M + 93M = 593M, range 515–640M.
- `nov_cohort_targets.py` – Nov '26 target split by cohort (Nov target not yet in the planning table; Oct target AED 8.62M is).
- `brand_health.py` – brand health tables and risk buckets (retail top 15, MP top 5).
- `ct_markdown_cap.py` – Charlotte Tilbury Nov markdown capped at 30% (55% LY): units lift interpolated between Nov '24 and Nov '25, effect on year-end WoC.
- `refresh_13oct.py` – 14 Oct refresh to 13 Oct data: rebuilds page/health.json, stock/PO, year-end WoC scenarios and impressions.
