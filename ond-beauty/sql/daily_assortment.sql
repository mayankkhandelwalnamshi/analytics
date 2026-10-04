-- OND Beauty dashboard: daily live assortment and live stock by country x product combo.
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "c,key,live_ssku,cb_ssku,live_stock,new_ssku;..."
--   c: 0 = KSA, 1 = UAE (Overall on the dashboard = KSA + UAE summed)
--   key = FARM_FINGERPRINT of brand|category|sub_category|business_model|season (names: sql/assortment_combos.sql)
-- Source: assortment_namshi.psku_sku_mapped, rows with stock_net > 0, is_live = 1, country in SA / AE,
-- joined to item_d on sku (Beauty, no samples & GWP). Product attributes are taken at sku_config level.
--   live_ssku  = distinct live supplier_sku (item_d; the sku when blank)
--   cb_ssku    = distinct live supplier_sku sold in KSA from the UAE warehouse (cross-border)
--   live_stock = stock_net on primary listings of partner 3001 (Namshi retail)
--   new_ssku   = distinct live supplier_sku activated in that country (item_d activated_at_sa / activated_at_ae)
--                between 1 Jul of the date's year and the date (newness: TY from 2026-07-01, LY from 2025-07-01, ...)
-- A product sits in exactly one combo, so distinct counts add up across combos.
-- Run per 10-day window ({FROM}/{TO}) for Oct-Dec 2024, Oct-Dec 2025 and 2026-10-01..yesterday.
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
cfg AS (
  SELECT i.sku_config,
    FARM_FINGERPRINT(CONCAT(IFNULL(ANY_VALUE(i.brand_code), '(none)'), '|', IFNULL(ANY_VALUE(i.category), '(none)'), '|',
      IFNULL(ANY_VALUE(i.sub_category), '(none)'), '|', IFNULL(ANY_VALUE(i.business_model), '(none)'), '|',
      IF(LOGICAL_OR(i.id_partner = 3001), IFNULL(ANY_VALUE(se.beauty_season), 'unassigned'), 'mp'))) AS k
  FROM `noonbinamshi.custom_views.item_d` i
  LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
sk AS (
  SELECT sku, ANY_VALUE(sku_config) AS sku_config, IFNULL(ANY_VALUE(supplier_sku), sku) AS ssku,
    DATE(MIN(activated_at_sa)) AS act_sa, DATE(MIN(activated_at_ae)) AS act_ae
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
p AS (
  SELECT p.date AS d, IF(p.country = 'SA', 0, 1) AS c, cfg.k, sk.ssku,
    IF(p.country = 'SA', sk.act_sa, sk.act_ae) BETWEEN DATE(EXTRACT(YEAR FROM p.date), 7, 1) AND p.date AS is_new,
    p.country = 'SA' AND p.warehouse_country = 'AE' AS is_cb,
    IF(p.is_primary = 1 AND p.id_partner = 3001, p.stock_net, 0) AS st
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p
  JOIN sk USING (sku)
  JOIN cfg USING (sku_config)
  WHERE p.date BETWEEN '{FROM}' AND '{TO}'
    AND p.stock_net > 0 AND p.is_live = 1 AND p.country IN ('SA', 'AE')
),
x AS (
  SELECT d, c, k, COUNT(DISTINCT ssku) la, COUNT(DISTINCT IF(is_cb, ssku, NULL)) cb, SUM(st) st,
    COUNT(DISTINCT IF(is_new, ssku, NULL)) nw FROM p GROUP BY 1, 2, 3
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%x,%d,%d,%d,%d', c, k, la, cb, st, nw), ';') r
FROM x GROUP BY 1 ORDER BY 1
