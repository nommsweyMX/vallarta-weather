import sys, json, math, datetime as dt
S=sys.argv[1]; H='/home/user/vallarta-weather/hurricane-simon'; PV=(20.61,-105.2345)
def geo(a,b,c,d):
    R=6371; p1,p2=math.radians(a),math.radians(c); dl=math.radians(d-b); x=math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*R*math.asin(math.sqrt(x))
def ll(a,b): return int(a[:-1])/10*(1 if a[-1]=='N' else -1), int(b[:-1])/10*(-1 if b[-1]=='W' else 1)
h=json.load(open(H+'/forecast/data/history.json'))['advisories']
def ptime(s, base):
    d,hm=s.split('/'); hh=int(hm[:2]); dd=int(d); m=base.month if dd>=base.day-1 else base.month+1; return dt.datetime(2026, m, dd, hh)
trend=[]
for a in h:
    iss=dt.datetime.strptime(a['issued'].title()+' 2026', '%b %d %H%MZ %Y'); pts=[]
    for p in a['track']:
        try: t=ptime(p[0], iss)
        except Exception: continue
        if p[1] and p[2]: pts.append((t, p[1], p[2], p[3]))
    pts.sort(); best=None
    for (t0,la0,lo0,v0),(t1,la1,lo1,v1) in zip(pts, pts[1:]):
        n=max(1,int((t1-t0).total_seconds()/3600))
        for i in range(n+1):
            f=i/n; la=la0+f*(la1-la0); lo=lo0+f*(lo1-lo0); v=v0+f*(v1-v0); d=geo(la,lo,*PV)
            if best is None or d<best[0]: best=(d, t0+(t1-t0)*i/n, v, la, lo)
    trend.append(dict(num=a['num'], issued=iss.strftime('%Y-%m-%dT%H:%MZ'), cpa_km=round(best[0]) if best else None, cpa_t=best[1].strftime('%Y-%m-%dT%H:%MZ') if best else None, cpa_kt=round(best[2]) if best else None, pv=a['pv'], n_pts=len(pts), init=list(pts[0][1:4]) if pts else None, track=[[t.strftime('%Y-%m-%dT%H:%MZ'),la,lo,v] for t,la,lo,v in pts]))
best={}
for line in open(S+'/atcf3/bep.dat'):
    f=[x.strip() for x in line.split(',')]
    if len(f)<9 or f[4]!='BEST': continue
    t=dt.datetime.strptime(f[2],'%Y%m%d%H'); best.setdefault(t,(*ll(f[6],f[7]),int(f[8])))
rows=[(t,la,lo,v,round(geo(la,lo,*PV))) for t,(la,lo,v) in sorted(best.items())]
cpa=None
for (t0,la0,lo0,v0,_),(t1,la1,lo1,v1,_) in zip(rows,rows[1:]):
    for i in range(7):
        f=i/6; la=la0+f*(la1-la0); lo=lo0+f*(lo1-lo0); d=geo(la,lo,*PV)
        if cpa is None or d<cpa[0]: cpa=(round(d), (t0+(t1-t0)*f).strftime('%Y-%m-%dT%H:%MZ'), round(v0+f*(v1-v0)))
snaps={}
for k in ('17a','17b','18','20'):
    src = f'{S}/hist/{k}/bay.json' if k != '20' else H+'/bay/data/bay.json'
    b=json.load(open(src)); snaps[k]=dict(num=b['advisory']['num'], t_obs=b['t_obs'], rain_cal=b.get('rain_cal'), sites={s['id']:dict(peak_vb=s['wind']['peak_vb_kmh'], peak_gb=s['wind']['peak_gb_kmh'], peak_t=s['wind']['peak_t'], rain=s.get('rain')) for s in b['sites']}, probs=b['wind_cal']['probs'], v50=b['wind_cal'].get('v50_kt'))
json.dump(dict(trend=trend, snaps=snaps, best=[[r[0].strftime('%Y-%m-%dT%H:%MZ'),r[1],r[2],r[3],r[4]] for r in rows], actual_cpa=dict(km=cpa[0], t=cpa[1], kt=cpa[2])), open(S+'/report/trend.json','w'))
print('advisories', len(trend), 'last', trend[-1]['num'], trend[-1]['cpa_km'], 'actual cpa', cpa, 'snaps', {k:(v['num'], v['sites']['amapas']['peak_gb']) for k,v in snaps.items()})
# refresh pv_hist in data.json for the odds chart
D=json.load(open(S+'/report/data.json')); D['pv_hist']=[(a['num'],a['issued'],a['pv']) for a in h]; D['best']=[[r[0].strftime('%Y-%m-%dT%H:%MZ'),r[1],r[2],r[3],None] for r in rows]; json.dump(D, open(S+'/report/data.json','w')); print('data.json pv_hist', len(D['pv_hist']))
