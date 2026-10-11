"""Build map.json for the Simon map page: tracks (satellite extrapolation and NHC), the storm-relative rain field,
building-by-building wind, rain and threat timelines, river catchments and landslide checks.
Usage: build_map.py WORK OUT.json
WORK holds mapwork/sat.json + rain_stack.npy (from process_sat.py), nhc.json (from ../tools/nhc_parse.py),
tiles_reg/ (terrarium z8), tiles/ (z13), tiles_ws/ (z12)."""
import sys, os, json, math, base64, datetime as dt, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from terrain import mosaic, sample, grid, slope_aspect, fill_and_flow, upstream

W, OUT = sys.argv[1], sys.argv[2]
SAT = json.load(open(W + '/mapwork/sat.json')); NHC = json.load(open(W + '/nhc.json'))
STACK = np.load(W + '/mapwork/rain_stack.npy'); FIELD = STACK.mean(0)          # storm-relative rain rate, mm/h, last 2 h of scans
KM0, DKM, NK = SAT['grid']['km0'], SAT['grid']['dkm'], SAT['grid']['n']
P = lambda s: dt.datetime.strptime(s, '%Y-%m-%dT%H:%MZ')
F = lambda t: t.strftime('%Y-%m-%dT%H:%MZ')
END = dt.datetime(2026, 10, 12, 18, 0)                                            # Monday 12:00 CST

# ---------------- time axis: observed satellite frames, then 10-minute forecast steps ----------------
fixes = SAT['fixes']; t_obs = P(SAT['motion']['t'])
obs_t = [P(x['t']) for x in fixes if P(x['t']) >= t_obs - dt.timedelta(hours=4)]
times = obs_t + [t_obs + dt.timedelta(minutes=10 * k) for k in range(1, int((END - t_obs).total_seconds() // 600) + 1)]
n_obs = len(obs_t); DT_H = 10 / 60

# smoothed observed centre (3-point running mean)
fl = np.array([x['lat'] for x in fixes]); fo = np.array([x['lon'] for x in fixes]); ft = [P(x['t']) for x in fixes]
sm = lambda a: np.concatenate([[a[0]], (a[:-2] + a[1:-1] + a[2:]) / 3, [a[-1]]])
fl, fo = sm(fl), sm(fo)

# ---------------- land mask for the storm centre (regional terrain) ----------------
REG = mosaic(W + '/tiles_reg', 8)
def on_land(la, lo): return float(sample(REG, np.array([la]), np.array([lo]))[0]) > 1.0

summ = NHC['summary']; tr = NHC['track']; tts = [P(p['t']) for p in tr]
cur = max((p for p in tr if P(p['t']) <= t_obs), key=lambda p: P(p['t']))        # latest analysed NHC point (intensity and radii now)
V0, G0 = float(cur['kt']), float(cur['gust'])

def nhc_at(t):
    if t < tts[0] or t > tts[-1]: return None
    k = max(i for i in range(len(tts) - 1) if tts[i] <= t); a, b = tr[k], tr[k + 1]; f = (t - tts[k]) / (tts[k + 1] - tts[k])
    I = lambda x, y: x + f * (y - x)
    return dict(lat=I(a['lat'], b['lat']), lon=I(a['lon'], b['lon']), v=I(a['kt'], b['kt']), g=I(a['gust'], b['gust']),
                r34=[I(a['r34'][j], b['r34'][j]) for j in range(4)], r50=[I(a['r50'][j], b['r50'][j]) for j in range(4)], r64=[I(a['r64'][j], b['r64'][j]) for j in range(4)])

M = SAT['motion']
def ext_track():
    out, landfall, vlf = [], None, None
    for t in times[n_obs:]:
        h = (t - t_obs).total_seconds() / 3600
        la, lo = M['lat'] + M['lat_per_h'] * h, M['lon'] + M['lon_per_h'] * h
        if landfall is None and on_land(la, lo): landfall = t
        if landfall is None: v = V0
        else:                                                                    # Kaplan & DeMaria (1995) inland decay
            tl = (t - landfall).total_seconds() / 3600; v = 26.7 + (0.9 * V0 - 26.7) * math.exp(-0.095 * tl)
        out.append(dict(lat=la, lon=lo, v=v, g=v * G0 / V0, r34=list(cur['r34']), r50=list(cur['r50']) if v > 50 else [0] * 4, r64=list(cur['r64']) if v > 64 else [0] * 4))
    return out, landfall

def nhc_track():
    out, landfall = [], None
    for t in times[n_obs:]:
        p = nhc_at(t); out.append(p)
        if landfall is None and on_land(p['lat'], p['lon']): landfall = t
    return out, landfall

past = [dict(lat=float(np.interp(t.timestamp(), [x.timestamp() for x in ft], fl)), lon=float(np.interp(t.timestamp(), [x.timestamp() for x in ft], fo)),
             v=V0, g=G0, r34=list(cur['r34']), r50=list(cur['r50']), r64=list(cur['r64'])) for t in obs_t]
SCN = {}
for k, fn in (('ext', ext_track), ('nhc', nhc_track)):
    fut, lf = fn(); SCN[k] = dict(track=past + fut, landfall=F(lf) if lf else None)

# ---------------- physics shared with the page script ----------------
def geo(la1, lo1, la2, lo2):
    """distance (km) and bearing (deg) from point 1 to point 2."""
    p1, p2 = math.radians(la1), math.radians(la2); dl = math.radians(lo2 - lo1)
    d = 2 * 6371 * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
    b = math.degrees(math.atan2(math.sin(dl) * math.cos(p2), math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
    return d, b

def wind(c, la, lo, land):
    """1-min sustained wind (kt) at 10 m over open water, gust (kt) and direction it blows FROM (deg) at a point."""
    km, brg = geo(c['lat'], c['lon'], la, lo); r = km / 1.852
    x = ((brg - 45) % 360) / 90; i = int(x) % 4; w = x - int(x)
    tw = lambda q: q[i] * (1 - w) + q[(i + 1) % 4] * w
    r64, r50, r34, vmax = tw(c['r64']), tw(c['r50']), tw(c['r34']), c['v']
    rmw = max(8.0, 0.5 * r64) if r64 > 0 else 10.0
    knots = [(rmw, vmax)]
    for rr, vv in ((r64, 64), (r50, 50), (r34, 34)):
        if vmax > vv and rr > knots[-1][0]: knots.append((rr, vv))
    if r <= rmw: v = vmax * r / rmw
    elif r >= knots[-1][0]: v = knots[-1][1] * knots[-1][0] / r
    else:
        for (ra, va), (rb, vb) in zip(knots, knots[1:]):
            if ra <= r <= rb: v = va + (vb - va) * (r - ra) / (rb - ra); break
    beta = 35 if land else 20                                                    # inflow angle
    toward = brg - 90 - beta                                                     # counter-clockwise circulation, turned inward
    return v, v * (c['g'] / c['v'] if c['v'] else 1.25), (toward + 180) % 360, km, brg

def rain(c, la, lo, scale):
    dy = (la - c['lat']) * 111.2; dx = (lo - c['lon']) * 111.2 * math.cos(math.radians(c['lat']))
    fi = (dx - KM0) / DKM; fj = (-dy - KM0) / DKM                                 # field rows run north -> south
    if not (0 <= fi < NK - 1 and 0 <= fj < NK - 1): return 0.0
    i, j = int(fi), int(fj); a, b = fi - i, fj - j
    return float(FIELD[j, i] * (1 - a) * (1 - b) + FIELD[j, i + 1] * a * (1 - b) + FIELD[j + 1, i] * (1 - a) * b + FIELD[j + 1, i + 1] * a * b) * scale

def tm(v): return 3.96 + 2.45 * (1 + (v - 35) / 33)                              # R-CLIPER peak rain rate (in/day) vs intensity
def rscale(c, k): return 1.0 if k < n_obs else tm(c['v']) / tm(V0)

# ---------------- terrain at the buildings, catchments ----------------
CITY = mosaic(W + '/tiles', 13)
def elev_slope(la, lo):
    g = 0.0002; L, O = grid(la + 2 * g, la - 2 * g, lo - 2 * g, lo + 2 * g, 5, 5); E = sample(CITY, L, O)
    s, _, _ = slope_aspect(E, g * 111200, g * 111200 * math.cos(math.radians(la)))
    return float(E[2, 2]), float(s[1:4, 1:4].mean())

WS = mosaic(W + '/tiles_ws', 12)
wla, wlo = grid(20.94, 20.16, -105.44, -104.71, 976, 913); WE = sample(WS, wla, wlo)
_, rec, acc = fill_and_flow(WE, WE <= 0.5)
cell_km2 = (0.0008 * 111.2) ** 2 * math.cos(math.radians(20.65))
BASINS = {}
for key, (pla, plo) in {'pitillal': (20.6477, -105.2087), 'cuale': (20.6060, -105.2330)}.items():
    m = (abs(wla - pla) < 0.006) & (abs(wlo - plo) < 0.006)
    k = int(np.argmax(np.where(m, acc, 0))); ws = upstream(rec, acc.shape, k)
    pts = np.argwhere(ws[::6, ::6]) * 6
    # outline for the map: boundary cells of the mask on a 0.0024-degree lattice
    sub = ws[::3, ::3]; edge = sub & ~(np.roll(sub, 1, 0) & np.roll(sub, -1, 0) & np.roll(sub, 1, 1) & np.roll(sub, -1, 1))
    BASINS[key] = dict(area_km2=round(float(acc.flat[k] * cell_km2)), outlet=[round(float(wla.flat[k]), 4), round(float(wlo.flat[k]), 4)],
                       max_elev=round(float(WE[ws].max())), cells=[(float(wla[j, i]), float(wlo[j, i])) for j, i in pts],
                       mask=dict(lat0=20.94, dlat=-0.0024, lon0=-105.44, dlon=0.0024, rows=[list(map(int, np.nonzero(r)[0])) for r in sub]))

# ---------------- buildings ----------------
B = [dict(id='amapas', lat=20.5984, lon=-105.2382, floor=8, height_m=24, faces='N',
          name=['Amapas at Cafeto & Olas Altas', 'Amapas esq. Cafeto y Olas Altas'], hood=['Amapas', 'Amapas'],
          story=['8th floor, north-facing windows', '8.º piso, ventanas al norte'], basin=None),
     dict(id='ezapata', lat=20.6014, lon=-105.2340, floor=3, height_m=9, street_brg=78,
          name=['Francisca Rodríguez 336', 'Francisca Rodríguez 336'], hood=['Emiliano Zapata', 'Emiliano Zapata'],
          story=['3rd floor, elevated, ringed by 8-story buildings', '3.er piso, en alto, rodeado de edificios de 8 pisos'], basin='cuale'),
     dict(id='pitillal', lat=20.6477, lon=-105.2087, floor=1, height_m=2, river_m=160,
          name=['Cinco de Mayo & Calle España', 'Cinco de Mayo y Calle España'], hood=['El Pitillal', 'El Pitillal'],
          story=['street level, 2-story house', 'a nivel de calle, casa de 2 pisos'], basin='pitillal')]

def exposure(b, frm):
    """wind at the building relative to the 10-m open-water wind: (sustained factor, gust/sustained ratio).
    From ASCE 7 velocity-pressure exposure coefficients, Kz: open water (D) at 10 m = 1.18 is the reference."""
    if b['id'] == 'amapas':                                                      # 8th floor (~24 m)
        over_bay = 200 <= frm <= 330                                             # wind crossing the bay (open water) vs the city
        return (math.sqrt(1.38 / 1.18), 1.25) if over_bay else (math.sqrt(0.93 / 1.18), 1.40)
    if b['id'] == 'ezapata':                                                     # 3rd floor (~9 m), built-up
        return math.sqrt(0.70 / 1.18), 1.45
    return math.sqrt(0.57 / 1.18), 1.45                                          # street level (~4.5 m), built-up

KMH = 1.852
def lvl(x, th): return int(sum(x >= t for t in th))
WIND_TH = (39, 63, 93, 119)              # km/h, on max(sustained, gust / 1.3)
RATE_TH = (2.5, 7.6, 25, 50)             # mm/h
RUN_TH = (15, 30, 60, 100)               # mm in 3 h
RIVER_TH = (20, 40, 70, 110)             # catchment-mean mm in 6 h, ending 3 h earlier (time for water to reach town)
CAINE = lambda D: 14.82 * D ** -0.39     # Caine (1980) rainfall intensity-duration threshold for shallow landslides, mm/h

def series(b, k):
    s = SCN[k]['track']; out = dict(rate=[], cum=[], v=[], g=[], frm=[], km=[], vb=[], gb=[], basin=[], lv={})
    for i, (t, c) in enumerate(zip(times, s)):
        land = True
        v, g, frm, km, brg = wind(c, b['lat'], b['lon'], land)
        fs, gr = exposure(b, frm)
        r = rain(c, b['lat'], b['lon'], rscale(c, i))
        out['rate'].append(r); out['v'].append(v * KMH); out['g'].append(g * KMH); out['frm'].append(frm); out['km'].append(km)
        out['vb'].append(v * KMH * fs); out['gb'].append(v * KMH * fs * gr)
        if b['basin']:
            cells = BASINS[b['basin']]['cells']; out['basin'].append(float(np.mean([rain(c, la, lo, rscale(c, i)) for la, lo in cells])))
    rate = np.array(out['rate']); mm = rate * DT_H; mm[:n_obs] = 0                 # count rain from now on
    cum = np.cumsum(mm); out['cum'] = list(cum)
    def trail(a, hours, lag=0):
        n, L = int(round(hours / DT_H)), int(round(lag / DT_H)); c = np.concatenate([[0], np.cumsum(a)])
        return np.array([c[max(i + 1 - L, 0)] - c[max(i + 1 - L - n, 0)] for i in range(len(a))])
    wl = [lvl(max(vb, gb / 1.3), WIND_TH) for vb, gb in zip(out['vb'], out['gb'])]
    L = dict(wind=wl, rate=[lvl(x, RATE_TH) for x in rate], runoff=[lvl(x, RUN_TH) for x in trail(mm, 3)])
    if b['id'] == 'amapas':
        def face(frm, l):
            d = min(abs(frm - 0), 360 - abs(frm - 0))
            return l if d <= 67.5 else max(l - 1, 0) if d <= 112.5 else max(l - 2, 0)
        L['windows'] = [face(f, l) for f, l in zip(out['frm'], wl)]
    if b['basin']:
        bm = np.array(out['basin']) * DT_H; bm[:n_obs] = 0
        L['river'] = [lvl(x, RIVER_TH) for x in trail(bm, 6, lag=3)]
        out['basin6'] = list(trail(bm, 6, lag=3))
    if b['id'] != 'pitillal':                                                    # hillside sites: rainfall vs the landslide threshold
        ratio = np.zeros(len(mm))
        for D in (1, 3, 6, 12, 24, 36):
            ratio = np.maximum(ratio, trail(mm, D) / D / CAINE(D))
        L['slide'] = [lvl(x, (0.5, 1, 2, 3)) for x in ratio]; out['caine'] = list(ratio)
    out['lv'] = L
    return out

def onsets(lv):
    res = {}
    for name, a in lv.items():
        a = np.array(a); pk = int(a.max()); f = {}
        for th in (2, 3, 4):
            idx = np.nonzero(a >= th)[0]
            if len(idx): f[str(th)] = [F(times[idx[0]]), F(times[idx[-1]])]
        res[name] = dict(peak=pk, at=F(times[int(np.argmax(a))]), first=f)
    return res

R2 = lambda a, n=1: [round(float(x), n) for x in a]
for b in B:
    b['elev_m'], b['slope_deg'] = [round(x, 1) for x in elev_slope(b['lat'], b['lon'])]
    b['scen'] = {}
    for k in SCN:
        s = series(b, k)
        mi = int(np.argmin(s['km'][n_obs:])) + n_obs
        b['scen'][k] = dict(rate=R2(s['rate']), cum=R2(s['cum']), v=R2(s['v'], 0), g=R2(s['g'], 0), vb=R2(s['vb'], 0), gb=R2(s['gb'], 0), frm=R2(s['frm'], 0),
                            km=R2(s['km']), basin6=R2(s.get('basin6', [])), basin_rate=R2(s.get('basin', [])), caine=R2(s.get('caine', []), 2), lv=s['lv'], onsets=onsets(s['lv']),
                            closest=dict(km=round(s['km'][mi], 1), t=F(times[mi])), total=round(s['cum'][-1]), peak_rate=round(max(s['rate'][n_obs:]), 1),
                            peak_rate_t=F(times[n_obs + int(np.argmax(s['rate'][n_obs:]))]), peak_gb=round(max(s['gb'][n_obs:])), peak_gb_t=F(times[n_obs + int(np.argmax(s['gb'][n_obs:]))]))
        print(b['id'], k, 'closest', b['scen'][k]['closest'], 'total', b['scen'][k]['total'], 'peak rate', b['scen'][k]['peak_rate'], b['scen'][k]['peak_rate_t'],
              'peak gust bldg', b['scen'][k]['peak_gb'], b['scen'][k]['peak_gb_t'], {n: (o['peak'], o['first'].get('2', [None])[0], o['first'].get('3', [None])[0]) for n, o in b['scen'][k]['onsets'].items()})

# ---------------- write ----------------
q = np.clip(np.round(FIELD * 2.5), 0, 255).astype(np.uint8)
trk = lambda s: [[round(c['lat'], 4), round(c['lon'], 4), round(c['v'], 1), round(c['g'], 1)] + [round(x) for x in c['r34'] + c['r50'] + c['r64']] for c in s]
json.dump(dict(
    generated=F(dt.datetime.now(dt.timezone.utc)), t_obs=F(t_obs), n_obs=n_obs, times=[F(t) for t in times],
    advisory=dict(num=summ['advisory'], issued=summ['issued_local'], location=summ['location'], intermediate=summ['intermediate'], earlier_fix=next((p for p in tr if p.get('earlier_fix')), None), kt=V0, gust=G0, wind_kmh=summ['wind_kmh'], pressure=summ['pressure_mb'], move=summ['move_dir'], move_kmh=summ['move_kmh']),
    fixes=[dict(t=x['t'], lat=x['lat'], lon=x['lon'], eye_c=x['eye_c'], wall_c=x['wall_c']) for x in SAT['fixes']], motion=M,
    ir=SAT['ir'], rain=dict(km0=KM0, dkm=DKM, n=NK, scale=2.5, q=base64.b64encode(q.tobytes()).decode(), scans=SAT['rain_times']),
    scen={k: dict(track=trk(v['track']), landfall=v['landfall']) for k, v in SCN.items()},
    nhc_track=[dict(t=p['t'], lat=p['lat'], lon=p['lon'], kt=p['kt'], note=p.get('note')) for p in tr],
    basins={k: {kk: vv for kk, vv in v.items() if kk != 'cells'} for k, v in BASINS.items()},
    bldg=B, V0=V0, G0=G0, th=dict(wind=WIND_TH, rate=RATE_TH, runoff=RUN_TH, river=RIVER_TH)), open(OUT, 'w'), separators=(',', ':'))
print('wrote', OUT, os.path.getsize(OUT), 'landfall', {k: v['landfall'] for k, v in SCN.items()})
