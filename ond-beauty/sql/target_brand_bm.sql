-- Fallback business model for target brands with no Beauty sales yet (data/target_bm_fallback.json):
-- the business model with most item_d SKUs (Beauty SKUs first, else any). build.py target_bm uses GMV when the brand has sales.
SELECT brand_code, LOWER(business_model) AS bm, COUNTIF(business_unit = 'beauty') AS beauty_skus, COUNT(*) AS skus
FROM `noonbinamshi.custom_views.item_d`
WHERE brand_code IN UNNEST(@brands)
GROUP BY 1, 2
