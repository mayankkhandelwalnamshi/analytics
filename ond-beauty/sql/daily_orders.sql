-- OND Beauty dashboard: daily distinct Beauty orders at each level the dashboard filters use.
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "level,c,key,orders;..."
--   level 0 = all Beauty (key ''), 1 = category, 2 = category|sub_category, 3 = brand,
--   5 = business_model, 6 = season  (level 4 is not used: mixed filters are estimated on the page from
--   brand-level orders scaled by the share of the brand's units that pass the filters)
-- Distinct counts don't add up across groups (one order can hold several), so each level is counted
-- exactly and the page sums the level that matches the active filters.
-- Same scope as sales. Run once per window (same windows as daily_beauty_cube.sql).
-- Combo key = brand, category, sub_category, business_model (item_d) and beauty season
-- (beauty_season_mapping on sku_config, 'unassigned' when missing). Brand type / group / POC are brand
-- attributes and are mapped on the page from sql/brand_attributes.sql.
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
  WHERE i.business_unit = 'beauty'
    AND IFNULL(i.inventory_type, '') <> 'samples & gwp'   -- samples & GWP are excluded from every metric
  GROUP BY 1
),
base AS (
  SELECT s.order_date_key AS d, CASE s.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, b.bm, b.season, s.order_nr
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN beauty b USING (sku)
  WHERE s.order_date_key BETWEEN '{FROM}' AND '{TO}'
    AND s.marketplace IN ('namshi', 'namshi_v2')
    AND s.gmv_inc_vat > 0
),
lv AS (
  SELECT d, c, 0 AS l, '' AS k, COUNT(DISTINCT order_nr) n FROM base GROUP BY 1, 2
  UNION ALL SELECT d, c, 1, cat, COUNT(DISTINCT order_nr) FROM base GROUP BY 1, 2, 4
  UNION ALL SELECT d, c, 2, CONCAT(cat, '|', sub), COUNT(DISTINCT order_nr) FROM base GROUP BY 1, 2, 4
  UNION ALL SELECT d, c, 3, brand, COUNT(DISTINCT order_nr) FROM base GROUP BY 1, 2, 4
  UNION ALL SELECT d, c, 5, bm, COUNT(DISTINCT order_nr) FROM base GROUP BY 1, 2, 4
  UNION ALL SELECT d, c, 6, season, COUNT(DISTINCT order_nr) FROM base GROUP BY 1, 2, 4
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%d,%s,%d', l, c, k, n), ';') r
FROM lv GROUP BY 1 ORDER BY 1
