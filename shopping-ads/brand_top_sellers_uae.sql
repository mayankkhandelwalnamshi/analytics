-- Shopping ads · brand top-seller SKU list (UAE)
-- Brands: top 20 by Namshi-retail UAE GMV since 1 Jul 2026 + Louzan + Clara.
-- Per brand: sku_configs ranked by UAE GMV since 1 Jul; keep configs inside the first 80% of brand GMV
-- (cumulative share computed on ALL the brand's configs), then keep only configs live in UAE on the latest snapshot.
DECLARE d_from DATE DEFAULT '2026-07-01';
DECLARE d_to   DATE DEFAULT DATE_SUB(CURRENT_DATE('Asia/Dubai'), INTERVAL 1 DAY);
DECLARE snap   DATE DEFAULT (SELECT MAX(date) FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY));

WITH it AS (
  SELECT sku, ANY_VALUE(sku_config) cfg, ANY_VALUE(brand_code) brand, ANY_VALUE(business_model) bm,
    ANY_VALUE(business_unit) bu, ANY_VALUE(product_title) title
  FROM `noonbinamshi.custom_views.item_d`
  WHERE business_unit = 'beauty' AND IFNULL(inventory_type, '') <> 'samples & gwp'
  GROUP BY 1
),
s AS (
  SELECT it.brand, it.cfg, it.bm, SUM(s.gmv_inc_vat) gmv, SUM(s.items_gross) units
  FROM `noonbinamshi.custom_views.sales_metrics` s JOIN it USING (sku)
  WHERE s.order_date_key BETWEEN d_from AND d_to AND s.country = 'AE'
    AND s.marketplace IN ('namshi', 'namshi_v2') AND s.gmv_inc_vat > 0
  GROUP BY 1, 2, 3
),
top_brands AS (
  SELECT brand, ROW_NUMBER() OVER (ORDER BY SUM(gmv) DESC) brand_rank
  FROM s WHERE bm = 'retail' GROUP BY 1
  QUALIFY brand_rank <= 20
),
brands AS (
  SELECT brand, brand_rank FROM top_brands
  UNION ALL
  SELECT DISTINCT brand, NULL FROM it
  WHERE REGEXP_CONTAINS(LOWER(brand), r'louzan|clara') AND brand NOT IN (SELECT brand FROM top_brands)
),
cfg AS (
  SELECT s.brand, b.brand_rank, s.cfg, SUM(s.gmv) gmv, SUM(s.units) units
  FROM s JOIN brands b USING (brand) GROUP BY 1, 2, 3
),
ranked AS (
  SELECT *, SUM(gmv) OVER (PARTITION BY brand) brand_gmv,
    SUM(gmv) OVER (PARTITION BY brand ORDER BY gmv DESC, cfg ROWS UNBOUNDED PRECEDING) cum_gmv
  FROM cfg
),
live AS (
  SELECT it.cfg FROM `noonbinamshi.assortment_namshi.psku_sku_mapped` p JOIN it USING (sku)
  WHERE p.date = snap AND p.country = 'AE' AND p.is_live = 1 AND p.stock_net > 0
  GROUP BY 1
),
title AS (SELECT cfg, ANY_VALUE(title) title FROM it GROUP BY 1)
SELECT r.brand_rank, r.brand, r.cfg AS sku_config, t.title AS product_title,
  ROUND(r.gmv) AS gmv_aed, r.units, ROUND(r.gmv / r.brand_gmv, 4) AS gmv_share_of_brand,
  ROUND(r.cum_gmv / r.brand_gmv, 4) AS cum_share, ROUND(r.brand_gmv) AS brand_gmv_aed
FROM ranked r JOIN title t USING (cfg)
WHERE r.cum_gmv - r.gmv < 0.8 * r.brand_gmv          -- config falls inside the top 80% of brand GMV
  AND r.cfg IN (SELECT cfg FROM live)                -- currently live in UAE
ORDER BY IFNULL(r.brand_rank, 99), r.brand, r.gmv DESC;
