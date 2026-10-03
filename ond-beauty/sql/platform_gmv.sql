-- OND Beauty dashboard: platform (all categories) daily GMV by country and the platform GMV target (all pods).
-- Same scope as the Beauty sales: Namshi marketplaces, gmv_inc_vat > 0, samples & GWP excluded (item_d inventory type).
-- Output saved as data/platform.json {"gmv": {date: [KSA, UAE, other GCC]}, "tgt": {...}}.
WITH it AS (SELECT sku, MAX(LOWER(inventory_type)) inventory_type FROM `noonbinamshi.custom_views.item_d` GROUP BY 1),
sales AS (
  SELECT FORMAT_DATE('%F', s.order_date_key) dd, CASE s.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END cc, SUM(s.gmv_inc_vat) val
  FROM `noonbinamshi.custom_views.sales_metrics` s LEFT JOIN it USING (sku)
  WHERE (s.order_date_key BETWEEN '2024-10-01' AND '2024-12-31' OR s.order_date_key BETWEEN '2025-10-01' AND '2025-12-31'
         OR s.order_date_key BETWEEN '2026-09-30' AND DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY))
    AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0 AND IFNULL(it.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1, 2),
tg AS (
  SELECT FORMAT_DATE('%F', date) dd, CASE country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END cc, SUM(gmv) val
  FROM `noonbinmlook.namshi_analytics_custom.planning_dod_merch_brand_category_targets`
  WHERE date BETWEEN '2026-10-01' AND '2026-12-31' GROUP BY 1, 2)
SELECT (SELECT STRING_AGG(FORMAT('%s,%d,%.0f', dd, cc, val), ';' ORDER BY dd, cc) FROM sales) gmv,
       (SELECT STRING_AGG(FORMAT('%s,%d,%.0f', dd, cc, val), ';' ORDER BY dd, cc) FROM tg) tgt
