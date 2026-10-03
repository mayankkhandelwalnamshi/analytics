-- OND Beauty dashboard: every metric by ageing bucket, for the "Ageing bucket" cut of the MTD tab (TY only: ageing_cost
-- starts on 2026-10-01). Billing project: noonprd-nm-analytics-ai. One row per day:
--   r = "b,c,brand,category,sub_category,business_model,season,gmv,u,mkd,np,rev,pc1,ppc1,gv,atc,si,nsi,asi,ansi,la,cb,st,nw,cv,rv,ur30,cg30,oos;..."
--   b: ageing bucket of the country x sku_config (namshi_analytics_custom.ageing_cost, MAX(sku_config_ageing_detailed) since
--      2026-10-01, i.e. the oldest bucket seen): 0 = 0-89 days, 1 = 90-179, 2 = 180-359, 3 = 360-719, 4 = 720+, 5 = no ageing
--   c: 0 = KSA, 1 = UAE, 2 = Other GCC (no ageing outside KSA / UAE)
-- Each metric has the same definition and scope as its own query (sql/daily_beauty_cube.sql, daily_traffic_cube.sql,
-- daily_assortment.sql, daily_inventory_value.sql, daily_retail_cogs.sql, daily_oos.sql). Retail units / COGS (ur30, cg30)
-- are daily values from 1 Sep (for the 30-day WoC window); everything else from 1 Oct. Run for 2026-09-01..yesterday ({TO}).
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
age AS (
  SELECT country, sku_config,
    CASE WHEN MAX(sku_config_ageing_detailed) < 'd' THEN 0 WHEN MAX(sku_config_ageing_detailed) < 'g' THEN 1
      WHEN MAX(sku_config_ageing_detailed) < 'm' THEN 2 WHEN MAX(sku_config_ageing_detailed) < 'n' THEN 3
      WHEN MAX(sku_config_ageing_detailed) IS NOT NULL THEN 4 END AS b
  FROM `noonbinmlook.namshi_analytics_custom.ageing_cost` WHERE date >= "2026-10-01" GROUP BY ALL
),
cfg AS (
  SELECT i.sku_config,
    IFNULL(ANY_VALUE(i.brand_code), '(none)') AS brand, IFNULL(ANY_VALUE(i.category), '(none)') AS cat,
    IFNULL(ANY_VALUE(i.sub_category), '(none)') AS sub, IFNULL(ANY_VALUE(i.business_model), '(none)') AS bm,
    IFNULL(ANY_VALUE(se.beauty_season), 'unassigned') AS season
  FROM `noonbinamshi.custom_views.item_d` i LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
sk AS (
  SELECT sku, ANY_VALUE(sku_config) AS sku_config, IFNULL(ANY_VALUE(supplier_sku), sku) AS ssku,
    DATE(MIN(activated_at_sa)) AS act_sa, DATE(MIN(activated_at_ae)) AS act_ae
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
u AS (
  -- sales (from 1 Oct) and retail units / COGS (from 1 Sep)
  SELECT s.order_date_key AS d, CASE s.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c, sk.sku_config, s.country AS cc,
    IF(s.order_date_key >= '2026-10-01', s.gmv_inc_vat, 0) gmv, IF(s.order_date_key >= '2026-10-01', s.items_gross, 0) un,
    IF(s.order_date_key >= '2026-10-01', s.markdown_discount_value, 0) mkd, IF(s.order_date_key >= '2026-10-01', s.normal_price_AED, 0) np,
    IF(s.order_date_key >= '2026-10-01', s.rev_gross, 0) rev, IF(s.order_date_key >= '2026-10-01', s.pc1_gross, 0) pc1,
    IF(s.order_date_key >= '2026-10-01', s.prov_pc1_gross, 0) ppc1,
    IF(cfg.bm = 'retail', s.items_gross, 0) ur, IF(cfg.bm = 'retail', s.cogs, 0) cg
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN sk USING (sku) JOIN cfg ON cfg.sku_config = sk.sku_config
  WHERE s.order_date_key BETWEEN '2026-09-01' AND '{TO}' AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
),
sales AS (
  SELECT d, c, sku_config, cc, SUM(gmv) gmv, SUM(un) un, SUM(mkd) mkd, SUM(np) np, SUM(rev) rev, SUM(pc1) pc1, SUM(ppc1) ppc1,
    SUM(ur) ur, SUM(cg) cg
  FROM u GROUP BY 1, 2, 3, 4
),
traffic AS (
  SELECT o.date AS d, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c, o.sku_config, o.country AS cc,
    SUM(o.glance_views) gv, SUM(o.cart_adds) atc, SUM(o.search_impressions) si, SUM(o.non_search_impressions) nsi,
    SUM(IF(o.platform IN ('ios', 'android'), o.search_impressions, 0)) asi,
    SUM(IF(o.platform IN ('ios', 'android'), o.non_search_impressions, 0)) ansi
  FROM `noonbinamshi.onsite_v1.onsite_measures` o JOIN cfg USING (sku_config)
  WHERE o.date BETWEEN '2026-10-01' AND '{TO}'
  GROUP BY 1, 2, 3, 4
),
p AS (
  SELECT p.date AS d, IF(p.country = 'SA', 0, 1) AS c, sk.sku_config, p.country AS cc, sk.ssku,
    IF(p.country = 'SA', sk.act_sa, sk.act_ae) BETWEEN DATE(EXTRACT(YEAR FROM p.date), 7, 1) AND p.date AS is_new,
    p.country = 'SA' AND p.warehouse_country = 'AE' AS is_cb,
    IF(p.is_primary = 1 AND p.id_partner = 3001, p.stock_net, 0) AS st,
    IF(p.is_primary = 1 AND p.id_partner = 3001, p.stock_net * p.offer_price, 0) AS rv
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p JOIN sk USING (sku)
  WHERE p.date BETWEEN '2026-10-01' AND '{TO}' AND p.stock_net > 0 AND p.is_live = 1 AND p.country IN ('SA', 'AE')
),
cost AS (
  SELECT s.trans_date AS d, IF(s.country_code = 'SA', 0, 1) AS c, sk.sku_config, s.country_code AS cc, SUM(s.inventory_value_derived) cv
  FROM `noonbinamshi.retail_v1.stock_summary_history` s JOIN sk USING (sku)
  WHERE s.trans_date BETWEEN '2026-10-01' AND '{TO}'
    AND s.stock_net_live > 0 AND s.id_partner = 3001 AND s.is_eligible_namshi > 0 AND s.country_code IN ('SA', 'AE')
  GROUP BY 1, 2, 3, 4
),
oosl AS (
  SELECT o.date AS d, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c, sk.sku_config, o.country AS cc, SUM(o.oos_gmv_loss) oos
  FROM `noonbinmlook.looker.out_of_stock_new` o JOIN sk USING (sku)
  WHERE o.date BETWEEN '2026-10-01' AND '{TO}'
  GROUP BY 1, 2, 3, 4
),
-- one bucket per country x sku_config: rows are grouped to the combo x bucket before distinct counts
lv AS (
  SELECT p.d, p.c, IFNULL(a.b, 5) b, cfg.brand, cfg.cat, cfg.sub, cfg.bm, cfg.season,
    COUNT(DISTINCT p.ssku) la, COUNT(DISTINCT IF(p.is_cb, p.ssku, NULL)) cb, SUM(p.st) st, COUNT(DISTINCT IF(p.is_new, p.ssku, NULL)) nw, SUM(p.rv) rv
  FROM p JOIN cfg USING (sku_config) LEFT JOIN age a ON a.country = p.cc AND a.sku_config = p.sku_config
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
),
flows AS (
  SELECT d, c, sku_config, cc, gmv, un, mkd, np, rev, pc1, ppc1, ur, cg, 0 gv, 0 atc, 0 si, 0 nsi, 0 asi, 0 ansi, 0 cv, 0 oos FROM sales
  UNION ALL SELECT d, c, sku_config, cc, 0, 0, 0, 0, 0, 0, 0, 0, 0, gv, atc, si, nsi, asi, ansi, 0, 0 FROM traffic
  UNION ALL SELECT d, c, sku_config, cc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, cv, 0 FROM cost
  UNION ALL SELECT d, c, sku_config, cc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, oos FROM oosl
),
fl AS (
  SELECT f.d, f.c, IFNULL(a.b, 5) b, cfg.brand, cfg.cat, cfg.sub, cfg.bm, cfg.season,
    SUM(gmv) gmv, SUM(un) un, SUM(mkd) mkd, SUM(np) np, SUM(rev) rev, SUM(pc1) pc1, SUM(ppc1) ppc1,
    SUM(gv) gv, SUM(atc) atc, SUM(si) si, SUM(nsi) nsi, SUM(asi) asi, SUM(ansi) ansi, SUM(cv) cv, SUM(ur) ur, SUM(cg) cg, SUM(oos) oos
  FROM flows f JOIN cfg USING (sku_config) LEFT JOIN age a ON a.country = f.cc AND a.sku_config = f.sku_config
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
),
y AS (
  SELECT d, c, b, brand, cat, sub, bm, season,
    IFNULL(fl.gmv, 0) gmv, IFNULL(fl.un, 0) un, IFNULL(fl.mkd, 0) mkd, IFNULL(fl.np, 0) np, IFNULL(fl.rev, 0) rev,
    IFNULL(fl.pc1, 0) pc1, IFNULL(fl.ppc1, 0) ppc1, IFNULL(fl.gv, 0) gv, IFNULL(fl.atc, 0) atc, IFNULL(fl.si, 0) si,
    IFNULL(fl.nsi, 0) nsi, IFNULL(fl.asi, 0) asi, IFNULL(fl.ansi, 0) ansi, IFNULL(lv.la, 0) la, IFNULL(lv.cb, 0) cb,
    IFNULL(lv.st, 0) st, IFNULL(lv.nw, 0) nw, IFNULL(fl.cv, 0) cv, IFNULL(lv.rv, 0) rv, IFNULL(fl.ur, 0) ur,
    IFNULL(fl.cg, 0) cg, IFNULL(fl.oos, 0) oos
  FROM fl FULL JOIN lv USING (d, c, b, brand, cat, sub, bm, season)
)
SELECT FORMAT_DATE('%F', d) d,
  STRING_AGG(FORMAT('%d,%d,%s,%s,%s,%s,%s,%.0f,%d,%.0f,%.0f,%.0f,%.0f,%.0f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.0f,%.0f,%d,%.0f,%.0f',
    b, c, brand, cat, sub, bm, season, gmv, un, mkd, np, rev, pc1, ppc1, gv, atc, si, nsi, asi, ansi, la, cb, st, nw, cv, rv, ur, cg, oos), ';') r
FROM y
WHERE gmv <> 0 OR un <> 0 OR gv + atc + si + nsi > 0 OR la > 0 OR st <> 0 OR cv <> 0 OR rv <> 0 OR ur <> 0 OR cg <> 0 OR oos <> 0
GROUP BY 1 ORDER BY 1
