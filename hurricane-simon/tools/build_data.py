"""Combine model point forecasts into worst / best / average hourly scenarios for the 3 addresses.
Window: Sat 10 Oct 2026 12:00 -> Mon 12 Oct 12:00 CST (UTC-6) = 48 hourly steps, 49 frames."""
import json, glob, os, sys, datetime as dt
import numpy as np
D = sys.argv[1]; OUT = sys.argv[2]
NH = 48
T0 = dt.datetime(2026, 10, 10, 12)
FRAMES = [(T0 + dt.timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(NH + 1)]
LOCS = [
    dict(id='amapas', lat=20.5984, lon=-105.2382),
    dict(id='pitillal', lat=20.6477, lon=-105.2087),
    dict(id='frodriguez', lat=20.6012, lon=-105.2358),
]
META = {
    'ecmwf_ifs': ('ECMWF IFS', 'ECMWF · EU', 9, 'global'),
    'ukmo_global_deterministic_10km': ('UK Met Office', 'Met Office · UK', 10, 'global'),
    'icon_global': ('ICON', 'DWD · DE', 13, 'global'),
    'gfs_global': ('GFS', 'NOAA · US', 13, 'global'),
    'gem_global': ('GEM', 'ECCC · CA', 15, 'global'),
    'cma_grapes_global': ('CMA GRAPES', 'CMA · CN', 15, 'global'),
    'bom_access_global': ('ACCESS-G', 'BoM · AU', 15, 'global'),
    'meteofrance_arpege_world': ('ARPEGE', 'Météo-France · FR', 25, 'global'),
    'jma_gsm': ('JMA GSM', 'JMA · JP', 55, 'global'),
    'ecmwf_aifs025_single': ('ECMWF AIFS', 'ECMWF · AI model', 25, 'ai'),
    'ncep_aigfs025': ('AI-GFS', 'NOAA · AI model', 25, 'ai'),
    'kma_gdps': ('KMA GDPS', 'KMA · KR', 12, 'global'),
    'gfs_graphcast025': ('GraphCast', 'Google DeepMind · AI model', 25, 'ai'),
    'hfsa': ('HAFS-A', 'NOAA · hurricane model', 6, 'hurricane'),
    'hfsb': ('HAFS-B', 'NOAA · hurricane model', 6, 'hurricane'),
}
models = {}   # id -> dict(meta, per-loc inc[48], gust[49] or None, cell)
OM_TRIED = [m for m in META if m not in ('hfsa', 'hfsb')]
excluded = []
for m in OM_TRIED:
    if not os.path.exists(os.path.join(D, 'om', m + '.json')):
        excluded.append(dict(m=m, label=META[m][0], why='blocked'))

def native_step(inc):
    a = np.array(inc)
    if a.sum() < 1: return None
    trip = a[:48].reshape(16, 3)
    return 3 if np.allclose(trip, trip[:, :1], atol=0.051) else 1

for fn in sorted(glob.glob(os.path.join(D, 'om', '*.json'))):
    mid = os.path.basename(fn)[:-5]
    if mid not in META: continue
    d = json.load(open(fn))
    per = []
    for li, loc in enumerate(d):
        h = loc['hourly']
        assert h['time'][0] == FRAMES[0] and h['time'][-1] == FRAMES[-1], (mid, h['time'][0], h['time'][-1])
        p = h['precipitation'][1:NH + 1]
        miss = sum(x is None for x in p)
        if miss > 3: per.append(None); continue
        inc = [float(x or 0) for x in p]
        g = h.get('wind_gusts_10m') or []
        gv = [x for x in g if x is not None]
        gust = [None if x is None else float(x) for x in g] if gv and max(gv) > 0 else None
        pr = [x for x in h.get('pressure_msl') or [] if x is not None]
        per.append(dict(inc=inc, gust=gust, cell=[round(loc['latitude'], 3), round(loc['longitude'], 3)],
                        pmin=round(min(pr), 1) if pr else None, missing=miss))
    if all(x is None for x in per):
        print('skip (no data)', mid); excluded.append(dict(m=mid, label=META[mid][0], why='nodata')); continue
    models[mid] = dict(per=per, step=native_step(next(x for x in per if x)['inc']))

for fn in sorted(glob.glob(os.path.join(D, 'hafs', '*_parent.json'))):
    d = json.load(open(fn)); mid = d['model']; cyc = d['cycle']
    c0 = dt.datetime.strptime(cyc, '%Y%m%d%H')            # UTC
    f0 = int(((T0 + dt.timedelta(hours=6)) - c0).total_seconds() // 3600)   # window start (CST -> UTC)
    st = d['steps']
    per = []
    for li in range(3):
        inc = []
        for f in range(f0 + 3, f0 + NH + 1, 3):
            v = max(st[str(f)]['apcp3'][li]['v'], 0.0)
            inc += [v / 3] * 3
        a0 = lambda f: st[str(f)]['apcp0'][li]['v']
        chk = a0(f0 + NH) - a0(f0)
        assert abs(chk - sum(inc)) < 0.3, (mid, li, chk, sum(inc))
        pr = [st[str(f)]['prmsl'][li]['v'] / 100 for f in range(f0, f0 + NH + 1, 3)]
        per.append(dict(inc=inc, gust=None, cell=[LOCS[li]['lat'], LOCS[li]['lon']], pmin=round(min(pr), 1), missing=0,
                        wmax=round(max(st[str(f)]['wmax'][li]['v'] for f in range(f0 + 3, f0 + NH + 1, 3)) * 3.6, 0)))
    models[mid] = dict(per=per, step=3, cycle=c0.strftime('%HZ %d %b'))

print('models:', list(models))

def roll(a, n):
    s = np.convolve(a, np.ones(n), 'valid'); i = int(np.argmax(s)); return round(float(s[i]), 1), i

def scen(inc, model=None):
    a = np.array(inc); cum = np.concatenate([[0], np.cumsum(a)])
    pk = int(np.argmax(a)); s3, i3 = roll(a, 3); s6, i6 = roll(a, 6); s24, i24 = roll(a, 24)
    return dict(model=model, inc=[round(float(x), 2) for x in a], cum=[round(float(x), 1) for x in cum],
                total=round(float(a.sum()), 1), peak=round(float(a[pk]), 1), peakAt=pk,
                max3=s3, max3At=i3, max6=s6, max6At=i6, max24=s24, max24At=i24)

out_locs = []
for li, L in enumerate(LOCS):
    avail = {m: v['per'][li] for m, v in models.items() if v['per'][li] is not None}
    tot = {m: sum(v['inc']) for m, v in avail.items()}
    order = sorted(tot, key=lambda m: -tot[m])
    worst, best = order[0], order[-1]
    M = np.array([avail[m]['inc'] for m in order])
    avg = M.mean(axis=0)
    cums = np.concatenate([np.zeros((len(order), 1)), np.cumsum(M, axis=1)], axis=1)
    gusts = [avail[m]['gust'] for m in order if avail[m]['gust']]
    G = np.array([[np.nan if x is None else x for x in g] for g in gusts], dtype=float)
    pkm = M.argmax(axis=0)
    rec = dict(
        id=L['id'], lat=L['lat'], lon=L['lon'],
        n=len(order), ranking=[dict(m=m, total=round(tot[m], 1), peak=round(max(avail[m]['inc']), 1),
                                     cell=avail[m]['cell'], pmin=avail[m]['pmin'], wmax=avail[m].get('wmax'),
                                     gustMax=(round(max(x for x in avail[m]['gust'] if x is not None)) if avail[m]['gust'] else None))
                                for m in order],
        worst=scen(avail[worst]['inc'], worst), best=scen(avail[best]['inc'], best), avg=scen(avg, 'mean'),
        band=dict(lo=[round(float(x), 1) for x in cums.min(axis=0)], hi=[round(float(x), 1) for x in cums.max(axis=0)]),
        hourMax=dict(v=[round(float(x), 1) for x in M.max(axis=0)], m=[order[i] for i in pkm]),
        gust=dict(n=len(gusts), hi=[round(float(x)) for x in np.nanmax(G, axis=0)], avg=[round(float(x)) for x in np.nanmean(G, axis=0)],
                  lo=[round(float(x)) for x in np.nanmin(G, axis=0)]),
        series={m: [round(x, 2) for x in avail[m]['inc']] for m in order},
    )
    # ensemble context
    ens = {}; pool = []
    for fn in sorted(glob.glob(os.path.join(D, 'ens', '*.json'))):
        sysid = os.path.basename(fn)[:-5]
        h = json.load(open(fn))[li]['hourly']
        tots = [sum(x or 0 for x in h[k][1:NH + 1]) for k in h if k.startswith('precipitation') and sum(v is None for v in h[k][1:NH + 1]) <= 3]
        if not tots: continue
        t = np.array(tots); pool += tots
        ens[sysid] = dict(n=len(t), p50=round(float(np.median(t))), p90=round(float(np.percentile(t, 90))), max=round(float(t.max())),
                          gt100=round(float((t > 100).mean() * 100)), gt200=round(float((t > 200).mean() * 100)))
    t = np.array(pool)
    rec['ens'] = dict(systems=ens, n=len(t), p10=round(float(np.percentile(t, 10))), p50=round(float(np.median(t))),
                      p90=round(float(np.percentile(t, 90))), max=round(float(t.max())),
                      gt50=round(float((t > 50).mean() * 100)), gt100=round(float((t > 100).mean() * 100)),
                      gt200=round(float((t > 200).mean() * 100)), gt300=round(float((t > 300).mean() * 100)))
    out_locs.append(rec)
    print(L['id'], 'n', len(order), 'worst', worst, round(tot[worst]), 'best', best, round(tot[best]), 'avg', round(avg.sum()), 'ens p50/p90', rec['ens']['p50'], rec['ens']['p90'], 'n', rec['ens']['n'])

mods = {m: dict(label=META[m][0], org=META[m][1], km=META[m][2], kind=META[m][3], step=v['step'], cycle=v.get('cycle'))
        for m, v in models.items()}
print('excluded', excluded)
json.dump(dict(excluded=excluded, generated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), frames=FRAMES, models=mods, locs=out_locs),
          open(OUT, 'w'), separators=(',', ':'))
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
