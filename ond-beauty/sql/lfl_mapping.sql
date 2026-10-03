-- Like-for-like date mapping for OND 2026: TY date -> LY (ly_lfl) and LLY (ly2_lfl).
SELECT FORMAT_DATE('%F', date) d, FORMAT_DATE('%F', MIN(ly_lfl)) ly, FORMAT_DATE('%F', MIN(ly2_lfl)) lly
FROM `noonbinmlook.namshi_analytics_custom.lfl_mapping`
WHERE date BETWEEN '2026-09-25' AND '2026-12-31'
GROUP BY 1 ORDER BY 1
