-- OND Beauty dashboard: daily Beauty sales by country, for TY + LY + LLY windows.
-- Billing project: noonprd-nm-analytics-ai
-- Output feeds ond-beauty/data/daily.json (see build.py).
--
-- Definitions
--   Beauty  = item_d.business_unit = 'beauty' (joined on sku; item_d has a few
--             duplicate sku rows, so it is de-duplicated first)
--   GMV     = gmv_inc_vat, all item statuses (gross, incl. cancelled/returned)
--   Units   = items_gross
--   MKD %   = markdown_discount_value / normal_price_AED
--   PC1 %   = pc1_gross / rev_gross
--   Prov PC1 % = prov_pc1_gross / rev_gross
--   Country = SA -> KSA, AE -> UAE, everything else -> OTH (Overall = all three)
--   LY / LLY windows are padded by a week on each side so both the
--   same-weekday (364/728 days) and same-date alignments are covered.

WITH beauty AS (
  SELECT DISTINCT sku
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty'
)
SELECT
  FORMAT_DATE('%F', s.order_date_key) AS d,
  CASE s.country WHEN 'SA' THEN 'KSA' WHEN 'AE' THEN 'UAE' ELSE 'OTH' END AS c,
  ROUND(SUM(s.gmv_inc_vat), 2)             AS gmv,
  SUM(s.items_gross)                       AS u,
  ROUND(SUM(s.markdown_discount_value), 2) AS mkd,
  ROUND(SUM(s.normal_price_AED), 2)        AS np,
  ROUND(SUM(s.rev_gross), 2)               AS rev,
  ROUND(SUM(s.pc1_gross), 2)               AS pc1,
  ROUND(SUM(s.prov_pc1_gross), 2)          AS ppc1
FROM `noonbinamshi.custom_views.sales_metrics` s
JOIN beauty b USING (sku)
WHERE s.order_date_key BETWEEN '2024-09-18' AND '2025-01-02'
   OR s.order_date_key BETWEEN '2025-09-18' AND '2026-01-02'
   -- TY: from 25 Sep up to yesterday (today is a partial day)
   OR s.order_date_key BETWEEN '2026-09-25' AND DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY)
GROUP BY 1, 2
ORDER BY 1, 2
