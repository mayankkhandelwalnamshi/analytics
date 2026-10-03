-- OND Beauty dashboard: retail supplier SKUs at risk per country (KSA, UAE), one JSON object per product, for the
-- "Risk SKUs" tab. Billing project: noonprd-nm-analytics-ai.
-- At risk = out of stock now (no live stock, own warehouse + CB, on {TO}) or WoC <= 3 weeks, where
--   WoC = stock / (units sold in the last 30 days / days live in those 30 days * 7) (no WoC when nothing sold in 30 days).
-- Universe: products with GMV since {H} (1 Jul 2026) in season carryover / unassigned / namshi noos / brand noos
-- (beauty_season_mapping; every config of the product must be in one of these); ranked by that GMV, top 500 per country.
-- Parameters: {FROM} = 1st of the month, {TO} = yesterday, {LY_DATES} = LY LFL dates of {FROM}..{TO} (sql/lfl_mapping.sql),
--             {L30} = {TO} - 29 days, {H} = 2026-07-01.
-- Product = configs linked by supplier_sku or barcode (see ids below); Beauty, business model retail, no samples & GWP.
-- Sales scope as sql/daily_beauty_cube.sql (Namshi marketplaces, gmv_inc_vat > 0).
--   gmv / u / rev / pc1 / ppc1   MTD;  ly = GMV on the LY LFL dates
--   co / pco = unit cost / provisional cost (ageing_cost sku_cost / sku_prov_cost on {TO}) of the sku whose live price is
--   shown, in that country (else the other country, e.g. KSA sold CB from the UAE warehouse)
--   u30 = units sold in the last 30 days; ld30 / ldm = days live (looker.live_days, live_day = 1 on any of the product's skus)
--         in the last 30 days / MTD
--   st / sc = stock_net of live Namshi retail listings (partner 3001) on {TO} from the country's own / the other warehouse
--   (sc = CB stock for KSA); live = any live listing with stock; cb = KSA listing live from the UAE warehouse;
--   op / np = offer / normal price of the live listing with the most stock (else the primary listing);
--   cfgs = the product's sku_configs with 1 when live in the country on {TO};  oos = OOS GMV loss MTD
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
it0 AS (
  SELECT sku, ANY_VALUE(sku_config) cfg, IFNULL(ANY_VALUE(se.beauty_season), 'unassigned') season, ANY_VALUE(supplier_sku) sup, ANY_VALUE(global_barcode) gb, ANY_VALUE(brand_code) brand,
    ANY_VALUE(category) cat, ANY_VALUE(sub_category) sub, ANY_VALUE(product_title) title, ANY_VALUE(image_url_1) img,
    COALESCE(ANY_VALUE(global_barcode), ANY_VALUE(pbarcode_canonical), ANY_VALUE(partner_barcode)) bc
  FROM `noonbinamshi.custom_views.item_d` LEFT JOIN season se USING (sku_config)
  WHERE business_unit = 'beauty' AND business_model = 'retail' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
-- One product = configs linked by a shared supplier_sku or barcode (global_barcode, or the barcode digits inside the
-- supplier SKU, e.g. CHA5060542727532), so a duplicate config of the same item counts as the same product.
ids0 AS (
  SELECT DISTINCT cfg, id FROM it0, UNNEST([cfg, sup, gb, REGEXP_EXTRACT(sup, r'(\d{8,14})$')]) id
  WHERE id IS NOT NULL AND (id = cfg OR LENGTH(id) >= 8)
),
-- an id shared by more than 10 configs is a placeholder (e.g. one supplier_sku on 500+ configs), not a product link
ids AS (SELECT * FROM ids0 WHERE id IN (SELECT id FROM ids0 GROUP BY id HAVING COUNT(DISTINCT cfg) <= 10)),
k0 AS (SELECT cfg, MIN(id) k FROM ids GROUP BY 1),
i1 AS (SELECT id, MIN(k) k FROM ids JOIN k0 USING (cfg) GROUP BY 1),
k1 AS (SELECT cfg, MIN(k) k FROM ids JOIN i1 USING (id) GROUP BY 1),
-- ok: every config of the product is in season carryover / unassigned / namshi noos / brand noos (only those products are shown)
it AS (
  SELECT it0.*, k1.k ssku,
    LOGICAL_AND(season IN ('carryover', 'unassigned', 'namshi noos', 'brand noos')) OVER (PARTITION BY k1.k) ok
  FROM it0 JOIN k1 USING (cfg)
),
s AS (
  SELECT s.country cc, it.ssku,
    SUM(IF(s.order_date_key BETWEEN '{H}' AND '{TO}', s.gmv_inc_vat, 0)) gh,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.gmv_inc_vat, 0)) gmv,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.items_gross, 0)) u,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.rev_gross, 0)) rev,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.pc1_gross, 0)) pc1,
    SUM(IF(s.order_date_key BETWEEN '{FROM}' AND '{TO}', s.prov_pc1_gross, 0)) ppc1,
    SUM(IF(s.order_date_key IN ({LY_DATES}), s.gmv_inc_vat, 0)) ly,
    SUM(IF(s.order_date_key BETWEEN '{L30}' AND '{TO}', s.items_gross, 0)) u30
  FROM `noonbinamshi.custom_views.sales_metrics` s JOIN it USING (sku)
  WHERE it.ok AND (s.order_date_key BETWEEN '{H}' AND '{TO}' OR s.order_date_key IN ({LY_DATES}))
    AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0 AND s.country IN ('SA', 'AE')
  GROUP BY 1, 2
),
base AS (SELECT * FROM s WHERE gh > 0),
p AS (
  -- Namshi retail (partner 3001) listings on {TO}; a KSA product can be live from the UAE warehouse (CB, non-primary listing)
  SELECT p.country cc, it.ssku, it.cfg, it.sku, p.warehouse_country wh, p.is_live = 1 AND p.stock_net > 0 lv,
    p.stock_net, p.offer_price, p.normal_price, p.is_primary
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p JOIN it USING (sku)
  WHERE p.date = '{TO}' AND p.country IN ('SA', 'AE') AND p.id_partner = 3001 AND it.ssku IN (SELECT ssku FROM base)
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
    ANY_VALUE(c.cfgs) cfgs, ANY_VALUE(pr.op) op, ANY_VALUE(pr.np) np, ANY_VALUE(pr.sku) psku
  FROM ps
  JOIN (SELECT cc, ssku, STRING_AGG(cfg || ':' || IF(lv, '1', '0'), '|' ORDER BY lv DESC, cfg) cfgs FROM pcfg GROUP BY 1, 2) c USING (cc, ssku)
  JOIN (
    -- current price: the live listing with the most stock, else the primary listing
    SELECT cc, ssku, ARRAY_AGG(STRUCT(offer_price AS op, normal_price AS np, sku) ORDER BY lv DESC, stock_net DESC, is_primary DESC LIMIT 1)[OFFSET(0)].*
    FROM p GROUP BY 1, 2
  ) pr USING (cc, ssku)
  GROUP BY 1, 2
),
ld AS (
  SELECT l.country cc, it.ssku,
    COUNT(DISTINCT IF(l.live_day > 0, l.date, NULL)) ld30,
    COUNT(DISTINCT IF(l.live_day > 0 AND l.date >= '{FROM}', l.date, NULL)) ldm
  FROM `noonbinmlook.looker.live_days` l JOIN it USING (sku)
  WHERE l.date BETWEEN '{L30}' AND '{TO}' AND l.country IN ('SA', 'AE') AND it.ssku IN (SELECT ssku FROM base)
  GROUP BY 1, 2
),
r AS (
  SELECT b.*, IFNULL(pc.stock, 0) + IFNULL(pc.stock_cb, 0) AS stk,
    SAFE_DIVIDE(IFNULL(pc.stock, 0) + IFNULL(pc.stock_cb, 0), b.u30 / GREATEST(IFNULL(ld.ld30, 0), 1) * 7) AS woc
  FROM base b
  LEFT JOIN pc ON pc.cc = b.cc AND pc.ssku = b.ssku
  LEFT JOIN ld ON ld.cc = b.cc AND ld.ssku = b.ssku
),
top AS (
  SELECT * FROM r WHERE stk <= 0 OR (u30 > 0 AND woc <= 3)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY cc ORDER BY gh DESC) <= 500
),
cost AS (
  -- unit cost / provisional cost of the sku whose live price is shown (ageing_cost, Namshi retail, on {TO})
  SELECT country cc, sku, ANY_VALUE(sku_cost) cost, ANY_VALUE(sku_prov_cost) pcost
  FROM `noonbinmlook.namshi_analytics_custom.ageing_cost`
  WHERE date = '{TO}' AND id_partner = 3001 AND country IN ('SA', 'AE') AND sku IN (SELECT sku FROM p WHERE ssku IN (SELECT ssku FROM top))
  GROUP BY 1, 2
),
o AS (
  SELECT o.country cc, it.ssku, SUM(o.oos_gmv_loss) oos
  FROM `noonbinmlook.looker.out_of_stock_new` o JOIN it USING (sku)
  WHERE o.date BETWEEN '{FROM}' AND '{TO}' AND o.country IN ('SA', 'AE') AND it.ssku IN (SELECT ssku FROM top)
  GROUP BY 1, 2
),
-- open purchase orders (Namshi retail partner 3001, Beauty re-order POs: dup / top up / reorder / bsrp titles, 2026 POs whose
-- ETA has passed, excluding POs re-dated to a future ETA): open order qty and open shipment qty per sku and country
po_orders AS (
  SELECT order_nr FROM `noonbinmlook.looker.po_expected_received_union`
  WHERE merch_team = 'beauty' AND LOWER(po_order_status) IN ('received', 'approved')
    AND collection_start_date >= '2026-01-01' AND final_date >= '2026-01-01' AND eta_date < CURRENT_DATE()
    AND (COALESCE(open_order_qty, 0) + COALESCE(open_shipment_qty, 0) + COALESCE(adj_expected_qty, 0) + COALESCE(qty_received, 0) + COALESCE(order_non_shipment_qty, 0)) > 0
    AND (LOWER(po_title) LIKE '%dup%' OR LOWER(po_title) LIKE '%top up%' OR LOWER(po_title) LIKE '%reorder%' OR LOWER(po_title) LIKE '%bsrp%')
    AND order_nr NOT IN (SELECT order_nr FROM `noonbinmlook.looker.po_expected_received_union` WHERE final_date >= '2026-01-01'
                         GROUP BY order_nr HAVING COUNT(DISTINCT eta_date) > 1 AND MAX(eta_date) > CURRENT_DATE())
  GROUP BY ALL
),
po_peru AS (
  SELECT sku AS zsku, order_nr, country, SUM(open_order_qty) ooq, SUM(open_shipment_qty) osq
  FROM `noonbinmlook.looker.po_expected_received_union`
  WHERE merch_team = 'beauty' AND LOWER(po_order_status) IN ('received', 'approved')
    AND (COALESCE(open_order_qty, 0) + COALESCE(open_shipment_qty, 0) + COALESCE(adj_expected_qty, 0) + COALESCE(qty_received, 0) + COALESCE(order_non_shipment_qty, 0)) > 0
    AND final_date >= '2026-01-01'
  GROUP BY ALL
),
po_lines AS (
  SELECT DISTINCT order_nr, zsku FROM `noonbinamshi.purchase.po_line`
  WHERE order_qty > 0 AND id_partner = 3001 AND order_nr IN (SELECT order_nr FROM po_orders)
),
po AS (
  SELECT pp.country cc, it.ssku, SUM(pp.ooq) ooq, SUM(pp.osq) osq
  FROM po_peru pp JOIN po_lines USING (order_nr, zsku) JOIN it ON it.sku = pp.zsku
  WHERE it.ssku IN (SELECT ssku FROM top)
  GROUP BY 1, 2
),
bg AS (
  -- brand GMV since {H} in the country, all Beauty business models (for the SKU's share of its brand)
  SELECT s.country cc, i.brand_code brand, SUM(s.gmv_inc_vat) bgh
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN (SELECT sku, ANY_VALUE(brand_code) brand_code FROM `noonbinamshi.custom_views.item_d`
        WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp' GROUP BY 1) i USING (sku)
  WHERE s.order_date_key BETWEEN '{H}' AND '{TO}' AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
    AND s.country IN ('SA', 'AE')
  GROUP BY 1, 2
),
info AS (
  SELECT ssku, ANY_VALUE(brand) brand, ANY_VALUE(cat) cat, ANY_VALUE(sub) sub, ANY_VALUE(title) title,
    ANY_VALUE(img) img, STRING_AGG(DISTINCT bc, ', ') bc, STRING_AGG(DISTINCT cfg, '|') allcfg,
    STRING_AGG(DISTINCT IFNULL(sup, sku), ', ') sups, COALESCE(STRING_AGG(DISTINCT NULLIF(season, 'unassigned'), ', ' ORDER BY NULLIF(season, 'unassigned')), 'unassigned') seasons
  FROM it WHERE ssku IN (SELECT ssku FROM top) GROUP BY 1
)
SELECT TO_JSON_STRING(STRUCT(
  IF(t.cc = 'SA', 0, 1) AS c, ROW_NUMBER() OVER (PARTITION BY t.cc ORDER BY t.gh DESC) AS rk, i.sups AS ss, ROUND(t.gh) AS gh, ROUND(bg.bgh) AS bgh,
  i.brand AS br, i.seasons AS sn, i.cat AS ca, i.sub AS su, i.title AS ti, i.img AS im, i.bc AS bc, IFNULL(pc.cfgs, i.allcfg) AS cf,
  ROUND(t.gmv) AS g, ROUND(t.ly) AS ly, t.u AS u, ROUND(t.rev) AS rv, ROUND(t.pc1) AS p1, ROUND(t.ppc1) AS pp,
  t.u30 AS u30, ROUND(COALESCE(c1.cost, c2.cost), 2) AS co, ROUND(COALESCE(c1.pcost, c2.pcost), 2) AS pco,
  IFNULL(pc.stock, 0) AS st, IFNULL(pc.stock_cb, 0) AS sc, IFNULL(pc.live, FALSE) AS lv, IFNULL(pc.cb, FALSE) AS cb, pc.op AS op, pc.np AS np,
  IFNULL(ld.ld30, 0) AS l30, IFNULL(ld.ldm, 0) AS lm, ROUND(IFNULL(o.oos, 0)) AS oo,
  IFNULL(po.ooq, 0) AS oq, IFNULL(po.osq, 0) AS os)) j
FROM top t
JOIN info i USING (ssku)
LEFT JOIN bg ON bg.cc = t.cc AND bg.brand = i.brand
LEFT JOIN pc ON pc.cc = t.cc AND pc.ssku = t.ssku
LEFT JOIN cost c1 ON c1.cc = t.cc AND c1.sku = pc.psku
LEFT JOIN cost c2 ON c2.cc <> t.cc AND c2.sku = pc.psku
LEFT JOIN ld ON ld.cc = t.cc AND ld.ssku = t.ssku
LEFT JOIN o ON o.cc = t.cc AND o.ssku = t.ssku
LEFT JOIN po ON po.cc = t.cc AND po.ssku = t.ssku
ORDER BY t.cc, t.gh DESC
