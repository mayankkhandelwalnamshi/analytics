-- Beauty · Nov '26 strategy · queries run 13 Oct 2026 (billing project noonprd-nm-analytics-ai)

-- 1. Monthly Beauty GMV / PC1 / markdown, Jan 2024 to date
WITH sk AS (SELECT sku FROM `noonbinamshi.custom_views.item_d` WHERE business_unit='beauty' AND IFNULL(inventory_type,'')<>'samples & gwp' GROUP BY 1)
SELECT FORMAT_DATE('%Y-%m', order_date_key) m, ROUND(SUM(gmv_inc_vat)) gmv, SUM(items_gross) units, ROUND(SUM(rev_gross)) rev, ROUND(SUM(pc1_gross)) pc1,
  ROUND(SUM(markdown_discount_value)) mkd, ROUND(SUM(normal_price_AED)) np
FROM `noonbinamshi.custom_views.sales_metrics` JOIN sk USING (sku)
WHERE order_date_key BETWEEN '2024-01-01' AND '2026-10-12' AND marketplace IN ('namshi','namshi_v2') AND gmv_inc_vat>0
GROUP BY 1 ORDER BY 1;

-- 2. Brand scorecard (L12M rank, Nov '24 / '25, YTD, 1-12 Oct, PC1 %, markdown %, retail units)
WITH sk AS (SELECT sku, IFNULL(ANY_VALUE(brand_code),'(none)') brand, ANY_VALUE(business_model) bm FROM `noonbinamshi.custom_views.item_d` WHERE business_unit='beauty' AND IFNULL(inventory_type,'')<>'samples & gwp' GROUP BY 1),
x AS (SELECT sk.brand, sk.bm, order_date_key d, gmv_inc_vat g, items_gross u, rev_gross r, pc1_gross c, markdown_discount_value m, normal_price_AED n
 FROM `noonbinamshi.custom_views.sales_metrics` JOIN sk USING (sku)
 WHERE order_date_key BETWEEN '2024-11-01' AND '2026-10-12' AND marketplace IN ('namshi','namshi_v2') AND gmv_inc_vat>0)
SELECT brand,
 SUM(IF(d BETWEEN '2025-10-01' AND '2026-09-30',g,0)) l12,
 SUM(IF(d BETWEEN '2024-11-01' AND '2024-11-30',g,0)) n24, SUM(IF(d BETWEEN '2025-11-01' AND '2025-11-30',g,0)) n25,
 SUM(IF(d BETWEEN '2025-01-01' AND '2025-09-30',g,0)) y25, SUM(IF(d BETWEEN '2026-01-01' AND '2026-09-30',g,0)) y26,
 SUM(IF(d BETWEEN '2025-10-01' AND '2025-10-12',g,0)) o25, SUM(IF(d BETWEEN '2026-10-01' AND '2026-10-12',g,0)) o26,
 SAFE_DIVIDE(SUM(IF(d >= '2026-01-01',c,0)),SUM(IF(d >= '2026-01-01',r,0))) pc1_ty,
 SAFE_DIVIDE(SUM(IF(d BETWEEN '2025-11-01' AND '2025-11-30',c,0)),SUM(IF(d BETWEEN '2025-11-01' AND '2025-11-30',r,0))) pc1_n25,
 SAFE_DIVIDE(SUM(IF(d >= '2026-01-01',m,0)),SUM(IF(d >= '2026-01-01',n,0))) mk_ty,
 SAFE_DIVIDE(SUM(IF(d BETWEEN '2025-11-01' AND '2025-11-30',m,0)),SUM(IF(d BETWEEN '2025-11-01' AND '2025-11-30',n,0))) mk_n25,
 SAFE_DIVIDE(SUM(IF(d BETWEEN '2024-11-01' AND '2024-11-30',m,0)),SUM(IF(d BETWEEN '2024-11-01' AND '2024-11-30',n,0))) mk_n24,
 SUM(IF(d BETWEEN '2025-12-01' AND '2025-12-31' AND bm='retail',u,0)) d25u_ret,
 SUM(IF(d BETWEEN '2025-11-01' AND '2025-11-30' AND bm='retail',u,0)) n25u_ret,
 SUM(IF(d BETWEEN '2025-09-13' AND '2025-10-12' AND bm='retail',u,0)) l4w_ly_u_ret,
 SUM(IF(d BETWEEN '2026-09-13' AND '2026-10-12' AND bm='retail',u,0)) l4w_u_ret
FROM x GROUP BY 1 ORDER BY l12 DESC;

-- 3. Retail stock: units, retail value (offer price) and cost, on 12 Oct 2026 and the last two year-ends
WITH cf AS (SELECT sku, IFNULL(ANY_VALUE(brand_code),'(none)') brand FROM `noonbinamshi.custom_views.item_d` WHERE business_unit='beauty' AND IFNULL(inventory_type,'')<>'samples & gwp' GROUP BY 1),
ps AS (SELECT p.date, cf.brand, SUM(p.stock_net) units, SUM(p.stock_net*p.offer_price) rval FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p JOIN cf USING (sku)
  WHERE p.date IN ('2026-10-12','2025-12-31','2024-12-31') AND p.stock_net > 0 AND p.is_live=1 AND p.is_primary=1 AND p.id_partner=3001 AND p.country IN ('SA','AE') GROUP BY 1,2),
iv AS (SELECT s.trans_date date, cf.brand, SUM(s.inventory_value_derived) cost FROM `noonbinamshi.retail_v1.stock_summary_history` s JOIN cf USING (sku)
  WHERE s.trans_date IN ('2026-10-12','2025-12-31','2024-12-31') AND s.stock_net_live > 0 AND s.id_partner=3001 AND s.is_eligible_namshi>0 AND s.country_code IN ('SA','AE') GROUP BY 1,2)
SELECT date, COALESCE(ps.brand, iv.brand) brand, IFNULL(units,0) units, IFNULL(rval,0) rval, IFNULL(cost,0) cost FROM ps FULL JOIN iv USING (date, brand);

-- 4. Open POs (ETA before 31 Dec 2026) by brand: qty, cost, retail value at today's primary retail offer price
WITH po AS (
  select order_nr, sku_config, ANY_VALUE(brand_code) brand, country as wh_country,
    sum(open_order_qty)+sum(open_shipment_qty) as q,
    sum(IFNULL(open_order_value,0))+sum(IFNULL(open_shipment_value,0)) as v
  from `noonbinmlook.looker.po_expected_received_union`
  where collection_start_date >= current_date() - 90 and final_date >= current_date() - 90 and eta_date < "2026-12-31"
    and lower(merch_team) = 'beauty' and lower(order_status) = 'open'
    and (coalesce(open_order_qty,0)+coalesce(open_shipment_qty,0)+coalesce(adj_expected_qty,0)+coalesce(qty_received,0)+coalesce(order_non_shipment_qty,0)) > 0
  group by order_nr, sku_config, country),
it AS (SELECT sku, ANY_VALUE(sku_config) sku_config FROM `noonbinamshi.custom_views.item_d` WHERE business_unit='beauty' GROUP BY 1),
pr AS (SELECT sku_config, MAX(IF(p.id_partner=3001 AND p.is_primary=1, p.offer_price, NULL)) op FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p JOIN it USING (sku)
  WHERE p.date = '2026-10-12' AND p.offer_price > 0 GROUP BY 1)
SELECT LOWER(brand) brand, SUM(q) qty, SUM(v) cost, SUM(q*pr.op) rval_op, SUM(IF(pr.op IS NULL, q, 0)) q_noprice, SUM(IF(pr.op IS NOT NULL, v, 0)) cost_matched
FROM po LEFT JOIN pr USING (sku_config) GROUP BY 1;   -- apply 80% fill in plan.py

-- 5. Sets / launches / core, Sep-Oct vs Nov, 2024 and 2025 (launch = first activated < 120 days before 1 Nov)
WITH sk AS (SELECT sku, ANY_VALUE(sub_category) sub, DATE(LEAST(IFNULL(MIN(activated_at_sa), TIMESTAMP '2099-01-01'), IFNULL(MIN(activated_at_ae), TIMESTAMP '2099-01-01'))) act
  FROM `noonbinamshi.custom_views.item_d` WHERE business_unit='beauty' AND IFNULL(inventory_type,'')<>'samples & gwp' GROUP BY 1),
x AS (SELECT EXTRACT(YEAR FROM order_date_key) y, IF(EXTRACT(MONTH FROM order_date_key)=11,'nov','sep_oct') per, order_date_key d,
  CASE WHEN sk.sub='gift_sets' THEN 'set' WHEN sk.act >= DATE_SUB(DATE(EXTRACT(YEAR FROM order_date_key),11,1), INTERVAL 120 DAY) THEN 'launch' ELSE 'core' END seg,
  gmv_inc_vat g, items_gross u, rev_gross r, pc1_gross c, markdown_discount_value m, normal_price_AED n
  FROM `noonbinamshi.custom_views.sales_metrics` JOIN sk USING (sku)
  WHERE (order_date_key BETWEEN '2024-09-01' AND '2024-11-30' OR order_date_key BETWEEN '2025-09-01' AND '2025-11-30') AND marketplace IN ('namshi','namshi_v2') AND gmv_inc_vat>0)
SELECT y, per, seg, COUNT(DISTINCT d) days, SUM(g) g, SUM(u) u, SUM(c)/SUM(r) pc1, SUM(m)/SUM(n) mkd FROM x GROUP BY 1,2,3;

-- 6. Impressions by brand and daily traffic, Nov '24 / Nov '25: onsite_v1.onsite_measures (search_impressions + non_search_impressions,
--    glance_views) joined to item_d on sku_config, alongside sales_metrics GMV / units (see daily.py for the daily rows).

-- 7. Rebates by brand (invoice entries, rebate_v1.rebate_income; table starts Jan 2025) joined to PC1 / revenue from sales_metrics.
--    PC1 incl. rebates % = (pc1_gross + rebate) / rev_gross. Every Beauty rebate line maps to a brand via sku, so no brand-group split.
WITH it AS (SELECT sku, MAX(brand_code) brand_code, MAX(merch_team) merch_team FROM `noonbinamshi.custom_views.item_d` GROUP BY 1),
rb AS (SELECT it.brand_code brand,
  SUM(IF(order_date BETWEEN '2025-11-01' AND '2025-11-30', value, 0)) rb_n25,
  SUM(IF(order_date BETWEEN '2025-01-01' AND '2025-10-12', value, 0)) rb_ytd25,
  SUM(IF(order_date BETWEEN '2026-01-01' AND '2026-10-12', value, 0)) rb_ytd26
 FROM `noonbinamfin.rebate_v1.rebate_income` r JOIN it USING (sku)
 WHERE it.merch_team='beauty' AND r.entry_type='invoice' AND r.order_date >= '2025-01-01' GROUP BY 1),
sk AS (SELECT sku, IFNULL(ANY_VALUE(brand_code),'(none)') brand FROM `noonbinamshi.custom_views.item_d` WHERE business_unit='beauty' AND IFNULL(inventory_type,'')<>'samples & gwp' GROUP BY 1),
s AS (SELECT sk.brand,
  SUM(IF(order_date_key BETWEEN '2025-11-01' AND '2025-11-30', rev_gross, 0)) rev_n25, SUM(IF(order_date_key BETWEEN '2025-11-01' AND '2025-11-30', pc1_gross, 0)) pc1_n25,
  SUM(IF(order_date_key BETWEEN '2026-01-01' AND '2026-10-12', rev_gross, 0)) rev_ytd26, SUM(IF(order_date_key BETWEEN '2026-01-01' AND '2026-10-12', pc1_gross, 0)) pc1_ytd26
 FROM `noonbinamshi.custom_views.sales_metrics` JOIN sk USING (sku)
 WHERE order_date_key BETWEEN '2025-01-01' AND '2026-10-12' AND marketplace IN ('namshi','namshi_v2') AND gmv_inc_vat>0 GROUP BY 1)
SELECT COALESCE(s.brand, rb.brand) brand, s.rev_n25, s.pc1_n25, rb.rb_n25, s.rev_ytd26, s.pc1_ytd26, rb.rb_ytd26
FROM s FULL JOIN rb ON s.brand = rb.brand;
