"""How well each model has forecast Simon so far, and what each one says now for the three sites.
Usage: model_skill.py ADECK BDECK FORECAST.json MAP.json OUT.json
Skill: every past forecast of each model (ATCF A-deck, all cycles) is checked against the best track (B-deck) at 12, 24, 36
and 48 h: mean position error (km) and mean absolute intensity error (kt), over all cycles and over the last two days.
Now: for each model's current forecast (interpolated 'early' version, as the NHC uses it), the closest pass to each site,
the strength then, and the peak sustained wind at the site if the center followed that model's line, using the NHC's current
wind radii (the 50- and 64-kt radii dropped once the model weakens the storm below them). Not capped by the NHC odds."""
import sys, json, math, datetime as dt
sys.path.insert(0, __import__('os').path.dirname(__file__))
from simon_phys import geo, wind, KMH

ADECK, BDECK, FJ, MJ, OUT = sys.argv[1:6]
FC = json.load(open(FJ)); MP = json.load(open(MJ))
NAMES = {'OFCL': ['NHC (oficial)', 'NHC (official)'], 'AVNO': ['GFS (EE. UU.)', 'GFS (US)'], 'HWRF': ['HWRF', 'HWRF'], 'HFSA': ['HAFS-A', 'HAFS-A'],
         'HFSB': ['HAFS-B', 'HAFS-B'], 'HMON': ['HMON', 'HMON'], 'GDMN': ['Google DeepMind', 'Google DeepMind'], 'CMC': ['Canadiense', 'Canadian'],
         'NVGM': ['NAVGEM (Marina EE. UU.)', 'NAVGEM (US Navy)'], 'UKX': ['UK Met Office', 'UK Met Office'], 'CTCX': ['COAMPS-TC', 'COAMPS-TC'],
         'TVCN': ['Consenso de trayectoria', 'Track consensus'], 'HCCA': ['Consenso corregido', 'Corrected consensus'],
         'DSHP': ['SHIPS (intensidad)', 'SHIPS (intensity)'], 'LGEM': ['LGEM (intensidad)', 'LGEM (intensity)'], 'IVCN': ['Consenso de intensidad', 'Intensity consensus']}
EARLY = {'HFAI': 'HFSA', 'HFBI': 'HFSB', 'HWFI': 'HWRF', 'HMNI': 'HMON', 'AVNI': 'AVNO', 'CMCI': 'CMC', 'UKXI': 'UKX', 'NVGI': 'NVGM', 'GDMI': 'GDMN', 'CTCI': 'CTCX', 'CMC2': 'CMC', 'UKX2': 'UKX', 'NVG2': 'NVGM', 'HWF2': 'HWRF', 'HMN2': 'HMON', 'AVN2': 'AVNO', 'GDM2': 'GDMN', 'CTC2': 'CTCX', 'HFA2': 'HFSA', 'HFB2': 'HFSB', 'EGRI': 'EGRR', 'EGR2': 'EGRR'}
TAUS = (12, 24, 36, 48)
def ll(a, b):
    la = int(a[:-1]) / 10 * (1 if a[-1] == 'N' else -1); lo = int(b[:-1]) / 10 * (-1 if b[-1] == 'W' else 1); return la, lo
def cyc(s): return dt.datetime.strptime(s, '%Y%m%d%H')

best = {}
for line in open(BDECK):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 9 or f[4] != 'BEST': continue
    t = cyc(f[2]); la, lo = ll(f[6], f[7]); best.setdefault(t, (la, lo, int(f[8])))
tb = sorted(best); print('best track', tb[0], '->', tb[-1], len(tb), 'points')

fc = {}                                                                  # (tech, cycle) -> {tau: (lat, lon, vmax)}
for line in open(ADECK):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 9 or f[4] not in NAMES: continue
    key = (f[4], cyc(f[2])); tau = int(f[5])
    if tau not in TAUS and tau != 0: continue
    la, lo = ll(f[6], f[7]); v = int(f[8]) if f[8] else 0
    fc.setdefault(key, {}).setdefault(tau, (la, lo, v))

skill = {}
recent_from = tb[-1] - dt.timedelta(hours=48)
for tech in NAMES:
    rows = {tau: dict(trk=[], trk_r=[], it=[], it_r=[], bias=[], bias_r=[]) for tau in TAUS}; n_cycles = set()
    for (tk, c), d in fc.items():
        if tk != tech: continue
        for tau in TAUS:
            if tau not in d: continue
            vt = c + dt.timedelta(hours=tau)
            if vt not in best: continue
            la, lo, v = d[tau]; bla, blo, bv = best[vt]
            n_cycles.add(c); rec = c >= recent_from
            if la != 0 or lo != 0:
                e = geo(la, lo, bla, blo)[0]; rows[tau]['trk'].append(e); rec and rows[tau]['trk_r'].append(e)
            if v:
                ie = v - bv; rows[tau]['it'].append(abs(ie)); rows[tau]['bias'].append(ie)
                rec and (rows[tau]['it_r'].append(abs(ie)), rows[tau]['bias_r'].append(ie))
    m = lambda a: round(sum(a) / len(a), 1) if a else None
    skill[tech] = dict(name=NAMES[tech], n=len(n_cycles),
                       taus={str(tau): dict(trk=m(r['trk']), trk_recent=m(r['trk_r']), n_trk=len(r['trk']), n_trk_recent=len(r['trk_r']),
                                            int=m(r['it']), int_recent=m(r['it_r']), bias=m(r['bias']), bias_recent=m(r['bias_r']), n_int=len(r['it'])) for tau, r in rows.items()})
# one ranking number: mean of the 12/24/36-h position errors (all cycles); intensity: mean abs error at 12/24/36 h
for tech, s in skill.items():
    t3 = [s['taus'][str(h)]['trk'] for h in (12, 24, 36) if s['taus'][str(h)]['trk'] is not None]
    i3 = [s['taus'][str(h)]['int'] for h in (12, 24, 36) if s['taus'][str(h)]['int'] is not None]
    t3r = [s['taus'][str(h)]['trk_recent'] for h in (12, 24, 36) if s['taus'][str(h)]['trk_recent'] is not None]
    i3r = [s['taus'][str(h)]['int_recent'] for h in (12, 24, 36) if s['taus'][str(h)]['int_recent'] is not None]
    s['trk_score'] = round(sum(t3) / len(t3), 1) if len(t3) == 3 else None; s['int_score'] = round(sum(i3) / len(i3), 1) if len(i3) == 3 else None
    s['trk_score_recent'] = round(sum(t3r) / len(t3r), 1) if len(t3r) == 3 else None; s['int_score_recent'] = round(sum(i3r) / len(i3r), 1) if len(i3r) == 3 else None
rank_trk = sorted([t for t in skill if skill[t]['trk_score'] is not None and skill[t]['n'] >= 6], key=lambda t: skill[t]['trk_score'])
rank_int = sorted([t for t in skill if skill[t]['int_score'] is not None and skill[t]['n'] >= 6], key=lambda t: skill[t]['int_score'])
print('track rank (km, 12-36 h mean):', [(t, skill[t]['trk_score'], skill[t]['trk_score_recent']) for t in rank_trk])
print('intensity rank (kt):', [(t, skill[t]['int_score'], skill[t]['int_score_recent'], skill[t]['taus']['24']['bias']) for t in rank_int])

# ---- what each model says now for the sites ----
SITES = {b['id']: (b['lat'], b['lon'], b['name']) for b in MP['bldg']}; SITES['pv'] = (20.6100, -105.2345, ['Puerto Vallarta (centro)', 'Puerto Vallarta (downtown)'])
cur = MP['advisory']['earlier_fix'] if MP['advisory'].get('earlier_fix') else None
CUR = cur or dict(r34=[80, 80, 70, 80], r50=[40, 40, 35, 40], r64=[20, 20, 15, 20])
c0 = dt.datetime.strptime(FC['cycle'], '%Y%m%d%H'); G_RATIO = float(MP['G0']) / float(MP['V0'])
def model_track(k):
    tr = FC['tracks'].get(k); it = FC['ints'].get(k)
    if not tr or len(tr['pts']) < 3: return None
    pts = [p for p in tr['pts'] if p[0] <= 72]
    ints = {p[0]: p[1] for p in it['pts']} if it else {p[0]: p[3] for p in pts}
    out = []
    for p in pts:
        v = ints.get(p[0], p[3]); out.append(dict(h=p[0], lat=p[1], lon=p[2], v=v))
    return out
# the NHC's forecast wind structure (its radii at the same hour, interpolated) on each model's own track and intensity;
# the 50- and 64-kt radii drop out once the model's intensity is below them
NP = [dict(h=(dt.datetime.strptime(p['t'], '%Y-%m-%dT%H:%MZ') - c0).total_seconds() / 3600, r34=p['r34'], r50=p['r50'], r64=p['r64'], v=p['kt']) for p in FC['nhc']['track'] if not p.get('earlier_fix')]
def nhc_radii(h):
    if h <= NP[0]['h']: return NP[0]
    for a, b in zip(NP, NP[1:]):
        if a['h'] <= h <= b['h']:
            f = (h - a['h']) / (b['h'] - a['h']); return {k: [a[k][q] + f * (b[k][q] - a[k][q]) for q in range(4)] for k in ('r34', 'r50', 'r64')}
    return NP[-1]
def interp(pts, h):
    for a, b in zip(pts, pts[1:]):
        if a['h'] <= h <= b['h']:
            f = (h - a['h']) / (b['h'] - a['h']); I = lambda x, y: x + f * (y - x)
            v = I(a['v'], b['v']); R = nhc_radii(h)
            return dict(lat=I(a['lat'], b['lat']), lon=I(a['lon'], b['lon']), v=v, g=v * G_RATIO, r34=R['r34'], r50=R['r50'] if v > 50 else [0] * 4, r64=R['r64'] if v > 64 else [0] * 4)
    return None
now = {}
for k in list(FC['tracks'].keys()) + ['OFCL']:
    pts = model_track(k) if k != 'OFCL' else [dict(h=(dt.datetime.strptime(p['t'], '%Y-%m-%dT%H:%MZ') - c0).total_seconds() / 3600, lat=p['lat'], lon=p['lon'], v=p['kt']) for p in FC['nhc']['track'] if not p.get('earlier_fix')]
    if not pts: continue
    res = {}
    for sid, (la, lo, nm) in SITES.items():
        bestc = None; pk = 0; pkt = None
        h = pts[0]['h']
        while h <= pts[-1]['h']:
            c = interp(pts, h)
            if c:
                v, g, frm, km, brg = wind(c, la, lo, True)
                if bestc is None or km < bestc['km']: bestc = dict(km=round(km, 1), h=h, v=round(c['v']), brg=round(brg))
                if v > pk: pk, pkt = v, h
            h += 0.5
        res[sid] = dict(closest=bestc, closest_t=(c0 + dt.timedelta(hours=bestc['h'])).strftime('%Y-%m-%dT%H:%MZ'), peak_kt=round(pk, 1), peak_t=(c0 + dt.timedelta(hours=pkt)).strftime('%Y-%m-%dT%H:%MZ') if pkt is not None else None)
    late = EARLY.get(k, k)
    now[k] = dict(name=FC['tracks'][k]['name'] if k in FC['tracks'] else 'NHC', late=late, skill=skill.get(late, {}).get('trk_score'), skill_recent=skill.get(late, {}).get('trk_score_recent'),
                  int_skill=skill.get(late, {}).get('int_score'), sites=res, hours=pts[-1]['h'])
print('now:', {k: (v['name'], v['sites']['pv']['closest'], v['sites']['pv']['peak_kt']) for k, v in now.items()})
json.dump(dict(cycle=FC['cycle'], best_end=tb[-1].strftime('%Y-%m-%dT%H:%MZ'), skill=skill, rank_trk=rank_trk, rank_int=rank_int, now=now, radii=CUR,
               note='Skill: mean error of each model’s own past forecasts of Simon vs the NHC best track. Now: peak sustained wind at the site if the center followed that model’s line exactly, with the NHC’s forecast wind radii at the same hour; not the NHC odds.'),
          open(OUT, 'w'), separators=(',', ':'))
print('wrote', OUT)
