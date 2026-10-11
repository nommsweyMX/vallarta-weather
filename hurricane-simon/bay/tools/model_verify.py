"""Verify every public ATCF track model on Hurricane Simon over the last two days, from Puerto Vallarta's point of view.
Usage: model_verify.py ADECK BDECK NOW OUT.json      NOW = YYYYMMDDHH,lat,lon,kt  (latest NHC advisory position, used as the "right now" target)
For each model and each forecast cycle in the 48 h before NOW: position error (km) of the forecast at each 6-h best-track time and at NOW,
the east/north displacement of the forecast from the real storm, the lead-time means (12/24/36 h) over the window, and the wind the model's
own track + intensity implied for Puerto Vallarta (parametric field with the NHC wind radii of the same cycle), to compare with the airport record."""
import sys, json, math, datetime as dt, os
sys.path.insert(0, os.path.dirname(__file__))
from simon_phys import geo, wind
ADECK, BDECK, NOWS, OUT = sys.argv[1:5]
ns = NOWS.split(','); NOW_T = dt.datetime.strptime(ns[0], '%Y%m%d%H'); NOW_P = (float(ns[1]), float(ns[2]), int(ns[3]))
PV = (20.6100, -105.2345)
MODELS = {'OFCL': 'NHC official forecast', 'AVNO': 'GFS (US)', 'AEMN': 'GEFS ensemble mean (US)', 'CMC': 'Canadian GEM', 'UKX': 'UK Met Office', 'NVGM': 'NAVGEM (US Navy)',
          'HWRF': 'HWRF (US hurricane model)', 'HMON': 'HMON (US hurricane model)', 'HFSA': 'HAFS-A (US hurricane model)', 'HFSB': 'HAFS-B (US hurricane model)', 'CTCX': 'COAMPS-TC (US Navy)',
          'GDMN': 'Google DeepMind (AI)', 'CEMN': 'ECMWF ensemble mean', 'HCCA': 'NHC corrected consensus', 'TVCN': 'Track consensus', 'CLP5': 'Climatology + persistence (baseline)'}
AI = {'GDMN'}
def ll(a, b): return int(a[:-1]) / 10 * (1 if a[-1] == 'N' else -1), int(b[:-1]) / 10 * (-1 if b[-1] == 'W' else 1)
def cyc(s): return dt.datetime.strptime(s, '%Y%m%d%H')
def iso(t): return t.strftime('%Y-%m-%dT%H:%MZ')
best = {}
for line in open(BDECK):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 9 or f[4] != 'BEST': continue
    best.setdefault(cyc(f[2]), (*ll(f[6], f[7]), int(f[8])))
fc = {}; RAD = {}
for line in open(ADECK):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 9: continue
    tech, c, tau = f[4], cyc(f[2]), int(f[5]); la, lo = ll(f[6], f[7]); v = int(f[8]) if f[8] else 0
    if la == 0 and lo == 0: continue
    fc.setdefault((tech, c), {}).setdefault(tau, (la, lo, v))
    if tech == 'OFCL' and len(f) >= 17:
        try: RAD.setdefault(c, {}).setdefault(tau, {})[int(f[11])] = [int(f[13]), int(f[14]), int(f[15]), int(f[16])]
        except ValueError: pass
W0 = NOW_T - dt.timedelta(hours=48)
# verification targets: best-track synoptic times inside the window, plus NOW (advisory position)
targets = {t: best[t] for t in sorted(best) if W0 <= t <= NOW_T}
targets[NOW_T] = NOW_P
def interp(d, h):
    ks = sorted(d)
    if h in d: return d[h]
    for a, b in zip(ks, ks[1:]):
        if a < h < b:
            f = (h - a) / (b - a); return tuple(d[a][i] + f * (d[b][i] - d[a][i]) for i in range(3))
    return None
def disp(p, q):    # east/north displacement (km) of forecast p from truth q, and distance
    de = (p[1] - q[1]) * 111.32 * math.cos(math.radians(q[0])); dn = (p[0] - q[0]) * 110.57
    return round(math.hypot(de, dn)), round(de), round(dn)
def radii(c, h):
    R = RAD.get(c) or RAD.get(max([k for k in RAD if k <= c] or [min(RAD)]))
    ks = sorted(R); k = max([x for x in ks if x <= h] or [ks[0]]); q = R.get(k, {})
    return {'r34': q.get(34, [60, 60, 50, 60]), 'r50': q.get(50, [30, 30, 25, 30]), 'r64': q.get(64, [15, 15, 15, 15])}
def pv_implied(d, c, until):
    """max parametric wind at PV (kt, sustained over open water, before exposure) along this forecast up to time 'until'"""
    if max(p[2] for p in d.values()) == 0: return None, None    # track-only aid (no intensity)
    pk = 0.0; at_now = None; h = 0.0; hmax = min(max(d), (until - c).total_seconds() / 3600)
    while h <= hmax + 1e-6:
        p = interp(d, h)
        if p:
            R = radii(c, h); cc = dict(lat=p[0], lon=p[1], v=p[2], g=p[2] * 1.22, r34=R['r34'], r50=R['r50'] if p[2] > 50 else [0] * 4, r64=R['r64'] if p[2] > 64 else [0] * 4)
            vv = wind(cc, PV[0], PV[1], True)[0]; pk = max(pk, vv)
            if abs(h - hmax) < 0.5: at_now = vv
        h += 1.0
    return round(pk, 1), (round(at_now, 1) if at_now is not None else None)
cycles = sorted({c for (t, c) in fc if W0 <= c <= NOW_T})
out = {}
for tech, name in MODELS.items():
    recs = []; pvw = {}
    for c in cycles:
        d = fc.get((tech, c))
        if not d or len(d) < 3: continue
        for v, q in targets.items():
            lead = (v - c).total_seconds() / 3600
            if lead <= 0 or lead > 48: continue
            p = interp(d, lead)
            if not p: continue
            err, de, dn = disp(p, q)
            recs.append(dict(c=iso(c), v=iso(v), lead=round(lead), err=err, de=de, dn=dn, fkt=round(p[2]), lat=round(p[0], 2), lon=round(p[1], 2)))
        pvw[iso(c)] = pv_implied(d, c, NOW_T)
    if not recs: continue
    def mean_at(L): r = [x['err'] for x in recs if abs(x['lead'] - L) <= 3 and x['v'] != iso(NOW_T)]; return (round(sum(r) / len(r)), len(r)) if r else (None, 0)
    m12, n12 = mean_at(12); m24, n24 = mean_at(24); m36, n36 = mean_at(36)
    ms = [m for m in (m12, m24, m36) if m is not None]
    nowr = {x['c']: x for x in recs if x['v'] == iso(NOW_T)}
    b24 = [x for x in recs if abs(x['lead'] - 24) <= 3 and x['v'] != iso(NOW_T)]
    out[tech] = dict(name=name, ai=tech in AI, cycles=sorted(nowr), n_cycles=len({x['c'] for x in recs}),
                     now={c: dict(err=x['err'], de=x['de'], dn=x['dn'], lead=x['lead'], fkt=x['fkt'], lat=x['lat'], lon=x['lon']) for c, x in nowr.items()},
                     mean=dict(h12=m12, h24=m24, h36=m36, n=min(n12, n24, n36), score=round(sum(ms) / len(ms)) if ms else None),
                     bias24=dict(de=round(sum(x['de'] for x in b24) / len(b24)), dn=round(sum(x['dn'] for x in b24) / len(b24))) if b24 else None,
                     pv_implied_kt={c: dict(max=w[0], now=w[1]) for c, w in pvw.items()}, recs=recs)
# ensembles in the deck: GEFS members AP01-AP30 (+AC00 control) -> error distribution at NOW per cycle
ens = {}
for c in cycles:
    errs = []
    for m in ['AC%02d' % 0] + ['AP%02d' % i for i in range(1, 31)]:
        d = fc.get((m, c))
        if not d: continue
        lead = (NOW_T - c).total_seconds() / 3600
        if lead > 48 or lead <= 0: continue
        p = interp(d, lead)
        if p: errs.append(disp(p, NOW_P))
    if len(errs) >= 10:
        errs.sort(); ds = [e[0] for e in errs]
        ens[iso(c)] = dict(n=len(errs), lead=round((NOW_T - c).total_seconds() / 3600), median_err=ds[len(ds) // 2], min_err=ds[0], max_err=ds[-1], within100=sum(1 for e in ds if e <= 100),
                          mean_de=round(sum(e[1] for e in errs) / len(errs)), mean_dn=round(sum(e[2] for e in errs) / len(errs)), members=[list(e) for e in errs])
res = dict(now=dict(t=iso(NOW_T), lat=NOW_P[0], lon=NOW_P[1], kt=NOW_P[2]), window_start=iso(W0), best=[dict(t=iso(t), lat=p[0], lon=p[1], kt=p[2]) for t, p in sorted(best.items()) if t >= W0 - dt.timedelta(hours=24)],
           cycles=[iso(c) for c in cycles], models=out, gefs_members=ens)
json.dump(res, open(OUT, 'w'), separators=(',', ':'))
print('NOW', res['now'], 'window from', iso(W0)); print('cycles', res['cycles'])
print(f"{'model':34s} {'score':>5s} {'h12':>5s} {'h24':>5s} {'h36':>5s} n | now-err by cycle (km, lead h) | bias24 E/N km | PV implied max kt by cycle")
for t, m in sorted(out.items(), key=lambda kv: (kv[1]['mean']['score'] is None, kv[1]['mean']['score'] or 0)):
    mm = m['mean']; nw = ' '.join(f"{c[5:13]}:{x['err']}({x['lead']})" for c, x in sorted(m['now'].items()))
    pv = ' '.join(f"{c[8:13]}:{w['max']}" for c, w in sorted(m['pv_implied_kt'].items()))
    print(f"{m['name']:34s} {str(mm['score']):>5s} {str(mm['h12']):>5s} {str(mm['h24']):>5s} {str(mm['h36']):>5s} {mm['n']} | {nw} | {m['bias24']} | {pv}")
for c, e in ens.items(): print('GEFS members', c, {k: v for k, v in e.items() if k != 'members'})
