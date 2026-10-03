-- OND Beauty dashboard: top 500 retail supplier SKUs per country (KSA, UAE) by MTD GMV, one JSON object per product
-- for the "Top SKU performance" tab. Billing project: noonprd-nm-analytics-ai.
-- Parameters: {FROM} = 1st of the month, {TO} = yesterday, {LY_DATES} = LY LFL dates of {FROM}..{TO} (sql/lfl_mapping.sql),
--             {L30} = {TO} - 29 days.
-- Product = item_d supplier_sku (the sku when blank); Beauty, business model retail, no samples & GWP.
-- Sales scope as sql/daily_beauty_cube.sql (Namshi marketplaces, gmv_inc_vat > 0).
--   gmv / u / rev / pc1 / ppc1   MTD;  ly = GMV on the LY LFL dates;  y_* = yesterday ({TO})
--   u30 = units sold in the last 30 days; ld30 / ldm = days live (looker.live_days, live_day = 1 on any of the product's skus)
--         in the last 30 days / MTD
--   st / sc = stock_net of live Namshi retail listings (partner 3001) on {TO} from the country's own / the other warehouse
--   (sc = CB stock for KSA); live = any live listing with stock; cb = KSA listing live from the UAE warehouse;
--   op / np = offer / normal price of the live listing with the most stock (else the primary listing);
--   cfgs = the product's sku_configs with 1 when live in the country on {TO};  oos = OOS GMV loss MTD
WITH it AS (
  SELECT sku, ANY_VALUE(sku_config) cfg, IFNULL(ANY_VALUE(supplier_sku), sku) ssku, ANY_VALUE(brand_code) brand,
    ANY_VALUE(category) cat, ANY_VALUE(sub_category) sub, ANY_VALUE(product_title) title, ANY_VALUE(image_url_1) img,
    COALESCE(ANY_VALUE(global_barcode), ANY_VALUE(pbarcode_canonical), ANY_VALUE(partner_barcode)) bc
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND business_model = 'retail' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
s AS (
  SELECT s.country cc, it.ssku,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.gmv_inc_vat, 0)) gmv,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.items_gross, 0)) u,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.rev_gross, 0)) rev,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.pc1_gross, 0)) pc1,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.prov_pc1_gross, 0)) ppc1,
    SUM(IF(s.order_date_key = '{TO}', s.rev_gross, 0)) y_rev, SUM(IF(s.order_date_key = '{TO}', s.pc1_gross, 0)) y_pc1,
    SUM(IF(s.order_date_key = '{TO}', s.prov_pc1_gross, 0)) y_ppc1,
    SUM(IF(s.order_date_key IN ({LY_DATES}), s.gmv_inc_vat, 0)) ly,
    SUM(IF(s.order_date_key BETWEEN '{L30}' AND '{TO}', s.items_gross, 0)) u30
  FROM `noonbinamshi.custom_views.sales_metrics` s JOIN it USING (sku)
  WHERE (s.order_date_key BETWEEN '{L30}' AND '{TO}' OR s.order_date_key IN ({LY_DATES}))
    AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0 AND s.country IN ('SA', 'AE')
  GROUP BY 1, 2
),
top AS (
  SELECT * FROM s WHERE gmv > 0 QUALIFY ROW_NUMBER() OVER (PARTITION BY cc ORDER BY gmv DESC) <= 500
),
p AS (
  -- Namshi retail (partner 3001) listings on {TO}; a KSA product can be live from the UAE warehouse (CB, non-primary listing)
  SELECT p.country cc, it.ssku, it.cfg, it.sku, p.warehouse_country wh, p.is_live = 1 AND p.stock_net > 0 lv,
    p.stock_net, p.offer_price, p.normal_price, p.is_primary
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p JOIN it USING (sku)
  WHERE p.date = '{TO}' AND p.country IN ('SA', 'AE') AND p.id_partner = 3001 AND it.ssku IN (SELECT ssku FROM top)
),
ps AS (
  -- one stock figure per sku x warehouse (a listing can repeat), counting live listings only
  SELECT cc, ssku, cfg, sku, wh, MAX(IF(lv, stock_net, 0)) st, LOGICAL_OR(lv) lv FROM p GROUP BY 1, 2, 3, 4, 5
),
pcfg AS (
  SELECT cc, ssku, cfg, LOGICAL_OR(lv) lv FROM ps GROUP BY 1, 2, 3
),
pc AS (
  SELECT ps.cc, ps.ssku,
    SUM(IF(ps.wh = ps.cc, ps.st, 0)) stock, SUM(IF(ps.wh <> ps.cc, ps.st, 0)) stock_cb,
    LOGICAL_OR(ps.lv) live, LOGICAL_OR(ps.cc = 'SA' AND ps.wh = 'AE' AND ps.lv) cb,
    ANY_VALUE(c.cfgs) cfgs, ANY_VALUE(pr.op) op, ANY_VALUE(pr.np) np
  FROM ps
  JOIN (SELECT cc, ssku, STRING_AGG(cfg || ':' || IF(lv, '1', '0'), '|' ORDER BY lv DESC, cfg) cfgs FROM pcfg GROUP BY 1, 2) c USING (cc, ssku)
  JOIN (
    -- current price: the live listing with the most stock, else the primary listing
    SELECT cc, ssku, ARRAY_AGG(STRUCT(offer_price AS op, normal_price AS np) ORDER BY lv DESC, stock_net DESC, is_primary DESC LIMIT 1)[OFFSET(0)].*
    FROM p GROUP BY 1, 2
  ) pr USING (cc, ssku)
  GROUP BY 1, 2
),
ld AS (
  SELECT l.country cc, it.ssku,
    COUNT(DISTINCT IF(l.live_day > 0, l.date, NULL)) ld30,
    COUNT(DISTINCT IF(l.live_day > 0 AND l.date >= '{FROM}', l.date, NULL)) ldm
  FROM `noonbinmlook.looker.live_days` l JOIN it USING (sku)
  WHERE l.date BETWEEN '{L30}' AND '{TO}' AND l.country IN ('SA', 'AE') AND it.ssku IN (SELECT ssku FROM top)
  GROUP BY 1, 2
),
o AS (
  SELECT o.country cc, it.ssku, SUM(o.oos_gmv_loss) oos
  FROM `noonbinmlook.looker.out_of_stock_new` o JOIN it USING (sku)
  WHERE o.date BETWEEN '{FROM}' AND '{TO}' AND o.country IN ('SA', 'AE') AND it.ssku IN (SELECT ssku FROM top)
  GROUP BY 1, 2
),
info AS (
  SELECT ssku, ANY_VALUE(brand) brand, ANY_VALUE(cat) cat, ANY_VALUE(sub) sub, ANY_VALUE(title) title,
    ANY_VALUE(img) img, STRING_AGG(DISTINCT bc, ', ') bc, STRING_AGG(DISTINCT cfg, '|') allcfg
  FROM it WHERE ssku IN (SELECT ssku FROM top) GROUP BY 1
)
SELECT TO_JSON_STRING(STRUCT(
  IF(t.cc = 'SA', 0, 1) AS c, ROW_NUMBER() OVER (PARTITION BY t.cc ORDER BY t.gmv DESC) AS rk, t.ssku AS ss,
  i.brand AS br, i.cat AS ca, i.sub AS su, i.title AS ti, i.img AS im, i.bc AS bc, IFNULL(pc.cfgs, i.allcfg) AS cf,
  ROUND(t.gmv) AS g, ROUND(t.ly) AS ly, t.u AS u, ROUND(t.rev) AS rv, ROUND(t.pc1) AS p1, ROUND(t.ppc1) AS pp,
  ROUND(t.y_rev) AS yr, ROUND(t.y_pc1) AS y1, ROUND(t.y_ppc1) AS yp, t.u30 AS u30,
  IFNULL(pc.stock, 0) AS st, IFNULL(pc.stock_cb, 0) AS sc, IFNULL(pc.live, FALSE) AS lv, IFNULL(pc.cb, FALSE) AS cb, pc.op AS op, pc.np AS np,
  IFNULL(ld.ld30, 0) AS l30, IFNULL(ld.ldm, 0) AS lm, ROUND(IFNULL(o.oos, 0)) AS oo)) j
FROM top t
JOIN info i USING (ssku)
LEFT JOIN pc ON pc.cc = t.cc AND pc.ssku = t.ssku
LEFT JOIN ld ON ld.cc = t.cc AND ld.ssku = t.ssku
LEFT JOIN o ON o.cc = t.cc AND o.ssku = t.ssku
ORDER BY t.cc, t.gmv DESC
