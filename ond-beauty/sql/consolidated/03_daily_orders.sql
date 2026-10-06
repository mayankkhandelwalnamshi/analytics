-- Beauty Pulse · 03 · DAILY ORDERS (plain table)
-- Replaces: daily_orders.
-- Distinct orders don't add up across products (one order can hold several), so each level is counted on its own:
-- one row per date x country x level x level_value. Use the level that matches the filter you need.
--   level 'all'          level_value = 'all'                (all Beauty)
--   level 'category'     level_value = category
--   level 'sub_category' level_value = 'category|sub_category'
--   level 'brand'        level_value = brand
--   level 'business_model', 'season'
-- AOV = gmv / orders and ITO = units / orders use 01_daily_product.sql totals at the same level.
-- Scope and season rule as 01 (sales): Namshi marketplaces, gmv_inc_vat > 0, Beauty, no samples & GWP, 'mp' when not 3001.
DECLARE d_from DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);
DECLARE d_to   DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);

WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
sku_dim AS (
  SELECT i.sku,
    IFNULL(ANY_VALUE(i.brand_code), '(none)') brand, IFNULL(ANY_VALUE(i.category), '(none)') category,
    IFNULL(ANY_VALUE(i.sub_category), '(none)') sub_category, IFNULL(ANY_VALUE(i.business_model), '(none)') business_model,
    IF(IFNULL(ANY_VALUE(i.id_partner), 0) <> 3001, 'mp', IFNULL(ANY_VALUE(se.beauty_season), 'unassigned')) season
  FROM `noonbinamshi.custom_views.item_d` i LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
base AS (
  SELECT s.order_date_key date, s.country, d.*, s.order_nr
  FROM `noonbinamshi.custom_views.sales_metrics` s JOIN sku_dim d USING (sku)
  WHERE s.order_date_key BETWEEN d_from AND d_to AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
)
SELECT date, country, level, level_value, COUNT(DISTINCT order_nr) orders
FROM base, UNNEST([
  STRUCT('all' AS level, 'all' AS level_value),
  STRUCT('category', category),
  STRUCT('sub_category', CONCAT(category, '|', sub_category)),
  STRUCT('brand', brand),
  STRUCT('business_model', business_model),
  STRUCT('season', season)
])
GROUP BY 1, 2, 3, 4;
