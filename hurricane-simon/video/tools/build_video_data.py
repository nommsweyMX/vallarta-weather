"""Extra data for the Simon explainer video: a catchment view (Sierra above Vallarta) with drainage network and
the Pitillal / Cuale catchments, and a terrain cross-section from the bay into the Sierra.
Usage: build_video_data.py WORK OUTDIR    (WORK as for map/tools/build_map.py; writes video.json + images)"""
import sys, os, json, math, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map', 'tools'))
from terrain import mosaic, sample, grid, hillshade, fill_and_flow, upstream

W, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
M = mosaic(W + '/tiles_ws', 12)

# ---- catchment view ----
V = dict(lat0=20.72, lat1=20.33, lon0=-105.34, lon1=-104.92, w=1080)
c = math.cos(math.radians(20.53)); V['h'] = int(round(V['w'] * (V['lat0'] - V['lat1']) / ((V['lon1'] - V['lon0']) * c)))
la, lo = grid(V['lat0'], V['lat1'], V['lon0'], V['lon1'], V['h'], V['w'])
E = ndimage.gaussian_filter(sample(M, la, lo), 1.0)
# sea: the region connected to the bay, bounded by the OSM coastline (the terrain tiles have false shoals in the bay)
import glob
from PIL import ImageDraw
im = Image.new('L', (V['w'], V['h']), 0); dr = ImageDraw.Draw(im)
for f in glob.glob(W + '/osm/*.json'):
    try: els = json.load(open(f)).get('elements', [])
    except Exception: continue
    for e in els:
        if e.get('type') == 'way' and e.get('tags', {}).get('natural') == 'coastline' and 'geometry' in e:
            dr.line([((g['lon'] - V['lon0']) / (V['lon1'] - V['lon0']) * V['w'], (V['lat0'] - g['lat']) / (V['lat0'] - V['lat1']) * V['h']) for g in e['geometry']], fill=255, width=2)
lab, _ = ndimage.label(np.asarray(im) == 0)
sx, sy = int((-105.32 - V['lon0']) / (V['lon1'] - V['lon0']) * V['w']), int((V['lat0'] - 20.62) / (V['lat0'] - V['lat1']) * V['h'])
sea = (lab == lab[sy, sx]) & (E < 60)
E = np.where(sea, np.minimum(E, -5), np.maximum(E, 1))
dy = (V['lat0'] - V['lat1']) / V['h'] * 111200; dx = (V['lon1'] - V['lon0']) / V['w'] * 111200 * c
hs = hillshade(np.where(sea, 0, E), dy, dx, zf=1.4)
T = [(0, (34, 44, 38)), (300, (40, 48, 40)), (900, (52, 52, 44)), (1600, (64, 58, 50)), (2600, (78, 72, 66))]
rgb = np.stack([np.interp(E, [t[0] for t in T], [t[1][k] for t in T]) for k in range(3)], -1) * (0.5 + 0.8 * hs)[..., None]
ci = np.floor(np.maximum(E, 0) / 200); line = ((ci != np.roll(ci, 1, 0)) | (ci != np.roll(ci, 1, 1))) & ~sea
rgb = np.where(line[..., None], rgb * 1.22, rgb); rgb[sea] = (16, 31, 47)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f'{OUT}/catch_base.webp', quality=84, method=6)

# drainage on a half-resolution grid, catchments for the two rivers
h2, w2 = V['h'] // 2, V['w'] // 2
la2, lo2 = grid(V['lat0'], V['lat1'], V['lon0'], V['lon1'], h2, w2); E2 = ndimage.gaussian_filter(sample(M, la2, lo2), 0.7)
sea2 = np.asarray(Image.fromarray(sea.astype(np.uint8) * 255).resize((w2, h2), Image.NEAREST)) > 0
_, rec, acc = fill_and_flow(E2, sea2 | (E2 <= 0.5))
ck = ((V['lat0'] - V['lat1']) / h2 * 111.2) * ((V['lon1'] - V['lon0']) / w2 * 111.2 * c)
basins = {}
for key, (pla, plo) in {'pitillal': (20.6480, -105.2143), 'cuale': (20.6024, -105.2383)}.items():
    m = (abs(la2 - pla) < 0.006) & (abs(lo2 - plo) < 0.006)
    k = int(np.argmax(np.where(m, acc, 0))); ws = upstream(rec, acc.shape, k)
    basins[key] = dict(mask=ws, outlet=[float(la2.flat[k]), float(lo2.flat[k])], area=float(acc.flat[k] * ck), oxy=[(k % w2 + 0.5) * 2, (k // w2 + 0.5) * 2])
    big = np.asarray(Image.fromarray(ws.astype(np.uint8) * 255).resize((V['w'], V['h']), Image.NEAREST)) > 0
    edge = big & ~ndimage.binary_erosion(big, iterations=3)
    col = (255, 196, 92) if key == 'pitillal' else (120, 200, 255)
    rgba = np.zeros((V['h'], V['w'], 4), np.uint8); rgba[big] = col + (46,); rgba[edge] = col + (235,)
    Image.fromarray(rgba, 'RGBA').save(f'{OUT}/basin_{key}.png', optimize=True)
    print(key, 'area km2', round(basins[key]['area']), 'outlet', basins[key]['outlet'])
ch = acc * ck > 1.5
donors = np.zeros(acc.size, int)
for k in range(acc.size):
    if rec[k] >= 0 and ch.flat[k]: donors[rec[k]] += 1
seen, lines = set(), []
for h0 in [k for k in range(acc.size) if ch.flat[k] and donors[k] == 0]:
    k, pts = h0, []
    while k >= 0 and ch.flat[k] and not sea2.flat[k]:
        j, i = divmod(k, w2); pts.append([round((i + 0.5) * 2, 1), round((j + 0.5) * 2, 1)])
        if k in seen: break
        seen.add(k); k = int(rec[k])
    if len(pts) > 3:
        j, i = divmod(h0, w2); b = 'pitillal' if basins['pitillal']['mask'][j, i] else 'cuale' if basins['cuale']['mask'][j, i] else ''
        end = pts[-1]; kk = int(end[1] / 2) * w2 + int(end[0] / 2)
        lines.append(dict(b=b, a=round(float(acc.flat[min(kk, acc.size - 1)] * ck), 1), p=[x for q in pts[::2] + [pts[-1]] for x in q]))
print('channels', len(lines), 'in basins', sum(1 for l in lines if l['b']))

# ---- cross-section: from the bay through the Zona Romantica into the Sierra ----
la0p, lo0p, brg = 20.6045, -105.2900, 95.0
d = np.round(np.arange(0, 40.01, 0.1), 2)
pla = la0p + d * math.cos(math.radians(brg)) / 111.2; plo = lo0p + d * math.sin(math.radians(brg)) / (111.2 * math.cos(math.radians(20.6)))
pe = ndimage.gaussian_filter1d(sample(M, pla, plo), 1.5)
coast = float(d[np.argmax(pe > 2)])
prof = dict(km=d.tolist(), elev=[round(float(x)) for x in pe], coast_km=coast, top_km=float(d[int(np.argmax(pe))]), top_m=int(round(float(pe.max()))),
            start=[la0p, lo0p], end=[float(pla[-1]), float(plo[-1])], brg=brg)
print('profile coast at km', coast, 'top', prof['top_m'], 'm at km', prof['top_km'])

# where the cross-section line runs on the catchment view
def vpx(a, b): return [round((b - V['lon0']) / (V['lon1'] - V['lon0']) * V['w'], 1), round((V['lat0'] - a) / (V['lat0'] - V['lat1']) * V['h'], 1)]
json.dump(dict(view=dict(bbox=[V['lat0'], V['lat1'], V['lon0'], V['lon1']], w=V['w'], h=V['h']),
               basins={k: dict(outlet=v['outlet'], area_km2=round(v['area']), oxy=v['oxy']) for k, v in basins.items()},
               channels=lines, profile=prof, profile_line=[vpx(pla[0], plo[0]), vpx(pla[-1], plo[-1])]),
          open(f'{OUT}/video.json', 'w'), separators=(',', ':'))
print('video.json', os.path.getsize(f'{OUT}/video.json'))
