-- OND Beauty dashboard: daily inventory value at cost and at retail by country x product combo (KSA, UAE).
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "c,key,cost_value,retail_value;..."  c: 0 = KSA, 1 = UAE
--   key = FARM_FINGERPRINT of brand|category|sub_category|business_model|season (names: sql/assortment_combos.sql)
--   cost_value   = inventory_value_derived, retail_v1.stock_summary_history: stock_net_live > 0, id_partner = 3001,
--                  is_eligible_namshi > 0
--   retail_value = stock_net * offer_price, assortment_namshi.psku_sku_mapped: is_primary = 1, id_partner = 3001,
--                  stock_net > 0, is_live = 1
-- Beauty and the samples & GWP exclusion come from item_d (joined on sku). Run per month ({FROM}/{TO}).
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
  SELECT sku, ANY_VALUE(sku_config) AS sku_config
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
cost AS (
  SELECT s.trans_date AS d, IF(s.country_code = 'SA', 0, 1) AS c, cfg.k, SUM(s.inventory_value_derived) cval
  FROM `noonbinamshi.retail_v1.stock_summary_history` s
  JOIN sk USING (sku) JOIN cfg USING (sku_config)
  WHERE s.trans_date BETWEEN '{FROM}' AND '{TO}'
    AND s.stock_net_live > 0 AND s.id_partner = 3001 AND s.is_eligible_namshi > 0 AND s.country_code IN ('SA', 'AE')
  GROUP BY 1, 2, 3
),
retail AS (
  SELECT p.date AS d, IF(p.country = 'SA', 0, 1) AS c, cfg.k, SUM(p.stock_net * p.offer_price) rval
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p
  JOIN sk USING (sku) JOIN cfg USING (sku_config)
  WHERE p.date BETWEEN '{FROM}' AND '{TO}'
    AND p.is_primary = 1 AND p.id_partner = 3001 AND p.stock_net > 0 AND p.is_live = 1 AND p.country IN ('SA', 'AE')
  GROUP BY 1, 2, 3
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%x,%.0f,%.0f', c, k, IFNULL(cval, 0), IFNULL(rval, 0)), ';') r
FROM cost FULL JOIN retail USING (d, c, k) GROUP BY 1 ORDER BY 1
