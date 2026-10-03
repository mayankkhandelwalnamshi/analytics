-- OND Beauty dashboard: daily retail units sold and COGS by warehouse country x product combo, for weeks of cover (WoC).
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "c,brand,category,sub_category,business_model,season,units,cogs;..."
-- Same scope as sql/daily_beauty_cube.sql (Namshi marketplaces, gmv_inc_vat > 0, Beauty, no samples & GWP), business model
-- retail only. cogs = sales_metrics.cogs. Run per window ({FROM}/{TO}) from 1 Sep, so the page can take the last 30 days
-- for any OND day: 2024-09-01..2024-12-31, 2025-09-01..2025-12-31, 2026-09-01..yesterday.
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
beauty AS (
  SELECT i.sku,
    IFNULL(ANY_VALUE(i.brand_code), '(none)')     AS brand,
    IFNULL(ANY_VALUE(i.category), '(none)')       AS cat,
    IFNULL(ANY_VALUE(i.sub_category), '(none)')   AS sub,
    IFNULL(ANY_VALUE(i.business_model), '(none)') AS bm,
    IFNULL(ANY_VALUE(se.beauty_season), 'unassigned') AS season
  FROM `noonbinamshi.custom_views.item_d` i
  LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND i.business_model = 'retail'
    AND IFNULL(i.inventory_type, '') <> 'samples & gwp'   -- samples & GWP are excluded from every metric
  GROUP BY 1
),
x AS (
  -- warehouse level: c = the shipping warehouse (warehouse_country_code), so the UAE warehouse's units include KSA
  -- cross-border and GCC orders, matching the stock / inventory value it holds
  SELECT s.order_date_key AS d, CASE s.warehouse_country_code WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, b.bm, b.season, SUM(s.items_gross) u, SUM(s.cogs) cogs
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN beauty b USING (sku)
  WHERE s.order_date_key BETWEEN '{FROM}' AND '{TO}'
    AND s.marketplace IN ('namshi', 'namshi_v2')
    AND s.gmv_inc_vat > 0
  GROUP BY 1, 2, 3, 4, 5, 6, 7
)
SELECT FORMAT_DATE('%F', d) d,
  STRING_AGG(FORMAT('%d,%s,%s,%s,%s,%s,%d,%.0f', c, brand, cat, sub, bm, season, IFNULL(u, 0), IFNULL(cogs, 0)), ';') r
FROM x GROUP BY 1 ORDER BY 1
