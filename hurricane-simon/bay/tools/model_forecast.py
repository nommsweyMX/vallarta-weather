"""Skill-weighted model consensus for Puerto Vallarta from the latest ATCF cycle.
Usage: model_forecast.py ADECK BDECK CYCLE OUT.json
Each track model is scored on its own forecasts of this storm against the best track (mean position error at 12/24/36 h,
all cycles and the last 48 h) and on how close its 6-h forecast from the previous cycle came to the latest best-track
position. Weights are 1/error^2 on the recent score. The weighted track, its spread, the closest pass to Vallarta, the
intensity then, and the peak wind at the three sites (NHC wind radii on each model's line) are reported."""
import sys, json, math, datetime as dt
sys.path.insert(0, __import__('os').path.dirname(__file__))
from simon_phys import geo, wind
ADECK, BDECK, CYC, OUT = sys.argv[1:5]
PV = (20.6100, -105.2345)
SITES = {'amapas': (20.5984, -105.2382), 'ezapata': (20.6014, -105.2340), 'pitillal': (20.6477, -105.2087), 'pv': PV}
NAMES = {'AVNI': 'GFS', 'CEMI': 'ECMWF ensemble mean', 'CMCI': 'Canadian', 'CTCI': 'COAMPS-TC', 'GDMI': 'Google DeepMind (AI)', 'HFAI': 'HAFS-A', 'HFBI': 'HAFS-B', 'HMNI': 'HMON', 'HWFI': 'HWRF',
         'NVG2': 'NAVGEM', 'UKXI': 'UK Met Office', 'HCCA': 'Corrected consensus', 'TVCN': 'Track consensus', 'OFCI': 'NHC previous', 'OFCL': 'NHC official'}
LATE = {'AVNI': 'AVNO', 'CEMI': 'CEMN', 'CMCI': 'CMC', 'CTCI': 'CTCX', 'GDMI': 'GDMN', 'HFAI': 'HFSA', 'HFBI': 'HFSB', 'HMNI': 'HMON', 'HWFI': 'HWRF', 'NVG2': 'NVGM', 'UKXI': 'UKX', 'HCCA': 'HCCA', 'TVCN': 'TVCN', 'OFCI': 'OFCL'}
AI = {'GDMI': True}
def ll(a, b): return int(a[:-1]) / 10 * (1 if a[-1] == 'N' else -1), int(b[:-1]) / 10 * (-1 if b[-1] == 'W' else 1)
def cyc(s): return dt.datetime.strptime(s, '%Y%m%d%H')
best = {}
for line in open(BDECK):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 9 or f[4] != 'BEST': continue
    best.setdefault(cyc(f[2]), (*ll(f[6], f[7]), int(f[8])))
tb = sorted(best); now_t = tb[-1]; now_p = best[now_t]
fc = {}
for line in open(ADECK):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 9: continue
    tech, c, tau = f[4], cyc(f[2]), int(f[5]); la, lo = ll(f[6], f[7]); v = int(f[8]) if f[8] else 0
    if la == 0 and lo == 0: continue
    fc.setdefault((tech, c), {}).setdefault(tau, (la, lo, v))
# ---- skill ----
def skill(tech):
    rows = {t: [] for t in (12, 24, 36)}; rec = {t: [] for t in (12, 24, 36)}; cur = None
    for (tk, c), d in fc.items():
        if tk != tech: continue
        for tau in (12, 24, 36):
            if tau in d and c + dt.timedelta(hours=tau) in best:
                e = geo(d[tau][0], d[tau][1], *best[c + dt.timedelta(hours=tau)][:2])[0]; rows[tau].append(e)
                if c >= now_t - dt.timedelta(hours=48): rec[tau].append(e)
        # how close was this model's 6-h forecast from the previous cycle to where the storm is now?
        if c == now_t - dt.timedelta(hours=6) and 6 in d: cur = geo(d[6][0], d[6][1], now_p[0], now_p[1])[0]
    m = lambda r: sum(r) / len(r) if r else None
    allm = [m(rows[t]) for t in (12, 24, 36)]; recm = [m(rec[t]) for t in (12, 24, 36)]
    return dict(all=round(sum(allm) / 3, 1) if all(x is not None for x in allm) else None, recent=round(sum(recm) / 3, 1) if all(x is not None for x in recm) else None,
                n_recent=min(len(rec[t]) for t in (12, 24, 36)), now6=round(cur, 1) if cur is not None else None)
C = cyc(CYC)
members = [t for t in NAMES if (t, C) in fc and len(fc[(t, C)]) >= 3]
SK = {t: skill(LATE.get(t, t)) for t in members}
# ---- weights (recent skill; fall back to whole-storm; consensus aids and the previous official are shown but not weighted in) ----
W = {}
for t in members:
    if t in ('HCCA', 'TVCN', 'OFCI'): continue
    s = SK[t]['recent'] if SK[t]['recent'] is not None and SK[t]['n_recent'] >= 2 else SK[t]['all']
    if s is None: continue
    W[t] = 1.0 / (s ** 2)
tot = sum(W.values()); W = {t: w / tot for t, w in W.items()}
# ---- weighted track ----
def interp(d, h):
    ks = sorted(d)
    for a, b in zip(ks, ks[1:]):
        if a <= h <= b:
            f = (h - a) / (b - a); return tuple(d[a][i] + f * (d[b][i] - d[a][i]) for i in range(3))
    return None
taus = list(range(0, 49, 3)); cons = []
for h in taus:
    pts = [(W[t], interp(fc[(t, C)], h)) for t in W]; pts = [(w, p) for w, p in pts if p]
    if not pts: continue
    ws = sum(w for w, _ in pts); la = sum(w * p[0] for w, p in pts) / ws; lo = sum(w * p[1] for w, p in pts) / ws; v = sum(w * p[2] for w, p in pts) / ws
    spread = math.sqrt(sum(w * geo(la, lo, p[0], p[1])[0] ** 2 for w, p in pts) / ws)
    cons.append(dict(h=h, t=(C + dt.timedelta(hours=h)).strftime('%Y-%m-%dT%H:%MZ'), lat=round(la, 2), lon=round(lo, 2), kt=round(v), spread_km=round(spread), n=len(pts)))
# ---- closest pass and winds per member and for the consensus ----
# NHC radii at the same hour from the official forecast (OFCL of this cycle if present, else OFCI)
OF = fc.get(('OFCL', C)) or fc.get(('OFCI', C))
RAD = {}
for line in open(ADECK):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 17 or f[2] != CYC or f[4] not in ('OFCL', 'OFCI'): continue
    try: tau, r = int(f[5]), int(f[11]); quad = [int(f[13]), int(f[14]), int(f[15]), int(f[16])]
    except ValueError: continue
    RAD.setdefault(tau, {})[r] = quad
def radii(h):
    ks = sorted(RAD) or [0]
    k = max([x for x in ks if x <= h] or [ks[0]]); q = RAD.get(k, {})
    return {'r34': q.get(34, [60, 60, 50, 60]), 'r50': q.get(50, [30, 30, 25, 30]), 'r64': q.get(64, [15, 15, 15, 15])}
def pass_stats(track_fn, hmax):
    out = {k: dict(km=1e9) for k in SITES}; pk = {k: 0.0 for k in SITES}; onshore = None
    h = 0.0
    while h <= hmax:
        p = track_fn(h)
        if p:
            la, lo, v = p; R = radii(h); c = dict(lat=la, lon=lo, v=v, g=v * 1.22, r34=R['r34'], r50=R['r50'] if v > 50 else [0] * 4, r64=R['r64'] if v > 64 else [0] * 4)
            for k, (sla, slo) in SITES.items():
                vv, g, frm, km, brg = wind(c, sla, slo, True)
                if km < out[k]['km']: out[k] = dict(km=round(km, 1), h=h, kt=round(v), brg=round(brg))
                pk[k] = max(pk[k], vv)
            bpv = geo(PV[0], PV[1], la, lo)[1]
            if onshore is None and 290 <= bpv <= 360 and geo(PV[0], PV[1], la, lo)[0] < 250: onshore = h    # center north-west of the city: wind at the bay from the south-west
        h += 0.5
    for k in out: out[k]['t'] = (C + dt.timedelta(hours=out[k]['h'])).strftime('%Y-%m-%dT%H:%MZ'); out[k]['peak_kt'] = round(pk[k], 1)
    return out, (C + dt.timedelta(hours=onshore)).strftime('%Y-%m-%dT%H:%MZ') if onshore is not None else None
per = {}
for t in members:
    d = fc[(t, C)]; hm = max(d)
    st, on = pass_stats(lambda h, d=d: interp(d, h), min(hm, 48)); per[t] = dict(name=NAMES[t], ai=bool(AI.get(t)), weight=round(W.get(t, 0), 3), skill=SK[t], sites=st, onshore=on, hours=hm)
cd = {c['h']: (c['lat'], c['lon'], c['kt']) for c in cons}
cst_, con_on = pass_stats(lambda h: interp(cd, h), max(cd))
# weighted distribution of the closest distance to PV and the peak wind at PV
dist_w = sorted([(per[t]['sites']['pv']['km'], W[t]) for t in W]); pk_w = sorted([(per[t]['sites']['pv']['peak_kt'], W[t]) for t in W])
def wq(pairs, q):
    c = 0.0
    for x, w in pairs:
        c += w
        if c >= q: return x
    return pairs[-1][0]
summary = dict(cycle=CYC, best_now=dict(t=now_t.strftime('%Y-%m-%dT%H:%MZ'), lat=now_p[0], lon=now_p[1], kt=now_p[2]), weights={t: round(W[t], 3) for t in sorted(W, key=lambda k: -W[k])},
               consensus=cons, consensus_pass=cst_, consensus_onshore=con_on,
               pv_closest_km=dict(p25=wq(dist_w, .25), p50=wq(dist_w, .5), p75=wq(dist_w, .75), within50=round(sum(w for x, w in dist_w if x <= 50), 2), within100=round(sum(w for x, w in dist_w if x <= 100), 2)),
               pv_peak_kt=dict(p25=wq(pk_w, .25), p50=wq(pk_w, .5), p75=wq(pk_w, .75), ge34=round(sum(w for x, w in pk_w if x >= 34), 2), ge50=round(sum(w for x, w in pk_w if x >= 50), 2), ge64=round(sum(w for x, w in pk_w if x >= 64), 2)),
               members=per)
json.dump(summary, open(OUT, 'w'), separators=(',', ':'))
print('cycle', CYC, 'best now', summary['best_now'])
print('weights:', summary['weights'])
print(f"{'model':24s} {'w':>5s} {'rec':>5s} {'all':>5s} {'now6':>5s} | PV closest km  when(CST)  kt | peakPV kt | onshore(CST)")
tc = lambda s: (dt.datetime.strptime(s, '%Y-%m-%dT%H:%MZ') - dt.timedelta(hours=6)).strftime('%a %H:%M') if s else '-'
for t in sorted(per, key=lambda k: -per[k]['weight']):
    p = per[t]; s = p['skill']; q = p['sites']['pv']
    print(f"{p['name']:24s} {p['weight']:5.2f} {str(s['recent']):>5s} {str(s['all']):>5s} {str(s['now6']):>5s} | {q['km']:7.0f} {tc(q['t'])} {q['kt']:3d} | {q['peak_kt']:5.1f} | {tc(p['onshore'])}")
print('consensus track:', [(c['h'], c['lat'], c['lon'], c['kt'], c['spread_km']) for c in cons if c['h'] % 6 == 0])
print('consensus PV pass:', cst_['pv'], 'CST', tc(cst_['pv']['t']), 'onshore', tc(con_on))
print('PV closest km percentiles', summary['pv_closest_km']); print('PV peak kt percentiles', summary['pv_peak_kt'])
for k in ('amapas', 'ezapata', 'pitillal'): print(k, 'consensus', cst_[k])
