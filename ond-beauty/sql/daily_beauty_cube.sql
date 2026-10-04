-- OND Beauty dashboard: daily Beauty sales by country x product combo.
-- Billing project: noonprd-nm-analytics-ai. One row per day, records packed to keep the result small:
--   r = "c,brand,category,sub_category,business_model,season,gmv,units,mkd,np,rev,pc1,ppc1;..."   c: 0=KSA 1=UAE 2=Other GCC
-- Run once per window ({FROM}/{TO}): 2024-10-01..2024-11-15, 2024-11-16..2024-12-31,
-- 2025-10-01..2025-11-15, 2025-11-16..2025-12-31, 2026-10-01..yesterday.
-- Scope: Namshi marketplaces (namshi, namshi_v2), gmv_inc_vat > 0, Beauty business unit, no samples & GWP.
-- Combo key = brand, category, sub_category, business_model (item_d) and beauty season
-- (beauty_season_mapping on sku_config, 'unassigned' when missing; 'mp' when the partner is not Namshi retail, item_d id_partner <> 3001). Brand type / group / POC are brand
-- attributes and are mapped on the page from sql/brand_attributes.sql.
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
beauty AS (
  SELECT i.sku,
    IFNULL(ANY_VALUE(i.brand_code), '(none)')     AS brand,
    IFNULL(ANY_VALUE(i.category), '(none)')       AS cat,
    IFNULL(ANY_VALUE(i.sub_category), '(none)')   AS sub,
    IFNULL(ANY_VALUE(i.business_model), '(none)') AS bm,
    IF(IFNULL(ANY_VALUE(i.id_partner), 0) <> 3001, 'mp', IFNULL(ANY_VALUE(se.beauty_season), 'unassigned')) AS season   -- non-Namshi partner = mp
  FROM `noonbinamshi.custom_views.item_d` i
  LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty'
    AND IFNULL(i.inventory_type, '') <> 'samples & gwp'   -- samples & GWP are excluded from every metric
  GROUP BY 1
),
x AS (
  SELECT s.order_date_key AS d, CASE s.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, b.bm, b.season,
    SUM(s.gmv_inc_vat) gmv, SUM(s.items_gross) u, SUM(s.markdown_discount_value) mkd, SUM(s.normal_price_AED) np,
    SUM(s.rev_gross) rev, SUM(s.pc1_gross) pc1, SUM(s.prov_pc1_gross) ppc1
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN beauty b USING (sku)
  WHERE s.order_date_key BETWEEN '{FROM}' AND '{TO}'
    AND s.marketplace IN ('namshi', 'namshi_v2')
    AND s.gmv_inc_vat > 0
  GROUP BY 1, 2, 3, 4, 5, 6, 7
)
SELECT FORMAT_DATE('%F', d) d,
  STRING_AGG(FORMAT('%d,%s,%s,%s,%s,%s,%.0f,%d,%.0f,%.0f,%.0f,%.0f,%.0f', c, brand, cat, sub, bm, season,
    IFNULL(gmv,0), IFNULL(u,0), IFNULL(mkd,0), IFNULL(np,0), IFNULL(rev,0), IFNULL(pc1,0), IFNULL(ppc1,0)), ';') r
FROM x GROUP BY 1 ORDER BY 1
