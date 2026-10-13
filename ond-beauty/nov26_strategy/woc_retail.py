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
