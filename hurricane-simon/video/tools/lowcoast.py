"""Low-lying coastal land (under 4 m, within 3 km of the sea) for the Greater Vallarta view: where storm surge and
waves can push sea water inland. Terrain: AWS Terrain Tiles (zoom 12, ~30 m source data), so heights are approximate.
Usage: lowcoast.py WORK OUT.png   (view from ../../map/data/layers.json)"""
import sys, os, json, math, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map', 'tools'))
from terrain import mosaic, sample, grid
W, out = sys.argv[1], sys.argv[2]
v = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map', 'data', 'layers.json')))['views']['city']
b = v['bbox']; la, lo = grid(b[0], b[1], b[2], b[3], v['h'], v['w'])
E = ndimage.gaussian_filter(sample(mosaic(W + '/tiles_ws', 12), la, lo), 1.0)
# sea from the base map (drawn from the OpenStreetMap coastline; the terrain tiles have false shoals in the bay)
base = np.asarray(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map', 'data', 'img', 'base_city_dark.webp')).convert('RGB')).astype(int)
sea = (np.abs(base - np.array([17, 33, 50])).sum(-1) < 18); sea = ndimage.binary_opening(sea, iterations=2); px_km = (b[3] - b[2]) * 111.2 * math.cos(math.radians(20.63)) / v['w']
dist = ndimage.distance_transform_edt(~sea) * px_km
low = (~sea) & (E < 4) & (dist < 3)
low = ndimage.binary_opening(low, iterations=1)
rgba = np.zeros((v['h'], v['w'], 4), np.uint8); rgba[low] = (90, 230, 255, 170)
Image.fromarray(rgba, 'RGBA').save(out, optimize=True); print('low coast px', int(low.sum()), 'km2', round(float(low.sum() * px_km ** 2), 1))
