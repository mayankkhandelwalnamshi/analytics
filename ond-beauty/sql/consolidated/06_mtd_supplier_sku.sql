-- Beauty Pulse · 06 · MONTH-TO-DATE BY SUPPLIER SKU (plain table: one row per country x supplier SKU)
-- Replaces: mtd_ssku. Feeds the MTD tab's "Supplier SKU" cut.
-- TY = 1st of the month .. d_to; LY / LLY = the like-for-like dates of those days (lfl_mapping; a mapped date in the
-- wrong year falls back to the same calendar date). Kept when the row has GMV in any of the three years or 20+ TY GVs.
-- Columns: country, supplier_sku, title (MAX(product_title)), brand, category, sub_category, business_model, season,
--   then for ty_ / ly_ / lly_: gmv, units, markdown, normal_price, revenue, pc1, prov_pc1, glance_views, add_to_carts,
--   search_impr, non_search_impr.
-- Same scope and rules as 01: Namshi marketplaces, gmv_inc_vat > 0, Beauty, no samples & GWP; supplier SKU = item_d
-- supplier_sku (sku_config when blank); one combo per supplier SKU, season 'mp' when none of its skus is Namshi retail.
-- Billing project: noonprd-nm-analytics-ai.
DECLARE d_to   DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);
DECLARE d_from DATE DEFAULT DATE_TRUNC(d_to, MONTH);
DECLARE dmap ARRAY<STRUCT<d DATE, y INT64>> DEFAULT (
  SELECT ARRAY_CONCAT_AGG([STRUCT(date AS d, 0 AS y),
    STRUCT(IF(EXTRACT(YEAR FROM ly_lfl) = EXTRACT(YEAR FROM date) - 1, ly_lfl, DATE_SUB(date, INTERVAL 1 YEAR)) AS d, 1 AS y),
    STRUCT(IF(EXTRACT(YEAR FROM ly2_lfl) = EXTRACT(YEAR FROM date) - 2, ly2_lfl, DATE_SUB(date, INTERVAL 2 YEAR)) AS d, 2 AS y)])
  FROM (SELECT date, MIN(ly_lfl) ly_lfl, MIN(ly2_lfl) ly2_lfl FROM `noonbinmlook.namshi_analytics_custom.lfl_mapping`
        WHERE date BETWEEN d_from AND d_to GROUP BY 1));
DECLARE dlist ARRAY<DATE> DEFAULT (SELECT ARRAY_AGG(DISTINCT x.d) FROM UNNEST(dmap) x);   -- literal filter for partition pruning

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
dt AS (SELECT DISTINCT x.d, x.y FROM UNNEST(dmap) x),
f AS (
  SELECT dt.y, x.country, b.ssku, x.gmv_inc_vat gmv, x.items_gross u, x.markdown_discount_value mkd, x.normal_price_AED np,
    x.rev_gross rev, x.pc1_gross pc1, x.prov_pc1_gross ppc1, 0 gv, 0 atc, 0 si, 0 nsi
  FROM `noonbinamshi.custom_views.sales_metrics` x JOIN dt ON x.order_date_key = dt.d JOIN b USING (sku)
  WHERE x.order_date_key IN UNNEST(dlist) AND x.marketplace IN ('namshi', 'namshi_v2') AND x.gmv_inc_vat > 0
  UNION ALL
  SELECT dt.y, o.country, m.ssku, 0, 0, 0, 0, 0, 0, 0, o.glance_views, o.cart_adds, o.search_impressions, o.non_search_impressions
  FROM `noonbinamshi.onsite_v1.onsite_measures` o JOIN dt ON o.date = dt.d JOIN m ON m.cfg = o.sku_config
  WHERE o.date IN UNNEST(dlist)
),
r AS (
  SELECT country, ssku,
    SUM(IF(y = 0, gmv, 0)) ty_gmv, SUM(IF(y = 0, u, 0)) ty_units, SUM(IF(y = 0, mkd, 0)) ty_markdown, SUM(IF(y = 0, np, 0)) ty_normal_price,
    SUM(IF(y = 0, rev, 0)) ty_revenue, SUM(IF(y = 0, pc1, 0)) ty_pc1, SUM(IF(y = 0, ppc1, 0)) ty_prov_pc1,
    SUM(IF(y = 0, gv, 0)) ty_glance_views, SUM(IF(y = 0, atc, 0)) ty_add_to_carts, SUM(IF(y = 0, si, 0)) ty_search_impr, SUM(IF(y = 0, nsi, 0)) ty_non_search_impr,
    SUM(IF(y = 1, gmv, 0)) ly_gmv, SUM(IF(y = 1, u, 0)) ly_units, SUM(IF(y = 1, mkd, 0)) ly_markdown, SUM(IF(y = 1, np, 0)) ly_normal_price,
    SUM(IF(y = 1, rev, 0)) ly_revenue, SUM(IF(y = 1, pc1, 0)) ly_pc1, SUM(IF(y = 1, ppc1, 0)) ly_prov_pc1,
    SUM(IF(y = 1, gv, 0)) ly_glance_views, SUM(IF(y = 1, atc, 0)) ly_add_to_carts, SUM(IF(y = 1, si, 0)) ly_search_impr, SUM(IF(y = 1, nsi, 0)) ly_non_search_impr,
    SUM(IF(y = 2, gmv, 0)) lly_gmv, SUM(IF(y = 2, u, 0)) lly_units, SUM(IF(y = 2, mkd, 0)) lly_markdown, SUM(IF(y = 2, np, 0)) lly_normal_price,
    SUM(IF(y = 2, rev, 0)) lly_revenue, SUM(IF(y = 2, pc1, 0)) lly_pc1, SUM(IF(y = 2, ppc1, 0)) lly_prov_pc1,
    SUM(IF(y = 2, gv, 0)) lly_glance_views, SUM(IF(y = 2, atc, 0)) lly_add_to_carts, SUM(IF(y = 2, si, 0)) lly_search_impr, SUM(IF(y = 2, nsi, 0)) lly_non_search_impr
  FROM f GROUP BY 1, 2
  HAVING SUM(gmv) > 0 OR SUM(IF(y = 0, gv, 0)) >= 20
)
SELECT r.country, r.ssku AS supplier_sku, i.title, i.brand, i.cat AS category, i.sub AS sub_category, i.bm AS business_model, i.season,
  r.* EXCEPT (country, ssku)
FROM r JOIN info i USING (ssku)
ORDER BY r.country, r.ty_gmv DESC;
