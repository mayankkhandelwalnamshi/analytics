-- OND Beauty dashboard: brand-level filter attributes (brand type, brand group, brand POC).
-- Missing values become 'unassigned'. Output: one row per brand_code.
SELECT b.brand_code,
  IFNULL(t.tag, 'unassigned')          AS brand_type,
  IFNULL(g.brand_group_, 'unassigned') AS brand_group,
  IFNULL(p.poc, 'unassigned')          AS brand_poc
FROM (SELECT DISTINCT brand_code FROM `noonbinamshi.custom_views.item_d` WHERE business_unit = 'beauty' AND brand_code IS NOT NULL) b
LEFT JOIN (SELECT brand AS brand_code, MAX(LOWER(tag)) AS tag
           FROM `noonbinmlook.namshi_analytics_custom.beauty_pestige_mastige_mapping` GROUP BY ALL) t USING (brand_code)
LEFT JOIN (SELECT LOWER(brands) AS brand_code, MAX(brand_group) AS brand_group_
           FROM `noonbinmlook.namshi_analytics_custom.brand_group_beauty` GROUP BY ALL) g USING (brand_code)
LEFT JOIN (SELECT brand AS brand_code, MAX(poc) AS poc
           FROM `noonbinmlook.namshi_analytics_custom.brand_poc_beauty` GROUP BY ALL) p USING (brand_code)
WHERE t.tag IS NOT NULL OR g.brand_group_ IS NOT NULL OR p.poc IS NOT NULL
ORDER BY 1
