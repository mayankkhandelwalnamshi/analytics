-- OND Beauty dashboard: item_d attributes per sku_config for the Risk SKUs cards (merged into data/risk_skus.json as cm).
-- Billing project: noonprd-nm-analytics-ai. Run after sql/risk_skus.sql with {CFGS} = every config in the cf field of
-- data/risk_skus.json. Per config: MAX(supplier_sku), barcode, category, sub_category, brand, title and image (item_d).
-- A card shows these from the configs it displays (the first shown config for category / title / image), not from
-- every config linked into the product.
SELECT sku_config cfg, MAX(supplier_sku) sup, MAX(COALESCE(global_barcode, pbarcode_canonical, partner_barcode)) bc,
  MAX(category) cat, MAX(sub_category) sub, MAX(brand_code) brand, MAX(product_title) title, MAX(image_url_1) img
FROM `noonbinamshi.custom_views.item_d` WHERE sku_config IN ({CFGS}) GROUP BY 1
