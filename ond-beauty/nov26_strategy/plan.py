# brand: l12, sh, n24, n25, y25, y26, o25, o26, pc1_ty, pc1_n25, pc1_n24, mk_ty, mk_n25, mk_n24, d25u_ret, n25u_ret, l4w_ly, l4w
B = {
'Charlotte Tilbury':(7418976,7.7,977196,1336512,6094211,4236117,422068,359714,33.0,-38.8,29.1,1.4,55.3,6.1,6810,13616,3770,3307),
'KIKO Milano':(6390135,6.6,1718413,1233982,6584232,4200090,254165,182673,40.1,15.8,21.8,17.9,40.8,38.3,7048,27402,9008,6083),
'Clara':(6216405,6.5,24160,429580,1597719,4914706,123110,120212,24.9,23.2,21.8,14.8,5.2,15.0,0,0,0,0),
'NYX':(5664642,5.9,1191686,1437628,5697452,3466824,172881,134621,13.4,-31.0,-35.5,25.9,51.0,50.4,7099,54165,11289,6473),
'Kérastase':(5228397,5.4,1267074,962796,5794680,3370966,172283,214305,30.4,6.0,9.1,8.6,33.1,24.7,2371,6415,3087,1897),
'MAC':(5013247,5.2,1324425,829669,5155841,3139880,268404,198846,31.0,14.6,-4.6,10.3,30.7,37.9,4136,8984,6681,3526),
'Kylie Cosmetics':(2917608,3.0,286933,360683,1905855,2147354,96594,95388,25.5,-36.2,5.2,13.3,51.9,28.0,1495,6250,2478,1889),
'Make Up For Ever':(2820223,2.9,974917,521336,3030237,1842876,86337,55870,37.8,-12.4,12.8,13.5,50.6,31.9,1784,5496,1945,872),
'Elizabeth Arden':(2736174,2.8,188833,186762,1886797,1748429,49088,49960,46.1,31.9,32.7,13.2,29.4,24.1,2530,806,1502,1112),
'Maybelline':(2206491,2.3,679903,536816,2324160,1310250,74424,50870,9.8,-26.4,-41.2,28.6,48.9,52.2,3882,19163,5489,2438),
'Estée Lauder':(2093255,2.2,701010,398494,1715389,1369692,48750,105868,24.2,-3.0,8.9,24.3,41.8,49.9,790,2142,659,895),
"L'Oréal Professionnel":(1943449,2.0,319495,353265,2212666,1294825,51516,68666,30.3,-0.9,15.3,7.9,36.2,23.1,1162,2971,1273,1029),
'SKIN1004':(1558185,1.6,47164,352923,1668218,907753,49836,36469,29.7,24.3,20.6,18.0,29.5,24.8,3022,7794,1863,1618),
'Lancôme':(1424365,1.5,275332,246751,1217668,1016050,42998,53725,23.3,16.9,10.8,17.8,26.5,27.1,283,987,907,614),
'Clinique':(1400507,1.5,425902,242433,1240823,936442,56699,85039,19.6,-8.6,-6.3,24.4,44.5,37.3,632,2233,1114,1020),
}
TOT=dict(l12=96136335,n24=17785925,n25=16440910,y25=87294308,y26=62852266,o25=3390683,o26=3148155,d25u=85511,n25u=285397,l4wly=94926,l4w=58654)
# stock 12 Oct: units, rval, cost
STK={'Charlotte Tilbury':(14213,2937632,1746653),'Clinique':(6373,1137519,521582),'Elizabeth Arden':(3140,954671,441552),'Estée Lauder':(4307,1117260,512731),'Kérastase':(3540,718710,468863),'KIKO Milano':(19957,1591372,711275),'Kylie Cosmetics':(3747,549096,357825),'Lancôme':(2003,447867,315170),"L'Oréal Professionnel":(2228,289196,184230),'MAC':(20443,2658352,1302848),'Make Up For Ever':(5508,846065,527875),'Maybelline':(14381,649728,491074),'NYX':(43647,1832352,1368642),'SKIN1004':(5911,285230,184234),'Clara':(0,0,0),'_other':(113092,12469322,8252462)}
# PO: qty, cost, rval_op, cost_matched
PO={'Charlotte Tilbury':(18323,2189059,3691288,2187670),'Clinique':(1545,149621,259066,149621),'Elizabeth Arden':(1004,162865,393613,162865),'Estée Lauder':(1597,307686,503922,280986),'Kérastase':(11305,1643864,2549224,1432914),'KIKO Milano':(48683,2065833,3532723,1481435),'Kylie Cosmetics':(8204,627534,1097027,627534),'Lancôme':(1745,222724,400714,221109),"L'Oréal Professionnel":(6968,647052,1154017,645514),'MAC':(12274,895664,1428881,806506),'Make Up For Ever':(2185,208232,384552,206966),'Maybelline':(16678,485334,805526,485334),'NYX':(42582,1377562,2145240,1338338),'SKIN1004':(10328,383507,639521,383507),'Clara':(0,0,0,0),'_other':(117739,6269437,10122058,5883554)}
# retail units: o_rest25 (13-31 Oct LY), n24, d24 ; and retail n25 gmv, n25 cogs, d25 cogs
RU={'Charlotte Tilbury':(2621,5589,4033),'Clinique':(396,3872,1409),'Elizabeth Arden':(168,864,1458),'Estée Lauder':(454,3467,1048),'Kérastase':(1302,8241,3257),'KIKO Milano':(4288,31511,10856),'Kylie Cosmetics':(1718,3441,1486),'Lancôme':(171,1380,604),"L'Oréal Professionnel":(599,2286,1236),'MAC':(1777,15812,4364),'Make Up For Ever':(814,7215,2581),'Maybelline':(3904,25183,4772),'NYX':(7548,41839,9447),'SKIN1004':(2138,1286,798),'_other':(24716,104016,37481)}
FILL=0.8
top_l12=sum(v[0] for v in B.values()); print('top15 share of L12M',round(top_l12/TOT['l12']*100,1), 'of N25', round(sum(v[3] for v in B.values())/TOT['n25']*100,1))
stk_u=sum(v[0] for v in STK.values()); stk_r=sum(v[1] for v in STK.values()); stk_c=sum(v[2] for v in STK.values())
po_q=sum(v[0] for v in PO.values()); po_c=sum(v[1] for v in PO.values())
po_r=sum(v[2]*v[1]/v[3] if v[3] else 0 for v in PO.values())
print('stock units',stk_u,'retail',round(stk_r/1e6,2),'cost',round(stk_c/1e6,2))
print('PO qty',po_q,'cost',round(po_c/1e6,2),'retail',round(po_r/1e6,2))
print('PO@80 qty',round(po_q*FILL),'cost',round(po_c*FILL/1e6,2),'retail',round(po_r*FILL/1e6,2))
avail_u=stk_u+po_q*FILL; avail_r=stk_r+po_r*FILL; avail_c=stk_c+po_c*FILL
print('available units',round(avail_u),'retail',round(avail_r/1e6,2),'cost',round(avail_c/1e6,2))
# Demand: LY retail units Oct13-31 + Nov + Dec
ly_oct=sum(v[0] for v in RU.values()); ly_nov=TOT['n25u']; ly_dec=TOT['d25u']
print('LY retail units: oct13-31',ly_oct,'nov',ly_nov,'dec',ly_dec)
target=round(ly_dec/31*7*10); print('YE target units',target)
wk_dec=ly_dec/31*7
for nm,o,n,d in (('Plan: Oct trend -38%, Nov +25%, Dec flat LY',0.62,1.25,1.0),('Nov flat LY, Dec flat',0.62,1.0,1.0),('Run-rate: all -38%',0.62,0.62,0.62)):
    dem=ly_oct*o+ly_nov*n+ly_dec*d; ye=avail_u-dem
    print(nm,'demand',round(dem),'YE units',round(ye),'WoC',round(ye/wk_dec,1))
# How many units must sell 13 Oct-31 Dec to hit target
print('units to sell for 10 WoC', round(avail_u-target), 'vs LY same period', ly_oct+ly_nov+ly_dec)
# retail GMV available vs Nov target
print('Nov target GMV', round(TOT['n25']*1.25/1e6,2))
print()
IM={ # brand: (g24, im24, g25, im25)
'Charlotte Tilbury':(977196,15016107,1336512,21071983),'Clara':(24160,68602,429580,1561884),'Clinique':(425902,14179676,242433,6260474),'Elizabeth Arden':(188833,1434889,186762,2460243),'Estée Lauder':(701010,13698597,398494,7424315),'Kérastase':(1267074,14918394,962796,7190803),'KIKO Milano':(1718413,38658535,1233982,42575283),'Kylie Cosmetics':(286933,5845399,360683,8092817),'Lancôme':(275332,3752720,246751,3805413),"L'Oréal Professionnel":(319495,9254417,353265,2489178),'MAC':(1324425,29960702,829669,18957086),'Make Up For Ever':(974917,17269417,521336,14156218),'Maybelline':(679903,18023489,536816,16948373),'NYX':(1191686,39444820,1437628,56414253),'SKIN1004':(47164,1498715,352923,6110718),'La Roche-Posay':(509428,6687325,306291,4976576)}
G25,I25=16440911,406544422; G24,I24=17785922,380541723
print('Nov25 beauty gmv/1k',round(G25/I25*1000,1),'imps needed for 20.55M at LY eff',round(20.55e6/(G25/I25*1000)/1e3,0),'M')
t15g=sum(v[2] for k,v in IM.items() if k!='La Roche-Posay'); t15i=sum(v[3] for k,v in IM.items() if k!='La Roche-Posay')
print('top15 N25 share gmv',round(t15g/G25*100,1),'share imps',round(t15i/I25*100,1))
for k,v in sorted(IM.items(), key=lambda kv:-kv[1][2]/kv[1][3]):
    print(f"{k:24s} gmv/1k N25 {v[2]/v[3]*1000:6.1f}  N24 {v[0]/v[1]*1000:6.1f}  shG {v[2]/G25*100:4.1f}% shI {v[3]/I25*100:4.1f}%")
print()
print(f"{'brand':24s} {'N24':>6} {'N25':>6} {'N YoY':>6} {'YTD YoY':>7} {'Oct YoY':>7} {'PC1 TY':>6} {'PC1 N25':>7} {'MKD TY':>6} {'N25':>5} {'N24':>5} | stk avail  WoC_plan WoC_run")
rows=[]
for k,v in B.items():
    l12,sh,n24,n25,y25,y26,o25,o26,p_ty,p25,p24,m_ty,m25,m24,d25u,n25u,l4ly,l4=v
    s=STK.get(k,(0,0,0)); po=PO.get(k,(0,0,0,1)); ru=RU.get(k,(0,0,0))
    avail=s[0]+po[0]*FILL
    wk=d25u/31*7 if d25u else None
    tr=l4/l4ly if l4ly else 1
    dem_plan=ru[0]*tr+n25u*1.25+d25u
    dem_run=(ru[0]+n25u+d25u)*tr
    wp=(avail-dem_plan)/wk if wk else None; wr=(avail-dem_run)/wk if wk else None
    rows.append((k,n25/n24-1, y26/y25-1, o26/o25-1))
    f=lambda x: f"{x:6.1f}" if x is not None else '   n/a'
    print(f"{k:24s} {n24/1e6:6.2f} {n25/1e6:6.2f} {(n25/n24-1)*100:+6.0f}% {(y26/y25-1)*100:+6.0f}% {(o26/o25-1)*100:+6.0f}% {p_ty:6.1f} {p25:7.1f} {m_ty:6.1f} {m25:5.1f} {m24:5.1f} | {s[0]:6d} {avail:7.0f} {f(wp)} {f(wr)}  trend {tr-1:+.0%} need_units {n25u*1.25:.0f}")
# Revised PO retail value (13 Oct 2026): SKUs with a live primary Namshi retail offer price use it; SKUs without one
# use cost x 1.35 (35% margin on cost) instead of the brand ratio gross-up above.
PO_RVAL_PRICED, PO_COST_NOPRICE = 29107372, 1342124
po_r2 = PO_RVAL_PRICED + PO_COST_NOPRICE * 1.35
print('PO retail (cost x1.35 fallback)', round(po_r2/1e6,2), '@80%', round(po_r2*FILL/1e6,2), 'available retail', round((stk_r + po_r2*FILL)/1e6,2))
