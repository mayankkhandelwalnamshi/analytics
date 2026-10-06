-- Beauty Pulse · 01 · DAILY PRODUCT PERFORMANCE (plain table)
-- Replaces: daily_beauty_cube, daily_traffic_cube, daily_oos, daily_retail_cogs.
-- Grain: one row per date x country x product combo (brand, category, sub_category, business_model, season).
-- Billing project: noonprd-nm-analytics-ai. Set the window below (one day for a daily run; backfill LY / LLY by
-- running Oct-Dec 2025 and 2024, and 1 Sep onwards for the WoC columns).
--
-- Columns
--   date, country (SA / AE / other GCC code), brand, category, sub_category, business_model, season
--   gmv, units, markdown, normal_price, revenue, pc1, prov_pc1        sales_metrics, Namshi marketplaces, gmv_inc_vat > 0
--   oos_gmv_loss                                                    looker.out_of_stock_new (KSA / UAE, from 2025-01-01)
--   glance_views, add_to_carts, search_impr, non_search_impr,
--   app_search_impr, app_non_search_impr                            onsite_v1.onsite_measures (app = ios + android)
--   wh_retail_units, wh_retail_cogs                                 retail business model, by SHIPPING WAREHOUSE country
--                                                                   (sales_metrics.warehouse_country_code), for WoC
-- Rules (same as the dashboard)
--   Beauty = item_d business_unit 'beauty'; samples & GWP (inventory_type) excluded everywhere.
--   season = beauty_season_mapping on sku_config ('unassigned' when missing), 'mp' when not Namshi retail:
--            by sku (id_partner <> 3001) for sales / OOS / COGS, by sku_config (no partner-3001 sku) for traffic.
--   Ratios on the page: ASP = gmv / units, MKD % = markdown / normal_price, PC1 % = pc1 / revenue,
--   Prov. PC1 % = prov_pc1 / revenue, CTR = glance_views / (search + non_search), UCR = units / glance_views.
--   Orders are NOT here (distinct counts don't add up across combos): see 03_daily_orders.sql.
DECLARE d_from DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);
DECLARE d_to   DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);

WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
sku_dim AS (   -- sku level: sales, OOS, COGS
  SELECT i.sku,
    IFNULL(ANY_VALUE(i.brand_code), '(none)') brand, IFNULL(ANY_VALUE(i.category), '(none)') category,
    IFNULL(ANY_VALUE(i.sub_category), '(none)') sub_category, IFNULL(ANY_VALUE(i.business_model), '(none)') business_model,
    IF(IFNULL(ANY_VALUE(i.id_partner), 0) <> 3001, 'mp', IFNULL(ANY_VALUE(se.beauty_season), 'unassigned')) season
  FROM `noonbinamshi.custom_views.item_d` i LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
cfg_dim AS (   -- sku_config level: traffic
  SELECT i.sku_config,
    IFNULL(ANY_VALUE(i.brand_code), '(none)') brand, IFNULL(ANY_VALUE(i.category), '(none)') category,
    IFNULL(ANY_VALUE(i.sub_category), '(none)') sub_category, IFNULL(ANY_VALUE(i.business_model), '(none)') business_model,
    IF(LOGICAL_OR(i.id_partner = 3001), IFNULL(ANY_VALUE(se.beauty_season), 'unassigned'), 'mp') season
  FROM `noonbinamshi.custom_views.item_d` i LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
facts AS (
  -- sales
  SELECT s.order_date_key date, s.country, d.brand, d.category, d.sub_category, d.business_model, d.season,
    s.gmv_inc_vat gmv, s.items_gross units, s.markdown_discount_value markdown, s.normal_price_AED normal_price,
    s.rev_gross revenue, s.pc1_gross pc1, s.prov_pc1_gross prov_pc1,
    0 oos_gmv_loss, 0 glance_views, 0 add_to_carts, 0 search_impr, 0 non_search_impr, 0 app_search_impr, 0 app_non_search_impr,
    0 wh_retail_units, 0 wh_retail_cogs
  FROM `noonbinamshi.custom_views.sales_metrics` s JOIN sku_dim d USING (sku)
  WHERE s.order_date_key BETWEEN d_from AND d_to AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
  UNION ALL
  -- retail units / COGS by shipping warehouse (WoC)
  SELECT s.order_date_key, s.warehouse_country_code, d.brand, d.category, d.sub_category, d.business_model, d.season,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, s.items_gross, s.cogs
  FROM `noonbinamshi.custom_views.sales_metrics` s JOIN sku_dim d USING (sku)
  WHERE s.order_date_key BETWEEN d_from AND d_to AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
    AND d.business_model = 'retail'
  UNION ALL
  -- OOS GMV loss
  SELECT o.date, o.country, d.brand, d.category, d.sub_category, d.business_model, d.season,
    0, 0, 0, 0, 0, 0, 0, o.oos_gmv_loss, 0, 0, 0, 0, 0, 0, 0, 0
  FROM `noonbinmlook.looker.out_of_stock_new` o JOIN sku_dim d USING (sku)
  WHERE o.date BETWEEN d_from AND d_to
  UNION ALL
  -- traffic
  SELECT t.date, t.country, d.brand, d.category, d.sub_category, d.business_model, d.season,
    0, 0, 0, 0, 0, 0, 0, 0, t.glance_views, t.cart_adds, t.search_impressions, t.non_search_impressions,
    IF(t.platform IN ('ios', 'android'), t.search_impressions, 0), IF(t.platform IN ('ios', 'android'), t.non_search_impressions, 0), 0, 0
  FROM `noonbinamshi.onsite_v1.onsite_measures` t JOIN cfg_dim d USING (sku_config)
  WHERE t.date BETWEEN d_from AND d_to
)
SELECT date, country, brand, category, sub_category, business_model, season,
  ROUND(SUM(gmv), 2) gmv, SUM(units) units, ROUND(SUM(markdown), 2) markdown, ROUND(SUM(normal_price), 2) normal_price,
  ROUND(SUM(revenue), 2) revenue, ROUND(SUM(pc1), 2) pc1, ROUND(SUM(prov_pc1), 2) prov_pc1,
  ROUND(SUM(oos_gmv_loss), 2) oos_gmv_loss,
  SUM(glance_views) glance_views, SUM(add_to_carts) add_to_carts, SUM(search_impr) search_impr, SUM(non_search_impr) non_search_impr,
  SUM(app_search_impr) app_search_impr, SUM(app_non_search_impr) app_non_search_impr,
  SUM(wh_retail_units) wh_retail_units, ROUND(SUM(wh_retail_cogs), 2) wh_retail_cogs
FROM facts
GROUP BY 1, 2, 3, 4, 5, 6, 7
HAVING SUM(facts.gmv) <> 0 OR SUM(facts.oos_gmv_loss) <> 0 OR SUM(facts.wh_retail_units) <> 0
  OR SUM(facts.glance_views + facts.add_to_carts + facts.search_impr + facts.non_search_impr) > 0;
