-- OND Beauty dashboard: daily Beauty traffic by country x brand x category x sub-category.
-- Billing project: noonprd-nm-analytics-ai. One row per day, records packed to keep the result small:
--   r = "c,brand,category,sub_category,gv,atc,si,nsi,app_si,app_nsi;..."   c: 0=KSA 1=UAE 2=Other GCC
-- Run once per month ({FROM}/{TO}) for Oct-Dec 2024 and Oct-Dec 2025, and for 2026-10-01..yesterday.
--
-- Source: onsite_v1.onsite_measures (all platforms). App = platform in ('ios', 'android').
--   GV = glance_views, ATC = cart_adds, impressions = search_impressions + non_search_impressions.
-- Beauty and brand / category / sub-category come from item_d at sku_config level (one row per sku_config).
-- To keep the page small, brand rows with < 5 GV, no ATC and < 500 impressions on a day are folded into
-- '(other brands)' within their country / category / sub-category (totals and category filters stay exact).
WITH beauty AS (
  SELECT sku_config,
    IFNULL(ANY_VALUE(brand_code), '(none)')   AS brand,
    IFNULL(ANY_VALUE(category), '(none)')     AS cat,
    IFNULL(ANY_VALUE(sub_category), '(none)') AS sub
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty'
    AND IFNULL(inventory_type, '') <> 'samples & gwp'   -- samples & GWP are excluded from every metric
  GROUP BY sku_config
),
x AS (
  SELECT o.date AS d,
    CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub,
    SUM(o.glance_views) gv, SUM(o.cart_adds) atc,
    SUM(o.search_impressions) si, SUM(o.non_search_impressions) nsi,
    SUM(IF(o.platform IN ('ios', 'android'), o.search_impressions, 0)) asi,
    SUM(IF(o.platform IN ('ios', 'android'), o.non_search_impressions, 0)) ansi
  FROM `noonbinamshi.onsite_v1.onsite_measures` o
  JOIN beauty b USING (sku_config)
  WHERE o.date BETWEEN '{FROM}' AND '{TO}'
  GROUP BY 1, 2, 3, 4, 5
),
f AS (
  SELECT d, c,
    IF(IFNULL(gv,0) < 5 AND IFNULL(atc,0) = 0 AND IFNULL(si,0) + IFNULL(nsi,0) < 500, '(other brands)', brand) AS brand,
    cat, sub, SUM(gv) gv, SUM(atc) atc, SUM(si) si, SUM(nsi) nsi, SUM(asi) asi, SUM(ansi) ansi
  FROM x GROUP BY 1, 2, 3, 4, 5
)
SELECT FORMAT_DATE('%F', d) d,
  STRING_AGG(FORMAT('%d,%s,%s,%s,%d,%d,%d,%d,%d,%d', c, brand, cat, sub,
    IFNULL(gv,0), IFNULL(atc,0), IFNULL(si,0), IFNULL(nsi,0), IFNULL(asi,0), IFNULL(ansi,0)), ';') r
FROM f
WHERE COALESCE(gv,0) + COALESCE(atc,0) + COALESCE(si,0) + COALESCE(nsi,0) > 0
GROUP BY 1 ORDER BY 1
