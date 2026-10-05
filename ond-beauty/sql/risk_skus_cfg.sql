-- OND Beauty dashboard: item_d attributes per sku_config for the Risk SKUs cards (merged into data/risk_skus.json as cm).
-- Billing project: noonprd-nm-analytics-ai. Run after sql/risk_skus.sql with {CFGS} = every config in the cf field of
-- data/risk_skus.json. Per config: MAX(supplier_sku), barcode, category, sub_category, brand, title, image (item_d)
-- and beauty season (beauty_season_mapping, 'unassigned' when unmapped).
-- A card shows these from the configs it displays (the first shown config for category / title / image / season, sn),
-- not from every config linked into the product.
SELECT i.sku_config cfg, MAX(supplier_sku) sup, MAX(COALESCE(global_barcode, pbarcode_canonical, partner_barcode)) bc,
  MAX(category) cat, MAX(sub_category) sub, MAX(brand_code) brand, MAX(product_title) title, MAX(image_url_1) img,
  IFNULL(ANY_VALUE(se.season), 'unassigned') season
FROM `noonbinamshi.custom_views.item_d` i
LEFT JOIN (SELECT sku_config, MAX(LOWER(season_tag)) season FROM `noonbinmlook.namshi_analytics_custom.beauty_season_mapping` GROUP BY 1) se
  ON se.sku_config = i.sku_config
WHERE i.sku_config IN ({CFGS}) GROUP BY 1
