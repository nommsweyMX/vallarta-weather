"""Parse NHC text products for an East Pacific storm into nhc.json.
Usage: nhc_parse.py RAWDIR OUT.json   (RAWDIR holds TCPEP5.html, TCMEP5.html, PWSEP5.html as saved from nhc.noaa.gov/text/)
Reads: public advisory (summary block), forecast advisory (track, intensity, wind radii by quadrant),
wind speed probabilities (Puerto Vallarta row)."""
import html, json, re, sys, os, datetime as dt

RAW, OUT = sys.argv[1], sys.argv[2]

def pre(name):
    t = open(os.path.join(RAW, name), encoding='utf-8', errors='replace').read()
    m = re.search(r'<pre[^>]*>(.*?)</pre>', t, re.S)
    return html.unescape(m.group(1) if m else t)

def radii(line):
    # "64 KT....... 10NE  15SE  10SW  10NW."  ->  [NE, SE, SW, NW] in nautical miles
    q = {quad: num for num, quad in re.findall(r'(\d+)(NE|SE|SW|NW)', line)}
    return [int(q.get(k, 0)) for k in ('NE', 'SE', 'SW', 'NW')]

def when(ddhhmm, ref):
    # "10/1500Z" -> datetime in the reference month (UTC)
    d, hm = ddhhmm.split('/'); return dt.datetime(ref.year, ref.month, int(d), int(hm[:2]), int(hm[2:4]))

def lat(s): return float(s[:-1]) * (1 if s[-1] == 'N' else -1)
def lon(s): return float(s[:-1]) * (-1 if s[-1] == 'W' else 1)

# ---- forecast advisory: track + radii ----
tcm = pre('TCMEP5.html')
hdr = re.search(r'FORECAST/ADVISORY NUMBER\s+(\w+).*?\n(\d{4}) UTC \w{3} (\w{3}) (\d+) (\d{4})', tcm, re.S)
ref = dt.datetime.strptime(f'{hdr.group(3)} {hdr.group(4)} {hdr.group(5)}', '%b %d %Y')
track = []
m0 = re.search(r'CENTER LOCATED NEAR ([\d.]+[NS]) ([\d.]+[EW]) AT (\S+)', tcm)
v0 = re.search(r'MAX SUSTAINED WINDS\s+(\d+) KT WITH GUSTS TO\s+(\d+) KT', tcm)
blk0 = tcm[v0.end():v0.end() + 400]
pt = dict(t=when(m0.group(3).rstrip('Z') + 'Z', ref), lat=lat(m0.group(1)), lon=lon(m0.group(2)), kt=int(v0.group(1)), gust=int(v0.group(2)), inland=False)
for k in (64, 50, 34):
    mm = re.search(rf'^{k} KT\.+\s*(.*)$', blk0, re.M)
    pt[f'r{k}'] = radii(mm.group(1)) if mm else [0, 0, 0, 0]
track.append(pt)
for m in re.finditer(r'FORECAST VALID (\S+) ([\d.]+[NS]) ([\d.]+[EW])(\.\.\.[A-Z/\- ]+)?[ \t]*\nMAX WIND\s+(\d+) KT\.\.\.GUSTS\s+(\d+) KT\.(.*?)(?=\n\s*\n)', tcm, re.S):
    pt = dict(t=when(m.group(1).rstrip('Z') + 'Z', ref), lat=lat(m.group(2)), lon=lon(m.group(3)), kt=int(m.group(5)), gust=int(m.group(6)),
              inland=bool(m.group(4) and 'INLAND' in m.group(4)), note=(m.group(4) or '').strip('. '))
    for k in (64, 50, 34):
        mm = re.search(rf'^{k} KT\.+\s*(.*)$', m.group(7), re.M)
        pt[f'r{k}'] = radii(mm.group(1)) if mm else [0, 0, 0, 0]
    track.append(pt)
n_valid = len(re.findall(r'FORECAST VALID \S+ [\d.]+[NS] [\d.]+[EW]', tcm))
assert len(track) == n_valid + 1, ('forecast points parsed', len(track) - 1, 'of', n_valid)
for p in track: p['t'] = p['t'].strftime('%Y-%m-%dT%H:%MZ')

# ---- public advisory summary ----
tcp = pre('TCPEP5.html')
g = lambda pat: (re.search(pat, tcp) or [None, None]) [1]
adv = re.search(r'(Intermediate )?Advisory Number\s+(\w+)', tcp)
issued = re.search(r'\n(\d{3,4} [AP]M) (C[SD]T) (\w{3}) (\w{3}) (\d+) (\d{4})', tcp)
summary = dict(
    advisory=adv.group(2), intermediate=bool(adv.group(1)),
    issued_local=f'{issued.group(1)} {issued.group(2)} {issued.group(3)} {issued.group(4)} {issued.group(5)}' if issued else None,
    location=g(r'LOCATION\.\.\.(.+)'),
    from_cabo=g(r'ABOUT [\d]+ MI\.\.\.(\d+ KM \w+ OF CABO CORRIENTES)'),
    wind_kmh=int(g(r'MAXIMUM SUSTAINED WINDS\.\.\.\d+ MPH\.\.\.(\d+) KM/H')),
    wind_mph=int(g(r'MAXIMUM SUSTAINED WINDS\.\.\.(\d+) MPH')),
    move_dir=g(r'PRESENT MOVEMENT\.\.\.(\w+) OR \d+ DEGREES'),
    move_kmh=int(g(r'PRESENT MOVEMENT\.\.\..*?AT \d+ MPH\.\.\.(\d+) KM/H')),
    pressure_mb=int(g(r'MINIMUM CENTRAL PRESSURE\.\.\.(\d+) MB')),
    warnings=re.findall(r'^\* (.+)$', re.split(r'\n\s*\n', tcp.split('A Hurricane Warning is in effect for')[1], maxsplit=1)[0], re.M) if 'A Hurricane Warning is in effect for' in tcp else [],
)

# ---- wind speed probabilities, Puerto Vallarta row (5-day cumulative) ----
pws = pre('PWSEP5.html')
probs = {}
for k in (34, 50, 64):
    m = re.search(rf'^P VALLARTA\s+{k}\s+(.*)$', pws, re.M)
    if m:
        cums = re.findall(r'\(\s*(\d+|X)\)', m.group(1))
        probs[str(k)] = 0 if not cums or cums[-1] == 'X' else int(cums[-1])
pws_adv = re.search(r'WIND SPEED PROBABILITIES NUMBER\s+(\w+)', pws)
# onset window for 34-kt winds: the column with the highest onset probability.
# Columns run from the synoptic hour before issuance: 0-12, 12-24, 24-36, 36-48, 48-72, 72-96, 96-120 h.
onset34 = None
ph = re.search(r'\n(\d{2})00 UTC \w{3} (\w{3}) (\d+) (\d{4})', pws)
m34 = re.search(r'^P VALLARTA\s+34\s+(.*)$', pws, re.M)
if ph and m34:
    issued = dt.datetime.strptime(f'{ph.group(2)} {ph.group(3)} {ph.group(4)} {ph.group(1)}', '%b %d %Y %H')
    base = issued.replace(hour=(issued.hour // 12) * 12)
    ops = [0 if v == 'X' else int(v) for v in re.findall(r'(X|\d+)(?:\(\s*(?:X|\d+)\))?', m34.group(1))]
    edges = [0, 12, 24, 36, 48, 72, 96, 120]
    if ops:
        k = max(range(len(ops)), key=lambda j: ops[j])
        onset34 = dict(op=ops[k], start=(base + dt.timedelta(hours=edges[k])).strftime('%Y-%m-%dT%H:%MZ'), end=(base + dt.timedelta(hours=edges[k + 1])).strftime('%Y-%m-%dT%H:%MZ'), all=ops)

json.dump(dict(track=track, summary=summary, pv_probs=probs, onset34=onset34, tcm_advisory=hdr.group(1), pws_advisory=pws_adv.group(1) if pws_adv else None),
          open(OUT, 'w'), indent=1)
print('track', [(p['t'], p['lat'], p['lon'], p['kt'], p['r64'], p['r34']) for p in track])
print('summary', summary); print('PV probs', probs, 'onset34', onset34)
