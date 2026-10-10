"""Fetch Open-Meteo deterministic models for the 3 addresses, nearest grid cell, with retries."""
import json, sys, time, urllib.request, urllib.parse, os
OUT = sys.argv[1]
MODELS = sys.argv[2].split(',')
PTS = [(20.5984, -105.2382), (20.6477, -105.2087), (20.6012, -105.2358)]
def url(m):
    q = {'latitude': ','.join(str(p[0]) for p in PTS), 'longitude': ','.join(str(p[1]) for p in PTS),
         'hourly': 'precipitation,wind_gusts_10m,wind_speed_10m,pressure_msl', 'models': m,
         'timezone': 'America/Mexico_City', 'start_hour': '2026-10-10T12:00', 'end_hour': '2026-10-12T12:00',
         'wind_speed_unit': 'kmh', 'cell_selection': 'nearest'}
    return 'https://api.open-meteo.com/v1/forecast?' + urllib.parse.urlencode(q)
for m in MODELS:
    fn = os.path.join(OUT, f'{m}.json')
    if os.path.exists(fn): print(m, 'cached'); continue
    for i in range(10):
        try:
            r = urllib.request.urlopen(url(m), timeout=120).read()
            d = json.loads(r)
            if isinstance(d, dict) and d.get('error'): raise RuntimeError(d.get('reason'))
            json.dump(d, open(fn, 'w')); print(m, 'ok try', i+1); break
        except Exception as e:
            body = ''
            if hasattr(e, 'read'):
                try: body = e.read().decode()[:200]
                except Exception: pass
            print(m, 'try', i+1, 'fail:', str(e)[:120], body); time.sleep(min(90, 15 * (i+1)))
