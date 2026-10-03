-- OND Beauty dashboard: daily Beauty sales by country x brand x category x sub-category.
-- Billing project: noonprd-nm-analytics-ai. One row per day, records packed to keep the result small:
--   r = "c,brand,category,sub_category,gmv,units,mkd,np,rev,pc1,ppc1;..."   c: 0=KSA 1=UAE 2=Other GCC
-- Run once per window ({FROM}/{TO}): 2024-10-01..2024-11-15, 2024-11-16..2024-12-31,
-- 2025-10-01..2025-11-15, 2025-11-16..2025-12-31, 2026-10-01..yesterday.
--
-- Definitions (aligned with the team's standard sales query):
--   Namshi marketplaces only (namshi, namshi_v2), rows with gmv_inc_vat > 0
--   Beauty = item_d.business_unit = 'beauty' (one row per sku)
--   GMV = gmv_inc_vat (all item statuses); Units = items_gross; MKD % = markdown_discount_value / normal_price_AED
--   PC1 % = pc1_gross / rev_gross; Prov PC1 % = prov_pc1_gross / rev_gross. Values rounded to whole AED.
WITH beauty AS (
  SELECT sku,
    IFNULL(ANY_VALUE(brand_code), '(none)')   AS brand,
    IFNULL(ANY_VALUE(category), '(none)')     AS cat,
    IFNULL(ANY_VALUE(sub_category), '(none)') AS sub
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty'
  GROUP BY sku
),
x AS (
  SELECT s.order_date_key AS d,
    CASE s.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub,
    SUM(s.gmv_inc_vat) gmv, SUM(s.items_gross) u, SUM(s.markdown_discount_value) mkd, SUM(s.normal_price_AED) np,
    SUM(s.rev_gross) rev, SUM(s.pc1_gross) pc1, SUM(s.prov_pc1_gross) ppc1
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN beauty b USING (sku)
  WHERE s.order_date_key BETWEEN '{FROM}' AND '{TO}'
    AND s.marketplace IN ('namshi', 'namshi_v2')
    AND s.gmv_inc_vat > 0
  GROUP BY 1, 2, 3, 4, 5
)
SELECT FORMAT_DATE('%F', d) d,
  STRING_AGG(FORMAT('%d,%s,%s,%s,%.0f,%d,%.0f,%.0f,%.0f,%.0f,%.0f', c, brand, cat, sub,
    IFNULL(gmv,0), IFNULL(u,0), IFNULL(mkd,0), IFNULL(np,0), IFNULL(rev,0), IFNULL(pc1,0), IFNULL(ppc1,0)), ';') r
FROM x GROUP BY 1 ORDER BY 1
