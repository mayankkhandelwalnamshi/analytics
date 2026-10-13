exec(open(__import__("pathlib").Path(__file__).with_name("daily.py")).read().split('S={')[0])
for y,D in ((2024,D24),(2025,D25)):
    g=[r[0] for r in D]; T=sum(g)
    print(y,'1-15 share',round(sum(g[:15])/T*100,1),'16-30',round(sum(g[15:])/T*100,1))
    srt=sorted(range(30),key=lambda i:-g[i]); peak=srt[:8]
    pk=sum(g[i] for i in peak); sh=T-pk
    print('  peak8 days',sorted(i+1 for i in peak),'gmv',round(pk/1e6,2),'shoulder22',round(sh/1e6,2),'shoulder/day',round(sh/22/1e3))
# fixed windows: 11.11 window 8-12, BF window 27-30 (2024 BF=29 Nov; 2025 BF=28 Nov)
for y,D in ((2024,D24),(2025,D25)):
    g=[r[0] for r in D]
    ev=sum(g[7:12])+sum(g[26:30]); print(y,'events (8-12 & 27-30) ',round(ev/1e6,2),'other 21 days',round((sum(g)-ev)/1e6,2), 'per day', round((sum(g)-ev)/21/1e3))
pc=[1824773,1590593,2623005,1648114,2046734,1576367,1767188,1640731,1729924,754222]
rv=[5460061,5765533,10642006,5869225,7692932,5617172,5833911,5751407,5975334,2951712]
print('PC1 2026 YTD',round(sum(pc)/sum(rv)*100,1))
pc25=[2002064,1930320,3392834,2169351,2287865,2079345,2175395,2777573,2076580]; rv25=[7240523,6477215,17338559,7442945,9423271,8111355,7728039,9377213,8315761]
print('PC1 2025 Jan-Sep',round(sum(pc25)/sum(rv25)*100,1))
print('Nov PC1 24',round(917696/16511853*100,1),'25',round(-791769/15258346*100,1))
print('Nov MKD 24',round(10311836/29105113*100,1),'25',round(12977390/29725126*100,1))
mk26=[981308,1332288,3440033,1379161,2056754,1293978,1431008,1705640,1902305,966873]; np26=[6929181,7633745,15087820,7742257,10396253,7356997,7731993,7937925,8355913,4140979]
print('MKD 2026 YTD',round(sum(mk26)/sum(np26)*100,1))
print('Nov/Sep 24',round(17785925/7948656,2),'25',round(16440910/8842244,2),'26 need',round(20551138/6374596,2))
print('Nov/day vs Oct1-12/day LY',round(16440910/30/(3390683/12),2),'TY need',round(20551138/30/(3148155/12),2))
print('Oct MTD yoy',round(3148155/3390683-1,3),'Sep yoy',round(6374596/8842244-1,3),'YTD yoy', round(62852266/87294308-1,3))
