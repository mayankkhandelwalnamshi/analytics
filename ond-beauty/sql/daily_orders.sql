-- OND Beauty dashboard: daily distinct Beauty orders at each level the dashboard filters use.
-- Billing project: noonprd-nm-analytics-ai. One row per day:
--   r = "level,c,key,orders;..."   c: 0=KSA 1=UAE 2=Other GCC
--   level 0 = all Beauty (key ''), 1 = category, 2 = category|sub_category, 3 = brand, 4 = brand|category|sub_category
-- Distinct counts don't add up across brands/categories (one order can hold several), so each level is
-- counted exactly; the page sums the level that matches the active filters.
-- Same scope as sales: Namshi marketplaces, gmv_inc_vat > 0, Beauty business unit.
-- Run once per month ({FROM}/{TO}) for Oct-Dec 2024 and Oct-Dec 2025, and for 2026-10-01..yesterday.
WITH beauty AS (
  SELECT sku,
    IFNULL(ANY_VALUE(brand_code), '(none)')   AS brand,
    IFNULL(ANY_VALUE(category), '(none)')     AS cat,
    IFNULL(ANY_VALUE(sub_category), '(none)') AS sub
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty'
  GROUP BY sku
),
base AS (
  SELECT s.order_date_key AS d, CASE s.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, s.order_nr
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
  UNION ALL SELECT d, c, 4, CONCAT(brand, '|', cat, '|', sub), COUNT(DISTINCT order_nr) FROM base GROUP BY 1, 2, 4
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%d,%s,%d', l, c, k, n), ';') r
FROM lv GROUP BY 1 ORDER BY 1
