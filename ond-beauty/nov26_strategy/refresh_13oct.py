# Data refresh to 13 Oct 2026 (queries re-run 14 Oct; stock/PO snapshot 13 Oct). Rebuilds page/health.json and prints
# every headline number the page uses. Same SQL as queries.sql / brand_health.py with 12 Oct -> 13 Oct (L45D = 30 Aug - 13 Oct).
import json
# bm, brand, ytd, ytd_ly, oct, oct_ly, pc1_ytd, pc1_ytd_ly, pc1_oct, pc1_oct_ly, mkd_n25, mkd_n24, jo, jo_ly, jo_u, jo_u_ly, u45
S=[('retail','charlotte_tilbury',4635376,6540883,399260,446672,33.0,32.3,33.9,29.8,55.3,6.1,1618575,2067471,8199,11238,4753),
('retail','kiko_milano',4391968,6853313,191879,269081,40.1,39.8,39.5,36.7,40.8,38.3,1612517,2054000,24589,29008,10048),
('retail','kerastase',3592165,5976929,221199,182249,30.3,24.4,27.3,30.1,33.1,24.7,1179846,1938190,5720,10053,2798),
('retail','mac_cosmetics',3345986,5428579,212006,276860,31.0,28.0,32.9,18.7,30.7,37.9,1113439,1758911,9703,16807,5315),
('retail','nyx_professional_makeup',3612557,5880406,145733,182970,13.4,12.6,15.1,24.2,51.0,50.4,1067751,2165533,24517,48067,9235),
('retail','kylie_cosmetics',2247000,2008632,99646,102776,25.5,20.0,21.5,23.7,51.9,28.0,750621,770490,6591,6722,2990),
('retail','elizabeth_arden',1800190,1936325,51761,49528,46.1,31.8,44.4,49.3,29.4,24.1,709966,888460,2360,3282,1248),
('retail','loreal_professionnel',1366102,2266395,71277,53729,30.3,21.5,27.0,32.5,36.2,23.1,520146,747572,3669,5157,1659),
('retail','make_up_for_ever',1904501,3123466,61625,93230,37.8,33.9,37.4,34.3,50.6,31.9,514839,778161,3226,5190,1292),
('retail','estee_lauder',1482136,1766905,112444,51517,24.2,26.5,10.2,32.5,41.8,49.9,461520,492166,2079,2201,1215),
('retail','lancome',1070463,1262401,54413,44733,23.3,28.9,13.9,28.9,26.5,27.1,436012,492370,2016,1987,869),
('retail','armani',1014985,1015247,83881,50489,23.0,28.7,9.5,28.7,36.3,30.0,415430,364858,973,809,560),
('retail','maybelline_new_york',1363504,2403165,53255,79038,9.8,4.6,13.6,3.2,48.9,52.2,395881,739649,9405,17705,3474),
('retail','anastasia_beverly_hills',840773,1006099,43852,31571,43.1,32.0,36.9,42.2,36.6,20.5,319486,303523,2671,2660,1231),
('retail','clinique',1024998,1298350,88556,57527,19.6,11.9,15.1,16.3,44.5,37.3,314531,417784,1998,2858,1303),
('mp','clara',5041929,1728073,127222,130354,24.9,24.2,25.6,24.1,5.2,15.0,1431909,1092076,4493,2656,2053),
('mp','louzan',683364,0,44001,0,41.3,None,41.6,None,None,None,341098,0,2075,0,898),
('mp','laverne',252714,0,55796,0,43.7,None,43.8,None,None,None,252714,0,1833,0,1647),
('mp','bath_body_works',498032,0,32236,0,27.5,None,27.4,None,63.0,None,234213,0,6692,0,3263),
('mp','h_m',474796,98572,9756,1465,11.0,41.8,10.9,26.8,40.4,48.4,177802,11175,10760,489,4667)]
T={'anastasia_beverly_hills':(7643931,6948209,216253,166268),'armani':(6186247,5458485,135635,119300),'charlotte_tilbury':(34107593,34490511,847347,790999),
'clinique':(8073906,9425587,148200,152664),'elizabeth_arden':(7782211,7456040,158922,195951),'estee_lauder':(7401400,11448029,211488,230145),
'kerastase':(11459875,16973850,278908,371717),'kiko_milano':(65269995,59922499,1637076,1677164),'kylie_cosmetics':(19623590,18972919,444032,433747),
'lancome':(9224840,9521704,224598,205222),'loreal_professionnel':(4987930,7604238,150078,201131),'mac_cosmetics':(30970686,39785601,973841,1013001),
'make_up_for_ever':(15017024,22138678,339293,410960),'maybelline_new_york':(14100682,21217168,474356,622821),'nyx_professional_makeup':(61121534,59950054,1353663,1779116),
'bath_body_works':(9966163,205,171066,3),'clara':(11852863,2347758,245773,97399),'h_m':(14309534,2042869,285654,33434),'laverne':(6281796,0,132493,0),'louzan':(4749020,0,98142,0)}
ST={'anastasia_beverly_hills':(1430,229613,5204,734936),'armani':(922,517507,435,251223),'charlotte_tilbury':(14028,2902273,18323,3695486),'clinique':(6338,1132108,1545,258165),
'elizabeth_arden':(3145,953491,1004,393613),'estee_lauder':(4295,1108536,1640,565109),'kerastase':(3467,733553,11520,2914411),'kiko_milano':(20103,1618172,48577,4331877),
'kylie_cosmetics':(3745,548875,8204,1092309),'lancome':(2004,451552,1745,403114),'loreal_professionnel':(2211,288605,7032,1185005),'mac_cosmetics':(19954,2730802,12175,1543051),
'make_up_for_ever':(5408,832712,2185,386357),'maybelline_new_york':(14354,649741,17018,825139),'nyx_professional_makeup':(45243,1877677,46213,2371092)}
out=[]
for bm,b,ytd,ytdl,o,ol,p,pl,po,pol,m25,m24,jo,jol,ju,jul,u45 in S:
    im,iml,gv,gvl=T[b]
    d=dict(bm=bm,brand=b,ytd=ytd,ytd_yoy=(ytd/ytdl-1) if ytdl else None,oct=o,oct_yoy=(o/ol-1) if ol else None,pc1=p,pc1_pp=(p-pl) if pl is not None else None,
      pc1o=po,pc1o_pp=(po-pol) if pol is not None else None,mkd25=m25,mkd24=m24,jo=jo,
      jo_gmv=(jo/jol-1) if jol else None, imps=(im/iml-1) if iml>1000 else None, ctr=((gv/im)/(gvl/iml)-1) if iml>1000 and gvl>0 else None,
      ucr=((ju/gv)/(jul/gvl)-1) if gvl>100 and jul>0 else None)
    if bm=='retail':
        u,rv,pq,prv=ST[b]; wk=u45/45*7
        d.update(stock=u,rv=rv,fwd_u=u+0.8*pq,fwd_rv=rv+0.8*prv,woc=u/wk,fwoc=(u+0.8*pq)/wk)
    out.append(d)
json.dump(out,open('page/health.json','w'))
def bucket(d):
    if d['bm']=='mp': return 'stable'
    if d['jo_gmv']<=-0.25 and d['woc']>=20: return 'high'
    if d['jo_gmv']>=-0.12 and d['ucr']>=-0.10 and d['woc']<20: return 'stable'
    return 'mid'
f=lambda v: ' – ' if v is None else f"{v*100:+.0f}%"
for d in out:
    print(f"{d['brand'][:22]:22s} {bucket(d):6s} jo {f(d['jo_gmv'])} imps {f(d['imps'])} ctr {f(d['ctr'])} ucr {f(d['ucr'])}" + (f" woc {d['woc']:.1f} fwoc {d['fwoc']:.1f}" if d['bm']=='retail' else ''))
ret=[d for d in out if d['bm']=='retail']; tj=sum(d['jo'] for d in ret)
for k in ('high','mid','stable'): print(k, round(sum(d['jo'] for d in ret if bucket(d)==k)/tj*100), [d['brand'] for d in ret if bucket(d)==k])

# Totals, 13 Oct
RET_JO, MP_JO = 18197498, 3915034
print('top15 retail share', round(tj/RET_JO*100), '% | MP top5', round(sum(d['jo'] for d in out if d['bm']=='mp')/MP_JO*100), '% | Clara', round(1431909/MP_JO*100),
      '% | top20 of beauty', round((tj+sum(d['jo'] for d in out if d['bm']=='mp'))/(RET_JO+MP_JO)*100), '% | MP share Jul-Oct', round(MP_JO/(RET_JO+MP_JO)*100,1))
OCT_TY, OCT_LY = 2877051+457960, 3239213+342359
print('1-13 Oct beauty YoY', round((OCT_TY/OCT_LY-1)*100,1), '| retail', round((2877051/3239213-1)*100,1), '| MP', round((457960/342359-1)*100,1), '| Oct pace', round(OCT_TY/13*31))
# Stock and POs at 80% fill
STK_U, STK_R, STK_C = 263180, 28587710, 17355140
PO_Q, PO_C, PO_R_PRICED, PO_C_NOP, PO_Q_PRE_NOV = 317508, 18295694, 30056724, 1397223, 286664
po_r = PO_R_PRICED + PO_C_NOP*1.35
AV = STK_U + 0.8*PO_Q; AVR = STK_R + 0.8*po_r; AVC = STK_C + 0.8*PO_C
print(f"stock {STK_U:,} + PO@80 {0.8*PO_Q:,.0f} = {AV:,.0f} units | retail {AVR/1e6:.2f}M cost {AVC/1e6:.2f}M | PO pre-Nov {PO_Q_PRE_NOV/PO_Q:.0%}")
# Retail year-end (WoC on Dec '25 retail units 85,511 -> 19.3K/wk; cap 193,089)
WK=85511/31*7; CAP=WK*10
LY={'oct':(4015211,50706),'nov':(15207634,285397),'dec':(7570876,85511)}   # 14-31 Oct, Nov, Dec 2025 retail
L4=((8277957,95005),(5852897,58777)); OC=((3239213,36860),(2877051,29500))
def tr(p): (g0,u0),(g1,u1)=p; return g1/g0,(g1/u1)/(g0/u0)
g4,a4=tr(L4); go,ao=tr(OC)
units=lambda per,gf,af: LY[per][1]*gf/af
for nm,gf,af in (('L4W trend',g4,a4),('Oct trend',go,ao)):
    sold=sum(units(p,gf,af) for p in LY); ye=AV-sold
    print(f"{nm}: retail GMV {gf-1:+.1%} ASP {af-1:+.1%} sold {sold:,.0f} YE {ye:,.0f} WoC {ye/WK:.1f}")
TGT=20551138*0.87; DRR=12741/7; oct_r=DRR*18; dec=85511*0.9
for nm,a in (('ASP 65',65.0),('ASP 62',62.0),('ASP 71',71.0),('ASP 53.3',15207634/285397)):
    nu=TGT/a; sold=oct_r+nu+dec; ye=AV-sold
    print(f"Plan {nm}: Oct {oct_r:,.0f} Nov {nu:,.0f} Dec {dec:,.0f} sold {sold:,.0f} YE {ye:,.0f} WoC {ye/WK:.2f}")
print('units to sell for cap', round(AV-CAP), '| cover of Nov retail need', round(AVR/TGT,1))
# Impressions needed (70/30 on Jul-13 Oct trend)
D={'retail':{'nov25':(15206297,285386,369371891,8823867),'ly':(27413288,323572,601856297,14971259),'ty':(18197498,199345,495123193,12531176)},
   'mp':{'nov25':(1233276,20502,37137031,743500),'ly':(3312292,41903,76539698,2015157),'ty':(3915034,62474,113935946,2449605)}}
TG={'retail':20551138*0.87,'mp':20551138*0.13}; W=0.7
fn=lambda t: dict(ctr=t[3]/t[2],ucr=t[1]/t[3],asp=t[0]/t[1],gpk=t[0]/t[2]*1000,im=t[2])
tot=0; lo=0; hi=0
for bm in ('retail','mp'):
    N,A,B=fn(D[bm]['nov25']),fn(D[bm]['ly']),fn(D[bm]['ty'])
    r={k:B[k]/A[k] for k in ('ctr','ucr','asp')}; w={k:W*r[k]+(1-W) for k in r}
    ctr,ucr,asp=N['ctr']*w['ctr'],N['ucr']*w['ucr'],N['asp']*w['asp']; gpk=ctr*ucr*asp*1000; im=TG[bm]/gpk*1000; tot+=im
    full=N['gpk']*r['ctr']*r['ucr']*r['asp']; i_lo=TG[bm]/N['gpk']*1000; i_hi=TG[bm]/full*1000; lo+=i_lo; hi+=i_hi
    print(f"{bm}: trend ctr {r['ctr']-1:+.0%} ucr {r['ucr']-1:+.0%} asp {r['asp']-1:+.0%} | Nov25 {N['ctr']*100:.2f}%/{N['ucr']*100:.2f}%/{N['asp']:.1f} -> {ctr*100:.2f}%/{ucr*100:.2f}%/{asp:.1f} gpk {N['gpk']:.1f}->{gpk:.1f} imps {im/1e6:.0f}M ({im/N['im']-1:+.0%}) range {i_lo/1e6:.0f}-{i_hi/1e6:.0f}M")
LYI=369371891+37137031
print(f"TOTAL {tot/1e6:.0f}M ({tot/LYI-1:+.0%}) gpk {(40.4)}->{20551138/tot*1000:.1f} range {lo/1e6:.0f}-{hi/1e6:.0f}M")
