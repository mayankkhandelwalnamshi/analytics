# Impressions needed by business model: Nov '25 funnel per segment x its own TY trend (1-12 Oct; Jul-Sep as range).
D={'mp':{'nov25':(1233276,20502,37137031,743500),'oct_ly':(323846,4303,7354890,168105),'oct_ty':(430987,6606,12666358,259196),'q3_ly':(2969933,37353,68650214,1833756),'q3_ty':(3457075,55421,100426555,2172253)},
   'retail':{'nov25':(15207743,285397,369416421,8824327),'oct_ly':(3066696,34956,63536737,1575476),'oct_ty':(2717025,27882,60372876,1591826),'q3_ly':(24178847,286742,534067098,13288335),'q3_ty':(15321377,169851,430128724,10820212)}}
TGT={'retail':20551138*0.88,'mp':20551138*0.12}  # MP at 12% of the Nov target
def f(t): g,u,im,gv=t; return dict(ctr=gv/im,ucr=u/gv,asp=g/u,gpk=g/im*1000,im=im)
tot={}
for bm in ('retail','mp'):
    N=f(D[bm]['nov25']); print(f"\n{bm.upper()} Nov25: ctr {N['ctr']*100:.2f}% ucr {N['ucr']*100:.2f}% asp {N['asp']:.1f} gpk {N['gpk']:.1f} imps {N['im']/1e6:.0f}M  target {TGT[bm]/1e6:.2f}M")
    for nm,a,b in (('flat',None,None),('oct','oct_ly','oct_ty'),('q3','q3_ly','q3_ty')):
        if a: A,B=f(D[bm][a]),f(D[bm][b]); r={k:B[k]/A[k] for k in ('ctr','ucr','asp')}; tr=B['im']/A['im']
        else: r={'ctr':1,'ucr':1,'asp':1}; tr=None
        gpk=N['ctr']*r['ctr']*N['ucr']*r['ucr']*N['asp']*r['asp']*1000; im=TGT[bm]/gpk*1000
        tot.setdefault(nm,0); tot[nm]+=im
        print(f"  {nm:5s} ctr {r['ctr']-1:+.0%} ucr {r['ucr']-1:+.0%} asp {r['asp']-1:+.0%}"+(f" imps trend {tr-1:+.0%}" if tr else '')+f" -> gpk {gpk:5.1f}  imps {im/1e6:5.0f}M ({im/N['im']-1:+.0%})")
print({k:round(v/1e6) for k,v in tot.items()})
