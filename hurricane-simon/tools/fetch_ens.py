import json, sys, time, urllib.request, urllib.parse, os
# Optional commercial key: set OPEN_METEO_API_KEY in the environment (never commit it).
KEY = os.environ.get('OPEN_METEO_API_KEY')
OUT = sys.argv[1]; MODELS = sys.argv[2].split(',')
PTS = [(20.5984, -105.2382), (20.6477, -105.2087), (20.6014, -105.2340)]
for m in MODELS:
    fn = os.path.join(OUT, f'{m}.json')
    if os.path.exists(fn): print(m, 'cached', flush=True); continue
    q = {'latitude': ','.join(str(p[0]) for p in PTS), 'longitude': ','.join(str(p[1]) for p in PTS),
         'hourly': 'precipitation', 'models': m, 'timezone': 'America/Mexico_City',
         'start_hour': '2026-10-10T12:00', 'end_hour': '2026-10-12T12:00', 'cell_selection': 'nearest'}
    free = 'https://ensemble-api.open-meteo.com/v1/ensemble?' + urllib.parse.urlencode(q)
    u = 'https://customer-ensemble-api.open-meteo.com/v1/ensemble?' + urllib.parse.urlencode(dict(q, apikey=KEY)) if KEY else free
    for i in range(8):
        try:
            d = json.loads(urllib.request.urlopen(u, timeout=150).read())
            if isinstance(d, dict) and d.get('error'): raise RuntimeError(d.get('reason'))
            json.dump(d, open(fn, 'w')); print(m, 'ok', i+1, flush=True); break
        except Exception as e:
            b = ''
            try: b = e.read().decode()[:150]
            except Exception: pass
            if KEY and u != free and 'requires the API' in b:
                print(m, 'key plan has no ensemble access; using the free endpoint', flush=True); u = free; continue
            print(m, 'fail', i+1, str(e)[:80], b, flush=True); time.sleep(5*(i+1))
