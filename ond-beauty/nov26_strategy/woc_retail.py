# Year-end WoC driven by RETAIL GMV only (Namshi retail business model), converted to units at retail ASP.
AV=503418; WK=85511/31*7; CAP=WK*10
LY={'oct':(4188254,52614),'nov':(15207634,285397),'dec':(7570876,85511)}   # 13-31 Oct, Nov, Dec 2025: retail GMV, units
L4=((8286032,94926),(5835072,58654)); OC=((3066837,34957),(2717167,27883))  # LY, TY
def tr(p):
    (g0,u0),(g1,u1)=p; return g1/g0, (g1/u1)/(g0/u0)
g4,a4=tr(L4); go,ao=tr(OC)
print('L4W retail GMV %+.1f%% ASP %+.1f%% units %+.1f%%'%((g4-1)*100,(a4-1)*100,(g4/a4-1)*100))
print('Oct  retail GMV %+.1f%% ASP %+.1f%% units %+.1f%%'%((go-1)*100,(ao-1)*100,(go/ao-1)*100))
def units(per,gf,af): g,u=LY[per]; return (g*gf)/((g/u)*af), g*gf
share=2717167/3148155; target=20551138
S={}
S['trend']=[units(p,g4,a4) for p in ('oct','nov','dec')]
S['oct']=[units(p,go,ao) for p in ('oct','nov','dec')]
nov_ret=target*share; nov_u=nov_ret/(LY['nov'][0]/LY['nov'][1]*ao)
S['plan']=[units('oct',go,ao),(nov_u,nov_ret),units('dec',go,ao)]
for k,v in S.items():
    sold=sum(x[0] for x in v); g=sum(x[1] for x in v); ye=AV-sold
    print(f"{k:6s} retail GMV {g/1e6:5.1f}M units sold {sold/1e3:5.0f}K  YE {ye/1e3:5.0f}K  WoC {ye/WK:4.1f}  nov ret GMV {v[1][1]/1e6:.1f}M units {v[1][0]/1e3:.0f}K")
print('retail share Oct TY',round(share*100,1),'Nov retail GMV target',round(nov_ret/1e6,2),'cap',round(CAP))
print('LY 13 Oct-31 Dec retail GMV', sum(v[0] for v in LY.values())/1e6)
# November ASP sensitivity (promo month): Oct/Dec at the October trend, Nov retail GMV = target x TY retail share.
asp_ly=LY['nov'][0]/LY['nov'][1]; rest=units('oct',go,ao)[0]+units('dec',go,ao)[0]
for nm,a in (('TY uplift +11%',asp_ly*ao),('LY promo ASP (base)',asp_ly),('5% below LY',asp_ly*0.95),('10% below LY',asp_ly*0.90)):
    nu=nov_ret/a; ye=AV-rest-nu
    print(f"Nov ASP {nm:20s} {a:5.1f}  Nov units {nu/1e3:4.0f}K  YE {ye/1e3:4.0f}K  WoC {ye/WK:4.1f}")
# Retail / MP split of the Nov target on the 1 Jul - 12 Oct 2026 mix (MP 17.7%), replacing the 1-12 Oct retail share.
MP_JUL_OCT, RET_JUL_OCT = 3888061, 18038402
mp_sh = MP_JUL_OCT / (MP_JUL_OCT + RET_JUL_OCT); nov_ret2 = target * (1 - mp_sh)
print(f"MP share {mp_sh:.1%}  Nov retail target {nov_ret2/1e6:.2f}M  MP target {target*mp_sh/1e6:.2f}M")
for nm,a in (('LY promo ASP (base)',asp_ly),('TY uplift +11%',asp_ly*ao),('10% below LY',asp_ly*0.90)):
    nu=nov_ret2/a; ye=AV-rest-nu
    print(f"Nov ASP {nm:20s} Nov units {nu/1e3:4.0f}K  YE {ye/1e3:4.0f}K  WoC {ye/WK:4.1f}")
# Decision (13 Oct 2026): MP fixed at 10% of the Nov target -> retail AED 18.5M, MP AED 2.1M.
nov_ret3 = target * 0.90
for nm,a in (('LY promo ASP (base)',asp_ly),('TY uplift +11%',asp_ly*ao),('10% below LY',asp_ly*0.90)):
    nu=nov_ret3/a; ye=AV-rest-nu
    print(f"[MP 10%] Nov ASP {nm:20s} Nov units {nu/1e3:4.0f}K  YE {ye/1e3:4.0f}K  WoC {ye/WK:4.1f}")
# Decision (13 Oct 2026, revised): MP at 12% of the Nov target -> retail AED 18.1M, MP AED 2.5M.
nov_ret4 = target * 0.88
for nm,a in (('LY promo ASP (base)',asp_ly),('TY uplift +11%',asp_ly*ao),('10% below LY',asp_ly*0.90)):
    nu=nov_ret4/a; ye=AV-rest-nu
    print(f"[MP 12%] Nov ASP {nm:20s} Nov units {nu/1e3:4.0f}K  YE {ye/1e3:4.0f}K  WoC {ye/WK:4.1f}")
# Decision (13 Oct 2026, final): MP at 11% of the Nov target -> retail AED 18.3M, MP AED 2.3M.
nov_ret5 = target * 0.89
for nm,a in (('LY promo ASP (base)',asp_ly),('TY uplift +11%',asp_ly*ao),('10% below LY',asp_ly*0.90)):
    nu=nov_ret5/a; ye=AV-rest-nu
    print(f"[MP 11%] Nov ASP {nm:20s} Nov units {nu/1e3:4.0f}K  YE {ye/1e3:4.0f}K  WoC {ye/WK:4.1f}")
# FINAL (13 Oct 2026): MP at 10% of the Nov target -> retail AED 18.5M, MP AED 2.1M (see the [MP 10%] block above).
# FINAL (13 Oct 2026, revised): MP at 13% of the Nov target -> retail AED 17.9M, MP AED 2.7M. Supersedes the 10% case.
nov_ret6 = target * 0.87
for nm,a in (('LY promo ASP (base)',asp_ly),('TY uplift +11%',asp_ly*ao),('10% below LY',asp_ly*0.90)):
    nu=nov_ret6/a; ye=AV-rest-nu
    print(f"[MP 13%] Nov ASP {nm:20s} Nov units {nu/1e3:5.1f}K  YE {ye:,.0f}  WoC {ye/WK:4.2f}  13Oct-31Dec units {(rest+nu)/1e3:.0f}K  Nov ret GMV {nov_ret6/1e6:.2f}M")
