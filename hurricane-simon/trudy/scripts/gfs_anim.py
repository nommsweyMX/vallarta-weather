"""Animated GFS forecast, 18Z Mon 13 Oct 2026, 0-384 h every 3 h: 10-m wind, sea-level pressure, Trudy and Simon,
and the run's wind and rain at Puerto Vallarta. Usage: gfs_anim.py GRIBDIR LAND.geojson OUTDIR"""
import sys, os, glob, math, json, datetime as dt
import numpy as np, eccodes as ec
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Polygon as MPoly
from shapely.geometry import shape, box
G, LAND, OUT = sys.argv[1:4]
C0 = dt.datetime(2026, 10, 13, 18); TZ = -6; PV = (20.61, -105.2345)
INK, INK2, MUTE, GRID, SURF = '#0b0b0b', '#52514e', '#7a7975', '#e6e4df', '#fcfcfb'
rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'figure.facecolor': SURF, 'axes.facecolor': '#dfe9f0', 'savefig.facecolor': SURF, 'axes.edgecolor': GRID})

def read(h):
    f = open(f'{G}/f{h:03d}.grb2', 'rb'); d = {}
    while True:
        m = ec.codes_grib_new_from_file(f)
        if m is None: break
        sn = ec.codes_get(m, 'shortName'); sr = ec.codes_get(m, 'stepRange'); nj, ni = ec.codes_get(m, 'Nj'), ec.codes_get(m, 'Ni')
        v = ec.codes_get_values(m).reshape(nj, ni)
        if 'lat' not in d:
            d['lat'] = np.linspace(ec.codes_get(m, 'latitudeOfFirstGridPointInDegrees'), ec.codes_get(m, 'latitudeOfLastGridPointInDegrees'), nj)
            lo0, lo1 = ec.codes_get(m, 'longitudeOfFirstGridPointInDegrees'), ec.codes_get(m, 'longitudeOfLastGridPointInDegrees')
            d['lon'] = np.linspace(lo0, lo1, ni) - 360
        key = sn + ('_avg' if '-' in str(sr) else '')
        d[key] = v; ec.codes_release(m)
    return d

HRS = list(range(0, 385, 3)); F = {h: read(h) for h in HRS}
lat, lon = F[0]['lat'], F[0]['lon']; LA, LO = np.meshgrid(lat, lon, indexing='ij')
ipv, jpv = int(np.argmin(abs(lat - PV[0]))), int(np.argmin(abs(lon - PV[1])))
# --- rain at Puerto Vallarta from the average precipitation rates (6-h averages at multiples of 6 h, 3-h at the others)
acc = {0: 0.0}; tot6 = 0.0
for h in HRS[1:]:
    a = F[h].get('prate_avg')
    if a is None: acc[h] = acc[HRS[HRS.index(h) - 1]]; continue
    r = float(a[ipv - 1:ipv + 2, jpv - 1:jpv + 2].mean()) * 3600   # mm/h, 3x3 mean around the city
    if h % 6 == 0: tot6 += r * 6; acc[h] = tot6
    else: acc[h] = tot6 + r * 3
wpv = {h: float(np.hypot(F[h]['10u'], F[h]['10v'])[ipv, jpv]) * 3.6 for h in HRS}
ppv = {h: float(F[h]['prmsl'][ipv, jpv]) / 100 for h in HRS}

# --- track the lows: smoothed sea-level pressure minimum within 2.5 degrees of the last position
def smooth(p, k=2):
    q = p.copy()
    for _ in range(k): q[1:-1, 1:-1] = (q[1:-1, 1:-1] * 4 + q[:-2, 1:-1] + q[2:, 1:-1] + q[1:-1, :-2] + q[1:-1, 2:]) / 8
    return q
def track(start, h0=0, rmax=2.5, back=False):
    out = []; la0, lo0 = start; alive = True
    for h in (HRS[::-1] if back else HRS):
        if (h > h0) if back else (h < h0): continue
        p = smooth(F[h]['prmsl'] / 100); mask = (abs(LA - la0) <= rmax) & (abs(LO - lo0) <= rmax)
        if not mask.any(): break
        pm = np.where(mask, p, np.inf); i, j = np.unravel_index(np.argmin(pm), pm.shape)
        env = float(np.mean(p[(abs(LA - lat[i]) <= 5) & (abs(LO - lon[j]) <= 5)]))
        depth = env - float(p[i, j]); onedge = abs(lat[i] - la0) >= rmax - 0.01 or abs(lon[j] - lo0) >= rmax - 0.01
        if depth < 1.5 or (onedge and h != h0) or (h != h0 and math.hypot(lat[i] - la0, lon[j] - lo0) > 1.3): out.append(None); break
        vmax = float(np.max(np.where((abs(LA - lat[i]) <= 3) & (abs(LO - lon[j]) <= 3), np.hypot(F[h]['10u'], F[h]['10v']), 0))) * 1.94384
        out.append((h, float(lat[i]), float(lon[j]), float(F[h]['prmsl'][i, j]) / 100, vmax)); la0, lo0 = lat[i], lon[j]
    return [x for x in out if x]
TRUDY = track((10.6, -95.6)); SIMON = track((20.1, -107.4))
# a later storm in this run: first time after day 8 that a closed low >= 2.5 hPa deep appears in 9-17N 95-106W
LATE = []
for h in HRS:
    if h < 228: continue
    p = smooth(F[h]['prmsl'] / 100); m = (LA >= 11) & (LA <= 17) & (LO >= -105) & (LO <= -96)
    pm = np.where(m, p, np.inf); i, j = np.unravel_index(np.argmin(pm), pm.shape)
    env = float(np.mean(p[(abs(LA - lat[i]) <= 5) & (abs(LO - lon[j]) <= 5)]))
    if env - p[i, j] >= 3 and 11.3 < lat[i] < 16.7 and -104.7 < lon[j] < -96.3:
        fw = track((float(lat[i]), float(lon[j])), h0=h); bw = track((float(lat[i]), float(lon[j])), h0=h, back=True)
        LATE = sorted(bw[1:] + fw, key=lambda x: x[0]); break
print('late storm', LATE[0][:4] if LATE else None, '->', LATE[-1][:4] if LATE else None, len(LATE))
for x in LATE[::4]: print('   L', x[0], round(x[1], 2), round(x[2], 2), round(x[3]), 'hPa', round(x[4]), 'kt', round(math.hypot(x[1] - PV[0], (x[2] - PV[1]) * math.cos(math.radians(20))) * 111), 'km from PV')
json.dump(dict(trudy=TRUDY, simon=SIMON, late=LATE, pv=dict(wind=wpv, mslp=ppv, rain=acc)), open(OUT + '/gfs_tracks.json', 'w'))
print('Trudy tracked to', TRUDY[-1][:4] if TRUDY else None, len(TRUDY), 'steps; Simon to', SIMON[-1][:4] if SIMON else None)
for x in TRUDY[::8]: print('   T', x[0], round(x[1], 2), round(x[2], 2), round(x[3]), 'hPa', round(x[4]), 'kt')

# --- static land
EXT = (-120, 6, -88, 30)
polys = []
bx = box(*EXT)
for f in json.load(open(LAND))['features']:
    gi = shape(f['geometry']).intersection(bx)
    if gi.is_empty: continue
    for p in ([gi] if gi.geom_type == 'Polygon' else list(gi.geoms) if gi.geom_type == 'MultiPolygon' else []): polys.append(list(p.exterior.coords))
# wind colours, km/h, with the tropical-cyclone thresholds as edges
EDGES = [0, 20, 30, 39, 50, 63, 89, 119, 154, 178, 209, 400]
COLS = ['#eef3f6', '#cfe3ef', '#a6cde3', '#7ab4d6', '#ffe08a', '#ffbf47', '#ff8a3d', '#e8452c', '#b5179e', '#7a0f8a', '#3d0a5c']
CM = ListedColormap(COLS); NORM = BoundaryNorm(EDGES, CM.N)
sub = (lat >= EXT[1] - 1) & (lat <= EXT[3] + 1); subj = (lon >= EXT[0] - 1) & (lon <= EXT[2] + 1)
la_s, lo_s = lat[sub], lon[subj]
for k, h in enumerate(HRS):
    d = F[h]; spd = np.hypot(d['10u'], d['10v'])[np.ix_(sub, subj)] * 3.6; p = smooth(d['prmsl'][np.ix_(sub, subj)] / 100, 1)
    fig = plt.figure(figsize=(9.6, 7.4), dpi=110)
    ax = fig.add_axes([0.06, 0.30, 0.80, 0.62]); cax = fig.add_axes([0.875, 0.30, 0.018, 0.62]); bx2 = fig.add_axes([0.06, 0.06, 0.80, 0.17])
    ax.pcolormesh(lo_s, la_s, spd, cmap=CM, norm=NORM, shading='nearest', zorder=1)
    for pp in polys: ax.add_patch(MPoly(pp, closed=True, facecolor='none', edgecolor='#3a3a3a', linewidth=0.7, zorder=3))
    cs = ax.contour(lo_s, la_s, p, levels=np.arange(960, 1024, 4), colors='#2b2b2b', linewidths=0.55, alpha=0.75, zorder=4)
    ax.clabel(cs, fontsize=5.5, fmt='%d', inline_spacing=1)
    for trk, col, name in ((TRUDY, '#111', 'Trudy'), (SIMON, '#7a3b00', 'Simon'), (LATE, '#5b2a86', 'Second GFS storm')):
        past = [x for x in trk if x[0] <= h]
        if past:
            ax.plot([x[2] for x in past], [x[1] for x in past], color=col, linewidth=1.6, zorder=6)
            if past[-1][0] == h:
                ax.plot(past[-1][2], past[-1][1], 'o', color=col, markersize=6, markeredgecolor='white', zorder=7)
                ax.text(past[-1][2] + 0.4, past[-1][1] + 0.35, f"{name} {past[-1][3]:.0f} hPa", fontsize=7, color=col, zorder=8, fontweight='bold', bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.6))
            elif name == 'Trudy' and h - past[-1][0] <= 48:
                ax.text(past[-1][2] + 0.4, past[-1][1] - 0.9, 'Trudy falls apart inland\nin this run', fontsize=6.8, color=col, zorder=8, bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.6))
    ax.plot(PV[1], PV[0], '*', color='#d6336c', markersize=12, markeredgecolor='white', zorder=9); ax.text(PV[1] + 0.35, PV[0] + 0.15, 'Puerto Vallarta', fontsize=7.5, color='#d6336c', fontweight='bold', zorder=9)
    ax.set_xlim(EXT[0], EXT[2]); ax.set_ylim(EXT[1], EXT[3]); ax.set_aspect(1 / math.cos(math.radians(18)))
    ax.set_xticks(range(-120, -87, 5)); ax.set_xticklabels([f'{-x}°W' for x in range(-120, -87, 5)], fontsize=7); ax.set_yticks(range(10, 31, 5)); ax.set_yticklabels([f'{y}°N' for y in range(10, 31, 5)], fontsize=7); ax.tick_params(length=0)
    vt = C0 + dt.timedelta(hours=h); lt = vt + dt.timedelta(hours=TZ)
    fig.text(0.06, 0.965, 'GFS model, run of 6 pm Monday 13 October 2026 (18Z): the next 384 hours', fontsize=11.5, fontweight='bold', color=INK)
    fig.text(0.06, 0.935, f"{lt:%a %d %b, %-I %p} Vallarta time  ·  forecast hour {h:3d}", fontsize=10.5, color='#1c5cab', fontweight='bold')
    note = 'One model run, not a forecast. The NHC called this GFS track for Trudy unrealistic.' if h <= 180 else 'Days 8–16 of one model run: a storm that does not exist yet. Treat as a scenario only.'
    ax.text(0.99, 0.985, note, transform=ax.transAxes, fontsize=7.2, color='#b3410f', ha='right', va='top', zorder=10, bbox=dict(facecolor='white', edgecolor='#b3410f', linewidth=0.6, alpha=0.9, pad=2.5))
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CM), cax=cax, ticks=EDGES[:-1]); cb.ax.tick_params(labelsize=6.5, length=0); cb.set_label('10-m wind, km/h (63 tropical storm, 119 hurricane)', fontsize=7)
    # bottom strip: the run at Puerto Vallarta
    x = [C0 + dt.timedelta(hours=hh + TZ) for hh in HRS]
    bx2.fill_between(x, [acc[hh] for hh in HRS], color='#9ec9e8', alpha=0.6, step=None, zorder=1, label='rain since the run started, mm (right)')
    b2 = bx2.twinx(); bx2, b2 = b2, bx2   # wind on the left axis
    b2.set_zorder(bx2.get_zorder() + 1); b2.patch.set_visible(False)
    b2.plot(x, [wpv[hh] for hh in HRS], color='#e8452c', linewidth=1.3, label='10-m wind, km/h (left)')
    b2.axvline(lt, color=INK, linewidth=1.2); b2.plot(lt, wpv[h], 'o', color='#e8452c', markersize=4)
    b2.set_ylim(0, max(70, max(wpv.values()) * 1.15)); bx2.set_ylim(0, max(50, max(acc.values()) * 1.15))
    b2.set_ylabel('wind km/h', fontsize=7, color='#e8452c'); bx2.set_ylabel('rain mm', fontsize=7, color='#4a7fb5')
    for a_ in (b2, bx2): a_.tick_params(labelsize=6.5, length=0)
    days = [dt.datetime(2026, 10, 14) + dt.timedelta(days=i) for i in range(0, 17, 2)]
    b2.set_xticks(days); b2.set_xticklabels([dd.strftime('%a %d') for dd in days], fontsize=6.5); b2.set_xlim(x[0], x[-1])
    b2.text(x[1], b2.get_ylim()[1] * 0.86, f'At Puerto Vallarta in this run: wind {wpv[h]:.0f} km/h now, rain {acc[h]:.0f} mm so far', fontsize=7.2, color=INK)
    fig.text(0.06, 0.015, 'NOAA GFS 0.25°, 3-hourly. Lows tracked as the minimum of smoothed sea-level pressure. Isobars every 4 hPa. Wind at the city: nearest grid point, open terrain, no building exposure.', fontsize=6.2, color=MUTE)
    fig.savefig(f'{OUT}/frames/f{k:03d}.png'); plt.close(fig)
print('frames', len(HRS))
