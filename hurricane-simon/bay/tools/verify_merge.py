"""Merge the ATCF verification with the gridded / AI-model extractions into one scored table for the verification graphic.
Usage: verify_merge.py VERIFY_ATCF.json CONSENSUS.json OUT.json [ecmwf_out.json] [noaa_out.json] [mlwp_out.json]
Every model is scored the same way: position error against the official (best-track) positions at 6-h times inside the last 48 h and
against the latest advisory position (NOW); the Puerto Vallarta wind and rain each model's run of ~24 h ago gave for the period up to NOW."""
import sys, json, math, datetime as dt, os
VA, CONS, OUT = sys.argv[1:4]; EXTRA = sys.argv[4:]
A = json.load(open(VA)); CS = json.load(open(CONS))
def P(s): return dt.datetime.strptime(s, '%Y-%m-%dT%H:%MZ')
def iso(t): return t.strftime('%Y-%m-%dT%H:%MZ')
NOW_T = P(A['now']['t']); NOW = (A['now']['lat'], A['now']['lon']); W0 = P(A['window_start'])
best = {P(b['t']): (b['lat'], b['lon']) for b in A['best']}
targets = {t: p for t, p in best.items() if W0 <= t <= NOW_T}; targets[NOW_T] = NOW
REF = NOW_T.replace(hour=0, minute=0)                      # the run of "yesterday evening" (00Z = 6 pm CST the day before) used for the dartboard and the PV columns
REF_ALT = REF - dt.timedelta(hours=12)
OBS = dict(wind_max_kt=9, wind_note=['viento máx. 17 km/h en los reportes del aeropuerto (METAR, 48 h; sin reportes entre el sáb 18:00 y el dom 13:00)', 'max wind 9 kt (10 mph) in the airport reports (METAR, 48 h; none between Sat 6 pm and Sun 1 pm)'],
           rain_mm_lo=0, rain_mm_hi=9, rain_note=['~9 mm en el aeropuerto hasta las 13:44 (un chubasco); en la ciudad, nada según los vecinos', '~0.35 in at the airport by 1:44 pm (one shower); none in town by residents’ reports'])
def disp(p, q):
    de = (p[1] - q[1]) * 111.32 * math.cos(math.radians(q[0])); dn = (p[0] - q[0]) * 110.57
    return round(math.hypot(de, dn)), round(de), round(dn)
def score_track(runs):
    """runs: {cycle_iso: [(h, lat, lon), ...]} -> same metrics as the ATCF script"""
    recs = []
    for c, pts in runs.items():
        ct = P(c)
        if not (W0 <= ct <= NOW_T) or len(pts) < 2: continue
        pts = sorted(pts)
        for v, q in targets.items():
            lead = (v - ct).total_seconds() / 3600
            if lead <= 0 or lead > 48: continue
            p = None
            for a, b in zip(pts, pts[1:]):
                if a[0] <= lead <= b[0]:
                    f = (lead - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0; p = (a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])); break
            if not p: continue
            err, de, dn = disp(p, q); recs.append(dict(c=c, v=iso(v), lead=round(lead), err=err, de=de, dn=dn, lat=round(p[0], 2), lon=round(p[1], 2)))
    if not recs: return None
    def mean_at(L): r = [x['err'] for x in recs if abs(x['lead'] - L) <= 3 and x['v'] != iso(NOW_T)]; return (round(sum(r) / len(r)), len(r)) if r else (None, 0)
    m = {L: mean_at(L) for L in (12, 24, 36)}; ms = [m[L][0] for L in m if m[L][0] is not None]
    nowr = {x['c']: x for x in recs if x['v'] == iso(NOW_T)}
    return dict(mean=dict(h12=m[12][0], h24=m[24][0], h36=m[36][0], n=min(m[L][1] for L in m), score=round(sum(ms) / len(ms)) if ms else None), now={c: dict(err=x['err'], de=x['de'], dn=x['dn'], lead=x['lead'], lat=x['lat'], lon=x['lon']) for c, x in nowr.items()}, n_cycles=len({x['c'] for x in recs}))
def ref_run(runs):
    for c in (iso(REF), iso(REF_ALT)):
        if c in runs: return c
    return None
def pv_from_grid(run, c):
    """max 10-m wind and accumulated rain at PV for times <= NOW, from one run's pv series"""
    pv = run.get('pv') or []; ct = P(c); seq = [p for p in pv if P(p['t'].replace(':00Z', 'Z') if p['t'].count(':') > 1 else p['t']) <= NOW_T]
    if not seq: return None
    mx = max(p.get('wind_kt') or 0 for p in seq); g = max((p.get('gust_kt') or 0) for p in seq) or None
    last = seq[-1]; rain = last.get('precip_mm'); rainb = last.get('precip_mm_box')
    return dict(wind_max_kt=round(mx, 1), gust_max_kt=round(g, 1) if g else None, rain_mm=None if rain is None else round(rain, 1), rain_mm_box=None if rainb is None else round(rainb, 1), to=last['t'], hours=round((P(last['t']) - ct).total_seconds() / 3600))
def pv_next(run, c, h0, h1):
    """for the latest run: max wind in [h0,h1] h and rain accumulated between h0 and h1 at PV"""
    pv = run.get('pv') or []
    if not pv: return None
    seg = [p for p in pv if h0 <= p['h'] <= h1]
    if len(seg) < 2: return None
    r0 = [p for p in pv if p['h'] <= h0]; r0 = r0[-1] if r0 else seg[0]
    rain = None if seg[-1].get('precip_mm') is None or r0.get('precip_mm') is None else round(seg[-1]['precip_mm'] - r0['precip_mm'], 1)
    return dict(wind_max_kt=round(max(p.get('wind_kt') or 0 for p in seg), 1), rain_mm=rain, run=c)
KIND_COL = {'nhc': '#ffffff', 'ai': '#ff8ad0', 'dyn': '#7fb5ff', 'ens': '#5ff0b4', 'cons': '#ffd166', 'base': '#7d8794', 'blend': '#c9b27c'}
ATCF = {'OFCL': (['NHC (pronóstico oficial)', 'NHC (official forecast)'], 'nhc'), 'GDMN': (['Google DeepMind · ciclones · IA', 'Google DeepMind · cyclone model · AI'], 'ai'), 'HCCA': (['Consenso corregido (NHC)', 'Corrected consensus (NHC)'], 'cons'),
        'TVCN': (['Consenso de trayectoria', 'Track consensus'], 'cons'), 'CLP5': (['Climatología + persistencia', 'Climatology + persistence'], 'base'), 'CEMN': (['ECMWF ensamble · media', 'ECMWF ensemble mean'], 'ens'),
        'AEMN': (['GEFS ensamble · media (EE. UU.)', 'GEFS ensemble mean (US)'], 'ens'), 'AVNO': (['GFS (EE. UU.)', 'GFS (US)'], 'dyn'), 'CMC': (['GEM (Canadá)', 'GEM (Canada)'], 'dyn'), 'UKX': (['UKMET (Reino Unido)', 'UKMET (UK)'], 'dyn'),
        'NVGM': (['NAVGEM (Marina EE. UU.)', 'NAVGEM (US Navy)'], 'dyn'), 'HWRF': (['HWRF (huracanes, EE. UU.)', 'HWRF (US hurricane model)'], 'dyn'), 'HMON': (['HMON (huracanes, EE. UU.)', 'HMON (US hurricane model)'], 'dyn'),
        'HFSA': (['HAFS-A (huracanes, EE. UU.)', 'HAFS-A (US hurricane model)'], 'dyn'), 'HFSB': (['HAFS-B (huracanes, EE. UU.)', 'HAFS-B (US hurricane model)'], 'dyn'), 'CTCX': (['COAMPS-TC (Marina EE. UU.)', 'COAMPS-TC (US Navy)'], 'dyn')}
GRID = {'ifs_oper': (['ECMWF IFS (Europa)', 'ECMWF IFS (Europe)'], 'dyn'), 'aifs_single': (['ECMWF AIFS · IA', 'ECMWF AIFS · AI'], 'ai'), 'aifs_ens': (['ECMWF AIFS ensamble · IA', 'ECMWF AIFS ensemble · AI'], 'ai'),
        'aigfs': (['AIGFS (NOAA) · IA', 'AIGFS (NOAA) · AI'], 'ai'), 'nbm': (['NBM · Mezcla nacional de modelos (EE. UU.)', 'NBM · National Blend of Models (US)'], 'blend'), 'hafs_a': (['HAFS-A (huracanes, EE. UU.)', 'HAFS-A (US hurricane model)'], 'dyn'),
        'fourcastnet': (['FourCastNet (NVIDIA) · IA', 'FourCastNet (NVIDIA) · AI'], 'ai'), 'pangu': (['Pangu-Weather (Huawei) · IA', 'Pangu-Weather (Huawei) · AI'], 'ai'), 'graphcast': (['GraphCast (Google DeepMind) · IA', 'GraphCast (Google DeepMind) · AI'], 'ai'), 'aurora': (['Aurora (Microsoft) · IA', 'Aurora (Microsoft) · AI'], 'ai'),
        'gfs': None, 'gefs_mean': None}          # gfs/gefs grids feed the AVNO/AEMN rows (PV wind and rain); positions come from the deck
GRID_TO_ATCF = {'gfs': 'AVNO', 'gefs_mean': 'AEMN', 'hafs_a': 'HFSA'}
rows = {}
for k, (nm, kind) in ATCF.items():
    m = A['models'].get(k)
    if not m: continue
    rc = ref_run(m['now']) or ref_run({c: 1 for c in m['pv_implied_kt']})
    pvw = m['pv_implied_kt'].get(rc) if rc else None
    rows[k] = dict(key=k, name=nm, kind=kind, color=KIND_COL[kind], score=m['mean']['score'], n=m['mean']['n'], h12=m['mean']['h12'], h24=m['mean']['h24'], h36=m['mean']['h36'], bias24=m['bias24'], now=m['now'], ref=rc,
                   pv=dict(wind_max_kt=pvw['max'] if pvw and pvw['max'] is not None else None, wind_src=('radii' if pvw and pvw.get('radii') == 'own' else 'track'), rain_mm=None, rain_src=None), src='ATCF')
members = {}
if 'gefs_members' in A:
    g = A['gefs_members'].get(iso(REF)) or A['gefs_members'].get(iso(REF_ALT))
    if g: members['gefs'] = dict(name=['GEFS', 'GEFS'], cycle=iso(REF) if iso(REF) in A['gefs_members'] else iso(REF_ALT), n=g['n'], within100=g['within100'], median_err=g['median_err'], pos=[[round(NOW[0] + e[2] / 110.57, 2), round(NOW[1] + e[1] / (111.32 * math.cos(math.radians(NOW[0]))), 2)] for e in g['members']])
def add_grid(key, d):
    spec = GRID.get(key, False)
    if spec is False or not isinstance(d, dict) or 'runs' not in d: return
    runs = d['runs']
    trk = {c: [(p['h'], p['lat'], p['lon']) for p in (r.get('track') or r.get('mean_track') or []) if not p.get('on_box_edge')] for c, r in runs.items()}
    trk = {iso(dt.datetime.strptime(c, '%Y%m%d%H')): v for c, v in trk.items() if v}
    st = score_track(trk) if trk else None
    rc = None
    for c in (REF, REF_ALT):
        if c.strftime('%Y%m%d%H') in runs: rc = c.strftime('%Y%m%d%H'); break
    pvv = pv_from_grid(runs[rc], iso(dt.datetime.strptime(rc, '%Y%m%d%H'))) if rc and runs[rc].get('pv') else None
    latest = max(runs); nxt = pv_next(runs[latest], latest, (NOW_T - dt.datetime.strptime(latest, '%Y%m%d%H')).total_seconds() / 3600, (NOW_T - dt.datetime.strptime(latest, '%Y%m%d%H')).total_seconds() / 3600 + 24) if runs[latest].get('pv') else None
    tgt = GRID_TO_ATCF.get(key)
    if tgt and tgt in rows:
        r = rows[tgt]
        if pvv: r['pv'] = dict(wind_max_kt=pvv['wind_max_kt'], gust_max_kt=pvv['gust_max_kt'], wind_src='grid', rain_mm=pvv['rain_mm'], rain_mm_box=pvv['rain_mm_box'], rain_src='grid', hours=pvv['hours'], run=rc)
        if nxt: r['next'] = nxt
        return
    nm, kind = spec
    rows[key] = dict(key=key, name=nm, kind=kind, color=KIND_COL[kind], score=st['mean']['score'] if st else None, n=st['mean']['n'] if st else 0, h12=st['mean']['h12'] if st else None, h24=st['mean']['h24'] if st else None, h36=st['mean']['h36'] if st else None,
                     bias24=None, now=st['now'] if st else {}, ref=iso(dt.datetime.strptime(rc, '%Y%m%d%H')) if rc else None,
                     pv=dict(wind_max_kt=pvv['wind_max_kt'] if pvv else None, gust_max_kt=pvv['gust_max_kt'] if pvv else None, wind_src='grid' if pvv else None, rain_mm=pvv['rain_mm'] if pvv else None, rain_mm_box=pvv['rain_mm_box'] if pvv else None, rain_src='grid' if pvv and pvv['rain_mm'] is not None else None, hours=pvv['hours'] if pvv else None, run=rc),
                     next=nxt, src=d.get('name', key), notes=d.get('notes'))
    # ensemble member cloud at NOW from the reference run
    if 'members' in (runs.get(rc) or {}):
        pos = []; errs = []
        for mid, tr in runs[rc]['members'].items():
            pts = sorted((p['h'], p['lat'], p['lon']) for p in tr); lead = (NOW_T - dt.datetime.strptime(rc, '%Y%m%d%H')).total_seconds() / 3600
            for a, b in zip(pts, pts[1:]):
                if a[0] <= lead <= b[0]:
                    f = (lead - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0; p = (a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])); pos.append([round(p[0], 2), round(p[1], 2)]); errs.append(disp(p, NOW)[0]); break
        if errs: errs.sort(); members[key] = dict(name=nm, cycle=iso(dt.datetime.strptime(rc, '%Y%m%d%H')), n=len(errs), within100=sum(1 for e in errs if e <= 100), median_err=errs[len(errs) // 2], pos=pos)
for f in EXTRA:
    if not os.path.exists(f): print('missing', f); continue
    d = json.load(open(f))
    for key, v in d.items():
        if key == 'failures': continue
        add_grid(key, v)
# "next" for ATCF rows from the consensus file (latest early cycle): closest pass and parametric peak wind at PV
L2E = {'GDMI': 'GDMN', 'HFAI': 'HFSA', 'HFBI': 'HFSB', 'HWFI': 'HWRF', 'HMNI': 'HMON', 'AVNI': 'AVNO', 'CMCI': 'CMC', 'UKXI': 'UKX', 'NVG2': 'NVGM', 'CTCI': 'CTCX', 'CEMI': 'CEMN', 'AEMI': 'AEMN', 'OFCL': 'OFCL', 'HCCA': 'HCCA', 'TVCN': 'TVCN'}
for e, m in CS['members'].items():
    k = L2E.get(e)
    if k in rows:
        rows[k].setdefault('next', {}); rows[k]['next'].update(dict(closest_km=m['sites']['pv']['km'], closest_t=m['sites']['pv']['t'], center_kt=m['sites']['pv']['kt'], brg=m['sites']['pv']['brg'], peak_kt_track=m['sites']['pv']['peak_kt'], onshore=m['onshore'], cycle=CS['cycle']))
order = sorted(rows.values(), key=lambda r: (r['score'] is None, r['score'] if r['score'] is not None else 0, r['key']))
res = dict(now=A['now'], window_start=A['window_start'], ref_cycle=iso(REF), best=A['best'], obs=OBS, models=order, members=members, consensus=dict(cycle=CS['cycle'], pv_closest=CS['pv_closest_km'], pv_peak=CS['pv_peak_kt'], pass_=CS['consensus_pass']['pv'], onshore=CS['consensus_onshore']))
json.dump(res, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False)
print(f"{'model':38s} {'kind':5s} {'score':>5s} {'n':>2s} | now@ref err/E/N | PVwind src | PVrain | next")
for r in order:
    nw = r['now'].get(r['ref'] or '', {}); nx = r.get('next') or {}
    print(f"{r['name'][1]:38s} {r['kind']:5s} {str(r['score']):>5s} {r['n']:>2d} | {str(nw.get('err')):>4s} {str(nw.get('de')):>5s} {str(nw.get('dn')):>5s} | {str(r['pv'].get('wind_max_kt')):>5s} {str(r['pv'].get('wind_src')):5s} | {str(r['pv'].get('rain_mm')):>6s} | {nx.get('closest_km')} {nx.get('peak_kt_track')} {nx.get('wind_max_kt')} {nx.get('rain_mm')}")
for k, m in members.items(): print('members', k, m['cycle'], m['n'], 'within100', m['within100'], 'median', m['median_err'])
