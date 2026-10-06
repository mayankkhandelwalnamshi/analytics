# Beauty Pulse · consolidated backend queries

Six BigQuery scripts that output plain tables. Together they replace the 18 dashboard queries in `sql/`; the OND recap is parked.
Billing project: `noonprd-nm-analytics-ai`. Each script starts with a `DECLARE` block, and its defaults are set for a daily run (yesterday).
To run a backfill, edit the dates in that block.

| # | Script | Grain | Replaces | Daily run | One-off backfill |
|---|---|---|---|---|---|
| 01 | `01_daily_product.sql` | date × country × brand × category × sub-category × business model × season | daily_beauty_cube, daily_traffic_cube, daily_oos, daily_retail_cogs | yesterday | Oct–Dec 2025 and 2024; 1 Sep onwards for the WoC columns |
| 02 | `02_daily_stock.sql` | date × country (SA/AE) × same combo | daily_assortment, daily_inventory_value, daily_inventory_ageing, assortment_combos | yesterday | Oct–Dec 2025 and 2024 |
| 03 | `03_daily_orders.sql` | date × country × level × level value | daily_orders | yesterday | Oct–Dec 2025 and 2024 |
| 04 | `04_reference.sql` | long table, filter on `dataset` | targets_beauty, platform_gmv, lfl_mapping, lfl_cohort, brand_attributes, target_brand_bm | yesterday (platform GMV) | platform GMV for OND 2025 / 2024 |
| 05 | `05_risk_skus.sql` | country × product card (top 500 at risk) | risk_skus, risk_skus_age, risk_skus_cfg | full refresh daily, after `psku_sku_mapped` lands | – |
| 06 | `06_mtd_supplier_sku.sql` | country × supplier SKU, MTD with LY / LLY | mtd_ssku | full refresh daily | – |

## Suggested setup (scheduled queries or dagman)
- **01–03 and the `platform_gmv` part of 04:** append yesterday to a date-partitioned table. Use `MERGE` or delete-then-insert on the date, so a re-run doesn't double count.
- **05, 06 and the rest of 04:** overwrite the table each day.
- **Order:** 04 → 01–03 → 05 → 06. Run 05 after the morning `psku_sku_mapped` snapshot.

## Rules shared by all scripts
- **Scope:** Beauty is item_d `business_unit = 'beauty'`; samples & GWP are excluded everywhere. Sales use Namshi marketplaces (`namshi`, `namshi_v2`) and `gmv_inc_vat > 0`.
- **Season:** comes from `beauty_season_mapping` (`'unassigned'` when missing). It is `'mp'` when the product isn't Namshi retail (partner 3001): judged per sku for sales, OOS and COGS, and per sku_config for traffic and stock.
- **Ratios are calculated on the dashboard from the summed columns, never averaged:**
  - ASP = gmv / units
  - MKD % = markdown / normal_price
  - PC1 % = pc1 / revenue
  - CTR = glance_views / (search_impr + non_search_impr)
- **Orders don't add up across products**, so use the row in 03 that matches the level you need.
- **Overall assortment** = KSA + UAE added together.
