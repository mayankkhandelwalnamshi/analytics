import json
rows=json.load(open('daily.json'))
# fields: d,c,bm,gmv,u,mkd,np,imp,gv
P={'Sept':(1,30),'1-18 Sep':(1,18),'19-25 Sep':(19,25),'26-30 Sep':(26,30)}
def agg(filt):
    out={}
    for pn,(a,b) in P.items():
        for y in ('2025','2026'):
            s=[0]*6
            for r in rows:
                if r[0][:4]==y and a<=int(r[0][8:])<=b and filt(r):
                    for i in range(6): s[i]+=r[3+i]
            g,u,m,np_,imp,gv=s; days=b-a+1
            out[(pn,y)]=dict(gmv=g,units=u,gmd=g/days,asp=g/u if u else 0,imp=imp,ctr=gv/imp if imp else 0,gv=gv,ucr=u/gv if gv else 0,mkd=m/np_ if np_ else 0,days=days)
    return out
CN={'SA':'KSA','AE':'UAE','KW':'Kuwait','QA':'Qatar','BH':'Bahrain','OM':'Oman'}
res={'Overall':agg(lambda r:True)}
for c in CN: res[CN[c]]=agg(lambda r,c=c:r[1]==c)
res['Other GCC']=agg(lambda r:r[1] not in('SA','AE'))
res['Retail']=agg(lambda r:r[2]=='retail'); res['MP']=agg(lambda r:r[2]=='mp')
for k in ['Overall','UAE','KSA','Other GCC','Retail','MP']:
    for pn in P:
        t,l=res[k][(pn,'2026')],res[k][(pn,'2025')]
        print(f"{k:9}{pn:10} GMV {t['gmv']/1e6:5.2f}M vs {l['gmv']/1e6:5.2f}M {t['gmv']/l['gmv']-1:+.1%} | ASP {t['asp']:.0f}/{l['asp']:.0f} | Imp {t['imp']/l['imp']-1:+.1%} | GV {t['gv']/l['gv']-1:+.1%} | CTR {t['ctr']*100:.2f}/{l['ctr']*100:.2f} | UCR {t['ucr']*100:.2f}/{l['ucr']*100:.2f} | MKD {t['mkd']*100:.1f}/{l['mkd']*100:.1f}")
# daily overall
daily={}
for r in rows:
    k=(r[0][:4],int(r[0][8:])); s=daily.setdefault(k,[0]*6)
    for i in range(6): s[i]+=r[3+i]
json.dump({'res':{k:{f"{a}|{b}":v for (a,b),v in d.items()} for k,d in res.items()},'daily':{f"{a}|{b}":v for (a,b),v in daily.items()}},open('agg.json','w'))
for dd in range(1,31):
    t,l=daily[('2026',dd)],daily[('2025',dd)]
    print(dd, round(t[0]/1e3), round(l[0]/1e3), f"mkd {t[2]/t[3]*100:.0f}/{l[2]/l[3]*100:.0f}", f"gv {t[5]/1e3:.0f}/{l[5]/1e3:.0f}", f"ucr {t[1]/t[5]*100:.2f}/{l[1]/l[5]*100:.2f}")
