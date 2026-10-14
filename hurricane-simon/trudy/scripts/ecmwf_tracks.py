"""Decode ECMWF open-data tropical-cyclone track BUFR files (IFS ENS, AIFS ENS) into an ATCF-style deck for one storm.
Usage: ecmwf_tracks.py OUT.dat PREFIX LAT0 LON0 FILE.bufr [FILE.bufr ...]
PREFIX: two letters for ensemble tech codes (EE -> EE01..EE50 + EC00 control; AE -> AE01.. + AC00), or four letters for a single run (AIFS, ECMO). The storm is the message whose
analysis position is closest to LAT0 LON0 (ECMWF numbers invests 70E, 71E, ...)."""
import sys, math, os, eccodes as ec
SID = os.environ.get('ECMWF_SID')   # optional: force the storm identifier (e.g. 71E)
OUT, PREFIX, LAT0, LON0 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]); FILES = sys.argv[5:]
def dist(la, lo): return math.hypot(la - LAT0, (lo - LON0) * math.cos(math.radians(LAT0)))
lines = []; shown = False
for fn in FILES:
    f = open(fn, 'rb'); best = None
    while True:
        h = ec.codes_bufr_new_from_file(f)
        if h is None: break
        hu = ec.codes_clone(h); ec.codes_set(hu, 'unpack', 1)
        n = ec.codes_get(hu, 'numberOfSubsets'); sid = ec.codes_get(hu, 'stormIdentifier').strip()
        yy, mm, dd, hh = [int(ec.codes_get_array(hu, k)[0]) for k in ('year', 'month', 'day', 'hour')]
        ec.codes_release(hu); members = []
        for s in range(1, n + 1):
            if n == 1: g = ec.codes_clone(h); ec.codes_set(g, 'unpack', 1)
            else:
                g0 = ec.codes_clone(h); ec.codes_set(g0, 'unpack', 1); ec.codes_set(g0, 'extractSubset', s); ec.codes_set(g0, 'doExtractSubsets', 1)
                g = ec.codes_clone(g0); ec.codes_release(g0); ec.codes_set(g, 'unpack', 1)
            sig = list(ec.codes_get_array(g, 'meteorologicalAttributeSignificance')); la = list(ec.codes_get_array(g, 'latitude')); lo = list(ec.codes_get_array(g, 'longitude'))
            def arr(k):
                try: return list(ec.codes_get_array(g, k))
                except Exception: return []
            pr = arr('pressureReducedToMeanSeaLevel'); wd = arr('windSpeedAt10M'); tp = arr('timePeriod')
            if not tp: ec.codes_release(g); continue
            mem = int(ec.codes_get_array(g, 'ensembleMemberNumber')[0]) if ec.codes_is_defined(g, 'ensembleMemberNumber') else 0
            if not shown:
                print(fn.split('/')[-1], sid, 'subsets', n, 'subset 1: sig', len(sig), sig[:8], 'lat', len(la), 'pres', len(pr), 'wind', len(wd), 'tp', len(tp), tp[:5], 'member', mem); shown = True
            # layout: pairs (centre, max-wind) per time; the first pair is the analysis
            pts = list(zip(sig, la, lo)); cen = [(s_, a, b) for s_, a, b in pts if s_ == 1]; mx = [(s_, a, b) for s_, a, b in pts if s_ == 3]
            steps = [0] + [int(t) for t in tp]
            trk = []
            for i, t in enumerate(steps):
                if i >= len(cen): break
                _, a, b = cen[i]
                if a is None or abs(a) > 90 or abs(b) > 360 or a == ec.CODES_MISSING_DOUBLE or b == ec.CODES_MISSING_DOUBLE: continue
                p = pr[i] / 100 if i < len(pr) and pr[i] != ec.CODES_MISSING_DOUBLE and pr[i] < 1.1e5 else None
                w = wd[i] * 1.9438 if i < len(wd) and wd[i] != ec.CODES_MISSING_DOUBLE and wd[i] < 200 else None
                trk.append((t, a, b, w, p))
            if trk: members.append((mem, trk))
            ec.codes_release(g)
        if SID and sid != SID: members = []
        if members:
            a0 = [m[1][0] for m in members if m[1][0][0] <= 24]
            if a0:
                d = sum(dist(x[1], x[2]) for x in a0) / len(a0)
                if best is None or d < best[0]: best = (d, sid, members, yy, mm, dd, hh)
        ec.codes_release(h)
    if best is None: print(fn, 'no storms'); continue
    d, sid, members, yy, mm, dd, hh = best
    if d > 3: print(f'{fn.split("/")[-1]}: nearest storm {sid} is {d:.1f} deg from the target; EP93 not in this file'); continue
    print(f'{fn.split("/")[-1]}: storm {sid} analysis {d:.2f} deg from target, {len(members)} members, cycle {yy}{mm:02d}{dd:02d}{hh:02d}')
    ctl = min(m[0] for m in members)
    for mem, trk in members:
        tech = PREFIX if len(PREFIX) == 4 else (f'{PREFIX}{mem:02d}' if mem <= 50 else f'{PREFIX[0]}C00')   # 4-letter PREFIX = single run
        for t, a, b, w, p in trk:
            lines.append(f"EP, 93, {yy}{mm:02d}{dd:02d}{hh:02d}, 03, {tech:>4}, {t:3d}, {abs(round(a*10)):4d}{'N' if a>=0 else 'S'}, {abs(round(b*10)):5d}{'W' if b<0 else 'E'}, {round(w) if w else 0:4d}, {round(p) if p else 0:5d}, XX,")
open(OUT, 'w').write('\n'.join(lines) + '\n'); print(len(lines), 'deck lines ->', OUT)
