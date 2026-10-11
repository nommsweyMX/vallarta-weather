"""Wind and rain over the whole Bay of Banderas on the NHC track, and the worst hours at the three sites.
Usage: bay_fields.py WORK MAP.json OUT.json
WORK holds mapwork/sat.json + rain_stack.npy and tiles_reg/ (as for build_map.py). Grid fields (0.01 deg):
peak sustained wind over open water if the center follows the NHC line exactly (not capped by the NHC odds), the time of that
peak, the direction then, when 34-kt (63 km/h, 39 mph) wind first arrives and ends, and the rain total from now to Monday noon
with the same scaling as the map page (satellite field scaled to the SMN upper bound). The site summaries come from the
map page series, which include the NHC-odds cap and the building exposure."""
import sys, os, re, json, math, datetime as dt, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'map', 'tools'))
from simon_phys import geo, wind, tm, lvl, KMH
from terrain import mosaic, sample
W, MJ, OUT = sys.argv[1:4]; TCP = sys.argv[4] if len(sys.argv) > 4 else None
MP = json.load(open(MJ)); SAT = json.load(open(W + '/mapwork/sat.json'))
STACK = np.load(W + '/mapwork/rain_stack.npy'); FIELD = STACK.mean(0) * MP['rain']['cal']
KM0, DKM, NK = SAT['grid']['km0'], SAT['grid']['dkm'], SAT['grid']['n']
P = lambda s: dt.datetime.strptime(s, '%Y-%m-%dT%H:%MZ'); F = lambda t: t.strftime('%Y-%m-%dT%H:%MZ')
times = [P(t) for t in MP['times']]; n_obs = MP['n_obs']; DT_H = 10 / 60; V0 = float(MP['V0'])
TR = MP['scen']['nhc']['track']
track = [dict(lat=p[0], lon=p[1], v=p[2], g=p[3], r34=p[4:8], r50=p[8:12], r64=p[12:16]) for p in TR]

def rain(c, la, lo, scale):
    dy = (la - c['lat']) * 111.2; dx = (lo - c['lon']) * 111.2 * math.cos(math.radians(c['lat']))
    fi = (dx - KM0) / DKM; fj = (-dy - KM0) / DKM
    if not (0 <= fi < NK - 1 and 0 <= fj < NK - 1): return 0.0
    i, j = int(fi), int(fj); a, b = fi - i, fj - j
    return float(FIELD[j, i] * (1 - a) * (1 - b) + FIELD[j, i + 1] * a * (1 - b) + FIELD[j + 1, i] * (1 - a) * b + FIELD[j + 1, i + 1] * a * b) * scale
def rscale(c, k): return 1.0 if k < n_obs else tm(c['v']) / tm(V0)

# ---- grid over the bay ----
LAT0, LAT1, LON0, LON1, D = 20.92, 20.30, -105.80, -105.10, 0.01
ny, nx = int(round((LAT0 - LAT1) / D)) + 1, int(round((LON1 - LON0) / D)) + 1
lats = [LAT0 - j * D for j in range(ny)]; lons = [LON0 + i * D for i in range(nx)]
REG = mosaic(W + '/tiles_reg', 8)
LA, LO = np.meshgrid(np.array(lats), np.array(lons), indexing='ij'); EL = sample(REG, LA.ravel(), LO.ravel()).reshape(ny, nx)
land = (EL > 1.0)
peak = np.zeros((ny, nx)); peak_i = np.zeros((ny, nx), int); pdir = np.zeros((ny, nx)); arr = np.full((ny, nx), -1, int); end = np.full((ny, nx), -1, int)
rain_mm = np.zeros((ny, nx)); prate = np.zeros((ny, nx)); prate_i = np.zeros((ny, nx), int); hf_arr = np.full((ny, nx), -1, int)
for j, la in enumerate(lats):
    for i, lo in enumerate(lons):
        pk = 0.0
        for k, c in enumerate(track):
            v, g, frm, km, brg = wind(c, la, lo, bool(land[j, i]))
            if v > pk: pk = v; peak_i[j, i] = k; pdir[j, i] = frm
            if v >= 34:
                if arr[j, i] < 0: arr[j, i] = k
                end[j, i] = k
            if v >= 64 and hf_arr[j, i] < 0: hf_arr[j, i] = k
            if k >= n_obs:
                r = rain(c, la, lo, rscale(c, k)); rain_mm[j, i] += r * DT_H
                if r > prate[j, i]: prate[j, i] = r; prate_i[j, i] = k
        peak[j, i] = pk
print('grid', ny, nx, 'peak kt max', peak.max().round(1), 'rain max mm', rain_mm[land].max().round(0), 'land cells', int(land.sum()))

# ---- named places on the bay (nearest grid cell) ----
PLACES = [('Punta Mita', 20.771, -105.526), ('Sayulita', 20.869, -105.441), ('Bucerías', 20.753, -105.333), ('Nuevo Vallarta', 20.699, -105.296),
          ('Aeropuerto PVR', 20.680, -105.254), ('El Pitillal', 20.648, -105.209), ('Centro PV', 20.610, -105.234), ('Zona Romántica', 20.603, -105.237),
          ('Amapas', 20.598, -105.238), ('Mismaloya', 20.531, -105.295), ('Boca de Tomatlán', 20.511, -105.318), ('Yelapa', 20.493, -105.445),
          ('Cabo Corrientes', 20.405, -105.690), ('El Tuito', 20.325, -105.321), ('Ixtapa', 20.700, -105.210), ('Las Juntas', 20.673, -105.232)]
def cell(la, lo): return int(round((LAT0 - la) / D)), int(round((lo - LON0) / D))
places = []
for nm, la, lo in PLACES:
    j, i = cell(la, lo)
    if not (0 <= j < ny and 0 <= i < nx): continue
    places.append(dict(name=nm, lat=la, lon=lo, peak_kt=round(float(peak[j, i]), 1), peak_t=F(times[peak_i[j, i]]), dir=round(float(pdir[j, i])),
                       arr=F(times[arr[j, i]]) if arr[j, i] >= 0 else None, end=F(times[end[j, i]]) if end[j, i] >= 0 else None,
                       hf=F(times[hf_arr[j, i]]) if hf_arr[j, i] >= 0 else None, rain_mm=round(float(rain_mm[j, i])), prate=round(float(prate[j, i]), 1), prate_t=F(times[prate_i[j, i]])))

# ---- site summaries from the map page series (NHC-odds cap + exposure) ----
def win(a, th):
    idx = [k for k, x in enumerate(a) if x >= th]
    return [F(times[idx[0]]), F(times[idx[-1]]), idx[-1] == len(a) - 1] if idx else None
sites = []
for b in MP['bldg']:
    s = b['scen']['nhc']; gb = s['gb']; vb = s['vb']; rate = s['rate']; lv = s['lv']
    kpk = int(np.argmax(gb)); gpk = gb[kpk]
    worst_w = win([1 if x >= 0.85 * gpk else 0 for x in gb], 1)
    krp = int(np.argmax(rate)); rpk = rate[krp]
    heavy = win(rate, 7.6); heaviest = win([1 if x >= max(0.6 * rpk, 7.6) else 0 for x in rate], 1)
    cum = s['cum']
    # wettest 6 h window
    n6 = int(round(6 / DT_H)); mm = np.array(rate) * DT_H; mm[:n_obs] = 0; c = np.concatenate([[0], np.cumsum(mm)]); w6 = c[n6:] - c[:-n6]
    k6 = int(np.argmax(w6)) if len(w6) else 0
    sites.append(dict(id=b['id'], name=b['name'], hood=b['hood'], story=b['story'], lat=b['lat'], lon=b['lon'], floor=b['floor'],
                      wind=dict(peak_vb_kmh=round(max(vb)), peak_gb_kmh=round(gpk), peak_t=F(times[kpk]), dir_at_peak=round(s['frm'][kpk]),
                                ts=win(lv['wind'], 2), strong=win(lv['wind'], 3), worst=worst_w, windows=win(lv['windows'], 2) if 'windows' in lv else None),
                      rain=dict(total_mm=round(cum[-1]), peak_rate=round(rpk, 1), peak_t=F(times[krp]), heavy=heavy, heaviest=heaviest,
                                wettest6=[F(times[k6]), F(times[min(k6 + n6, len(times) - 1)]), round(float(w6[k6]))] if len(w6) else None),
                      river=dict(elevated=win(lv['river'], 2), dangerous=win(lv['river'], 3), extreme=win(lv['river'], 4)) if 'river' in lv else None,
                      streets=dict(some=win(lv['runoff'], 2), bad=win(lv['runoff'], 3)),
                      slide=dict(possible=win(lv['slide'], 2), likely=win(lv['slide'], 3)) if 'slide' in lv else None,
                      closest=s['closest']))
WC = MP['wind_cal']
# NHC rainfall statement ('... totals of 8 to 16 inches ..., with isolated maximum ... totals of 30 inches ...'); mm as the NHC rounds them
rain_nhc = None
if TCP and os.path.exists(TCP):
    import html as _h; raw = open(TCP, encoding='utf-8', errors='replace').read(); m = re.search(r'<pre[^>]*>(.*?)</pre>', raw, re.S); body = _h.unescape(m.group(1)) if m else raw
    body = re.sub(r'\s+', ' ', body); m1 = re.search(r'totals of (\d+) to (\d+) inches', body); m2 = re.search(r'isolated (?:maximum )?(?:storm )?totals? of (\d+) inches', body)
    if m1: lo, hi = int(m1.group(1)), int(m1.group(2)); iso = int(m2.group(1)) if m2 else None; mm = lambda x: {8: 200, 10: 250, 12: 300, 15: 380, 16: 400, 20: 500, 25: 640, 30: 760}.get(x, int(round(x * 25.4 / 10) * 10)); rain_nhc = dict(lo=lo, hi=hi, iso=iso, mm=[mm(lo), mm(hi), mm(iso) if iso else None], add=('additional' in body[max(0, m1.start() - 60):m1.start()]))
print('rain_nhc', rain_nhc)
out = dict(generated=MP['generated'], t_obs=MP['t_obs'], advisory=MP['advisory'], times=MP['times'], n_obs=n_obs, wind_cal=WC, rain_cal=MP['rain']['cal'], cal_max24=MP['rain']['cal_max24'],
           landfall=MP['scen']['nhc']['landfall'], rain_nhc=rain_nhc, track=[[round(c['lat'], 3), round(c['lon'], 3), round(c['v'])] for c in track],
           grid=dict(lat0=LAT0, lon0=LON0, d=D, ny=ny, nx=nx, land=[int(x) for x in land.ravel()], peak_kt=[round(float(x), 1) for x in peak.ravel()], peak_i=[int(x) for x in peak_i.ravel()],
                     dir=[round(float(x)) for x in pdir.ravel()], arr=[int(x) for x in arr.ravel()], end=[int(x) for x in end.ravel()], hf=[int(x) for x in hf_arr.ravel()],
                     rain_mm=[round(float(x)) for x in rain_mm.ravel()], prate_i=[int(x) for x in prate_i.ravel()], elev=[round(float(x)) for x in EL.ravel()]),
           places=places, sites=sites)
json.dump(out, open(OUT, 'w'), separators=(',', ':')); print('wrote', OUT, os.path.getsize(OUT))
for p in places: print(p['name'], 'peak', p['peak_kt'], 'kt at', p['peak_t'][5:16], 'from', p['dir'], 'arr', p['arr'], 'hf', p['hf'], 'rain', p['rain_mm'])
for s in sites: print(s['id'], s['wind'], s['rain']['total_mm'], s['rain']['wettest6'], s['river'], s['streets'], s['slide'], s['closest'])
