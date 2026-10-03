-- OND Beauty dashboard: inventory value at cost by ageing band, by country x product combo (KSA, UAE), TY only.
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "c,key,0-89,90-179,180-359,360-719,720+;..." (AED at cost)
-- Cost value as in sql/daily_inventory_value.sql; ageing from namshi_analytics_custom.ageing_cost (sku_config_ageing_detailed),
-- one bucket per country x sku_config. Stock without an ageing bucket is in none of the bands. Run for 2026-10-01..yesterday.
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
age AS (
  -- one ageing bucket per country x sku_config (the oldest seen since 1 Oct 2026; the buckets are lettered a.0-29 .. n.720+)
  SELECT country, sku_config, MAX(sku_config_ageing_detailed) AS ageing
  FROM `noonbinmlook.namshi_analytics_custom.ageing_cost` WHERE date >= "2026-10-01" GROUP BY ALL
),
cost AS (
  SELECT s.trans_date AS d, IF(s.country_code = 'SA', 0, 1) AS c, cfg.k,
    CASE WHEN ag.ageing < 'd' THEN 0 WHEN ag.ageing < 'g' THEN 1 WHEN ag.ageing < 'm' THEN 2 WHEN ag.ageing < 'n' THEN 3 WHEN ag.ageing IS NOT NULL THEN 4 END AS b,
    SUM(s.inventory_value_derived) cval
  FROM `noonbinamshi.retail_v1.stock_summary_history` s
  JOIN sk USING (sku) JOIN cfg USING (sku_config)
  LEFT JOIN age ag ON ag.country = s.country_code AND ag.sku_config = sk.sku_config
  WHERE s.trans_date BETWEEN '{FROM}' AND '{TO}'
    AND s.stock_net_live > 0 AND s.id_partner = 3001 AND s.is_eligible_namshi > 0 AND s.country_code IN ('SA', 'AE')
  GROUP BY 1, 2, 3, 4
),
y AS (
  SELECT d, c, k, SUM(IF(b = 0, cval, 0)) a0, SUM(IF(b = 1, cval, 0)) a1, SUM(IF(b = 2, cval, 0)) a2,
    SUM(IF(b = 3, cval, 0)) a3, SUM(IF(b = 4, cval, 0)) a4 FROM cost GROUP BY 1, 2, 3
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%x,%.0f,%.0f,%.0f,%.0f,%.0f', c, k, a0, a1, a2, a3, a4), ';') r
FROM y GROUP BY 1 ORDER BY 1
