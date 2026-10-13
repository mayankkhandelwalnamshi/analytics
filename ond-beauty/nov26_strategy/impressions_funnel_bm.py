# Impressions needed, retail vs MP. Nov '26 funnel = Nov '25 actual x (70% x Jul-Oct TY/LY trend + 30% x no change).
D={'retail':{'nov25':(15207743,285397,369416421,8824327),
             'ly':(24178847+3066696,286742+34956,534067098+63536737,13288335+1575476),
             'ty':(15321377+2717025,169851+27882,430128724+60372876,10820212+1591826)},
   'mp':{'nov25':(1233276,20502,37137031,743500),
         'ly':(2969933+323846,37353+4303,68650214+7354890,1833756+168105),
         'ty':(3457075+430987,55421+6606,100426555+12666358,2172253+259196)}}
T=20551138; TGT={'retail':T*0.90,'mp':T*0.10}; W=0.7
def f(t): g,u,im,gv=t; return dict(ctr=gv/im,ucr=u/gv,asp=g/u,gpk=g/im*1000,im=im)
tot=0; tot_lvl=0
for bm in ('retail','mp'):
    N,A,B=f(D[bm]['nov25']),f(D[bm]['ly']),f(D[bm]['ty'])
    r={k:B[k]/A[k] for k in ('ctr','ucr','asp')}; w={k:W*r[k]+(1-W) for k in r}
    ctr,ucr,asp=N['ctr']*w['ctr'],N['ucr']*w['ucr'],N['asp']*w['asp']; gpk=ctr*ucr*asp*1000; im=TGT[bm]/gpk*1000; tot+=im
    lvl=W*B['gpk']+(1-W)*N['gpk']; im_l=TGT[bm]/lvl*1000; tot_lvl+=im_l
    print(f"{bm.upper():6s} Jul-Oct TY vs LY: imps {B['im']/A['im']-1:+.0%} ctr {r['ctr']-1:+.1%} ucr {r['ucr']-1:+.1%} asp {r['asp']-1:+.1%} gpk {B['gpk']/A['gpk']-1:+.1%}")
    print(f"       weighted adj: ctr {w['ctr']-1:+.1%} ucr {w['ucr']-1:+.1%} asp {w['asp']-1:+.1%} -> Nov26 ctr {ctr*100:.2f}% ucr {ucr*100:.2f}% asp {asp:.1f} gpk {gpk:.1f} (Nov25 {N['gpk']:.1f})")
    print(f"       target {TGT[bm]/1e6:.2f}M -> imps {im/1e6:.0f}M ({im/N['im']-1:+.0%} vs LY {N['im']/1e6:.0f}M) | level-blend gpk {lvl:.1f} -> {im_l/1e6:.0f}M")
print(f"TOTAL imps {tot/1e6:.0f}M ({tot/406544422-1:+.0%}) blended gpk {T/tot*1000:.1f} | level-blend total {tot_lvl/1e6:.0f}M")
