"""Hazard overlays for the video and map views, from official sources:
- CENAPRED national landslide susceptibility (15 m), classes Alto and Muy alto (ANR Fenomenos_Geologicos 385, 386)
- CENAPRED ANRI flood model for Puerto Vallarta, maximum depth for a 100-year return period (RegionOccidente_ANRI 297)
- Atlas de Peligros y Riesgos Puerto Vallarta 2024: zones where landslide material may come to rest (GeoJSON from the atlas GIS package)
  and the 2017-2023 landslide inventory (GeoJSON transcribed from Tomo II, Cuadro 30)
Usage: fetch_atlas_layers.py ATLAS_GIS_DIR OUTDIR   (views read from ../../map/data/layers.json)"""
import sys, os, json, io, urllib.request, urllib.parse, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); MAP = os.path.join(HERE, '..', '..', 'map', 'data')
GIS, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
VIEWS = json.load(open(os.path.join(MAP, 'layers.json')))['views']
SRV = 'https://rmgir.proyectomesoamerica.org/server/rest/services/'

def export(service, layers, bbox, w, h):
    lat0, lat1, lon0, lon1 = bbox
    q = dict(bbox=f'{lon0},{lat1},{lon1},{lat0}', bboxSR=4326, imageSR=4326, size=f'{w},{h}', format='png32', transparent='true', layers='show:' + ','.join(map(str, layers)), f='image')
    for a in range(4):
        try:
            return Image.open(io.BytesIO(urllib.request.urlopen(SRV + service + '/export?' + urllib.parse.urlencode(q), timeout=180).read())).convert('RGBA')
        except Exception as e:
            print('retry', service, layers, e)
    raise SystemExit('export failed')

def px(v, lat, lon): b = v['bbox']; return ((lon - b[2]) / (b[3] - b[2]) * v['w'], (b[0] - lat) / (b[0] - b[1]) * v['h'])

dep = json.load(open(os.path.join(GIS, 'atlas2024_zonas_deposicion_laderas.geojson')))
inv = json.load(open(os.path.join(GIS, 'atlas2024_inventario_deslizamientos_from_pdf.geojson')))
meta = {}
for key, v in VIEWS.items():
    w, h = v['w'], v['h']
    # landslide susceptibility: Alto (orange) and Muy alto (red)
    hi = np.asarray(export('ANR/Fenomenos_Geologicos/MapServer', [385], v['bbox'], w, h)); vh = np.asarray(export('ANR/Fenomenos_Geologicos/MapServer', [386], v['bbox'], w, h))
    s = np.zeros((h, w, 4), np.uint8); s[hi[..., 3] > 0] = (232, 140, 56, 200); s[vh[..., 3] > 0] = (226, 66, 44, 225)
    Image.fromarray(s, 'RGBA').save(f'{OUT}/atlas_slide_{key}.png', optimize=True)
    # flood model depth, Tr 100 years (CENAPRED colours, blues)
    fl = export('ANRI/RegionOccidente_ANRI/MapServer', [297], v['bbox'], w, h); fl.save(f'{OUT}/atlas_flood_{key}.png', optimize=True)
    # atlas deposition zones (outline + light fill) and landslide inventory points
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for f in dep['features']:
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'Polygon' else [p for mp in g['coordinates'] for p in mp]
        for ring in polys[:1] if g['type'] == 'Polygon' else polys:
            pts = [px(v, c[1], c[0]) for c in ring]
            if len(pts) > 2: d.polygon(pts, fill=(255, 214, 120, 60), outline=(255, 214, 120, 235), width=2 if key == 'city' else 3)
    n_in = 0
    for f in inv['features']:
        x, y = px(v, f['geometry']['coordinates'][1], f['geometry']['coordinates'][0])
        if 0 <= x < w and 0 <= y < h:
            r = 3 if key == 'city' else 6; d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 235), outline=(30, 20, 10, 255), width=1); n_in += 1
    im.save(f'{OUT}/atlas_dep_{key}.png', optimize=True)
    meta[key] = dict(inventory_points=n_in, slide_px=int((s[..., 3] > 0).sum()), flood_px=int((np.asarray(fl)[..., 3] > 0).sum()))
    print(key, meta[key])
json.dump(meta, open(f'{OUT}/atlas_layers_meta.json', 'w'))
