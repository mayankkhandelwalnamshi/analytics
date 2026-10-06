-- Beauty Pulse · Nov Flashback tab (LY / LLY). One run per year {Y} (2024, 2025, or 2026 for the current Sept baseline).
-- Window: the 2026 dates 1 .. 30 Nov (LY / LLY dates outside November dropped), split into cohort periods (lfl_mapping cohorts, consecutive days with the same
-- cohort = one period); each period's LY / LLY dates come from lfl_mapping (ly_lfl for 2025, ly2_lfl for 2024), a date
-- mapped from two periods counts in the first. Period 0 = September of {Y} (BAU baseline).
-- {DT} = the literal (date, period) list built by build.py --flashback-sql; {RANGE} = the literal date range for pruning.
-- Output: one row per (period, country): d = "Y|p|days|c", r = "brand,cat,sub,gmv,units,mkd,np,gv,si,nsi;..."
-- Brand rows with no GMV and under 500 impressions fold into "(other brands)" within their category / sub-category.
-- Same scope as the rest of the dashboard: Namshi marketplaces, gmv_inc_vat > 0, Beauty, no samples & GWP.
WITH dt AS (SELECT * FROM UNNEST([{DT}])),
nd AS (SELECT p, COUNT(*) days FROM dt GROUP BY 1),
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
  SELECT dt.p, CASE x.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END c, sk.brand, sk.cat, sk.sub,
    SUM(x.gmv_inc_vat) gmv, SUM(x.items_gross) u, SUM(x.markdown_discount_value) mkd, SUM(x.normal_price_AED) np
  FROM `noonbinamshi.custom_views.sales_metrics` x JOIN sk USING (sku) JOIN dt ON dt.d = x.order_date_key
  WHERE x.order_date_key BETWEEN {RANGE} AND x.marketplace IN ('namshi', 'namshi_v2') AND x.gmv_inc_vat > 0
  GROUP BY 1, 2, 3, 4, 5
),
t AS (
  SELECT dt.p, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END c, cf.brand, cf.cat, cf.sub,
    SUM(o.glance_views) gv, SUM(o.search_impressions) si, SUM(o.non_search_impressions) nsi
  FROM `noonbinamshi.onsite_v1.onsite_measures` o JOIN cf ON cf.cfg = o.sku_config JOIN dt ON dt.d = o.date
  WHERE o.date BETWEEN {RANGE}
  GROUP BY 1, 2, 3, 4, 5
),
j AS (
  SELECT COALESCE(s.p, t.p) p, COALESCE(s.c, t.c) c,
    IF(IFNULL(s.gmv, 0) = 0 AND IFNULL(t.si, 0) + IFNULL(t.nsi, 0) < 500, '(other brands)', COALESCE(s.brand, t.brand)) brand,
    COALESCE(s.cat, t.cat) cat, COALESCE(s.sub, t.sub) sub,
    IFNULL(s.gmv, 0) gmv, IFNULL(s.u, 0) u, IFNULL(s.mkd, 0) mkd, IFNULL(s.np, 0) np,
    IFNULL(t.gv, 0) gv, IFNULL(t.si, 0) si, IFNULL(t.nsi, 0) nsi
  FROM s FULL JOIN t ON s.p = t.p AND s.c = t.c AND s.brand = t.brand AND s.cat = t.cat AND s.sub = t.sub
),
g AS (
  SELECT p, c, brand, cat, sub, SUM(gmv) gmv, SUM(u) u, SUM(mkd) mkd, SUM(np) np, SUM(gv) gv, SUM(si) si, SUM(nsi) nsi
  FROM j GROUP BY 1, 2, 3, 4, 5
)
SELECT FORMAT('%d|%d|%d|%d', {Y}, g.p, nd.days, g.c) d,
  STRING_AGG(FORMAT('%s,%s,%s,%.0f,%d,%.0f,%.0f,%d,%d,%d', brand, cat, sub, gmv, u, mkd, np, gv, si, nsi), ';') r
FROM g JOIN nd USING (p)
GROUP BY 1 ORDER BY 1
