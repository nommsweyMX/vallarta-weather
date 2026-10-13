"""Invest EP93 (future Trudy): what every track model says for Puerto Vallarta and the three buildings.
Usage: trudy_models.py ADECK BDECK LAND.geojson OUT.json
For every aid of the latest full cycle (12Z) and the latest early cycle (18Z): the track is interpolated hourly, the closest pass
to Puerto Vallarta, the time and strength then, landfall (first hour over land, Natural Earth 50 m polygons), and the wind the
parametric field (simon_phys) gives at the three buildings, with the model's own wind radii where the deck has them and
climatological radii otherwise. Probabilities: GEFS members equally weighted; deterministic + AI aids weighted by their Simon
position skill (inverse-square of the 12-36 h mean error)."""
import sys, json, math, datetime as dt, os
sys.path.insert(0, os.environ.get('SIMON_TOOLS', '/home/user/vallarta-weather/hurricane-simon/bay/tools'))
from simon_phys import geo, wind, exposure, KMH
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.prepared import prep

ADECK, BDECK, LAND, OUT = sys.argv[1:5]   # ADECK may be several files joined with ','
PV = (20.61, -105.2345); TZ = -6
SITES = {'amapas': (20.5984, -105.2382, 'D Terrace, Amapas (8th floor)'), 'ezapata': (20.6060, -105.2330, 'Casa Francisca, Emiliano Zapata (3rd floor)'),
         'pitillal': (20.6477, -105.2087, 'El Pitillal house (street level)')}
NAMES = {'AVNO': 'GFS', 'AVNI': 'GFS (early)', 'UKX': 'UKMET', 'UKXI': 'UKMET (early)', 'CEMN': 'Canadian ens. mean', 'CEMI': 'Canadian ens. mean (early)',
         'NVGM': 'NAVGEM', 'NVGI': 'NAVGEM (early)', 'HWRF': 'HWRF', 'HWFI': 'HWRF (early)', 'HMON': 'HMON', 'HMNI': 'HMON (early)',
         'HFSA': 'HAFS-A', 'HFAI': 'HAFS-A (early)', 'HFSB': 'HAFS-B', 'HFBI': 'HAFS-B (early)', 'CTCX': 'COAMPS-TC', 'CTCI': 'COAMPS-TC (early)',
         'GDMN': 'Google DeepMind', 'GDMI': 'Google DeepMind (early)', 'AEMN': 'GEFS mean', 'AEMI': 'GEFS mean (early)',
         'HCCA': 'NHC corrected consensus', 'TVCN': 'Track consensus', 'CLP5': 'Climatology-persistence', 'AC00': 'GEFS control',
         'ECMO': 'ECMWF IFS', 'AIFS': 'ECMWF AIFS (AI)', 'EEMN': 'ECMWF ens. mean', 'AEMM': 'AIFS ens. mean'}
GROUP = {'AVNO': 'global', 'AVNI': 'global', 'UKX': 'global', 'UKXI': 'global', 'CEMN': 'global', 'CEMI': 'global', 'NVGM': 'global', 'NVGI': 'global',
         'HWRF': 'regional', 'HWFI': 'regional', 'HMON': 'regional', 'HMNI': 'regional', 'HFSA': 'regional', 'HFAI': 'regional', 'HFSB': 'regional',
         'HFBI': 'regional', 'CTCX': 'regional', 'CTCI': 'regional', 'GDMN': 'ai', 'GDMI': 'ai', 'AEMN': 'ensmean', 'AEMI': 'ensmean',
         'HCCA': 'consensus', 'TVCN': 'consensus', 'CLP5': 'climo', 'ECMO': 'global', 'AIFS': 'ai', 'EEMN': 'ensmean', 'AEMM': 'ensmean'}
# Simon verification, mean position error 12-36 h (km), from the final report (Figure 2 / Appendix B). Early (interpolated) aids inherit.
SIMON_ERR = json.loads(os.environ.get('SIMON_ERR', '{}')) or {'GDMN': 33, 'HCCA': 38, 'TVCN': 55, 'AVNO': 70, 'UKX': 75, 'CEMN': 70, 'NVGM': 80,
                                                              'HWRF': 75, 'HMON': 120, 'HFSA': 117, 'CTCX': 129, 'HFSB': 169, 'AEMN': 70, 'CLP5': 150}
LATE = {'HFAI': 'HFSA', 'HFBI': 'HFSB', 'HWFI': 'HWRF', 'HMNI': 'HMON', 'AVNI': 'AVNO', 'UKXI': 'UKX', 'NVGI': 'NVGM', 'GDMI': 'GDMN', 'CTCI': 'CTCX', 'CEMI': 'CEMN', 'AEMI': 'AEMN'}

def ll(a, b):
    la = int(a[:-1]) / 10 * (1 if a[-1] == 'N' else -1); lo = int(b[:-1]) / 10 * (-1 if b[-1] == 'W' else 1); return la, lo
def cyc(s): return dt.datetime.strptime(s, '%Y%m%d%H')
def region(la, lo):
    if la < 15.5: return 'Central America / Chiapas'
    if lo > -98.5: return 'Oaxaca'
    if lo > -101.5: return 'Guerrero'
    if lo > -104.4: return 'Michoacán / Colima'
    if la < 21.0 and lo > -106.0: return 'Jalisco (Bahía de Banderas)'
    if la < 22.6 and lo > -106.5: return 'Nayarit'
    if la < 26.5 and lo > -110.0: return 'Sinaloa'
    if la < 23.5 and lo <= -108.0: return 'Baja California Sur'
    if lo <= -108.0: return 'Baja California peninsula'
    return 'Sonora / Gulf of California'

land = prep(unary_union([shape(f['geometry']) for f in json.load(open(LAND))['features']]).buffer(0))
def on_land(la, lo): return land.contains(Point(lo, la))

tracks = {}
for line in (l for fn in ADECK.split(',') for l in open(fn)):
    f = [x.strip() for x in line.split(',')]
    if len(f) < 9: continue
    tech = f[4]; c = cyc(f[2]); tau = int(f[5])
    if not (tech in NAMES or tech.startswith('AP') or tech.startswith('EE') or tech.startswith('AE') or tech in ('EC00', 'AE00')): continue
    la, lo = ll(f[6], f[7])
    if la == 0 and lo == 0: continue
    v = int(f[8]) if f[8] else 0
    rec = tracks.setdefault((c, tech), {}).setdefault(tau, dict(lat=la, lon=lo, v=v, r={}))
    if len(f) > 16 and f[11] in ('34', '50', '64') and f[12] in ('NEQ', 'AAA'):
        q = [max(0, int(x or 0)) for x in f[13:17]]
        if f[12] == 'AAA': q = [q[0]] * 4
        if any(q): rec['r'][int(f[11])] = q

def climo_radii(v):
    r34 = min(130, 45 + 0.9 * (v - 34)) if v > 34 else 0; r50 = min(70, 15 + 0.55 * (v - 50)) if v > 50 else 0; r64 = min(45, 10 + 0.4 * (v - 64)) if v > 64 else 0
    return [r34] * 4, [r50] * 4, [r64] * 4

def hourly(trk):
    taus = sorted(t for t in trk if t <= 168)
    has_radii = any(trk[t]['r'] for t in taus)
    out = []
    for h in range(taus[0], taus[-1] + 1):
        a = max(t for t in taus if t <= h); b = min(t for t in taus if t >= h); w = 0 if a == b else (h - a) / (b - a)
        A, B = trk[a], trk[b]
        la = A['lat'] + (B['lat'] - A['lat']) * w; lo = A['lon'] + (B['lon'] - A['lon']) * w; v = A['v'] + (B['v'] - A['v']) * w
        if has_radii:
            rr = {}
            for th in (34, 50, 64):
                qa = A['r'].get(th, [0] * 4); qb = B['r'].get(th, [0] * 4); rr[th] = [qa[i] + (qb[i] - qa[i]) * w for i in range(4)]
            r34, r50, r64 = rr[34], rr[50], rr[64]
        else: r34, r50, r64 = climo_radii(v)
        out.append(dict(h=h, lat=la, lon=lo, v=v, r34=r34, r50=r50, r64=r64))
    return out, has_radii

def analyze(c, tech, trk):
    hs, has_radii = hourly(trk)
    if len(hs) < 24: return None
    d = [geo(p['lat'], p['lon'], *PV)[0] for p in hs]
    i = min(range(len(d)), key=d.__getitem__)
    cpa = hs[i]; t_cpa = c + dt.timedelta(hours=cpa['h'])
    # landfall: first hour over land after having been over water
    lf = None; wet = False
    for p in hs:
        isl = on_land(p['lat'], p['lon'])
        if not isl: wet = True
        elif wet and lf is None:
            lf = dict(h=p['h'], lat=round(p['lat'], 2), lon=round(p['lon'], 2), v=round(p['v']), t=(c + dt.timedelta(hours=p['h'])).strftime('%Y-%m-%d %HZ'),
                      region=region(p['lat'], p['lon'])); break
    # winds at Puerto Vallarta (open water) and at the three sites
    pv_series = []; site_peak = {k: dict(v=0, g=0, h=None, frm=None) for k in SITES}; rain = 0.0; rain_peak = 0.0
    def rcliper(v, km):
        # Tuleya et al. (2007) R-CLIPER: rate (mm/h) vs distance for a storm of intensity v (kt); no terrain enhancement
        if v < 20: return 0.0
        U = 1 + (v - 35) / 33; T0 = max(0.3, -1.10 + 3.96 * U); Tm = max(T0, 3.96 + 2.45 * U); rm = max(15, 64.5 - 13.0 * U); re = max(60, 150 - 16.0 * U)
        return T0 + (Tm - T0) * km / rm if km < rm else Tm * math.exp(-(km - rm) / re)
    for p in hs:
        cdict = dict(lat=p['lat'], lon=p['lon'], v=p['v'], g=1.25 * p['v'], r34=p['r34'], r50=p['r50'], r64=p['r64'])
        if p['v'] <= 0: pv_series.append(0); continue
        rr = rcliper(p['v'], geo(p['lat'], p['lon'], *PV)[0]); rain += rr; rain_peak = max(rain_peak, rr)
        vpv = wind(cdict, *PV)[0]; pv_series.append(vpv)
        for k, (sla, slo, _) in SITES.items():
            vv, gg, frm, km, brg = wind(cdict, sla, slo)
            fac, gr = exposure(k, frm); vs = vv * fac
            if vs > site_peak[k]['v']: site_peak[k] = dict(v=vs, g=vs * gr, h=p['h'], frm=frm)
    def span(th):
        hh = [p['h'] for p, vv in zip(hs, pv_series) if vv >= th]
        return (hh[0], hh[-1]) if hh else None
    peak_pv = max(pv_series); hp = hs[pv_series.index(peak_pv)]['h']
    vmax = max(p['v'] for p in hs); hv = hs[[p['v'] for p in hs].index(vmax)]['h']
    return dict(cycle=c.strftime('%Y%m%d%H'), tech=tech, name=NAMES.get(tech, tech), group=GROUP.get(tech, 'gefs' if tech.startswith('A') and tech[1] in 'PC' else 'ecens' if tech.startswith('E') else 'aiens'), has_radii=has_radii,
                last_tau=hs[-1]['h'], cpa_km=round(d[i]), cpa_h=cpa['h'], cpa_t=t_cpa.strftime('%Y-%m-%d %HZ'),
                cpa_local=(t_cpa + dt.timedelta(hours=TZ)).strftime('%a %d %b %H:%M'), cpa_v=round(cpa['v']), cpa_lat=round(cpa['lat'], 2), cpa_lon=round(cpa['lon'], 2),
                cpa_brg=round(geo(*PV, cpa['lat'], cpa['lon'])[1]), peak_v=round(vmax), peak_t=(c + dt.timedelta(hours=hv)).strftime('%Y-%m-%d %HZ'),
                landfall=lf, pv_peak_kt=round(peak_pv, 1), pv_peak_t=(c + dt.timedelta(hours=hp) + dt.timedelta(hours=TZ)).strftime('%a %d %b %H:%M'),
                pv34=span(34), pv50=span(50), pv64=span(64), rain_mm=round(rain), rain_peak_mmh=round(rain_peak, 1),
                sites={k: dict(kmh=round(s['v'] * KMH), gust_kmh=round(s['g'] * KMH), t=(c + dt.timedelta(hours=s['h']) + dt.timedelta(hours=TZ)).strftime('%a %d %b %H:%M') if s['h'] is not None else None, frm=s['frm'])
                       for k, s in site_peak.items()},
                track=[(p['h'], round(p['lat'], 2), round(p['lon'], 2), round(p['v']), round(geo(p['lat'], p['lon'], *PV)[0])) for p in hs if p['h'] % 6 == 0])

res = []
for (c, tech), trk in sorted(tracks.items()):
    if c < cyc('2026101206'): continue
    r = analyze(c, tech, trk)
    if r: res.append(r)
cycles = sorted(set(r['cycle'] for r in res))
print('cycles', cycles)

def wq(vals, ws, q):
    s = sorted(zip(vals, ws)); tot = sum(ws); acc = 0
    for v, w in s:
        acc += w
        if acc >= q * tot: return v
    return s[-1][0]

summary = {}
for c in cycles:
    R = [r for r in res if r['cycle'] == c]
    aids = [r for r in R if r['group'] in ('global', 'regional', 'ai', 'consensus', 'ensmean')]
    S = {}
    for grp in ('gefs', 'ecens', 'aiens'):
      gefs = [r for r in R if r['group'] == grp]
      if gefs:
        n = len(gefs)
        S[grp] = dict(n=n, within={str(k): round(100 * sum(r['cpa_km'] <= k for r in gefs) / n) for k in (100, 200, 300)},
                         pv34=round(100 * sum(1 for r in gefs if r['pv34']) / n), pv50=round(100 * sum(1 for r in gefs if r['pv50']) / n), pv64=round(100 * sum(1 for r in gefs if r['pv64']) / n),
                         cpa_median=wq([r['cpa_km'] for r in gefs], [1] * n, 0.5), cpa_q25=wq([r['cpa_km'] for r in gefs], [1] * n, 0.25), cpa_q75=wq([r['cpa_km'] for r in gefs], [1] * n, 0.75),
                         cpa_h_median=wq([r['cpa_h'] for r in gefs], [1] * n, 0.5),
                         landfall={reg: sum(1 for r in gefs if r['landfall'] and r['landfall']['region'] == reg) for reg in sorted(set(r['landfall']['region'] for r in gefs if r['landfall']))},
                         no_landfall=sum(1 for r in gefs if not r['landfall']), peak_median=wq([r['peak_v'] for r in gefs], [1] * n, 0.5),
                         rain_median=wq([r['rain_mm'] for r in gefs], [1] * n, 0.5), rain_q90=wq([r['rain_mm'] for r in gefs], [1] * n, 0.9),
                         sites={k: dict(median=wq([r['sites'][k]['kmh'] for r in gefs], [1] * n, 0.5), q90=wq([r['sites'][k]['kmh'] for r in gefs], [1] * n, 0.9), max=max(r['sites'][k]['kmh'] for r in gefs)) for k in SITES})
    if aids:
        ws = [1 / SIMON_ERR.get(LATE.get(r['tech'], r['tech']), 90) ** 2 for r in aids]
        S['aids'] = dict(n=len(aids), techs=[r['tech'] for r in aids], weights={r['tech']: round(w / sum(ws), 3) for r, w in zip(aids, ws)},
                         within={str(k): round(100 * sum(w for r, w in zip(aids, ws) if r['cpa_km'] <= k) / sum(ws)) for k in (100, 200, 300)},
                         within_unweighted={str(k): round(100 * sum(r['cpa_km'] <= k for r in aids) / len(aids)) for k in (100, 200, 300)},
                         pv34=round(100 * sum(w for r, w in zip(aids, ws) if r['pv34']) / sum(ws)), pv64=round(100 * sum(w for r, w in zip(aids, ws) if r['pv64']) / sum(ws)),
                         pv34_unweighted=round(100 * sum(1 for r in aids if r['pv34']) / len(aids)),
                         cpa_median=wq([r['cpa_km'] for r in aids], ws, 0.5), cpa_q25=wq([r['cpa_km'] for r in aids], ws, 0.25), cpa_q75=wq([r['cpa_km'] for r in aids], ws, 0.75),
                         cpa_h_median=wq([r['cpa_h'] for r in aids], ws, 0.5),
                         rain_median=wq([r['rain_mm'] for r in aids], ws, 0.5), rain_q90=wq([r['rain_mm'] for r in aids], ws, 0.9),
                         sites={k: dict(median=wq([r['sites'][k]['kmh'] for r in aids], ws, 0.5), q90=wq([r['sites'][k]['kmh'] for r in aids], ws, 0.9), max=max(r['sites'][k]['kmh'] for r in aids)) for k in SITES})
    summary[c] = S
    print(f'\n=== cycle {c}: {len(R)} tracks')
    for r in sorted(R, key=lambda r: r['cpa_km']):
        if r['group'] in ('gefs', 'ecens', 'aiens') and r['cpa_km'] > 300: continue
        lf = f"landfall {r['landfall']['region']} {r['landfall']['t']} {r['landfall']['v']} kt" if r['landfall'] else 'no landfall'
        print(f"{r['tech']:5} {r['name']:28} CPA {r['cpa_km']:5} km {r['cpa_local']} ({r['cpa_v']:3} kt, brg {r['cpa_brg']:3}) peak {r['peak_v']:3} kt | PV {r['pv_peak_kt']:5.1f} kt 34kt:{r['pv34']} | "
              f"amapas {r['sites']['amapas']['kmh']:3} ezapata {r['sites']['ezapata']['kmh']:3} pitillal {r['sites']['pitillal']['kmh']:3} km/h rain {r['rain_mm']:3} mm | {lf}" + ('' if r['has_radii'] else ' [climo radii]'))
    print(json.dumps(S, indent=None)[:2500])
json.dump(dict(summary=summary, tracks=res, sites=SITES, simon_err=SIMON_ERR), open(OUT, 'w'))
