-- OND Beauty dashboard: month-to-date performance by supplier SKU for the MTD performance tab (cut "Supplier SKU").
-- Billing project: noonprd-nm-analytics-ai. Run per month with {DATES} = one STRUCT(DATE 'yyyy-mm-dd' AS d, y AS y) per day:
-- y = 0 for each TY day of the month so far (1st .. yesterday), y = 1 / 2 for its LY / LLY like-for-like date (data/lfl.json),
-- and {DLIST} = the same dates as a quoted list (onsite_measures needs a literal date filter for partition pruning).
-- Output rows (j, packed text, see build.py):
--   "v|c|ssku|f0..f10 (TY)|f0..f10 (LY)|f0..f10 (LLY)"   f = gmv,u,mkd,np,rev,pc1,ppc1,gv,atc,si,nsi   c: 0=KSA 1=UAE 2=Other GCC
--   "i|ssku|brand|cat|sub|bm|season|title"                 one per supplier SKU (title = MAX(product_title))
-- A (country, supplier SKU) row is kept when it has GMV in any of the three years or 20+ TY glance views.
-- Same scope and attributes as sql/daily_beauty_cube.sql: Namshi marketplaces, gmv_inc_vat > 0, Beauty, no samples & GWP;
-- supplier SKU = item_d supplier_sku (sku_config when blank). One combo per supplier SKU (item_d); season 'mp' when
-- none of its skus is Namshi retail (id_partner 3001). Traffic (onsite_measures, by sku_config) maps config -> supplier SKU.
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
b AS (
  SELECT i.sku, ANY_VALUE(i.sku_config) cfg, IFNULL(ANY_VALUE(i.supplier_sku), ANY_VALUE(i.sku_config)) ssku,
    ANY_VALUE(i.id_partner) pid, ANY_VALUE(i.product_title) title,
    IFNULL(ANY_VALUE(i.brand_code), '(none)') brand, IFNULL(ANY_VALUE(i.category), '(none)') cat,
    IFNULL(ANY_VALUE(i.sub_category), '(none)') sub, IFNULL(ANY_VALUE(i.business_model), '(none)') bm,
    IFNULL(ANY_VALUE(se.beauty_season), 'unassigned') season
  FROM `noonbinamshi.custom_views.item_d` i LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
info AS (
  SELECT ssku, ANY_VALUE(brand) brand, ANY_VALUE(cat) cat, ANY_VALUE(sub) sub, ANY_VALUE(bm) bm,
    IF(LOGICAL_OR(pid = 3001), ANY_VALUE(season), 'mp') season, MAX(title) title
  FROM b GROUP BY 1
),
m AS (SELECT cfg, ANY_VALUE(ssku) ssku FROM b GROUP BY 1),
dt AS (SELECT * FROM UNNEST([{DATES}])),
s AS (
  SELECT dt.y, CASE x.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END c, b.ssku,
    SUM(x.gmv_inc_vat) gmv, SUM(x.items_gross) u, SUM(x.markdown_discount_value) mkd, SUM(x.normal_price_AED) np,
    SUM(x.rev_gross) rev, SUM(x.pc1_gross) pc1, SUM(x.prov_pc1_gross) ppc1
  FROM `noonbinamshi.custom_views.sales_metrics` x JOIN dt ON x.order_date_key = dt.d JOIN b USING (sku)
  WHERE x.order_date_key IN ({DLIST}) AND x.marketplace IN ('namshi', 'namshi_v2') AND x.gmv_inc_vat > 0
  GROUP BY 1, 2, 3
),
t AS (
  SELECT dt.y, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END c, m.ssku,
    SUM(o.glance_views) gv, SUM(o.cart_adds) atc, SUM(o.search_impressions) si, SUM(o.non_search_impressions) nsi
  FROM `noonbinamshi.onsite_v1.onsite_measures` o JOIN dt ON o.date = dt.d JOIN m ON m.cfg = o.sku_config
  WHERE o.date IN ({DLIST})
  GROUP BY 1, 2, 3
),
f AS (
  SELECT COALESCE(s.y, t.y) y, COALESCE(s.c, t.c) c, COALESCE(s.ssku, t.ssku) ssku,
    FORMAT('%.0f,%d,%.0f,%.0f,%.0f,%.0f,%.0f,%d,%d,%d,%d', IFNULL(s.gmv, 0), IFNULL(s.u, 0), IFNULL(s.mkd, 0), IFNULL(s.np, 0),
      IFNULL(s.rev, 0), IFNULL(s.pc1, 0), IFNULL(s.ppc1, 0), IFNULL(t.gv, 0), IFNULL(t.atc, 0), IFNULL(t.si, 0), IFNULL(t.nsi, 0)) v,
    IFNULL(s.gmv, 0) gmv, IF(COALESCE(s.y, t.y) = 0, IFNULL(t.gv, 0), 0) gv0
  FROM s FULL JOIN t ON s.y = t.y AND s.c = t.c AND s.ssku = t.ssku
),
r AS (
  SELECT c, ssku, MAX(IF(y = 0, v, NULL)) v0, MAX(IF(y = 1, v, NULL)) v1, MAX(IF(y = 2, v, NULL)) v2
  FROM f GROUP BY 1, 2 HAVING SUM(gmv) > 0 OR SUM(gv0) >= 20
)
SELECT FORMAT('v|%d|%s|%s|%s|%s', c, ssku, IFNULL(v0, '0,0,0,0,0,0,0,0,0,0,0'), IFNULL(v1, '0,0,0,0,0,0,0,0,0,0,0'), IFNULL(v2, '0,0,0,0,0,0,0,0,0,0,0')) j FROM r
UNION ALL
SELECT FORMAT('i|%s|%s|%s|%s|%s|%s|%s', ssku, brand, cat, sub, bm, season, REPLACE(IFNULL(title, ''), '|', '/')) j
FROM info JOIN (SELECT DISTINCT ssku FROM r) USING (ssku)
