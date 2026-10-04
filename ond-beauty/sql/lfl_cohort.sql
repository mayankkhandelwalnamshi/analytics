-- OND Beauty dashboard: LFL cohort of each OND 2026 date (MS, BAU 1, BAU 2, PD, Pre / Post 11.11, Black Friday ...),
-- from the same LFL table as sql/lfl_mapping.sql. Saved as data/lfl_cohort.json {date: cohort}; used by the Cohort cut.
SELECT FORMAT_DATE('%F', date) d, MIN(cohort) cohort
FROM `noonbinmlook.namshi_analytics_custom.lfl_mapping`
WHERE date BETWEEN '2026-10-01' AND '2026-12-31'
GROUP BY 1 ORDER BY 1
