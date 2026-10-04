-- OND Beauty dashboard: daily out-of-stock GMV loss by country x product combo.
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "c,brand,category,sub_category,business_model,season,oos_gmv_loss;..."
-- Source: noonbinmlook.looker.out_of_stock_new (one row per date x country x sku; KSA and UAE only; history from 2025-01-01).
-- Run once per window ({FROM}/{TO}): 2025-10-01..2025-12-31 and 2026-10-01..yesterday.
-- Combo key = brand, category, sub_category, business_model (item_d) and beauty season
-- (beauty_season_mapping on sku_config, 'unassigned' when missing; 'mp' when the partner is not Namshi retail, item_d id_partner <> 3001). Brand type / group / POC are brand
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
    IF(IFNULL(ANY_VALUE(i.id_partner), 0) <> 3001, 'mp', IFNULL(ANY_VALUE(se.beauty_season), 'unassigned')) AS season   -- non-Namshi partner = mp
  FROM `noonbinamshi.custom_views.item_d` i
  LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty'
    AND IFNULL(i.inventory_type, '') <> 'samples & gwp'   -- samples & GWP are excluded from every metric
  GROUP BY 1
),
x AS (
  SELECT o.date AS d, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, b.bm, b.season, SUM(o.oos_gmv_loss) loss
  FROM `noonbinmlook.looker.out_of_stock_new` o
  JOIN beauty b USING (sku)
  WHERE o.date BETWEEN '{FROM}' AND '{TO}'
  GROUP BY 1, 2, 3, 4, 5, 6, 7
  HAVING ROUND(loss) <> 0
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%s,%s,%s,%s,%s,%.0f', c, brand, cat, sub, bm, season, loss), ';') r
FROM x GROUP BY 1 ORDER BY 1
