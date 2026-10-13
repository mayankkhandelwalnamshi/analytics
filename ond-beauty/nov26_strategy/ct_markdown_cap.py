# Charlotte Tilbury: Nov '26 markdown capped at 30% (Nov '25 ran 55.3%). Effect on CT units and on year-end retail WoC.
# CT retail, sales_metrics (beauty excl. samples & gwp, namshi marketplaces, gmv>0): month -> (GMV, units, full price, MKD %)
CT={'2024-10':(751223,4169,786654,4.1),'2024-11':(977196,5589,1106013,6.1),
    '2025-10':(927596,4693,963688,3.1),'2025-11':(1336512,13616,3012020,55.3),'2025-12':(918751,6810,1329689,30.9),
    '2026-10':(359714,1649,372418,3.4)}   # Oct '26 = 1-12 Oct
CAP_MKD=30.0
# Nov unit lift over October, observed at two markdown depths, interpolated linearly to the cap.
l24=CT['2024-11'][1]/CT['2024-10'][1]; l25=CT['2025-11'][1]/CT['2025-10'][1]
m24,m25=CT['2024-11'][3],CT['2025-11'][3]
lift=l24+(l25-l24)*(CAP_MKD-m24)/(m25-m24)
oct26=CT['2026-10'][1]/12*31                      # October '26 run-rate units
nov_u=oct26*lift
g,u,fp,m=CT['2025-11']; fp_u=fp/u; realis=(g/fp)/(1-m/100)   # GMV vs full price net of markdown (coupons/VAT)
asp=fp_u*(1-CAP_MKD/100)*realis; nov_g=nov_u*asp
print(f"Nov lift vs Oct: {l24:.2f}x at {m24}% MKD (Nov '24), {l25:.2f}x at {m25}% (Nov '25) -> {lift:.2f}x at {CAP_MKD:.0f}%")
print(f"Oct '26 run-rate {oct26:,.0f} units -> Nov '26 CT {nov_u:,.0f} units at ASP {asp:.0f} (LY {g/u:.0f}) = AED {nov_g/1e6:.2f}M")
# Plan case (woc_retail.py): Nov retail AED 18.5M at LY promo ASP -> 347K units, YE 46,135, 19.3K units/wk.
RET_NOV_LY=(15207634,285397); WK=85511/31*7; TGT=20551138*0.87; YE=57705   # MP 13% plan case (woc_retail.py)
ct_g_sh=g/RET_NOV_LY[0]; ct_u_sh=u/RET_NOV_LY[1]
plan_ct_u=TGT/(RET_NOV_LY[0]/RET_NOV_LY[1])*ct_u_sh; plan_ct_g=TGT*ct_g_sh
oth_asp=(RET_NOV_LY[0]-g)/(RET_NOV_LY[1]-u)
gap=plan_ct_g-nov_g; fill_u=gap/oth_asp
print(f"Plan had CT at AED {plan_ct_g/1e6:.2f}M / {plan_ct_u:,.0f} units (LY share {ct_g_sh:.1%} GMV, {ct_u_sh:.1%} units)")
print(f"CT units -{plan_ct_u-nov_u:,.0f}; GMV gap AED {gap/1e6:.2f}M")
for nm,ye in (("gap not filled",YE+plan_ct_u-nov_u),("gap filled by other brands at LY ASP %.0f"%oth_asp,YE+plan_ct_u-nov_u-fill_u)):
    print(f"  {nm:40s} YE {ye:,.0f} units  WoC {ye/WK:.1f}")
# CT's own closing stock: forward units (stock 12 Oct + 80% PO) minus 13 Oct - 31 Dec sales.
fwd=28871; rest_oct=oct26-CT['2026-10'][1]; ty_tr=oct26/CT['2025-10'][1]; dec=CT['2025-12'][1]*ty_tr
for nm,n in (("plan (LY share)",plan_ct_u),("30% MKD cap",nov_u)):
    close=fwd-rest_oct-n-dec
    print(f"CT {nm:16s} sells {rest_oct+n+dec:,.0f} (Oct {rest_oct:,.0f} Nov {n:,.0f} Dec {dec:,.0f}) closes {close:,.0f} units = {close/(dec/31*7):.1f} WoC on its Dec rate")
# Plan at Nov '26 retail ASP 65 (woc_retail.py): 275,069 Nov units, YE 118,175. CT keeps its LY unit share of the plan.
NOV_U65, YE65 = 275069, 118175
p_u=NOV_U65*ct_u_sh; oth65=(TGT-plan_ct_g)/(NOV_U65-p_u); fill65=gap/oth65; ye65=YE65+p_u-nov_u-fill65
print(f"[ASP 65] plan CT {p_u:,.0f} units -> capped {nov_u:,.0f} ({nov_u-p_u:+,.0f}); gap filled at other-brand ASP {oth65:.1f} = {fill65:,.0f} units; YE {ye65:,.0f} WoC {ye65/WK:.2f}")
close=fwd-rest_oct-p_u-dec; print(f"[ASP 65] CT closes {close:,.0f} in plan vs {fwd-rest_oct-nov_u-dec:,.0f} capped")
