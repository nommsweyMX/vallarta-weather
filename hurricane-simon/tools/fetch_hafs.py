"""Extract HAFS point series (APCP 3h, GUST, PRMSL, 10m max wind) at the 3 addresses via idx byte ranges."""
import sys, json, re, urllib.request, numpy as np, pygrib, os
from concurrent.futures import ThreadPoolExecutor
MODEL, CYC = sys.argv[1], sys.argv[2]
DOM0 = os.environ.get('HAFS_DOM', 'storm')          # hfsa 2026101006
OUT = sys.argv[3]
F0, F1 = int(sys.argv[4]), int(sys.argv[5])    # forecast hours covering the window
D, H = CYC[:8], CYC[8:]
BASE = f'https://noaa-nws-hafs-pds.s3.amazonaws.com/{MODEL}/{D}/{H}/20e.{CYC}.{MODEL}'
PTS = [(20.5984, -105.2382), (20.6477, -105.2087), (20.6012, -105.2358)]
def get(url, rng=None):
    for i in range(6):
        try:
            req = urllib.request.Request(url, headers={'Range': f'bytes={rng[0]}-{rng[1]}'} if rng else {})
            return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e:
            print('retry', url[-50:], e, file=sys.stderr)
    raise RuntimeError(url)
def fields(dom, f):
    idx = get(f'{BASE}.{dom}.atm.f{f:03d}.grb2.idx').decode().strip().split('\n')
    offs = [int(l.split(':')[1]) for l in idx]
    want = {
        'apcp3': rf':APCP:surface:{f-3}-{f} hour acc fcst:' if f >= 3 else None,
        'apcp0': (rf':APCP:surface:0-{f//24} day acc fcst:' if f % 24 == 0 else rf':APCP:surface:0-{f} hour acc fcst:'),
        'gust': r':GUST:surface:\d+ hour fcst:',
        'prmsl': r':PRMSL:mean sea level:\d+ hour fcst:',
        'wmax': r':WIND:10 m above ground:\d+-\d+ hour max fcst:',
    }
    res = {}
    for k, pat in want.items():
        if not pat: continue
        for i, l in enumerate(idx):
            if re.search(pat, l):
                end = offs[i+1]-1 if i+1 < len(offs) else ''
                res[k] = (offs[i], end); break
    out = {}
    for k, rng in res.items():
        msg = pygrib.fromstring(get(f'{BASE}.{dom}.atm.f{f:03d}.grb2', rng))
        lats, lons = msg.latlons(); vals = msg.values
        la1, lo1 = lats[:, 0], lons[0, :]
        lo1 = np.where(lo1 > 180, lo1 - 360, lo1)
        pv = []
        for (pla, plo) in PTS:
            if not (min(la1) <= pla <= max(la1) and min(lo1) <= plo <= max(lo1)): pv.append(None); continue
            # bilinear on regular grid
            iy = np.searchsorted(la1, pla) if la1[0] < la1[-1] else len(la1) - np.searchsorted(la1[::-1], pla)
            ix = np.searchsorted(lo1, plo)
            iy0, ix0 = max(iy-1, 0), max(ix-1, 0)
            y0, y1, x0, x1 = la1[iy0], la1[iy0+1], lo1[ix0], lo1[ix0+1]
            ty, tx = (pla-y0)/(y1-y0), (plo-x0)/(x1-x0)
            v = (vals[iy0, ix0]*(1-ty)*(1-tx) + vals[iy0+1, ix0]*ty*(1-tx) + vals[iy0, ix0+1]*(1-ty)*tx + vals[iy0+1, ix0+1]*ty*tx)
            # local 15 km neighbourhood max for context
            ny, nx = int(round(0.135/abs(la1[1]-la1[0]))), int(round(0.145/abs(lo1[1]-lo1[0])))
            nb = vals[max(iy0-ny,0):iy0+ny+2, max(ix0-nx,0):ix0+nx+2]
            pv.append({'v': float(v), 'nbmax': float(np.max(nb)), 'res': float(abs(la1[1]-la1[0]))})
        out[k] = pv
    return out
def one(f):
    o = fields(DOM0, f)
    if 'apcp3' not in o or any(x is None for x in o['apcp3']):
        o = fields('parent', f); o['dom'] = 'parent'
    else: o['dom'] = 'storm'
    print(MODEL, CYC, f, o['dom'], [round(x['v'],1) if x else None for x in o['apcp3']], file=sys.stderr)
    return f, o
with ThreadPoolExecutor(6) as ex:
    res = dict(ex.map(one, range(F0, F1+1, 3)))
json.dump({'model': MODEL, 'cycle': CYC, 'pts': PTS, 'steps': {str(k): v for k, v in sorted(res.items())}}, open(os.path.join(OUT, f'{MODEL}_{CYC}' + ('' if DOM0 == 'storm' else '_' + DOM0) + '.json'), 'w'))
print('done', MODEL, CYC)
