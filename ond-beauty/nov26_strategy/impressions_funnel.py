M={ # g,u,im,gv
'2025-07':(8290997,101214,194663624,5233018),'2025-08':(10014889,122869,230532901,5504189),'2025-09':(8842244,100014,177476052,4384792),
'2025-10m':(3390683,39260,70894210,1743637),'2025-11':(16440910,305899,406544422,9567804),
'2026-07':(6236584,76205,179351462,4333244),'2026-08':(6166883,79248,189106872,4581654),'2026-09':(6374596,69817,162104326,4077634),'2026-10m':(3148155,34489,73035347,1850956)}
def agg(ks):
    g,u,im,gv=[sum(M[k][i] for k in ks) for i in range(4)]
    return dict(g=g,u=u,im=im,gv=gv,ctr=gv/im,ucr=u/gv,asp=g/u,gpk=g/im*1000)
LY=agg(['2025-07','2025-08','2025-09']); TY=agg(['2026-07','2026-08','2026-09'])
OL=agg(['2025-10m']); OT=agg(['2026-10m']); N=agg(['2025-11'])
for nm,a,b in (('L3M Jul-Sep',LY,TY),('1-12 Oct',OL,OT)):
    print(nm, 'imps %+.1f%%'%((b['im']/a['im']-1)*100), *['%s %.3f->%.3f (%+.1f%%)'%(k,a[k]*(100 if k in('ctr','ucr') else 1),b[k]*(100 if k in('ctr','ucr') else 1),(b[k]/a[k]-1)*100) for k in ('ctr','ucr','asp','gpk')])
T=20551138
print('Nov25: ctr %.3f ucr %.3f asp %.1f gpk %.2f imps %.0fM'%(N['ctr']*100,N['ucr']*100,N['asp'],N['gpk'],N['im']/1e6))
for nm,a,b in (('Nov25 flat',N,N),('Oct trend',OL,OT),('L3M trend',LY,TY)):
    f={k:b[k]/a[k] for k in ('ctr','ucr','asp')}
    ctr,ucr,asp=N['ctr']*f['ctr'],N['ucr']*f['ucr'],N['asp']*f['asp']
    gpk=ctr*ucr*asp*1000; im=T/gpk*1000
    print(f"{nm:12s} ctr {ctr*100:.2f}% ucr {ucr*100:.2f}% asp {asp:.1f} gpk {gpk:.1f} -> imps {im/1e6:.0f}M ({im/N['im']-1:+.0%}) views {im*ctr/1e6:.1f}M units {T/asp/1e3:.0f}K")
# what UCR needed to make 508M work under Oct ctr/asp trend
f_ctr=OT['ctr']/OL['ctr']; f_asp=OT['asp']/OL['asp']
need_ucr=T/(508e6*N['ctr']*f_ctr*N['asp']*f_asp)
print('UCR needed at 508M w/ Oct ctr&asp', round(need_ucr*100,2))
