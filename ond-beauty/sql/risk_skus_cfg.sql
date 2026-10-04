-- OND Beauty dashboard: supplier SKU and barcode per sku_config for the Risk SKUs cards (merged into data/risk_skus.json as cm).
-- Billing project: noonprd-nm-analytics-ai. Run after sql/risk_skus.sql with {CFGS} = every config in the cf field of
-- data/risk_skus.json. One value per config: MAX(supplier_sku) and MAX(global_barcode) over the config's skus (item_d);
-- a card lists the supplier SKUs / barcodes of the configs it shows, not of every config linked into the product.
SELECT TO_JSON_STRING(ARRAY_AGG(STRUCT(cfg, sup, bc))) j FROM (
  SELECT sku_config cfg, MAX(supplier_sku) sup, MAX(COALESCE(global_barcode, pbarcode_canonical, partner_barcode)) bc
  FROM `noonbinamshi.custom_views.item_d` WHERE sku_config IN ({CFGS}) GROUP BY 1
)
