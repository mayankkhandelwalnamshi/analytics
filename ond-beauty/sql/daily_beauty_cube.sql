-- OND Beauty dashboard: daily Beauty sales by country x brand x category x sub-category.
-- Billing project: noonprd-nm-analytics-ai. Output is packed one row per day to keep the result small:
--   r = "c,k,gmv,u,mkd,np,rev,pc1,ppc1;..."   c: 0=KSA 1=UAE 2=Other,  k: combo index
-- Combo index k is the 0-based position in brand/cat/sub order (same ordering as dims query below).
-- Replace {FROM}/{TO} with each window: 2024-09-18..2025-01-02, 2025-09-18..2026-01-02, 2026-09-25..yesterday.
--
-- Definitions: Beauty = item_d.business_unit='beauty' (1 row per sku); GMV = gmv_inc_vat, all statuses;
-- Units = items_gross; MKD% = markdown_discount_value/normal_price_AED; PC1% = pc1_gross/rev_gross;
-- Prov PC1% = prov_pc1_gross/rev_gross.  Values rounded to whole AED.
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
  SELECT s.order_date_key AS d,
    CASE s.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, s.gmv_inc_vat, s.items_gross, s.markdown_discount_value,
    s.normal_price_AED, s.rev_gross, s.pc1_gross, s.prov_pc1_gross
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN beauty b USING (sku)
  WHERE s.order_date_key BETWEEN '2024-09-18' AND '2025-01-02'
     OR s.order_date_key BETWEEN '2025-09-18' AND '2026-01-02'
     OR s.order_date_key BETWEEN '2026-09-25' AND DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY)
),
combos AS (
  SELECT brand, cat, sub, DENSE_RANK() OVER (ORDER BY brand, cat, sub) - 1 AS k
  FROM (SELECT DISTINCT brand, cat, sub FROM base)
),
x AS (
  SELECT d, c, k,
    SUM(gmv_inc_vat) gmv, SUM(items_gross) u, SUM(markdown_discount_value) mkd, SUM(normal_price_AED) np,
    SUM(rev_gross) rev, SUM(pc1_gross) pc1, SUM(prov_pc1_gross) ppc1
  FROM base JOIN combos USING (brand, cat, sub)
  WHERE d BETWEEN '{FROM}' AND '{TO}'
  GROUP BY 1, 2, 3
)
SELECT FORMAT_DATE('%F', d) d,
  STRING_AGG(FORMAT('%d,%d,%.0f,%d,%.0f,%.0f,%.0f,%.0f,%.0f', c, k, IFNULL(gmv,0), IFNULL(u,0), IFNULL(mkd,0), IFNULL(np,0), IFNULL(rev,0), IFNULL(pc1,0), IFNULL(ppc1,0)), ';') r
FROM x GROUP BY 1 ORDER BY 1

-- Dims (combo list, row k = combo index):
-- SELECT STRING_AGG(CONCAT(brand,'\t',cat,'\t',sub), '\n' ORDER BY brand, cat, sub) FROM (SELECT DISTINCT brand, cat, sub FROM base)
