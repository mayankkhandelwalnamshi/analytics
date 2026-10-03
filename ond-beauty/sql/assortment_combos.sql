-- OND Beauty dashboard: name lookup for the combo keys used in sql/daily_assortment.sql.
SELECT STRING_AGG(FORMAT('%x,%s', k, combo), ';') r FROM (
  SELECT DISTINCT FARM_FINGERPRINT(combo) k, combo FROM (
    SELECT CONCAT(IFNULL(ANY_VALUE(i.brand_code), '(none)'), '|', IFNULL(ANY_VALUE(i.category), '(none)'), '|',
      IFNULL(ANY_VALUE(i.sub_category), '(none)'), '|', IFNULL(ANY_VALUE(i.business_model), '(none)'), '|',
      IFNULL(ANY_VALUE(se.beauty_season), 'unassigned')) AS combo
    FROM `noonbinamshi.custom_views.item_d` i
    LEFT JOIN (SELECT sku_config, MAX(LOWER(season_tag)) AS beauty_season
               FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1) se USING (sku_config)
    WHERE i.business_unit = 'beauty' AND IFNULL(i.inventory_type, '') <> 'samples & gwp'
    GROUP BY i.sku_config))
