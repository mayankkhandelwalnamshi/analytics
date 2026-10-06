-- Beauty Pulse · 04 · REFERENCE DATA (plain table, long format: filter on `dataset`)
-- Replaces: targets_beauty, platform_gmv, lfl_mapping, lfl_cohort, brand_attributes (target_brand_bm is no longer needed:
-- the business model of a target brand can be derived from 01 by the brand's main business model).
--   dataset 'beauty_target'    date, country, brand, category, gmv           planning_dod_merch_brand_category_targets, pod cp_beauty
--   dataset 'platform_target'  date, country, gmv                            same table, all pods
--   dataset 'platform_gmv'     date, country, gmv                            all categories on Namshi (same sales scope as Beauty)
--   dataset 'lfl'              date, ly_date, lly_date, cohort               lfl_mapping (TY date -> LY / LLY like-for-like date)
--   dataset 'brand_attr'       brand, brand_type, brand_group, brand_poc     'unassigned' when missing
-- Run daily (platform_gmv needs yesterday); the rest only changes when the source tables change.
DECLARE d_from DATE DEFAULT DATE '2026-10-01';                                     -- OND window for targets / LFL
DECLARE d_to   DATE DEFAULT DATE '2026-12-31';
DECLARE g_from DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);  -- platform GMV window
DECLARE g_to   DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);

WITH tg AS (
  SELECT date, country, pod_code, brand, category, SUM(gmv) gmv
  FROM `noonbinmlook.namshi_analytics_custom.planning_dod_merch_brand_category_targets`
  WHERE date BETWEEN d_from AND d_to GROUP BY 1, 2, 3, 4, 5
),
it AS (SELECT sku, MAX(LOWER(inventory_type)) inventory_type FROM `noonbinamshi.custom_views.item_d` GROUP BY 1)
SELECT 'beauty_target' dataset, date, country, IFNULL(brand, '(none)') brand, IFNULL(category, '(none)') category,
  ROUND(SUM(gmv), 2) gmv, CAST(NULL AS DATE) ly_date, CAST(NULL AS DATE) lly_date, CAST(NULL AS STRING) cohort,
  CAST(NULL AS STRING) brand_type, CAST(NULL AS STRING) brand_group, CAST(NULL AS STRING) brand_poc
FROM tg WHERE pod_code = 'cp_beauty' GROUP BY 1, 2, 3, 4, 5 HAVING SUM(gmv) <> 0
UNION ALL
SELECT 'platform_target', date, country, NULL, NULL, ROUND(SUM(gmv), 2), NULL, NULL, NULL, NULL, NULL, NULL
FROM tg GROUP BY 1, 2, 3
UNION ALL
SELECT 'platform_gmv', s.order_date_key, s.country, NULL, NULL, ROUND(SUM(s.gmv_inc_vat), 2), NULL, NULL, NULL, NULL, NULL, NULL
FROM `noonbinamshi.custom_views.sales_metrics` s LEFT JOIN it USING (sku)
WHERE s.order_date_key BETWEEN g_from AND g_to AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
  AND IFNULL(it.inventory_type, '') <> 'samples & gwp'
GROUP BY 1, 2, 3
UNION ALL
SELECT 'lfl', date, NULL, NULL, NULL, NULL,
  -- a mapped date in the wrong year (the table has a few) falls back to the same calendar date
  IF(EXTRACT(YEAR FROM MIN(ly_lfl)) = EXTRACT(YEAR FROM date) - 1, MIN(ly_lfl), DATE_SUB(date, INTERVAL 1 YEAR)),
  IF(EXTRACT(YEAR FROM MIN(ly2_lfl)) = EXTRACT(YEAR FROM date) - 2, MIN(ly2_lfl), DATE_SUB(date, INTERVAL 2 YEAR)),
  REPLACE(MIN(cohort), '_', ' '), NULL, NULL, NULL
FROM `noonbinmlook.namshi_analytics_custom.lfl_mapping`
WHERE date BETWEEN d_from AND d_to GROUP BY 1, 2
UNION ALL
SELECT 'brand_attr', NULL, NULL, b.brand_code, NULL, NULL, NULL, NULL, NULL,
  IFNULL(t.tag, 'unassigned'), IFNULL(g.brand_group_, 'unassigned'), IFNULL(p.poc, 'unassigned')
FROM (SELECT DISTINCT brand_code FROM `noonbinamshi.custom_views.item_d` WHERE business_unit = 'beauty' AND brand_code IS NOT NULL) b
LEFT JOIN (SELECT brand AS brand_code, MAX(LOWER(tag)) tag
           FROM `noonbinmlook.namshi_analytics_custom.beauty_pestige_mastige_mapping` GROUP BY ALL) t USING (brand_code)
LEFT JOIN (SELECT LOWER(brands) AS brand_code, MAX(brand_group) brand_group_
           FROM `noonbinmlook.namshi_analytics_custom.brand_group_beauty` GROUP BY ALL) g USING (brand_code)
LEFT JOIN (SELECT brand AS brand_code, MAX(poc) poc
           FROM `noonbinmlook.namshi_analytics_custom.brand_poc_beauty` GROUP BY ALL) p USING (brand_code);
