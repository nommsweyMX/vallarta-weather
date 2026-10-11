"""Map layers for the Simon map page: shaded-relief base images (light and dark) for each view, vector layers
(coast, rivers, streets, buildings) in each view's pixel space, labels, and the regional base under the satellite loop.
Usage: build_layers.py WORK OUTDIR
WORK holds tiles/ (terrarium z13), tiles_ws/ (z12), tiles_reg/ (z8), osm/*.json (Overpass), osm/zr_api.xml and
raw/osm__*.xml (OSM API extracts), mapwork/map.json (catchments)."""
import sys, os, glob, json, math, xml.etree.ElementTree as ET, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from terrain import mosaic, sample, grid, hillshade, fill_and_flow

W, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
VIEWS = {
    'city': dict(lat0=20.80, lat1=20.46, lon0=-105.40, lon1=-105.06, w=900, dem='tiles_ws', z=12, contour=100, minor=False),
    'zr':   dict(lat0=20.6110, lat1=20.5915, lon0=-105.2470, lon1=-105.2260, w=800, dem='tiles', z=13, contour=10, minor=True),
    'pit':  dict(lat0=20.6600, lat1=20.6360, lon0=-105.2260, lon1=-105.1950, w=800, dem='tiles', z=13, contour=5, minor=True),
}
for v in VIEWS.values():
    c = math.cos(math.radians((v['lat0'] + v['lat1']) / 2))
    v['h'] = int(round(v['w'] * (v['lat0'] - v['lat1']) / ((v['lon1'] - v['lon0']) * c)))

TINT_L = [(-1e9, (205, 225, 238)), (0.5, (233, 239, 226)), (100, (225, 233, 212)), (400, (222, 222, 198)), (900, (214, 204, 182)), (1600, (204, 190, 172)), (2600, (196, 184, 176))]
TINT_D = [(-1e9, (16, 30, 44)), (0.5, (35, 44, 38)), (100, (38, 46, 37)), (400, (44, 46, 38)), (900, (50, 46, 40)), (1600, (56, 50, 46)), (2600, (62, 58, 56))]
def tint(E, T):
    xs = [max(t[0], -50) for t in T]; return np.stack([np.interp(E, xs, [t[1][k] for t in T]) for k in range(3)], -1)

# ---- OSM ways from Overpass JSON and OSM API XML ----
ways = {}
for f in glob.glob(W + '/osm/*.json'):
    try: j = json.load(open(f))
    except Exception: continue
    for e in j.get('elements', []):
        if e['type'] == 'way' and 'geometry' in e: ways[e['id']] = (e.get('tags', {}), [(g['lat'], g['lon']) for g in e['geometry']])
        if e['type'] == 'relation':
            for m in e.get('members', []):
                if m.get('type') == 'way' and 'geometry' in m and m.get('role') == 'outer':
                    ways[('r', e['id'], m['ref'])] = (dict(e.get('tags', {})), [(g['lat'], g['lon']) for g in m['geometry']])
for f in [W + '/osm/zr_api.xml'] + glob.glob(W + '/raw/osm__*.xml'):
    r = ET.parse(f).getroot(); nd = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in r.iter('node')}
    for w in r.iter('way'):
        t = {x.get('k'): x.get('v') for x in w.iter('tag')}; refs = [x.get('ref') for x in w.iter('nd')]
        if all(x in nd for x in refs): ways[int(w.get('id'))] = (t, [nd[x] for x in refs])
print('ways', len(ways))

SEA_SEED = {'city': (20.65, -105.33), 'zr': (20.600, -105.2455), 'pit': None}
def sea_mask(key, v):
    """sea = the region connected to a point in the bay, bounded by the OSM coastline."""
    if not SEA_SEED[key]: return np.zeros((v['h'], v['w']), bool)
    from PIL import ImageDraw
    from scipy import ndimage
    im = Image.new('L', (v['w'], v['h']), 0); d = ImageDraw.Draw(im)
    for t, ll in ways.values():
        if t.get('natural') == 'coastline': d.line([px(v, a, b) for a, b in ll], fill=255, width=2)
    lab, _ = ndimage.label(np.asarray(im) == 0)
    x, y = px(v, *SEA_SEED[key]); return lab == lab[int(y), int(x)]

def base(key, v):
    M = mosaic(W + '/' + v['dem'], v['z']); la, lo = grid(v['lat0'], v['lat1'], v['lon0'], v['lon1'], v['h'], v['w'])
    E = sample(M, la, lo); dy = (v['lat0'] - v['lat1']) / v['h'] * 111200; dx = (v['lon1'] - v['lon0']) / v['w'] * 111200 * math.cos(math.radians(la.mean()))
    from scipy import ndimage
    E = ndimage.gaussian_filter(E, 1.0 if key == 'city' else 9.0)                 # source DEM is ~90 m: smooth the upsampling blocks
    sea = sea_mask(key, v); E = np.where(sea, np.minimum(E, -5), np.maximum(E, 1))
    hs = hillshade(E, dy, dx, zf=1.3 if key == 'city' else 2.0)
    ci = np.floor(np.maximum(E, 0) / v['contour']); line = (ci != np.roll(ci, 1, 0)) | (ci != np.roll(ci, 1, 1)); line &= ~sea
    for mode, T in (('light', TINT_L), ('dark', TINT_D)):
        rgb = tint(E, T); rgb[sea] = (198, 221, 236) if mode == 'light' else (17, 33, 50)
        shade = (0.62 + 0.42 * hs) if mode == 'light' else (0.55 + 0.75 * hs)
        rgb = np.where(sea[..., None], rgb, rgb * shade[..., None])
        rgb = np.where(line[..., None], rgb * (0.86 if mode == 'light' else 1.25), rgb)
        Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f'{OUT}/base_{key}_{mode}.webp', quality=80, method=6)
    # steep slopes (landslide-prone) as an alpha mask
    from terrain import slope_aspect
    sl, _, _ = slope_aspect(E, dy, dx); steep = (sl >= 22) & ~sea
    Image.fromarray(np.stack([np.full(steep.shape, 255, np.uint8), (steep * 255).astype(np.uint8)], -1), 'LA').save(f'{OUT}/slope_{key}.png', optimize=True)
    return M, E, la, lo

def px(v, la, lo): return ((lo - v['lon0']) / (v['lon1'] - v['lon0']) * v['w'], (v['lat0'] - la) / (v['lat0'] - v['lat1']) * v['h'])

def simplify(pts, tol):
    if len(pts) < 3: return pts
    a, b = np.array(pts[0]), np.array(pts[-1]); d = b - a; n = np.hypot(*d)
    P = np.array(pts); q = P - a; dist = np.abs(d[0] * q[:, 1] - d[1] * q[:, 0]) / n if n > 0 else np.hypot(q[:, 0], q[:, 1])
    i = int(np.argmax(dist))
    if dist[i] > tol: return simplify(pts[:i + 1], tol)[:-1] + simplify(pts[i:], tol)
    return [pts[0], pts[-1]]

def clip_in(v, pts, m=40): return any(-m <= x <= v['w'] + m and -m <= y <= v['h'] + m for x, y in pts)
def enc(pts): return [round(c, 1) for p in pts for c in p]

ROAD = {'motorway': 0, 'trunk': 0, 'primary': 0, 'secondary': 1, 'tertiary': 2, 'motorway_link': 1, 'trunk_link': 1, 'primary_link': 1,
        'secondary_link': 2, 'tertiary_link': 2, 'residential': 3, 'unclassified': 3, 'living_street': 3, 'pedestrian': 4, 'steps': 4, 'footway': 5}
STREET_LABELS = {'zr': ['Olas Altas', 'Amapas', 'Francisca Rodríguez', 'Basilio Badillo', 'Ignacio L. Vallarta', 'Insurgentes', 'Púlpito', 'Francisco I. Madero', 'Lázaro Cárdenas', 'Constitución', 'Pino Suárez', 'Aquiles Serdán', 'Manuel M. Diéguez', 'Gómez', 'Rodolfo Gómez', 'Cafeto'],
                 'pit': ['Cinco de Mayo', 'España', 'Avenida Prisciliano Sánchez', 'Avenida Politécnico Nacional', 'Independencia', 'Hidalgo', 'Morelos', 'Avenida Francisco Villa', 'Avenida Las Torres', 'Juárez', 'Libertad', 'Guadalupe Victoria', 'Lázaro Cárdenas', 'Allende', 'Galeana', 'Brasil', 'Argentina', 'Venezuela', 'Colombia', 'Chile']}

L = dict(views={})
for key, v in VIEWS.items():
    M, E, la, lo = base(key, v)
    lay = dict(roads=[[], [], [], [], [], []], rivers=[], streams=[], coast=[], water=[], bldg=[], labels=[], streets=[])
    tol = 1.2 if key == 'city' else 0.6
    names = {}
    for wid, (t, ll) in ways.items():
        pts = [px(v, a, b) for a, b in ll]
        if not clip_in(v, pts): continue
        hw = t.get('highway')
        if hw in ROAD:
            c = ROAD[hw]
            if key == 'city' and c >= 3 and hw != 'residential' and hw != 'unclassified': continue
            if key == 'city' and c == 5: continue
            if c == 5 and not v['minor']: continue
            lay['roads'][c].append(enc(simplify(pts, tol)))
            nm = t.get('name')
            if nm and key in STREET_LABELS and any(nm.lower().endswith(s.lower()) or nm.lower() == s.lower() for s in STREET_LABELS[key]):
                names.setdefault(nm, []).append(pts)
        elif t.get('waterway') in ('river',):
            lay['rivers'].append(enc(simplify(pts, tol)))
        elif t.get('waterway') in ('stream', 'canal', 'drain', 'ditch'):
            lay['streams'].append(enc(simplify(pts, tol)))
        elif t.get('natural') == 'coastline':
            lay['coast'].append(enc(simplify(pts, tol)))
        elif t.get('natural') in ('water', 'wetland') or t.get('landuse') == 'reservoir':
            lay['water'].append(enc(simplify(pts, tol)))
        elif 'building' in t and key != 'city':
            lv = t.get('building:levels'); h = t.get('height')
            try: lvn = int(float(lv)) if lv else (int(float(h) / 3) if h else 0)
            except ValueError: lvn = 0
            lay['bldg'].append([lvn] + enc(simplify(pts, 0.3)))
    # street name labels: middle of the longest run of each named street
    for nm, runs in names.items():
        best = max(runs, key=lambda p: sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1)))
        seg = max(range(len(best) - 1), key=lambda i: math.hypot(best[i + 1][0] - best[i][0], best[i + 1][1] - best[i][1]))
        (x1, y1), (x2, y2) = best[seg], best[seg + 1]; ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        if 0 <= (x1 + x2) / 2 <= v['w'] and 0 <= (y1 + y2) / 2 <= v['h']:
            lay['streets'].append([nm.replace('Avenida ', 'Av. '), round((x1 + x2) / 2, 1), round((y1 + y2) / 2, 1), round(ang, 1)])
    if key == 'city':
        # drainage network from the terrain (channels draining more than 4 km2), to show rivers up in the sierra
        wla, wlo = grid(v['lat0'], v['lat1'], v['lon0'], v['lon1'], v['h'] // 2, v['w'] // 2); WE = sample(M, wla, wlo)
        _, rec, acc = fill_and_flow(WE, WE <= 0.5)
        ck = ((v['lat0'] - v['lat1']) / (v['h'] // 2) * 111.2) * ((v['lon1'] - v['lon0']) / (v['w'] // 2) * 111.2 * math.cos(math.radians(20.63)))
        ch = acc * ck > 4; seen = set(); lines = []
        # trace each channel cell downstream into polylines, starting from channel heads
        donors = np.zeros(acc.size, int)
        for k in range(acc.size):
            if rec[k] >= 0 and ch.flat[k]: donors[rec[k]] += 1
        heads = [k for k in range(acc.size) if ch.flat[k] and donors[k] == 0]
        for h0 in heads:
            k, pts = h0, []
            while k >= 0 and ch.flat[k] and WE.flat[k] > 0.5:
                j, i = divmod(k, wla.shape[1]); pts.append(((i + 0.5) * 2, (j + 0.5) * 2))
                if k in seen: break
                seen.add(k); k = int(rec[k])
            if len(pts) > 2: lines.append([round(float(acc.flat[h0] * ck), 1), enc(simplify(pts, 1.5))])
        # width class by drainage area at the line's end
        lay['drain'] = []
        for _, e in lines:
            x, y = e[-2] / 2 - 0.5, e[-1] / 2 - 0.5; k = int(round(y)) * wla.shape[1] + int(round(x))
            a = float(acc.flat[min(max(k, 0), acc.size - 1)] * ck)
            lay['drain'].append([0 if a < 20 else 1 if a < 100 else 2] + e)
        # highest summits per 6-km cell (for mountain labels)
        peaks = []
        cs = int(v['w'] * 6 / ((v['lon1'] - v['lon0']) * 111.2 * math.cos(math.radians(20.63))))
        for j0 in range(0, v['h'], cs):
            for i0 in range(0, v['w'], cs):
                blk = E[j0:j0 + cs, i0:i0 + cs]
                if blk.size == 0 or blk.max() < 500: continue
                j, i = np.unravel_index(np.argmax(blk), blk.shape)
                if 3 < j0 + j < v['h'] - 3 and 3 < i0 + i < v['w'] - 3 and blk.max() >= E[max(j0 + j - cs // 2, 0):j0 + j + cs // 2, max(i0 + i - cs // 2, 0):i0 + i + cs // 2].max():
                    peaks.append([int(i0 + i), int(j0 + j), int(round(blk.max()))])
        lay['peaks'] = peaks
    lay['roads'] = [r for r in lay['roads']]
    L['views'][key] = dict(bbox=[v['lat0'], v['lat1'], v['lon0'], v['lon1']], w=v['w'], h=v['h'], contour=v['contour'], layers=lay)
    print(key, v['w'], v['h'], {k: len(x) if not isinstance(x[0] if x else None, list) or k != 'roads' else [len(y) for y in x] for k, x in lay.items()})

# ---- regional base under the satellite loop (dark, with coastline) ----
R = mosaic(W + '/tiles_reg', 8); rla, rlo = grid(22.2, 15.0, -109.4, -101.8, 480, 480); RE = sample(R, rla, rlo)
hs = hillshade(RE, 7.2 / 480 * 111200, 7.6 / 480 * 111200 * math.cos(math.radians(18.6)), zf=8)
rgb = np.where((RE > 0.5)[..., None], np.array([46, 52, 44])[None, None] * (0.6 + 0.7 * hs)[..., None], np.array([14, 26, 40])[None, None] + 0 * hs[..., None])
land = RE > 0.5; coast = land & ~(np.roll(land, 1, 0) & np.roll(land, -1, 0) & np.roll(land, 1, 1) & np.roll(land, -1, 1))
rgb[coast] = (226, 196, 120)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f'{OUT}/reg_base.webp', quality=82, method=6)
# coastline polyline for drawing above the clouds: marching along land/sea boundary pixels is enough as dots
L['reg'] = dict(bbox=[22.2, 15.0, -109.4, -101.8], w=480, h=480, coast=[[int(i), int(j)] for j, i in np.argwhere(coast[::1, ::1])][::1])
json.dump(L, open(f'{OUT}/layers.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print('layers.json', os.path.getsize(f'{OUT}/layers.json'))
