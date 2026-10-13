import json
# bm, brand, ytd, ytd_ly, oct, oct_ly, pc1_ytd, pc1_ytd_ly, pc1_oct, pc1_oct_ly, mkd_n25, mkd_n24, jo, jo_ly, jo_u, jo_u_ly, u45
S=[('retail','kiko_milano',4382763,6838397,182673,254165,40.1,39.8,39.2,36.4,40.8,38.3,1603312,2039083,24464,28838,10270),
('retail','charlotte_tilbury',4595831,6516279,359714,422068,33.0,32.3,33.5,29.7,55.3,6.1,1579030,2042867,8030,11109,4707),
('retail','kerastase',3585272,5966963,214305,172283,30.4,24.4,27.4,29.9,33.1,24.7,1172953,1928224,5680,10004,2853),
('retail','mac_cosmetics',3334447,5420885,198704,268134,31.0,28.0,32.7,18.3,30.7,37.9,1100407,1751217,9587,16732,5367),
('retail','nyx_professional_makeup',3601445,5870316,134621,172881,13.4,12.6,15.1,24.7,51.0,50.4,1056639,2155443,24243,47828,9253),
('retail','kylie_cosmetics',2242742,2002449,95388,96594,25.5,20.0,21.0,23.3,51.9,28.0,746363,764307,6557,6676,3069),
('retail','elizabeth_arden',1798388,1935885,49960,49088,46.1,31.8,44.1,49.3,29.4,24.1,708164,888020,2354,3279,1252),
('retail','loreal_professionnel',1363491,2264182,68666,51516,30.3,21.5,27.0,32.0,36.2,23.1,517536,745359,3651,5143,1718),
('retail','make_up_for_ever',1898745,3116573,55870,86337,37.8,33.9,38.2,34.1,50.6,31.9,509084,771268,3180,5149,1289),
('retail','estee_lauder',1475560,1764139,105868,48750,24.2,26.4,9.0,32.6,41.8,49.9,454944,489399,2053,2189,1228),
('retail','lancome',1069775,1260667,53725,42998,23.3,28.9,13.8,28.8,26.5,27.1,435324,490636,2012,1978,901),
('retail','armani',1012650,1014035,81545,49277,23.0,28.7,9.1,28.4,36.3,30.0,413094,363646,968,807,568),
('retail','maybelline_new_york',1361120,2398552,50870,74424,9.8,4.6,13.5,3.3,48.9,52.2,393497,735036,9347,17577,3537),
('retail','anastasia_beverly_hills',838905,1004705,41984,30178,43.0,31.9,36.4,41.9,36.6,20.5,317618,302129,2655,2650,1257),
('retail','clinique',1026506,1304233,85039,56828,19.6,12.0,14.6,16.2,44.4,37.3,311673,420825,1980,2875,1302),
('mp','clara',5034919,1720828,120212,123110,24.9,24.2,25.6,24.3,5.2,15.0,1424899,1084831,4471,2637,2087),
('mp','louzan',681095,0,41732,0,41.3,None,41.7,None,None,None,338829,0,2062,0,904),
('mp','laverne',249458,0,52540,0,43.7,None,43.8,None,None,None,249458,0,1813,0,1656),
('mp','bath_body_works',496060,0,30264,0,27.5,None,27.5,None,63.0,None,232241,0,6626,0,3283),
('mp','h_m',474228,98534,9188,1428,11.0,41.8,11.0,26.9,40.4,48.4,177233,11137,10730,487,5209)]
T={'anastasia_beverly_hills':(7603156,6912808,214908,165477),'armani':(6129125,5422522,134710,118663),'charlotte_tilbury':(33542497,34064829,830715,779306),'clinique':(7962225,9432856,146530,152598),'elizabeth_arden':(7759753,7404975,158252,194891),'estee_lauder':(7322176,11377356,209423,228491),'kerastase':(11353162,16863236,276528,369440),'kiko_milano':(64863628,59428210,1626968,1664352),'kylie_cosmetics':(19528756,18821845,440644,429410),'lancome':(9168666,9465970,223096,204137),'loreal_professionnel':(4950204,7578692,148870,200114),'mac_cosmetics':(30683591,39554673,963671,1006938),'make_up_for_ever':(14875755,21933957,335474,407216),'maybelline_new_york':(13991114,21085814,469384,618217),'nyx_professional_makeup':(60141956,59596093,1338655,1768665),
'bath_body_works':(9884505,205,169801,3),'clara':(11783381,2319126,244412,96158),'h_m':(14258849,2032866,284590,33256),'laverne':(6184002,0,130987,0),'louzan':(4702580,0,97277,0)}
ST={'anastasia_beverly_hills':(1438,230739,5204,734936),'armani':(939,525163,435,251192),'charlotte_tilbury':(14213,2937632,18323,3693164),'clinique':(6388,1139751,1545,258023),'elizabeth_arden':(3140,954671,1004,393613),'estee_lauder':(4307,1117260,1597,539884),'kerastase':(3540,718710,11305,2834008),'kiko_milano':(19957,1591372,48683,4321661),'kylie_cosmetics':(3747,549096,8204,1097027),'lancome':(2003,447867,1745,402894),'loreal_professionnel':(2228,289196,6968,1156093),'mac_cosmetics':(20218,2626527,12274,1549222),'make_up_for_ever':(5508,846065,2185,386262),'maybelline_new_york':(14381,649728,16678,805526),'nyx_professional_makeup':(43647,1832352,42582,2198193)}
out=[]
for s in S:
    bm,b,ytd,ytdl,o,ol,p,pl,po,pol,m25,m24,jo,jol,ju,jul,u45=s
    im,iml,gv,gvl=T[b]
    d=dict(bm=bm,brand=b,ytd=ytd,ytd_yoy=(ytd/ytdl-1) if ytdl else None,oct=o,oct_yoy=(o/ol-1) if ol else None,pc1=p,pc1_pp=(p-pl) if pl is not None else None,pc1o=po,pc1o_pp=(po-pol) if pol is not None else None,mkd25=m25,mkd24=m24,
      jo_gmv=(jo/jol-1) if jol else None, imps=(im/iml-1) if iml>1000 else None, ctr=((gv/im)/(gvl/iml)-1) if iml>1000 and gvl>0 else None, ucr=((ju/gv)/(jul/gvl)-1) if gvl>100 and jul>0 else None)
    if bm=='retail':
        u,rv,pq,prv=ST[b]; wk=u45/45*7
        d.update(stock=u,rv=rv,fwd_u=u+0.8*pq,fwd_rv=rv+0.8*prv,woc=u/wk,fwoc=(u+0.8*pq)/wk)
    out.append(d)
f=lambda v,p=0: '  –  ' if v is None else (f"{v*100:+.{p}f}%")
for d in out:
    print(f"{d['brand'][:20]:20s} JOgmv {f(d['jo_gmv'])} imps {f(d['imps'])} ctr {f(d['ctr'])} ucr {f(d['ucr'])} | ytd {d['ytd']/1e6:.2f} {f(d['ytd_yoy'])} oct {d['oct']/1e3:.0f}K {f(d['oct_yoy'])} pc1 {d['pc1']} ({d['pc1_pp'] if d['pc1_pp'] is None else round(d['pc1_pp'],1)}) pc1o {d['pc1o']} ({None if d['pc1o_pp'] is None else round(d['pc1o_pp'],1)}) mkd {d['mkd25']}/{d['mkd24']}" + (f" | woc {d['woc']:.1f} fwoc {d['fwoc']:.1f} rv {d['rv']/1e6:.2f} frv {d['fwd_rv']/1e6:.2f}" if d['bm']=='retail' else ''))
json.dump(out,open('health.json','w'))

# Buckets (post-July trends vs LY, 1 Jul - 12 Oct, and current WoC on last-45-day sales):
#   Stable : GMV >= -12%, UCR >= -10%, WoC < 20      High : GMV <= -25% and WoC >= 20      Mid : the rest
def bucket(d):
    if d['bm'] == 'mp': return 'Stable'
    if d['jo_gmv'] <= -0.25 and d['woc'] >= 20: return 'High risk'
    if d['jo_gmv'] >= -0.12 and d['ucr'] >= -0.10 and d['woc'] < 20: return 'Stable'
    return 'Mid risk'
for d in out: print(f"{d['brand']:26s} {bucket(d)}")
