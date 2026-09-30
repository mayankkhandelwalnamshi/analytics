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
    SUM(s.gmv_inc_vat) gmv, SUM(s.items_gross) u, SUM(s.markdown_discount_value) mkd,
    SUM(s.normal_price_AED) np, SUM(s.rev_gross) rev, SUM(s.pc1_gross) pc1, SUM(s.prov_pc1_gross) ppc1
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN beauty b USING (sku)
  WHERE s.order_date_key BETWEEN '2024-09-18' AND '2025-01-02'
     OR s.order_date_key BETWEEN '2025-09-18' AND '2026-01-02'
     OR s.order_date_key BETWEEN '2026-09-25' AND DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY)
  GROUP BY 1, 2, 3, 4, 5
),
combos AS (
  SELECT brand, cat, sub, DENSE_RANK() OVER (ORDER BY brand, cat, sub) - 1 AS k
  FROM (SELECT DISTINCT brand, cat, sub FROM x)
)
