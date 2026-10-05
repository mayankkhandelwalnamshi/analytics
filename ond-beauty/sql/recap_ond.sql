-- OND Beauty dashboard: OND recap tab (LY / LLY). One run per year and date window: {Y} = 2025 or 2024,
-- {FROM} / {TO} inside 1 Sep .. 31 Dec of {Y} (e.g. Sep-Oct, then Nov-Dec). September is the BAU baseline.
-- Billing project: noonprd-nm-analytics-ai. Saved into data/recap_raw.json by build.py --recap.
-- Each date gets the OND 2026 cohort it is like-for-like with (namshi_analytics_custom.lfl_mapping, the same cohorts as the
-- dashboard's Cohort cut): 2025 dates through ly_lfl, 2024 dates through ly2_lfl of the 2026 rows; a date no 2026 day maps
-- to is "Other". September is all "Sep (BAU)".
-- Output: one row per (month, cohort, country): d = "Y|M|cohort|days|c", r = "brand,cat,sub,gmv,mkd,np,rev,pc1,ppc1,si,nsi;..."
-- Brand rows with no GMV and under 500 impressions fold into "(other brands)" within their category / sub-category.
-- Same scope as sql/daily_beauty_cube.sql (Namshi marketplaces, gmv_inc_vat > 0, Beauty, no samples & GWP) and
-- sql/daily_traffic_cube.sql (onsite_measures, all platforms, by sku_config).
WITH coh AS (
  SELECT d, MIN(cohort) cohort FROM (
    SELECT IF({Y} = 2025, ly_lfl, ly2_lfl) d, REPLACE(cohort, '_', ' ') cohort
    FROM `noonbinmlook.namshi_analytics_custom.lfl_mapping`
    WHERE date BETWEEN '2026-10-01' AND '2026-12-31'
  ) WHERE d BETWEEN '{FROM}' AND '{TO}' GROUP BY 1
),
dt AS (
  SELECT d, EXTRACT(MONTH FROM d) m, IF(EXTRACT(MONTH FROM d) = 9, 'Sep (BAU)', IFNULL(coh.cohort, 'Other')) cohort
  FROM UNNEST(GENERATE_DATE_ARRAY('{FROM}', '{TO}')) d LEFT JOIN coh USING (d)
),
nd AS (SELECT m, cohort, COUNT(*) days FROM dt GROUP BY 1, 2),
sk AS (
  SELECT sku, IFNULL(ANY_VALUE(brand_code), '(none)') brand, IFNULL(ANY_VALUE(category), '(none)') cat,
    IFNULL(ANY_VALUE(sub_category), '(none)') sub
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp' GROUP BY 1
),
cf AS (
  SELECT sku_config cfg, IFNULL(ANY_VALUE(brand_code), '(none)') brand, IFNULL(ANY_VALUE(category), '(none)') cat,
    IFNULL(ANY_VALUE(sub_category), '(none)') sub
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp' GROUP BY 1
),
s AS (
  SELECT dt.m, dt.cohort, CASE x.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END c, sk.brand, sk.cat, sk.sub,
    SUM(x.gmv_inc_vat) gmv, SUM(x.markdown_discount_value) mkd, SUM(x.normal_price_AED) np,
    SUM(x.rev_gross) rev, SUM(x.pc1_gross) pc1, SUM(x.prov_pc1_gross) ppc1
  FROM `noonbinamshi.custom_views.sales_metrics` x JOIN sk USING (sku) JOIN dt ON dt.d = x.order_date_key
  WHERE x.order_date_key BETWEEN '{FROM}' AND '{TO}' AND x.marketplace IN ('namshi', 'namshi_v2') AND x.gmv_inc_vat > 0
  GROUP BY 1, 2, 3, 4, 5, 6
),
t AS (
  SELECT dt.m, dt.cohort, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END c, cf.brand, cf.cat, cf.sub,
    SUM(o.search_impressions) si, SUM(o.non_search_impressions) nsi
  FROM `noonbinamshi.onsite_v1.onsite_measures` o JOIN cf ON cf.cfg = o.sku_config JOIN dt ON dt.d = o.date
  WHERE o.date BETWEEN '{FROM}' AND '{TO}'
  GROUP BY 1, 2, 3, 4, 5, 6
),
j AS (
  SELECT COALESCE(s.m, t.m) m, COALESCE(s.cohort, t.cohort) cohort, COALESCE(s.c, t.c) c,
    IF(IFNULL(s.gmv, 0) = 0 AND IFNULL(t.si, 0) + IFNULL(t.nsi, 0) < 500, '(other brands)', COALESCE(s.brand, t.brand)) brand,
    COALESCE(s.cat, t.cat) cat, COALESCE(s.sub, t.sub) sub,
    IFNULL(s.gmv, 0) gmv, IFNULL(s.mkd, 0) mkd, IFNULL(s.np, 0) np, IFNULL(s.rev, 0) rev, IFNULL(s.pc1, 0) pc1,
    IFNULL(s.ppc1, 0) ppc1, IFNULL(t.si, 0) si, IFNULL(t.nsi, 0) nsi
  FROM s FULL JOIN t ON s.m = t.m AND s.cohort = t.cohort AND s.c = t.c AND s.brand = t.brand AND s.cat = t.cat AND s.sub = t.sub
),
g AS (
  SELECT m, cohort, c, brand, cat, sub, SUM(gmv) gmv, SUM(mkd) mkd, SUM(np) np, SUM(rev) rev, SUM(pc1) pc1, SUM(ppc1) ppc1,
    SUM(si) si, SUM(nsi) nsi
  FROM j GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT FORMAT('%d|%d|%s|%d|%d', {Y}, g.m, g.cohort, nd.days, g.c) d,
  STRING_AGG(FORMAT('%s,%s,%s,%.0f,%.0f,%.0f,%.0f,%.0f,%.0f,%d,%d', brand, cat, sub, gmv, mkd, np, rev, pc1, ppc1, si, nsi), ';') r
FROM g JOIN nd USING (m, cohort)
GROUP BY 1 ORDER BY 1
