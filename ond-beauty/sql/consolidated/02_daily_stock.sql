-- Beauty Pulse · 02 · DAILY ASSORTMENT, STOCK & INVENTORY (plain table)
-- Replaces: daily_assortment, daily_inventory_value, daily_inventory_ageing, assortment_combos (names are in the rows now).
-- Grain: one row per date x country (SA / AE) x product combo (brand, category, sub_category, business_model, season).
-- Billing project: noonprd-nm-analytics-ai. Set the window below (one day for a daily run; backfill LY / LLY by
-- running Oct-Dec 2025 and 2024).
--
-- Columns
--   live_assortment   distinct live supplier SKUs with stock (psku_sku_mapped stock_net > 0, is_live = 1)
--   cb_assortment     of those, live in KSA from the UAE warehouse (cross-border); 0 for AE
--   new_assortment    of those, activated in that country (item_d activated_at_sa / _ae) between 1 Jul of the date's year and the date
--   live_stock        stock_net on primary Namshi retail listings (partner 3001)
--   inv_value_cost    inventory_value_derived, retail_v1.stock_summary_history (stock_net_live > 0, partner 3001, is_eligible_namshi > 0)
--   inv_value_retail  stock_net x offer_price on primary, live, Namshi retail listings
--   age_0_89 .. age_720_plus   inv_value_cost split by ageing band (ageing_cost.sku_config_ageing_detailed, the oldest
--                              bucket per country x sku_config since d_age_from); cost with no bucket is in none of them
-- Rules: attributes at sku_config level; season 'mp' when the config has no Namshi retail (3001) sku. A supplier SKU sits
-- in one combo, so assortment counts add up across combos within a country; Overall = KSA + UAE added together.
DECLARE d_from DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);
DECLARE d_to   DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);
DECLARE d_age_from DATE DEFAULT DATE '2026-10-01';   -- start of the ageing look-back (the dashboard uses 1 Oct 2026)

WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
cfg_dim AS (
  SELECT i.sku_config,
    IFNULL(ANY_VALUE(i.brand_code), '(none)') brand, IFNULL(ANY_VALUE(i.category), '(none)') category,
    IFNULL(ANY_VALUE(i.sub_category), '(none)') sub_category, IFNULL(ANY_VALUE(i.business_model), '(none)') business_model,
    IF(LOGICAL_OR(i.id_partner = 3001), IFNULL(ANY_VALUE(se.beauty_season), 'unassigned'), 'mp') season
  FROM `noonbinamshi.custom_views.item_d` i LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
sku_dim AS (
  SELECT sku, ANY_VALUE(sku_config) sku_config, IFNULL(ANY_VALUE(supplier_sku), sku) ssku,
    DATE(MIN(activated_at_sa)) act_sa, DATE(MIN(activated_at_ae)) act_ae
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
listings AS (
  SELECT p.date, p.country, c.brand, c.category, c.sub_category, c.business_model, c.season, k.ssku,
    IF(p.country = 'SA', k.act_sa, k.act_ae) BETWEEN DATE(EXTRACT(YEAR FROM p.date), 7, 1) AND p.date is_new,
    p.country = 'SA' AND p.warehouse_country = 'AE' is_cb,
    IF(p.is_primary = 1 AND p.id_partner = 3001, p.stock_net, 0) stock,
    IF(p.is_primary = 1 AND p.id_partner = 3001, p.stock_net * p.offer_price, 0) rval
  FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p
  JOIN sku_dim k USING (sku) JOIN cfg_dim c ON c.sku_config = k.sku_config
  WHERE p.date BETWEEN d_from AND d_to AND p.stock_net > 0 AND p.is_live = 1 AND p.country IN ('SA', 'AE')
),
asrt AS (
  SELECT date, country, brand, category, sub_category, business_model, season,
    COUNT(DISTINCT ssku) live_assortment, COUNT(DISTINCT IF(is_cb, ssku, NULL)) cb_assortment,
    COUNT(DISTINCT IF(is_new, ssku, NULL)) new_assortment, SUM(stock) live_stock, SUM(rval) inv_value_retail
  FROM listings GROUP BY 1, 2, 3, 4, 5, 6, 7
),
age AS (
  SELECT country, sku_config, MAX(sku_config_ageing_detailed) ageing   -- buckets are lettered a.0-29 .. n.720+
  FROM `noonbinmlook.namshi_analytics_custom.ageing_cost` WHERE date >= d_age_from GROUP BY ALL
),
inv AS (
  SELECT s.trans_date date, s.country_code country, c.brand, c.category, c.sub_category, c.business_model, c.season,
    SUM(s.inventory_value_derived) inv_value_cost,
    SUM(IF(ag.ageing < 'd', s.inventory_value_derived, 0)) age_0_89,
    SUM(IF(ag.ageing >= 'd' AND ag.ageing < 'g', s.inventory_value_derived, 0)) age_90_179,
    SUM(IF(ag.ageing >= 'g' AND ag.ageing < 'm', s.inventory_value_derived, 0)) age_180_359,
    SUM(IF(ag.ageing >= 'm' AND ag.ageing < 'n', s.inventory_value_derived, 0)) age_360_719,
    SUM(IF(ag.ageing >= 'n', s.inventory_value_derived, 0)) age_720_plus
  FROM `noonbinamshi.retail_v1.stock_summary_history` s
  JOIN sku_dim k USING (sku) JOIN cfg_dim c ON c.sku_config = k.sku_config
  LEFT JOIN age ag ON ag.country = s.country_code AND ag.sku_config = k.sku_config
  WHERE s.trans_date BETWEEN d_from AND d_to
    AND s.stock_net_live > 0 AND s.id_partner = 3001 AND s.is_eligible_namshi > 0 AND s.country_code IN ('SA', 'AE')
  GROUP BY 1, 2, 3, 4, 5, 6, 7
)
SELECT date, country, brand, category, sub_category, business_model, season,
  IFNULL(a.live_assortment, 0) live_assortment, IFNULL(a.cb_assortment, 0) cb_assortment, IFNULL(a.new_assortment, 0) new_assortment,
  IFNULL(a.live_stock, 0) live_stock, ROUND(IFNULL(v.inv_value_cost, 0), 2) inv_value_cost, ROUND(IFNULL(a.inv_value_retail, 0), 2) inv_value_retail,
  ROUND(IFNULL(v.age_0_89, 0), 2) age_0_89, ROUND(IFNULL(v.age_90_179, 0), 2) age_90_179, ROUND(IFNULL(v.age_180_359, 0), 2) age_180_359,
  ROUND(IFNULL(v.age_360_719, 0), 2) age_360_719, ROUND(IFNULL(v.age_720_plus, 0), 2) age_720_plus
FROM asrt a FULL JOIN inv v USING (date, country, brand, category, sub_category, business_model, season);
