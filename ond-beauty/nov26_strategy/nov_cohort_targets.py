"""Nov '26 Beauty target (AED 20.6M) split by November cohort (lfl_mapping cohort dates).

planning_dod_merch_brand_category_targets (cp_beauty) only holds October 2026 (AED 8.62M) as of 13 Oct 2026,
so the November cohort targets are an allocation: each cohort's average Nov '24 / Nov '25 GMV per day,
indexed to its month's daily average, times the 2026 day count, normalised to AED 20,551,138.
"""
# cohort, 2026 dates, TY days, Nov '25 GMV, LY days, Nov '24 GMV, LLY days
C = [('MS', '1-6 Nov', 6, 1854805, 6, 2239163, 6), ('Pre 11.11', '7-10 Nov', 4, 1975823, 4, 2851377, 4),
     ('11.11', '11 Nov', 1, 913169, 1, 989146, 1), ('Post 11.11', '12-14 Nov', 3, 1633586, 3, 1586836, 3),
     ('BAU', '15-19 Nov', 5, 2418156, 6, 2079289, 7), ('BF week', '20-24 Nov', 5, 2306274, 5, 3334409, 5),
     ('Pre BF', '25-26 Nov', 2, 1523664, 2, 1979216, 2), ('Black Friday', '27 Nov', 1, 1320009, 1, 1512952, 1),
     ('Post BF', '28-30 Nov', 3, 2495534, 2, 1213538, 1)]
T = 20551138
LY = sum(c[3] for c in C); LLY = sum(c[5] for c in C)
w = [((c[3] / c[4]) / (LY / 30) + (c[5] / c[6]) / (LLY / 30)) / 2 * c[2] for c in C]
for c, wi in zip(C, w):
    t = T * wi / sum(w)
    print(f"{c[0]:12s} {c[1]:9s} target {t/1e6:5.2f}M  per day {t/c[2]/1e3:5.0f}K  vs Nov '25 per day {t/c[2]/(c[3]/c[4])-1:+.0%}")
