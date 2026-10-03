-- OND Beauty dashboard: daily live assortment and live stock by country x product combo.
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "c,key,live_cfg,cb_cfg,live_stock;..."
--   c: 0 = KSA, 1 = UAE, 2 = KSA + UAE together (distinct products are counted once across both countries)
--   key = FARM_FINGERPRINT of brand|category|sub_category|business_model|season (names: sql/assortment_combos.sql)
-- Source: assortment_namshi.psku_sku_mapped, rows with stock_net > 0, is_live = 1, country in SA / AE,
-- joined to item_d on sku (Beauty, no samples & GWP). Product attributes are taken at sku_config level.
--   live_cfg   = distinct live sku_config
--   cb_cfg     = distinct live sku_config sold in KSA from the UAE warehouse (cross-border)
--   live_stock = stock_net on primary listings of partner 3001 (Namshi retail)
-- A product sits in exactly one combo, so distinct counts add up across combos (not across countries: c = 2).
-- Run per 10-day window ({FROM}/{TO}) for Oct-Dec 2024, Oct-Dec 2025 and 2026-10-01..yesterday.
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
cfg AS (
  SELECT i.sku_config,
    FARM_FINGERPRINT(CONCAT(IFNULL(ANY_VALUE(i.brand_code), '(none)'), '|', IFNULL(ANY_VALUE(i.category), '(none)'), '|',
      IFNULL(ANY_VALUE(i.sub_category), '(none)'), '|', IFNULL(ANY_VALUE(i.business_model), '(none)'), '|',
      IFNULL(ANY_VALUE(se.beauty_season), 'unassigned'))) AS k
  FROM `noonbinamshi.custom_views.item_d` i
  LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
sk AS (
  SELECT sku, ANY_VALUE(sku_config) AS sku_config
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
p AS (
  SELECT p.date AS d, IF(p.country = 'SA', 0, 1) AS c, cfg.k, sk.sku_config,
    p.country = 'SA' AND p.warehouse_country = 'AE' AS is_cb,
    IF(p.is_primary = 1 AND p.id_partner = 3001, p.stock_net, 0) AS st
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p
  JOIN sk USING (sku)
  JOIN cfg USING (sku_config)
  WHERE p.date BETWEEN '{FROM}' AND '{TO}'
    AND p.stock_net > 0 AND p.is_live = 1 AND p.country IN ('SA', 'AE')
),
x AS (
  SELECT d, c, k, COUNT(DISTINCT sku_config) la, COUNT(DISTINCT IF(is_cb, sku_config, NULL)) cb, SUM(st) st FROM p GROUP BY 1, 2, 3
  UNION ALL
  SELECT d, 2, k, COUNT(DISTINCT sku_config), COUNT(DISTINCT IF(is_cb, sku_config, NULL)), SUM(st) FROM p GROUP BY 1, 3
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%x,%d,%d,%d', c, k, la, cb, st), ';') r
FROM x GROUP BY 1 ORDER BY 1
