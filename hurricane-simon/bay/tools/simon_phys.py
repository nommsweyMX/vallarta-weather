"""Wind and rain physics shared by the bay graphics, copied from map/tools/build_map.py so the numbers match the map page:
parametric wind field from the NHC wind radii, building exposure factors (ASCE 7) and the threat thresholds."""
import math

def geo(la1, lo1, la2, lo2):
    """distance (km) and bearing (deg, from point 1 to point 2)"""
    R = 6371.0; p1, p2 = math.radians(la1), math.radians(la2); dl = math.radians(lo2 - lo1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    d = 2 * R * math.asin(math.sqrt(a))
    y = math.sin(dl) * math.cos(p2); x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return d, (math.degrees(math.atan2(y, x)) + 360) % 360

def wind(c, la, lo, land=True):
    """1-min sustained wind (kt) at 10 m over open water, gust (kt) and direction it blows FROM (deg) at a point.
    c: dict(lat, lon, v, g, r34, r50, r64) with radii in nautical miles by quadrant NE, SE, SW, NW."""
    km, brg = geo(c['lat'], c['lon'], la, lo); r = km / 1.852
    x = ((brg - 45) % 360) / 90; i = int(x) % 4; w = x - int(x)
    tw = lambda q: q[i] * (1 - w) + q[(i + 1) % 4] * w
    r64, r50, r34, vmax = tw(c['r64']), tw(c['r50']), tw(c['r34']), c['v']
    rmw = max(8.0, 0.5 * r64) if r64 > 0 else 10.0
    knots = [(rmw, vmax)]
    for rr, vv in ((r64, 64), (r50, 50), (r34, 34)):
        if vmax > vv and rr > knots[-1][0]: knots.append((rr, vv))
    if r <= rmw: v = vmax * r / rmw
    elif r >= knots[-1][0]: v = knots[-1][1] * knots[-1][0] / r
    else:
        v = knots[-1][1]
        for (ra, va), (rb, vb) in zip(knots, knots[1:]):
            if ra <= r <= rb: v = va + (vb - va) * (r - ra) / (rb - ra); break
    beta = 35 if land else 20
    toward = brg - 90 - beta
    return v, v * (c['g'] / c['v'] if c['v'] else 1.25), (toward + 180) % 360, km, brg

def exposure(site, frm):
    """(sustained factor, gust/sustained ratio) relative to the 10-m open-water wind, as in build_map.py"""
    if site == 'amapas':
        over_bay = 200 <= frm <= 330
        return (math.sqrt(1.38 / 1.18), 1.25) if over_bay else (math.sqrt(0.93 / 1.18), 1.40)
    if site == 'ezapata': return math.sqrt(0.70 / 1.18), 1.45
    return math.sqrt(0.57 / 1.18), 1.45

KMH = 1.852; MPH = 1.15078
WIND_TH = (39, 63, 93, 119)     # km/h
RATE_TH = (2.5, 7.6, 25, 50)    # mm/h
RUN_TH = (15, 30, 60, 100)      # mm in 3 h
RIVER_TH = (20, 40, 70, 110)    # catchment-mean mm in 6 h, 3 h earlier
def lvl(x, th): return int(sum(x >= t for t in th))
def tm(v): return 3.96 + 2.45 * (1 + (v - 35) / 33)   # R-CLIPER peak rain rate vs intensity
