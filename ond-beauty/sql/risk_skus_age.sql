-- OND Beauty dashboard: current age of the live configs on the Risk SKUs tab (merged into data/risk_skus.json as ag / ab).
-- Billing project: noonprd-nm-analytics-ai. Run after sql/risk_skus.sql with {SNAP} = the same latest snapshot date and {CFGS} = the configs flagged
-- live (":1") in the cf field of data/risk_skus.json. A product's age = its oldest live config in the card's country
-- (the other country's ageing when the config has none there, e.g. KSA live via CB from the UAE warehouse).
SELECT TO_JSON_STRING(ARRAY_AGG(STRUCT(cc, cfg, m, b))) j FROM (
  SELECT country cc, sku_config cfg, ROUND(MAX(sku_config_ageing_in_months), 1) m, MAX(sku_config_ageing_detailed) b
  FROM `noonbinmlook.namshi_analytics_custom.ageing_cost`
  WHERE date = '{SNAP}' AND id_partner = 3001 AND country IN ('SA', 'AE') AND sku_config IN ({CFGS})
  GROUP BY 1, 2
)
