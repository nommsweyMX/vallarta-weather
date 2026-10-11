"""Significant wave height (HTSGW) from HAFS's coupled WAVEWATCH III, at a point in the bay off Playa Los Muertos.
Usage: fetch_waves.py hfsa 2026101012 OUTDIR F0 F1   (forecast hours covering the window, 3-hourly)"""
import sys, json, os, re, urllib.request, numpy as np, pygrib
MODEL, CYC, OUT, F0, F1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
URL = f'https://noaa-nws-hafs-pds.s3.amazonaws.com/{MODEL}/{CYC[:8]}/{CYC[8:]}/20e.{CYC}.{MODEL}.ww3.grb2'
PT = (20.597, -105.243)          # ~500 m off Playa Los Muertos / Amapas
def get(url, rng=None):
    for i in range(6):
        try:
            req = urllib.request.Request(url, headers={'Range': 'bytes=%d-%s' % rng} if rng else {})
            return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e: print('retry', e, file=sys.stderr)
    raise RuntimeError(url)
idx = get(URL + '.idx').decode().strip().split('\n'); offs = [int(l.split(':')[1]) for l in idx]
out = {}
for f in range(F0, F1 + 1, 3):
    pat = ':HTSGW:surface:anl:' if f == 0 else f':HTSGW:surface:{f} hour fcst:'
    i = next(k for k, l in enumerate(idx) if pat in l)
    msg = pygrib.fromstring(get(URL, (offs[i], offs[i + 1] - 1)))
    lats, lons = msg.latlons(); lons = np.where(lons > 180, lons - 360, lons)
    v = np.ma.masked_invalid(np.ma.asarray(msg.values))
    d = np.hypot((lats - PT[0]) * 111, (lons - PT[1]) * 111 * np.cos(np.radians(PT[0])))
    d = np.ma.array(d, mask=np.ma.getmaskarray(v))
    j = np.unravel_index(np.ma.argmin(d), d.shape)
    near = d <= 12
    out[f] = dict(hs=float(v[j]), cell=[float(lats[j]), float(lons[j])], km=float(d[j]),
                  hs12=float(v[near].max()) if np.any(near & ~np.ma.getmaskarray(v)) else None, res=float(abs(lats[1, 0] - lats[0, 0])))
    print(MODEL, CYC, f, round(out[f]['hs'], 2), 'cell', [round(x, 3) for x in out[f]['cell']], round(out[f]['km'], 1), 'km', file=sys.stderr)
json.dump({'model': MODEL, 'cycle': CYC, 'pt': PT, 'steps': out}, open(os.path.join(OUT, f'{MODEL}_{CYC}_ww3.json'), 'w'))
