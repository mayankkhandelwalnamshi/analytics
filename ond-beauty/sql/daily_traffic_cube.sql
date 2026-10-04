-- OND Beauty dashboard: daily Beauty traffic by country x product combo.
-- Billing project: noonprd-nm-analytics-ai. One row per day, records packed to keep the result small:
--   r = "level,c,brand,category,sub_category,business_model,season,gv,atc,si,nsi,app_si,app_nsi;..."
--   level 0: by category x sub_category x business_model x season (brand = '*') - exact for all non-brand filters
--   level 1: by brand x category x sub_category (business_model, season = '*') - used when a brand filter is on
-- (one level holding every attribute at once is too large for the page).
-- Run once per month ({FROM}/{TO}) for Oct-Dec 2024 and Oct-Dec 2025, and for 2026-10-01..yesterday.
-- Source: onsite_v1.onsite_measures (all platforms). App = platform in ('ios', 'android').
--   GV = glance_views, ATC = cart_adds, impressions = search_impressions + non_search_impressions.
-- Product attributes come from item_d at sku_config level. To keep the page small, brand rows with < 5 GV,
-- no ATC and < 500 impressions on a day are folded into '(other brands)' (totals stay exact).
-- Combo key = brand, category, sub_category, business_model (item_d) and beauty season
-- (beauty_season_mapping on sku_config, 'unassigned' when missing; 'mp' when the partner is not Namshi retail, item_d id_partner <> 3001). Brand type / group / POC are brand
-- attributes and are mapped on the page from sql/brand_attributes.sql.
WITH season AS (
  SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
  FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1
),
beauty AS (
  SELECT i.sku_config,
    IFNULL(ANY_VALUE(i.brand_code), '(none)')     AS brand,
    IFNULL(ANY_VALUE(i.category), '(none)')       AS cat,
    IFNULL(ANY_VALUE(i.sub_category), '(none)')   AS sub,
    IFNULL(ANY_VALUE(i.business_model), '(none)') AS bm,
    IF(LOGICAL_OR(i.id_partner = 3001), IFNULL(ANY_VALUE(se.beauty_season), 'unassigned'), 'mp') AS season   -- no Namshi partner sku = mp
  FROM `noonbinamshi.custom_views.item_d` i
  LEFT JOIN season se USING (sku_config)
  WHERE i.business_unit = 'beauty'
    AND IFNULL(i.inventory_type, '') <> 'samples & gwp'   -- samples & GWP are excluded from every metric
  GROUP BY 1
),
x AS (
  SELECT o.date AS d, CASE o.country WHEN 'SA' THEN 0 WHEN 'AE' THEN 1 ELSE 2 END AS c,
    b.brand, b.cat, b.sub, b.bm, b.season,
    SUM(o.glance_views) gv, SUM(o.cart_adds) atc,
    SUM(o.search_impressions) si, SUM(o.non_search_impressions) nsi,
    SUM(IF(o.platform IN ('ios', 'android'), o.search_impressions, 0)) asi,
    SUM(IF(o.platform IN ('ios', 'android'), o.non_search_impressions, 0)) ansi
  FROM `noonbinamshi.onsite_v1.onsite_measures` o
  JOIN beauty b USING (sku_config)
  WHERE o.date BETWEEN '{FROM}' AND '{TO}'
  GROUP BY 1, 2, 3, 4, 5, 6, 7
),
l0 AS (
  SELECT d, c, 0 AS l, '*' AS brand, cat, sub, bm, season,
    SUM(gv) gv, SUM(atc) atc, SUM(si) si, SUM(nsi) nsi, SUM(asi) asi, SUM(ansi) ansi
  FROM x GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
),
b1 AS (
  SELECT d, c, brand, cat, sub,
    SUM(gv) gv, SUM(atc) atc, SUM(si) si, SUM(nsi) nsi, SUM(asi) asi, SUM(ansi) ansi
  FROM x GROUP BY 1, 2, 3, 4, 5
),
l1 AS (
  SELECT d, c, 1 AS l,
    IF(IFNULL(gv,0) < 5 AND IFNULL(atc,0) = 0 AND IFNULL(si,0) + IFNULL(nsi,0) < 500, '(other brands)', brand) AS brand,
    cat, sub, '*' AS bm, '*' AS season,
    SUM(gv) gv, SUM(atc) atc, SUM(si) si, SUM(nsi) nsi, SUM(asi) asi, SUM(ansi) ansi
  FROM b1 GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
)
SELECT FORMAT_DATE('%F', d) d,
  STRING_AGG(FORMAT('%d,%d,%s,%s,%s,%s,%s,%d,%d,%d,%d,%d,%d', l, c, brand, cat, sub, bm, season,
    IFNULL(gv,0), IFNULL(atc,0), IFNULL(si,0), IFNULL(nsi,0), IFNULL(asi,0), IFNULL(ansi,0)), ';') r
FROM (SELECT * FROM l0 UNION ALL SELECT * FROM l1)
WHERE COALESCE(gv,0) + COALESCE(atc,0) + COALESCE(si,0) + COALESCE(nsi,0) > 0
GROUP BY 1 ORDER BY 1
