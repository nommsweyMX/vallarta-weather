"""How the NHC forecast for Simon changed from advisory to advisory: the forecast track and intensity of each
Forecast/Advisory, and the Puerto Vallarta wind speed probabilities of each Wind Speed Probabilities product.
Usage: nhc_history.py ARCHDIR OUT.json   (downloads missing ep202026.fstadv.NNN / .wndprb.NNN from the NHC archive into ARCHDIR)"""
import sys, os, re, html, json, urllib.request

ARCH, OUT = sys.argv[1], sys.argv[2]; os.makedirs(ARCH, exist_ok=True)
URL = 'https://www.nhc.noaa.gov/archive/2026/ep20/ep202026.{kind}.{n:03d}.shtml?'

def text(kind, n):
    p = os.path.join(ARCH, f'ep202026.{kind}.{n:03d}.txt')
    if not os.path.exists(p):
        try: raw = urllib.request.urlopen(URL.format(kind=kind, n=n), timeout=30).read().decode('utf-8', 'replace')
        except Exception: return None
        m = re.search(r'<pre[^>]*>(.*?)</pre>', raw, re.S)
        if not m: return None
        open(p, 'w').write(html.unescape(m.group(1)))
    return open(p).read()

def ll(a, b): return float(a[:-1]) * (1 if a[-1] == 'N' else -1), float(b[:-1]) * (-1 if b[-1] == 'W' else 1)

advs = []
for n in range(1, 60):
    t = text('fstadv', n)
    if t is None: break
    hdr = re.search(r'(\d{4}) UTC \w{3} (\w{3}) (\d+) (\d{4})', t)
    c = re.search(r'CENTER LOCATED NEAR\s+([\d.]+[NS])\s+([\d.]+[EW]) AT (\d\d/\d{4}Z)', t)
    v0 = re.search(r'MAX SUSTAINED WINDS\s+(\d+) KT', t)
    track = [[c.group(3)] + list(ll(c.group(1), c.group(2))) + [int(v0.group(1)), 'INIT']]
    for m in re.finditer(r'(?:FORECAST|OUTLOOK) VALID (\d\d/\d{4}Z)\s+([\d.]+[NS])\s+([\d.]+[EW])([^\n]*)\nMAX WIND\s+(\d+) KT', t):
        track.append([m.group(1)] + list(ll(m.group(2), m.group(3))) + [int(m.group(5)), m.group(4).strip(' .')])
    pv = None
    w = text('wndprb', n)
    if w:
        pv = {}
        for k in ('34', '50', '64'):
            r = re.search(r'P VALLARTA\s+' + k + r'\s+(.*)', w)
            if r:
                cum = re.findall(r'\(\s*(\w+)\)', r.group(1)); pv[k] = 0 if not cum or cum[-1] == 'X' else int(cum[-1])
            else: pv[k] = 0
    advs.append(dict(num=n, issued=f'{hdr.group(2)} {hdr.group(3)} {hdr.group(1)}Z', track=track, pv=pv))
json.dump(dict(advisories=advs), open(OUT, 'w'), separators=(',', ':'))
print('advisories', [a['num'] for a in advs], 'PV 64-kt', [(a['num'], a['pv'] and a['pv']['64']) for a in advs][-6:])
