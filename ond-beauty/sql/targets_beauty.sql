-- OND Beauty dashboard: daily GMV targets for Beauty, packed one row per day.
-- Billing project: noonprd-nm-analytics-ai.  r = "c,brand,category,gmv;..."  c: 0=KSA 1=UAE 2=Other GCC
-- Source: planning_dod_merch_brand_category_targets, pod_code = 'cp_beauty', from 1 Oct 2026 onwards.
-- Target grain is date x country x brand x category (category = item_d.category, brand = item_d.brand_code),
-- so the Target line follows the Category and Brand filters but not Sub-category.
SELECT FORMAT_DATE('%F', date) d,
  STRING_AGG(FORMAT('%d,%s,%s,%.0f', CASE country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END,
                    IFNULL(brand, '(none)'), IFNULL(category, '(none)'), g), ';') r
FROM (
  SELECT date, country, brand, category, SUM(gmv) g
  FROM `noonbinmlook.namshi_analytics_custom.planning_dod_merch_brand_category_targets`
  WHERE pod_code = 'cp_beauty' AND date BETWEEN '2026-10-01' AND '2026-12-31'
  GROUP BY 1, 2, 3, 4
  HAVING g <> 0
)
GROUP BY 1 ORDER BY 1
