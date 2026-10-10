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
    dict(id='frodriguez', lat=20.6014, lon=-105.2340),
]
META = {
    'ecmwf_ifs': ('ECMWF IFS', 'ECMWF', 9, 'global'),
    'ukmo_global_deterministic_10km': ('UK Met Office', 'Met Office', 10, 'global'),
    'icon_global': ('ICON', 'DWD', 13, 'global'),
    'gfs_global': ('GFS', 'NOAA', 13, 'global'),
    'gem_global': ('GEM', 'ECCC', 15, 'global'),
    'cma_grapes_global': ('CMA GRAPES', 'CMA', 15, 'global'),
    'bom_access_global': ('ACCESS-G', 'BoM', 15, 'global'),
    'meteofrance_arpege_world': ('ARPEGE', 'Météo-France', 25, 'global'),
    'jma_gsm': ('JMA GSM', 'JMA', 55, 'global'),
    'ecmwf_aifs025_single': ('ECMWF AIFS', 'ECMWF', 25, 'ai'),
    'ncep_aigfs025': ('AI-GFS', 'NOAA', 25, 'ai'),
    'kma_gdps': ('KMA GDPS', 'KMA', 12, 'global'),
    'gfs_graphcast025': ('GraphCast', 'Google DeepMind', 25, 'ai'),
    'hfsa': ('HAFS-A', 'NOAA', 6, 'hurricane'),
    'hfsb': ('HAFS-B', 'NOAA', 6, 'hurricane'),
}
models = {}   # id -> dict(meta, per-loc inc[48], gust[49] or None, cell)
ELEV = {}     # location index -> terrain elevation (m) reported by Open-Meteo for the address
OM_TRIED = [m for m in META if m not in ('hfsa', 'hfsb')]
excluded = []
for m in OM_TRIED:
    if not os.path.exists(os.path.join(D, 'om', m + '.json')):
        excluded.append(dict(m=m, label=META[m][0], why='blocked'))

def native_step(inc):
    # block structure is aligned to 00/06/12/18 UTC = 18/00/06/12 CST; frame 0 is 12 CST, so blocks start at index 0
    a = np.array(inc)
    if a.sum() < 1: return None
    for n in (6, 3):
        b = a[:48].reshape(48 // n, n)
        if np.allclose(b, b[:, :1], atol=0.051): return n
    return 1

def tail_step(inc):
    # hourly models can coarsen near the end of the window (e.g. UK Met Office goes 3-hourly);
    # returns (n, first index) when every aligned n-block from there on is flat and some rain falls in it
    a = np.array(inc[:48])
    for n in (6, 3):
        k = 48
        while k - n >= 0 and np.allclose(a[k - n:k], a[k - n], atol=0.051): k -= n
        if k <= 48 - 2 * n and a[k:].sum() > 0.5: return n, k
    return None

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
        ws = h.get('wind_speed_10m') or []
        wv = [x for x in ws if x is not None]
        wind = [None if x is None else float(x) for x in ws] if wv and max(wv) > 0 and len(wv) >= NH else None
        pr = [x for x in h.get('pressure_msl') or [] if x is not None]
        ELEV.setdefault(li, loc.get('elevation'))
        per.append(dict(inc=inc, gust=gust, wind=wind, cell=[round(loc['latitude'], 3), round(loc['longitude'], 3)],
                        pmin=round(min(pr), 1) if pr else None, missing=miss))
    if all(x is None for x in per):
        print('skip (no data)', mid); excluded.append(dict(m=mid, label=META[mid][0], why='nodata')); continue
    first = next(x for x in per if x)['inc']; st = native_step(first)
    models[mid] = dict(per=per, step=st, tail=(tail_step(first) if st == 1 else None))

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
        wk = [st[str(f)]['wmax'][li]['v'] * 3.6 for f in range(f0, f0 + NH + 1, 3)]          # km/h at every 3rd frame
        wind = [float(np.interp(i, range(0, NH + 1, 3), wk)) for i in range(NH + 1)]
        per.append(dict(inc=inc, gust=None, wind=wind, cell=[LOCS[li]['lat'], LOCS[li]['lon']], pmin=round(min(pr), 1), missing=0,
                        wmax=round(max(st[str(f)]['wmax'][li]['v'] for f in range(f0 + 3, f0 + NH + 1, 3)) * 3.6, 0)))
    models[mid] = dict(per=per, step=3, cycle=c0.strftime('%HZ %d %b'))

print('models:', list(models))

# ---- NHC forecast track -> wind at a fixed point (estimate) ----
NHC = json.load(open(os.path.join(D, 'nhc.json'))) if os.path.exists(os.path.join(D, 'nhc.json')) else None

def geo(la1, lo1, la2, lo2):
    p1, p2, dl = np.radians(la1), np.radians(la2), np.radians(lo2 - lo1)
    d = 2 * 6371 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2))
    b = (np.degrees(np.arctan2(np.sin(dl) * np.cos(p2), np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl))) + 360) % 360
    return float(d), float(b)

def nhc_wind(t_utc, la, lo):
    """Sustained wind and gust (kt) at a point if Simon follows the NHC track exactly.
    Track, intensity and the 34/50/64-kt radii (largest extent per quadrant) are interpolated in time; the radius
    toward the point is interpolated between quadrant centres; speed is piecewise-linear between the radii,
    with a radius of maximum wind of half the 64-kt radius (8 nm minimum) and a 1/r decay beyond the 34-kt radius."""
    tr = NHC['track']; ts = [dt.datetime.strptime(p['t'], '%Y-%m-%dT%H:%MZ') for p in tr]
    if t_utc < ts[0] or t_utc > ts[-1]: return None
    k = max(i for i in range(len(ts) - 1) if ts[i] <= t_utc)
    a, b = tr[k], tr[k + 1]; f = (t_utc - ts[k]) / (ts[k + 1] - ts[k])
    I = lambda x, y: x + f * (y - x)
    clat, clon, vmax, gmax = I(a['lat'], b['lat']), I(a['lon'], b['lon']), I(a['kt'], b['kt']), I(a['gust'], b['gust'])
    km, brg = geo(clat, clon, la, lo); r = km / 1.852
    def toward(key):
        q = [I(a[key][j], b[key][j]) for j in range(4)]            # NE SE SW NW
        x = ((brg - 45) % 360) / 90; i = int(x) % 4; w = x - int(x)
        return q[i] * (1 - w) + q[(i + 1) % 4] * w
    r64, r50, r34 = toward('r64'), toward('r50'), toward('r34')
    rmw = max(8.0, 0.5 * r64) if r64 > 0 else 10.0
    knots = [(rmw, vmax)]
    for rr, vv in ((r64, 64), (r50, 50), (r34, 34)):
        if vmax > vv and rr > knots[-1][0]: knots.append((rr, vv))
    if r <= rmw: v = vmax * r / rmw
    elif r >= knots[-1][0]: v = knots[-1][1] * (knots[-1][0] / r)
    else:
        for (ra, va), (rb, vb) in zip(knots, knots[1:]):
            if ra <= r <= rb: v = va + (vb - va) * (r - ra) / (rb - ra); break
    return dict(kt=v, gust=v * (gmax / vmax if vmax else 1.25), km=km, brg=brg, ctr=(clat, clon), vmax=vmax)

def roll(a, n):
    s = np.convolve(a, np.ones(n), 'valid'); i = int(np.argmax(s)); return round(float(s[i]), 1), i

def scen(inc, model=None):
    a = np.array(inc); cum = np.concatenate([[0], np.cumsum(a)])
    pk = int(np.argmax(a)); s3, i3 = roll(a, 3); s6, i6 = roll(a, 6); s24, i24 = roll(a, 24)
    return dict(model=model, inc=[round(float(x), 3) for x in a], cum=[round(float(x), 3) for x in cum],
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
        id=L['id'], lat=L['lat'], lon=L['lon'], elev=ELEV.get(li),
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
    # ---- wind: models (sustained + gusts), NHC-track estimate, worst/avg/best ----
    ws = {m: avail[m]['wind'] for m in order if avail[m].get('wind')}
    W = np.array([[np.nan if x is None else x for x in ws[m]] for m in ws], dtype=float)
    nhc = [nhc_wind(dt.datetime.strptime(fr, '%Y-%m-%dT%H:%M') + dt.timedelta(hours=6), L['lat'], L['lon']) if NHC else None for fr in FRAMES]
    ns = np.array([x['kt'] * 1.852 if x else np.nan for x in nhc]); ng = np.array([x['gust'] * 1.852 if x else np.nan for x in nhc])
    hiS, hiG = np.nanmax(W, axis=0), np.nanmax(G, axis=0)
    wS, wG = np.fmax(ns, hiS), np.fmax(ng, hiG)
    srcS = [('nhc' if (not np.isnan(ns[i]) and ns[i] >= hiS[i]) else list(ws)[int(np.nanargmax(W[:, i]))]) for i in range(NH + 1)]
    R0 = lambda a: [None if np.isnan(x) else int(round(float(x))) for x in a]
    rec['wind'] = dict(
        nS=len(ws), nG=len(gusts), models=list(ws), gModels=[m for m in order if avail[m]['gust']],
        nhc=dict(s=R0(ns), g=R0(ng), km=[None if x is None else round(x['km'], 1) for x in nhc], brg=[None if x is None else round(x['brg']) for x in nhc]),
        worst=dict(s=R0(wS), g=R0(wG), src=srcS),
        avg=dict(s=R0(np.nanmean(W, axis=0)), g=R0(np.nanmean(G, axis=0))),
        best=dict(s=R0(np.nanmin(W, axis=0)), g=R0(np.nanmin(G, axis=0))),
        modelS={m: R0(np.array([np.nan if x is None else x for x in ws[m]], dtype=float)) for m in ws},
    )
    if NHC:   # closest approach of the NHC-track center, at 5-minute resolution
        t0 = dt.datetime.strptime(FRAMES[0], '%Y-%m-%dT%H:%M') + dt.timedelta(hours=6)
        near = min(((x['km'], k) for k in range(0, NH * 12 + 1) for x in [nhc_wind(t0 + dt.timedelta(minutes=5 * k), L['lat'], L['lon'])] if x), default=None)
        if near:
            rec['wind']['minKm'] = round(near[0], 1); rec['wind']['minAt'] = (t0 + dt.timedelta(minutes=5 * near[1]) - dt.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M')
    print('   wind', L['id'], 'closest', rec['wind'].get('minKm'), 'km at', rec['wind'].get('minAt'), '| nhc peak', int(np.nanmax(ns)), '/', int(np.nanmax(ng)), 'km/h at', FRAMES[int(np.nanargmax(ns))],
          'min dist', min(x['km'] for x in nhc if x), '| models S max', int(np.nanmax(W)), 'G max', int(np.nanmax(G)))
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

mods = {m: dict(label=META[m][0], org=META[m][1], km=META[m][2], kind=META[m][3], step=v['step'], cycle=v.get('cycle'),
                tail=(dict(step=v['tail'][0], fromFrame=v['tail'][1]) if v.get('tail') else None))
        for m, v in models.items()}
print('excluded', excluded)
# ---- waves in the bay off Los Muertos (context only; storm surge is not modeled here) ----
waves = {}
for fn in sorted(glob.glob(os.path.join(D, 'waves', '*_ww3.json'))):
    d = json.load(open(fn)); c0 = dt.datetime.strptime(d['cycle'], '%Y%m%d%H')
    f0 = int(((T0 + dt.timedelta(hours=6)) - c0).total_seconds() // 3600)
    hs = [d['steps'][str(f)]['hs'] for f in range(f0, f0 + NH + 1, 3)]
    waves[d['model'] + '_ww3'] = dict(label=META[d['model']][0] + ' WAVEWATCH III', hs=[round(float(np.interp(i, range(0, NH + 1, 3), hs)), 2) for i in range(NH + 1)],
                                      km=round(d['steps'][str(f0)]['km'], 1))
for fn in sorted(glob.glob(os.path.join(D, 'marine', '*.json'))):
    mid = os.path.basename(fn)[:-5]
    if mid == 'best_match': continue
    d = json.load(open(fn)); hs = (d.get('hourly') or {}).get('wave_height') or []
    if len(hs) == NH + 1 and all(x is not None for x in hs) and max(hs) > 0.05:
        km, _ = geo(20.597, -105.243, d['latitude'], d['longitude'])
        waves[mid] = dict(label={'meteofrance_wave': 'Météo-France MFWAM', 'ecmwf_wam025': 'ECMWF WAM', 'ncep_gfswave025': 'GFS-Wave'}.get(mid, mid),
                          hs=[round(x, 2) for x in hs], km=round(km, 1))
print('waves', {k: (v['label'], max(v['hs']), v['km']) for k, v in waves.items()})

json.dump(dict(nhc=NHC, waves=waves, excluded=excluded, generated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), frames=FRAMES, models=mods, locs=out_locs),
          open(OUT, 'w'), separators=(',', ':'))
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
