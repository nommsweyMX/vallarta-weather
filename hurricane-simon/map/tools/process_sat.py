"""GOES-18 mesoscale IR loop (parallax-corrected), eye fixes, motion, and the storm-relative rain-rate field.
Usage: process_sat.py GOESDIR OUTDIR
GOESDIR/ir: ABI-L2-CMIPM2 band 13 files; GOESDIR/rr: ABI-L2-RRQPEF files (both GOES-18)."""
import sys, os, glob, re, json, datetime as dt, numpy as np, h5py
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
from goesgeo import proj, axis, ll2xy, parallax_shift

G, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT + '/frames', exist_ok=True)
# regional display grid (equirectangular)
NY = NX = 480; LAT0, LAT1, LON0, LON1 = 22.2, 15.0, -109.4, -101.8
lat = np.linspace(LAT0, LAT1, NY)[:, None] * np.ones((1, NX)); lon = np.ones((NY, 1)) * np.linspace(LON0, LON1, NX)[None, :]

def stime(f):
    s = re.search(r'_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})', f)
    return dt.datetime(int(s.group(1)), 1, 1) + dt.timedelta(days=int(s.group(2)) - 1, hours=int(s.group(3)), minutes=int(s.group(4)), seconds=int(s.group(5)))

def hgt(bt): return np.clip((300.0 - bt) / 6.7, 0, 17) * 1000.0      # cloud-top height (m) from brightness temperature

class Img:
    def __init__(s, f, var):
        h = h5py.File(f, 'r'); s.H, s.lam0 = proj(h); s.x = axis(h, 'x'); s.y = axis(h, 'y'); v = h[var]
        s.v, s.fill, s.sc, s.off = v, v.attrs['_FillValue'][0], float(v.attrs['scale_factor'][0]), float(v.attrs['add_offset'][0])
        s.cache = None
    def idx(s, la, lo):
        X, Y = ll2xy(la, lo, s.H, s.lam0)
        return np.round((X - s.x[0]) / (s.x[1] - s.x[0])).astype(int), np.round((Y - s.y[0]) / (s.y[1] - s.y[0])).astype(int)
    def sample(s, la, lo):
        ix, iy = s.idx(la, lo)
        i0, i1, j0, j1 = max(ix.min() - 60, 0), min(ix.max() + 60, len(s.x)), max(iy.min() - 60, 0), min(iy.max() + 60, len(s.y))
        if s.cache is None or not (s.cache[1] <= i0 and i1 <= s.cache[1] + s.cache[0].shape[1] and s.cache[2] <= j0 and j1 <= s.cache[2] + s.cache[0].shape[0]):
            raw = s.v[j0:j1, i0:i1].astype(float); s.cache = (np.where(raw == s.fill, np.nan, raw * s.sc + s.off), i0, j0)   # read only the needed window
        a, i0, j0 = s.cache; ix = ix - i0; iy = iy - j0
        ok = (ix >= 0) & (ix < a.shape[1]) & (iy >= 0) & (iy < a.shape[0])
        r = np.full(ix.shape, np.nan); r[ok] = a[iy[ok], ix[ok]]; return r

def corrected(img, btimg, la, lo, it=3):
    """sample img at the apparent position of the cloud above (la, lo), using btimg to estimate cloud height."""
    bt = btimg.sample(la, lo)
    for _ in range(it):
        pla, plo = parallax_shift(la, lo, hgt(np.nan_to_num(bt, nan=300.0)), btimg.H, btimg.lam0)
        bt = btimg.sample(pla, plo)
    return bt if img is btimg else img.sample(pla, plo)

# ---- IR palette (BT in K -> RGBA): grey cloud ramp, colours for cold tops, transparent where warm/clear ----
def colour(bt):
    c = bt - 273.15
    stops = [(-90, (255, 255, 255)), (-82, (196, 92, 220)), (-76, (214, 40, 40)), (-70, (240, 140, 30)), (-64, (244, 214, 60)),
             (-58, (60, 176, 80)), (-50, (40, 110, 210)), (-40, (110, 200, 230)), (-30, (215, 220, 226)), (0, (120, 128, 138)), (20, (60, 66, 74))]
    xs = [s[0] for s in stops]; rgb = np.zeros(c.shape + (4,), np.uint8)
    for k in range(3): rgb[..., k] = np.nan_to_num(np.interp(c, xs, [s[1][k] for s in stops])).astype(np.uint8)
    a = np.interp(c, [-20, 5, 18], [235, 150, 0]); a[np.isnan(c)] = 0; rgb[np.isnan(c)] = 0
    rgb[..., 3] = a.astype(np.uint8); return rgb

irs = sorted(glob.glob(G + '/ir/*.nc')); rrs = sorted(glob.glob(G + '/rr/*.nc'))
for old in glob.glob(OUT + '/frames/ir*.webp'): os.remove(old)
fixes = []; guess = (17.6, -104.8)
for f in irs:
    t = stime(f); im = Img(f, 'CMI')
    # eye: warmest smoothed pixel within 45 km of the previous fix, on the apparent (uncorrected) image
    sl = slice(None)
    la = np.arange(guess[0] + 0.45, guess[0] - 0.45, -0.01)[:, None] * np.ones((1, 91)); lo = np.ones((len(la), 1)) * np.arange(guess[1] - 0.45, guess[1] + 0.46, 0.01)[None, :91]
    bt = ndimage.uniform_filter(np.nan_to_num(im.sample(la, lo), nan=200.0), 3)
    j, i = np.unravel_index(np.argmax(bt), bt.shape)
    m = (bt > bt[j, i] - 8) & (np.hypot((la - la[j, i]) * 111, (lo - lo[j, i]) * 104) < 15)
    ela, elo = float((la * m).sum() / m.sum()), float((lo * m).sum() / m.sum())
    ring = np.hypot((la - ela) * 111, (lo - elo) * 104); ring = (ring > 15) & (ring < 45)
    cla, clo = parallax_shift(np.array(ela), np.array(elo), 14000.0, im.H, im.lam0)    # cloud seen 14 km up appears here...
    tla, tlo = 2 * ela - float(cla), 2 * elo - float(clo)                                # ...so the true eye is the reverse shift
    fixes.append(dict(t=t.strftime('%Y-%m-%dT%H:%MZ'), app=[round(ela, 3), round(elo, 3)], lat=round(tla, 3), lon=round(tlo, 3), eye_c=round(float(bt[j, i]) - 273.15, 1), wall_c=round(float(np.percentile(bt[ring], 10)) - 273.15, 1)))
    guess = (ela, elo)
    if t >= stime(irs[-1]) - dt.timedelta(hours=4):
        rgba = colour(corrected(im, im, lat, lon))
        Image.fromarray(rgba, 'RGBA').save(f'{OUT}/frames/ir_{t:%Y%m%d%H%M}.webp', quality=78, method=6)
    print(fixes[-1], flush=True)

# ---- extended frame for the extrapolation: latest full-disk band-13 image over a taller box (fills in south of the mesoscale sector) ----
EXT = None
fds = sorted(glob.glob(G + '/fd/*C13*.nc'))
if fds:
    f = fds[-1]; t = stime(f); im = Img(f, 'CMI'); ny2 = int(round((LAT0 - 11.4) / ((LAT0 - LAT1) / (NY - 1)))) + 1
    la2 = np.linspace(LAT0, 11.4, ny2)[:, None] * np.ones((1, NX)); lo2 = np.ones((ny2, 1)) * np.linspace(LON0, LON1, NX)[None, :]
    Image.fromarray(colour(corrected(im, im, la2, lo2)), 'RGBA').save(f'{OUT}/frames/irx_{t:%Y%m%d%H%M}.webp', quality=78, method=6)
    EXT = dict(file=f'irx_{t:%Y%m%d%H%M}.webp', t=t.strftime('%Y-%m-%dT%H:%MZ'), lat0=LAT0, lat1=11.4, ny=ny2)
    print('extended frame', EXT)

# ---- motion: least-squares fit to the true eye fixes of the last 6 h ----
T = np.array([(dt.datetime.strptime(x['t'], '%Y-%m-%dT%H:%MZ') - dt.datetime(2026, 10, 10)).total_seconds() / 3600 for x in fixes])
LA = np.array([x['lat'] for x in fixes]); LO = np.array([x['lon'] for x in fixes])
w = T >= T[-1] - 6
pa = np.polyfit(T[w], LA[w], 1); po = np.polyfit(T[w], LO[w], 1)
vn = pa[0] * 111.2; ve = po[0] * 111.2 * np.cos(np.radians(LA[-1]))
motion = dict(hours=float(T[-1] - T[w][0]), lat_per_h=float(pa[0]), lon_per_h=float(po[0]), kmh=float(np.hypot(vn, ve)), dir_to=float(np.degrees(np.arctan2(ve, vn)) % 360),
              t=fixes[-1]['t'], lat=float(np.polyval(pa, T[-1])), lon=float(np.polyval(po, T[-1])), resid_km=float(np.sqrt(np.mean(((LA[w] - np.polyval(pa, T[w])) * 111) ** 2 + ((LO[w] - np.polyval(po, T[w])) * 104) ** 2))))
print('motion', motion)

# ---- storm-relative rain rate (km grid, +-300 km, 3 km) from each RRQPE scan in the last 2 h ----
fixt = np.array([dt.datetime.strptime(x['t'], '%Y-%m-%dT%H:%MZ').timestamp() for x in fixes])
K = np.arange(-300, 301, 3.0); KX, KY = np.meshgrid(K, -K)           # rows: north at top
stack, times = [], []
for f in rrs:
    t = stime(f) + dt.timedelta(minutes=5)
    if t < stime(irs[-1]) - dt.timedelta(hours=2): continue
    ts = t.timestamp(); cla_, clo_ = np.interp(ts, fixt, LA), np.interp(ts, fixt, LO)
    la = cla_ + KY / 111.2; lo = clo_ + KX / (111.2 * np.cos(np.radians(la)))
    irf = min(irs, key=lambda g: abs((stime(g) - t).total_seconds()))
    rr = corrected(Img(f, 'RRQPE'), Img(irf, 'CMI'), la, lo)
    stack.append(np.nan_to_num(rr)); times.append(t.strftime('%H:%MZ')); print('rr', t, np.nanmax(rr), flush=True)
stack = np.array(stack)
np.save(OUT + '/rain_stack.npy', stack.astype(np.float32))
json.dump(dict(fixes=fixes, motion=motion, rain_times=times, grid=dict(km0=-300, dkm=3, n=len(K)),
               ir=dict(lat0=LAT0, lat1=LAT1, lon0=LON0, lon1=LON1, nx=NX, ny=NY, ext=EXT, frames=sorted(os.path.basename(p) for p in glob.glob(OUT + '/frames/ir_*.webp')))),
          open(OUT + '/sat.json', 'w'), indent=1)
