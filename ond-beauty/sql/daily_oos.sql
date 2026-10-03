-- OND Beauty dashboard: daily out-of-stock GMV loss by country x brand x category x sub-category.
-- Billing project: noonprd-nm-analytics-ai. One row per day:  r = "c,brand,category,sub_category,oos_gmv_loss;..."
-- Source: noonbinmlook.looker.out_of_stock_new (one row per date x country x sku; KSA and UAE only; history from 2025-01-01).
-- Beauty, brand / category / sub-category and the samples & GWP exclusion come from item_d (joined on sku), as for sales.
-- Run once per month ({FROM}/{TO}) for Oct-Dec 2025 and for 2026-10-01..yesterday.
WITH beauty AS (
  SELECT sku,
    IFNULL(ANY_VALUE(brand_code), '(none)')   AS brand,
    IFNULL(ANY_VALUE(category), '(none)')     AS cat,
    IFNULL(ANY_VALUE(sub_category), '(none)') AS sub
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty'
    AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY sku
),
x AS (
  SELECT o.date AS d, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, SUM(o.oos_gmv_loss) loss
  FROM `noonbinmlook.looker.out_of_stock_new` o
  JOIN beauty b USING (sku)
  WHERE o.date BETWEEN '{FROM}' AND '{TO}'
  GROUP BY 1, 2, 3, 4, 5
  HAVING ROUND(loss) <> 0
)
SELECT FORMAT_DATE('%F', d) d, STRING_AGG(FORMAT('%d,%s,%s,%s,%.0f', c, brand, cat, sub, loss), ';') r
FROM x GROUP BY 1 ORDER BY 1
