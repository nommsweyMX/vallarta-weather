"""Data for the Simon forecast video: best track (history), the NHC forecast, model tracks and intensity guidance
from the public ATCF decks, Puerto Vallarta wind probabilities, and a dark relief basemap for the eastern Pacific.
Usage: forecast_data.py WORK OUTDIR   (WORK/atcf/bep.dat, WORK/atcf/aep.dat, WORK/nhc.json, WORK/tiles_ep z6 terrarium)"""
import sys, os, json, math, glob, urllib.request, datetime as dt, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map', 'tools'))
from terrain import mosaic, sample, grid, hillshade

W, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
def ll(s): v = int(s.strip()[:-1]) / 10; return -v if s.strip()[-1] in 'SW' else v
def rows(path):
    for line in open(path):
        f = [x.strip() for x in line.split(',')]
        if len(f) > 8: yield f

# ---- best track (one row per time; 34-kt row carries the basics) ----
best = {}
for f in rows(W + '/atcf/bep.dat'):
    t = f[2]; best.setdefault(t, dict(t=dt.datetime.strptime(t, '%Y%m%d%H').strftime('%Y-%m-%dT%H:%MZ'), lat=ll(f[6]), lon=ll(f[7]), kt=int(f[8]), mb=int(f[9]) if f[9] else None, ty=f[10]))
best = [best[k] for k in sorted(best)]

# ---- latest a-deck cycle: model tracks and intensities ----
cycles = sorted({f[2] for f in rows(W + '/atcf/aep.dat')})
TRACK_AIDS = {'HFAI': 'HAFS-A', 'HFBI': 'HAFS-B', 'HWFI': 'HWRF', 'HMNI': 'HMON', 'AVNI': 'GFS', 'CMC2': 'Canadian', 'CMCI': 'Canadian', 'UKX2': 'UK Met', 'UKXI': 'UK Met',
              'NVG2': 'NAVGEM', 'NVGI': 'NAVGEM', 'GDMI': 'Google DeepMind', 'CTCI': 'COAMPS-TC', 'OFCI': 'NHC (prev.)', 'OFCL': 'NHC'}
INT_AIDS = {'DSHP': 'SHIPS', 'LGEM': 'LGEM', 'HFAI': 'HAFS-A', 'HFBI': 'HAFS-B', 'HWFI': 'HWRF', 'HMNI': 'HMON', 'CTCI': 'COAMPS-TC', 'IVCN': 'Consensus', 'OFCL': 'NHC', 'OFCI': 'NHC (prev.)'}
def aids(cyc):
    out = {}
    for f in rows(W + '/atcf/aep.dat'):
        if f[2] != cyc: continue
        a = f[4]; tau = int(f[5]); 
        try: la, lo, kt = ll(f[6]), ll(f[7]), int(f[8] or 0)
        except Exception: continue
        if f[11] not in ('34', '0', ''): continue
        out.setdefault(a, {})[tau] = (la, lo, kt)
    return {a: [[tau] + list(v) for tau, v in sorted(d.items())] for a, d in out.items()}
cyc = cycles[-1]; A = aids(cyc)
if len([a for a in TRACK_AIDS if a in A]) < 5 and len(cycles) > 1: cyc = cycles[-2]; A = aids(cyc)
tracks = {a: dict(name=TRACK_AIDS[a], pts=A[a]) for a in TRACK_AIDS if a in A and a != 'OFCI'}
ints = {a: dict(name=INT_AIDS[a], pts=[[p[0], p[3]] for p in A[a] if p[3] > 0]) for a in INT_AIDS if a in A}
print('cycle', cyc, 'tracks', list(tracks), 'intensity', list(ints))

nhc = json.load(open(W + '/nhc.json'))
# ---- dark relief basemap 9.5-24.5N, 110.5-89.5W ----
BB = dict(lat0=24.5, lat1=9.5, lon0=-110.5, lon1=-89.5, w=1160)
BB['h'] = int(round(BB['w'] * (BB['lat0'] - BB['lat1']) / ((BB['lon1'] - BB['lon0']) * math.cos(math.radians(17)))))
M = mosaic(W + '/tiles_ep', 6); la, lo = grid(BB['lat0'], BB['lat1'], BB['lon0'], BB['lon1'], BB['h'], BB['w']); E = ndimage.gaussian_filter(sample(M, la, lo), 0.6)
land = E > 0.5; hs = hillshade(np.where(land, E, 0), 15 / BB['h'] * 111200, 21 / BB['w'] * 111200 * math.cos(math.radians(17)), zf=12)
deep = np.clip(-E / 5000, 0, 1)
rgb = np.where(land[..., None], np.array([44, 50, 42])[None, None] * (0.55 + 0.75 * hs)[..., None],
               (np.array([22, 40, 60])[None, None] * (1 - deep[..., None]) + np.array([9, 18, 30])[None, None] * deep[..., None]))
coast = land & ~ndimage.binary_erosion(land); rgb[coast] = (214, 190, 130)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f'{OUT}/ep_base.webp', quality=84, method=6)
json.dump(dict(cycle=cyc, best=best, nhc=dict(track=nhc['track'], summary=nhc['summary'], pv_probs=nhc['pv_probs'], tcm=nhc.get('tcm_advisory'), pws=nhc.get('pws_advisory'), onset34=nhc.get('onset34')),
               tracks=tracks, ints=ints, ep=BB,
               cone=dict(nm={12: 25, 24: 37, 36: 48, 48: 56, 60: 66, 72: 78, 96: 106, 120: 138}, source='https://www.nhc.noaa.gov/aboutcone.shtml (2026, eastern North Pacific)')),
          open(f'{OUT}/forecast.json', 'w'), separators=(',', ':'))
print('wrote', OUT, os.path.getsize(f'{OUT}/forecast.json'))
