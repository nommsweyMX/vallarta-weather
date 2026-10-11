"""Bahía de Banderas: bathymetry picture and wave-ray refraction for long hurricane swell.
Rays follow the linear dispersion relation for a wave period T and bend toward shallower (slower) water (Snell's law
in gradient form). Where rays crowd together at the shore, wave energy concentrates. Depths: AWS Terrain Tiles
(terrarium, zoom 10; in the ocean these come from global bathymetry, about 1 km scale), so this is a schematic.
Usage: waves.py WORK OUTDIR   (WORK/tiles_bay10)"""
import sys, os, json, math, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map', 'tools'))
from terrain import mosaic, sample, grid, hillshade

W, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
V = dict(lat0=20.90, lat1=20.36, lon0=-105.78, lon1=-105.18, w=1080)
cl = math.cos(math.radians(20.63)); V['h'] = int(round(V['w'] * (V['lat0'] - V['lat1']) / ((V['lon1'] - V['lon0']) * cl)))
M = mosaic(W + '/tiles_bay10', 10)
la, lo = grid(V['lat0'], V['lat1'], V['lon0'], V['lon1'], V['h'], V['w'])
E = ndimage.gaussian_filter(sample(M, la, lo), 1.2)
dx = (V['lon1'] - V['lon0']) / V['w'] * 111200 * cl; dy = (V['lat0'] - V['lat1']) / V['h'] * 111200
sea = E < 0
# picture: depth shading for the sea (lighter = shallower), hillshade for land, depth contours
d = np.clip(-E, 0, 1600)
t = np.sqrt(d / 1600)
sea_rgb = np.stack([np.interp(t, [0, 0.15, 0.5, 1], c) for c in ([70, 32, 18, 8], [150, 96, 52, 22], [190, 150, 98, 52])], -1)
hs = hillshade(np.where(sea, 0, E), dy, dx, zf=1.6)
land_rgb = np.array([46, 52, 42])[None, None] * (0.55 + 0.75 * hs)[..., None]
rgb = np.where(sea[..., None], sea_rgb, land_rgb)
for lev in (50, 100, 200, 500, 1000):
    ci = (-E >= lev); edge = ci & ~ndimage.binary_erosion(ci); rgb[edge & sea] = rgb[edge & sea] * 0.55 + np.array([200, 230, 255]) * 0.45
coast = ~sea & ndimage.binary_dilation(sea); rgb[coast] = (214, 190, 130)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f'{OUT}/bay_base.webp', quality=86, method=6)

# phase speed for period T in depth h (Newton on the dispersion relation)
T = 14.0; g = 9.81; om = 2 * math.pi / T
def cfun(h):
    h = np.maximum(h, 0.5); k = om ** 2 / g * np.ones_like(h)
    for _ in range(30): f = g * k * np.tanh(k * h) - om ** 2; df = g * np.tanh(k * h) + g * k * h / np.cosh(k * h) ** 2; k = k - f / df
    return om / k
C = np.where(sea, cfun(-E), np.nan)
Cf = np.nan_to_num(C, nan=float(np.nanmin(C)))
gy, gx = np.gradient(Cf, dy, dx)              # rows run north -> south: gy is d/d(south)
gnorth = -gy
def interp(a, x, y):
    i, j = int(x), int(y)
    if not (0 <= i < V['w'] - 1 and 0 <= j < V['h'] - 1): return None
    fx, fy = x - i, y - j
    return a[j, i] * (1 - fx) * (1 - fy) + a[j, i + 1] * fx * (1 - fy) + a[j + 1, i] * (1 - fx) * fy + a[j + 1, i + 1] * fx * fy

def trace(x, y, th):
    pts = [(x, y)]; step = 0.6
    for _ in range(4000):
        if not sea[int(y), int(x)] or E[int(y), int(x)] > -1.5: return pts, True
        c = interp(Cf, x, y); cx_ = interp(gx, x, y); cy_ = interp(gnorth, x, y)
        if c is None: return pts, False
        th += -(cx_ * math.cos(th) - cy_ * math.sin(th)) / c * step * dx
        x += math.sin(th) * step; y -= math.cos(th) * step
        if not (0 <= x < V['w'] - 1 and 0 <= y < V['h'] - 1): return pts, False
        pts.append((x, y))
    return pts, False

res = {}
for name, frm in (('SW', 225), ('S', 195), ('W', 265)):
    th0 = math.radians((frm + 180) % 360); rays = []; hits = []
    # launch along a line perpendicular to the wave direction, offshore of the bay mouth
    cx0, cy0 = 40, V['h'] * 0.62 if frm < 250 else V['h'] * 0.5
    px, py = math.cos(th0), math.sin(th0)                      # perpendicular to travel, in pixel space (x east, y south)
    for s in np.linspace(-900, 900, 260):
        x, y = cx0 + px * s - math.sin(th0) * 0, cy0 + py * s
        # back off along the ray direction until in the domain's offshore water
        for _ in range(400):
            if 2 <= x < V['w'] - 2 and 2 <= y < V['h'] - 2 and sea[int(y), int(x)] and -E[int(y), int(x)] > 300: break
            x += math.sin(th0) * 3; y -= math.cos(th0) * 3
        else: continue
        if not (2 <= x < V['w'] - 2 and 2 <= y < V['h'] - 2): continue
        pts, hit = trace(x, y, th0)
        if len(pts) > 10:
            rays.append([round(c, 1) for p in pts[::6] + [pts[-1]] for c in p])
            if hit: hits.append(pts[-1])
    # shoreline energy: rays arriving per 1.5 km of coast, relative to the median
    B = 18                                                       # about 1 km cells along the shore
    H2 = np.zeros((V['h'] // B + 1, V['w'] // B + 1))
    for hx, hy in hits: H2[int(hy) // B, int(hx) // B] += 1
    mean = H2[H2 > 0].mean() if (H2 > 0).any() else 1
    spots = [[int(i * B + B / 2), int(j * B + B / 2), round(float(H2[j, i] / mean), 2),
              round(float(V['lat0'] - (j * B + B / 2) / V['h'] * (V['lat0'] - V['lat1'])), 4), round(float(V['lon0'] + (i * B + B / 2) / V['w'] * (V['lon1'] - V['lon0'])), 4)]
             for j, i in zip(*np.nonzero(H2 > 0))]
    res[name] = dict(frm=frm, rays=rays, spots=spots)
    print(name, 'rays', len(rays), 'hits', len(hits), 'max rel', max((s[2] for s in spots), default=0))
json.dump(dict(view=dict(bbox=[V['lat0'], V['lat1'], V['lon0'], V['lon1']], w=V['w'], h=V['h']), T=T, dirs=res,
               depth_note='Terrarium bathymetry (global grid); schematic'), open(f'{OUT}/waves.json', 'w'), separators=(',', ':'))
print('waves.json', os.path.getsize(f'{OUT}/waves.json'))
