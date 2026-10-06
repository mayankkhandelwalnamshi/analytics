-- Beauty Pulse · 05 · RISK SKUs (plain table: one row per country x product card)
-- Replaces: risk_skus, risk_skus_age, risk_skus_cfg (the age and card-attribute lookups are joined in here).
-- Retail supplier SKUs at risk per country (KSA, UAE): out of stock now (no live stock incl. CB) or WoC <= 3 weeks, WoC at
-- warehouse level = stock in the country's warehouse / (units shipped from that warehouse in the last 30 days / days live x 7).
-- Universe: products with GMV since h_from in season carryover / unassigned / namshi noos / brand noos (every config of the
-- product); top 500 per country by that GMV. Product = configs linked by supplier_sku or barcode.
-- Card attributes (brand, category, sub_category, title, image, season) come from the card's LEAD config: the first of the
-- configs it shows (its live configs in that country; else its configs listed there; else all its configs).
-- Supplier SKUs / barcodes = MAX(supplier_sku) / barcode of each shown config. Age = oldest live config (card country,
-- else the other country). Billing project: noonprd-nm-analytics-ai. Run once a day, after psku_sku_mapped has landed.
DECLARE d_to   DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);   -- last full sales day
DECLARE d_from DATE DEFAULT DATE_TRUNC(d_to, MONTH);                                -- MTD start
DECLARE h_from DATE DEFAULT DATE '2026-07-01';                                       -- ranking GMV since
DECLARE l30    DATE DEFAULT DATE_SUB(d_to, INTERVAL 29 DAY);                         -- last 30 days for WoC
DECLARE snap   DATE DEFAULT (SELECT MAX(date) FROM `noonbinamshi.assortment_namshi.psku_sku_mapped`
                             WHERE date BETWEEN d_to AND CURRENT_DATE('Asia/Dubai'));   -- latest stock / live / price snapshot
DECLARE ly_dates ARRAY<DATE> DEFAULT (SELECT ARRAY_AGG(DISTINCT ly_lfl) FROM `noonbinmlook.namshi_analytics_custom.lfl_mapping`
                                      WHERE date BETWEEN d_from AND d_to);           -- LY like-for-like dates of the MTD

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
s0 AS (
  -- sales by sale country x shipping warehouse (warehouse_country_code), all countries so the UAE warehouse keeps its GCC orders
  SELECT s.country, s.warehouse_country_code wh, it.ssku,
    SUM(IF(s.order_date_key BETWEEN h_from AND d_to, s.gmv_inc_vat, 0)) gh,
    SUM(IF(s.order_date_key BETWEEN d_from AND d_to, s.gmv_inc_vat, 0)) gmv,
    SUM(IF(s.order_date_key BETWEEN d_from AND d_to, s.items_gross, 0)) u,
    SUM(IF(s.order_date_key BETWEEN d_from AND d_to, s.rev_gross, 0)) rev,
    SUM(IF(s.order_date_key BETWEEN d_from AND d_to, s.pc1_gross, 0)) pc1,
    SUM(IF(s.order_date_key BETWEEN d_from AND d_to, s.prov_pc1_gross, 0)) ppc1,
    SUM(IF(s.order_date_key IN UNNEST(ly_dates), s.gmv_inc_vat, 0)) ly,
    SUM(IF(s.order_date_key BETWEEN l30 AND d_to, s.items_gross, 0)) u30
  FROM `noonbinamshi.custom_views.sales_metrics` s JOIN it USING (sku)
  WHERE it.ok AND (s.order_date_key BETWEEN h_from AND d_to OR s.order_date_key IN UNNEST(ly_dates))
    AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
  GROUP BY 1, 2, 3
),
s AS (
  -- per country: sales of the country (sale rows) + L30D units shipped from the country's warehouse (u30w, for WoC)
  SELECT cc, ssku, SUM(gh) gh, SUM(gmv) gmv, SUM(u) u, SUM(rev) rev, SUM(pc1) pc1, SUM(ppc1) ppc1, SUM(ly) ly, SUM(u30) u30, SUM(u30w) u30w
  FROM (
    SELECT country cc, ssku, gh, gmv, u, rev, pc1, ppc1, ly, u30, 0 u30w FROM s0 WHERE country IN ('SA', 'AE')
    UNION ALL
    SELECT wh, ssku, 0, 0, 0, 0, 0, 0, 0, 0, u30 FROM s0 WHERE wh IN ('SA', 'AE')
  )
  GROUP BY 1, 2
),
base AS (SELECT * FROM s WHERE gh > 0),
p AS (
  -- Namshi retail (partner 3001) listings on d_to; a KSA product can be live from the UAE warehouse (CB, non-primary listing)
  SELECT p.country cc, it.ssku, it.cfg, it.sku, p.warehouse_country wh, p.is_live = 1 AND p.stock_net > 0 lv,
    p.stock_net, p.offer_price, p.normal_price, p.is_primary
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p JOIN it USING (sku)
  -- current status: the latest psku_sku_mapped snapshot (today's when it has landed), not yesterday's
  WHERE p.date = snap
    AND p.country IN ('SA', 'AE') AND p.id_partner = 3001 AND it.ssku IN (SELECT ssku FROM base)
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
    COUNT(DISTINCT IF(l.live_day > 0 AND l.date >= d_from, l.date, NULL)) ldm
  FROM `noonbinmlook.looker.live_days` l JOIN it USING (sku)
  WHERE l.date BETWEEN l30 AND d_to AND l.country IN ('SA', 'AE') AND it.ssku IN (SELECT ssku FROM base)
  GROUP BY 1, 2
),
r AS (
  SELECT b.*, IFNULL(pc.stock, 0) + IFNULL(pc.stock_cb, 0) AS stk,
    SAFE_DIVIDE(IFNULL(pc.stock, 0), b.u30w / GREATEST(IFNULL(ld.ld30, 0), 1) * 7) AS woc
  FROM base b
  LEFT JOIN pc ON pc.cc = b.cc AND pc.ssku = b.ssku
  LEFT JOIN ld ON ld.cc = b.cc AND ld.ssku = b.ssku
),
top AS (
  SELECT * FROM r WHERE stk <= 0 OR (u30w > 0 AND woc <= 3)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY cc ORDER BY gh DESC) <= 500
),
cost AS (
  -- unit cost / provisional cost of the sku whose live price is shown (ageing_cost, Namshi retail, on d_to)
  SELECT country cc, sku, ANY_VALUE(sku_cost) cost, ANY_VALUE(sku_prov_cost) pcost
  FROM `noonbinmlook.namshi_analytics_custom.ageing_cost`
  WHERE date = d_to AND id_partner = 3001 AND country IN ('SA', 'AE') AND sku IN (SELECT sku FROM p WHERE ssku IN (SELECT ssku FROM top))
  GROUP BY 1, 2
),
o AS (
  SELECT o.country cc, it.ssku, SUM(o.oos_gmv_loss) oos
  FROM `noonbinmlook.looker.out_of_stock_new` o JOIN it USING (sku)
  WHERE o.date BETWEEN d_from AND d_to AND o.country IN ('SA', 'AE') AND it.ssku IN (SELECT ssku FROM top)
  GROUP BY 1, 2
),
-- open purchase orders (Namshi retail partner 3001, 2026 Beauty POs, any ETA) per sku and country: open order qty and
-- open shipment qty on approved / received POs; pending qty = open order + open shipment qty on POs still in draft or pending approval
po_orders AS (
  SELECT order_nr FROM `noonbinmlook.looker.po_expected_received_union`
  WHERE merch_team = 'beauty' AND LOWER(po_order_status) IN ('received', 'approved', 'pending_approval', 'draft')
    AND collection_start_date >= '2026-01-01' AND final_date >= '2026-01-01'
    AND (COALESCE(open_order_qty, 0) + COALESCE(open_shipment_qty, 0) + COALESCE(adj_expected_qty, 0) + COALESCE(qty_received, 0) + COALESCE(order_non_shipment_qty, 0)) > 0
  GROUP BY ALL
),
po_peru AS (
  SELECT sku AS zsku, order_nr, country, LOWER(po_order_status) IN ('received', 'approved') ok,
    SUM(open_order_qty) ooq, SUM(open_shipment_qty) osq
  FROM `noonbinmlook.looker.po_expected_received_union`
  WHERE merch_team = 'beauty' AND LOWER(po_order_status) IN ('received', 'approved', 'pending_approval', 'draft')
    AND (COALESCE(open_order_qty, 0) + COALESCE(open_shipment_qty, 0) + COALESCE(adj_expected_qty, 0) + COALESCE(qty_received, 0) + COALESCE(order_non_shipment_qty, 0)) > 0
    AND final_date >= '2026-01-01'
  GROUP BY ALL
),
po_lines AS (
  SELECT DISTINCT order_nr, zsku FROM `noonbinamshi.purchase.po_line`
  WHERE order_qty > 0 AND id_partner = 3001 AND order_nr IN (SELECT order_nr FROM po_orders)
),
po AS (
  SELECT pp.country cc, it.ssku, SUM(IF(pp.ok, pp.ooq, 0)) ooq, SUM(IF(pp.ok, pp.osq, 0)) osq,
    SUM(IF(pp.ok, 0, IFNULL(pp.ooq, 0) + IFNULL(pp.osq, 0))) pq
  FROM po_peru pp JOIN po_lines USING (order_nr, zsku) JOIN it ON it.sku = pp.zsku
  WHERE it.ssku IN (SELECT ssku FROM top)
  GROUP BY 1, 2
),
bg AS (
  -- brand GMV since h_from in the country, all Beauty business models (for the SKU's share of its brand)
  SELECT s.country cc, i.brand_code brand, SUM(s.gmv_inc_vat) bgh
  FROM `noonbinamshi.custom_views.sales_metrics` s
  JOIN (SELECT sku, ANY_VALUE(brand_code) brand_code FROM `noonbinamshi.custom_views.item_d`
        WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp' GROUP BY 1) i USING (sku)
  WHERE s.order_date_key BETWEEN h_from AND d_to AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
    AND s.country IN ('SA', 'AE')
  GROUP BY 1, 2
),
-- configs a card shows: live ones in the country; else the ones listed in the country; else all the product's configs
allc AS (SELECT DISTINCT ssku, cfg FROM it WHERE ssku IN (SELECT ssku FROM top)),
shown AS (
  SELECT t.cc, t.ssku, a.cfg, IFNULL(pf.lv, FALSE) lv,
    CASE WHEN pf.lv THEN 2 WHEN pf.cfg IS NOT NULL THEN 1 ELSE 0 END pri
  FROM top t JOIN allc a USING (ssku)
  LEFT JOIN pcfg pf ON pf.cc = t.cc AND pf.ssku = t.ssku AND pf.cfg = a.cfg
  QUALIFY pri = MAX(pri) OVER (PARTITION BY t.cc, t.ssku)
),
cfg_attr AS (
  SELECT i.sku_config cfg, MAX(i.supplier_sku) sup, MAX(COALESCE(i.global_barcode, i.pbarcode_canonical, i.partner_barcode)) bc,
    MAX(i.category) cat, MAX(i.sub_category) sub, MAX(i.brand_code) brand, MAX(i.product_title) title, MAX(i.image_url_1) img,
    IFNULL(ANY_VALUE(se.beauty_season), 'unassigned') season
  FROM `noonbinamshi.custom_views.item_d` i LEFT JOIN season se USING (sku_config)
  WHERE i.sku_config IN (SELECT cfg FROM allc) GROUP BY 1
),
ages AS (
  SELECT country, sku_config cfg, ROUND(MAX(sku_config_ageing_in_months), 1) m, MAX(sku_config_ageing_detailed) b
  FROM `noonbinmlook.namshi_analytics_custom.ageing_cost`
  WHERE date = snap AND id_partner = 3001 AND country IN ('SA', 'AE') AND sku_config IN (SELECT cfg FROM shown WHERE lv)
  GROUP BY 1, 2
),
shown_age AS (
  -- a live config's age in the card's country, else in the other country (e.g. KSA live via CB from the UAE warehouse)
  SELECT sh.cc, sh.ssku, sh.cfg, sh.lv, COALESCE(a1.m, a2.m) m, IF(a1.m IS NOT NULL, a1.b, a2.b) b
  FROM shown sh
  LEFT JOIN ages a1 ON a1.country = sh.cc AND a1.cfg = sh.cfg
  LEFT JOIN ages a2 ON a2.country <> sh.cc AND a2.cfg = sh.cfg
),
card AS (
  SELECT sa.cc, sa.ssku, MIN(sa.cfg) lead_cfg,
    STRING_AGG(DISTINCT sa.cfg || IF(sa.lv, ' (live)', ''), ', ') configs,
    STRING_AGG(DISTINCT ca.sup, ', ') supplier_skus, STRING_AGG(DISTINCT ca.bc, ', ') barcodes,
    MAX(IF(sa.lv, sa.m, NULL)) age_months,
    ARRAY_AGG(IF(sa.lv AND sa.m IS NOT NULL, sa.b, NULL) IGNORE NULLS ORDER BY IF(sa.lv, sa.m, NULL) DESC LIMIT 1)[SAFE_OFFSET(0)] age_band
  FROM shown_age sa LEFT JOIN cfg_attr ca ON ca.cfg = sa.cfg
  GROUP BY 1, 2
)
SELECT
  t.cc AS country, snap AS snapshot_date, ROW_NUMBER() OVER (PARTITION BY t.cc ORDER BY t.gh DESC) AS rank_in_country,
  cd.lead_cfg AS sku_config, cd.configs, cd.supplier_skus, cd.barcodes,
  la.brand, la.season, la.cat AS category, la.sub AS sub_category, la.title, la.img AS image_url,
  ROUND(t.gh) AS gmv_since_h, ROUND(bg.bgh) AS brand_gmv_since_h, ROUND(SAFE_DIVIDE(t.gh, bg.bgh), 4) AS share_of_brand,
  ROUND(t.gmv) AS gmv_mtd, ROUND(t.ly) AS gmv_ly, t.u AS units_mtd, ROUND(t.rev) AS revenue_mtd, ROUND(t.pc1) AS pc1_mtd,
  ROUND(t.ppc1) AS prov_pc1_mtd, t.u30 AS units_l30, t.u30w AS units_l30_warehouse,
  ROUND(COALESCE(c1.cost, c2.cost), 2) AS unit_cost, ROUND(COALESCE(c1.pcost, c2.pcost), 2) AS unit_prov_cost,
  IFNULL(pc.stock, 0) AS stock_own_wh, IFNULL(pc.stock_cb, 0) AS stock_other_wh, IFNULL(pc.live, FALSE) AS is_live,
  IFNULL(pc.cb, FALSE) AS live_cb, pc.op AS offer_price, pc.np AS normal_price,
  IFNULL(ld.ld30, 0) AS live_days_l30, IFNULL(ld.ldm, 0) AS live_days_mtd, ROUND(t.woc, 1) AS woc_weeks,
  t.stk <= 0 AS is_oos, ROUND(IFNULL(o.oos, 0)) AS oos_gmv_loss_mtd,
  IFNULL(po.ooq, 0) AS open_order_qty, IFNULL(po.osq, 0) AS open_shipment_qty, IFNULL(po.pq, 0) AS pending_po_qty,
  IF(IFNULL(pc.live, FALSE), cd.age_months, NULL) AS age_months, IF(IFNULL(pc.live, FALSE), cd.age_band, NULL) AS age_band
FROM top t
JOIN card cd USING (cc, ssku)
LEFT JOIN cfg_attr la ON la.cfg = cd.lead_cfg
LEFT JOIN bg ON bg.cc = t.cc AND bg.brand = la.brand
LEFT JOIN pc ON pc.cc = t.cc AND pc.ssku = t.ssku
LEFT JOIN cost c1 ON c1.cc = t.cc AND c1.sku = pc.psku
LEFT JOIN cost c2 ON c2.cc <> t.cc AND c2.sku = pc.psku
LEFT JOIN ld ON ld.cc = t.cc AND ld.ssku = t.ssku
LEFT JOIN o ON o.cc = t.cc AND o.ssku = t.ssku
LEFT JOIN po ON po.cc = t.cc AND po.ssku = t.ssku
ORDER BY t.cc, t.gh DESC;
