"""Analog climatology for Invest EP93 (future Trudy) from HURDAT2 (NE Pacific, 1949-2025).
Usage: trudy_climo.py HURDAT2 OUT.json
Analogs: every storm with a 6-hourly fix within R km of the EP93 position of 12 Oct 18Z (8.1N 93.9W), between 12 Sep and 11 Nov
of any year. From that fix forward: closest pass to Puerto Vallarta, days to it, intensity then, peak intensity, landfall region."""
import sys, json, math, datetime as dt
HUR, OUT = sys.argv[1:3]
P0 = (8.1, -93.9); PV = (20.61, -105.2345); DOY0 = dt.date(2026, 10, 12).timetuple().tm_yday
def geo(la1, lo1, la2, lo2):
    R = 6371.0; p1, p2 = math.radians(la1), math.radians(la2); dl = math.radians(lo2 - lo1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
storms = []; cur = None
for line in open(HUR):
    f = [x.strip() for x in line.split(',')]
    if f[0].startswith('EP') or f[0].startswith('CP'):
        cur = dict(id=f[0], name=f[1], fixes=[]); storms.append(cur); continue
    if cur is None or len(f) < 7: continue
    t = dt.datetime.strptime(f[0] + f[1], '%Y%m%d%H%M')
    la = float(f[4][:-1]) * (1 if f[4][-1] == 'N' else -1); lo = float(f[5][:-1]) * (-1 if f[5][-1] == 'W' else 1)
    v = int(f[6]) if f[6] not in ('', '-999') else None
    cur['fixes'].append((t, f[3], la, lo, v))
print(len(storms), 'storms')

def region(la, lo):
    """coarse landfall / closest-approach region names for the Mexican Pacific"""
    if la < 15.5: return 'Central America / Chiapas'
    if lo > -98.5: return 'Oaxaca'
    if lo > -101.5: return 'Guerrero'
    if lo > -104.4: return 'Michoacán / Colima'
    if la < 21.0 and lo > -106.0: return 'Jalisco (Bahía de Banderas)'
    if la < 22.6 and lo > -106.5: return 'Nayarit'
    if la < 26.0 and lo > -110.0: return 'Sinaloa'
    if lo <= -108.0 and la > 22.0: return 'Baja California Sur'
    return 'open Pacific'

def analogs(R, season=30):
    out = []
    for s in storms:
        hit = None
        for i, (t, st, la, lo, v) in enumerate(s['fixes']):
            doy = t.timetuple().tm_yday
            if abs(doy - DOY0) <= season and geo(la, lo, *P0) <= R:
                hit = i; break
        if hit is None: continue
        fx = s['fixes'][hit:]
        d = [geo(la, lo, *PV) for (_, _, la, lo, _) in fx]
        i = min(range(len(d)), key=d.__getitem__)
        vmax = max([v for (_, _, _, _, v) in fx if v is not None] or [0])
        # first fix over Mexican land north of 15N = crude landfall: use status 'L' flag in HURDAT2 record id if present
        land = next(((t, la, lo, v) for (t, st, la, lo, v) in fx if False), None)
        out.append(dict(id=s['id'], name=s['name'], year=fx[0][0].year, t0=fx[0][0].strftime('%Y-%m-%d %HZ'), lat0=fx[0][2], lon0=fx[0][3], v0=fx[0][4],
                        cpa_km=round(d[i]), cpa_t=fx[i][0].strftime('%Y-%m-%d %HZ'), cpa_days=round((fx[i][0] - fx[0][0]).total_seconds() / 86400, 1),
                        v_cpa=fx[i][4], cpa_lat=fx[i][2], cpa_lon=fx[i][3], region=region(fx[i][2], fx[i][3]), vmax=vmax,
                        track=[(round(la, 1), round(lo, 1), v) for (_, _, la, lo, v) in fx]))
    return out

res = {}
for R in (300, 500):
    a = analogs(R); n = len(a)
    within = {str(k): sum(1 for x in a if x['cpa_km'] <= k) for k in (100, 200, 300, 500)}
    ts_pv = sum(1 for x in a if x['cpa_km'] <= 200 and (x['v_cpa'] or 0) >= 34)
    hu_pv = sum(1 for x in a if x['cpa_km'] <= 150 and (x['v_cpa'] or 0) >= 64)
    days = sorted(x['cpa_days'] for x in a if x['cpa_km'] <= 300)
    res[str(R)] = dict(n=n, within=within, ts_within200=ts_pv, hu_within150=hu_pv, days_to_cpa_within300=days,
                       regions={r: sum(1 for x in a if x['region'] == r) for r in sorted(set(x['region'] for x in a))},
                       major=sum(1 for x in a if x['vmax'] >= 96), hurricane=sum(1 for x in a if x['vmax'] >= 64),
                       storms=sorted(a, key=lambda x: x['cpa_km']))
    print(f'R={R} km: {n} analogs; within 100/200/300/500 km of PV: {within}; TS at PV(<=200 km & >=34 kt): {ts_pv}; HU(<=150 & >=64): {hu_pv}; became hurricane {res[str(R)]["hurricane"]}, major {res[str(R)]["major"]}')
    print('  regions:', res[str(R)]['regions']); print('  days to CPA (<=300 km):', days)
    for x in res[str(R)]['storms'][:12]:
        print(f"   {x['year']} {x['name']:>10} from {x['lat0']:.1f}N {-x['lon0']:.1f}W ({x['t0']}) -> CPA {x['cpa_km']} km on {x['cpa_t']} (+{x['cpa_days']} d) at {x['v_cpa']} kt; peak {x['vmax']} kt; {x['region']}")
json.dump(res, open(OUT, 'w'))
