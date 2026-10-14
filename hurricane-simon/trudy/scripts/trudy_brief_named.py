"""Brief for a named storm with NHC advisories: NHC forecast and wind-speed probabilities first, then the five best Simon models,
ensembles and climatology, the three addresses and timing, and the long-range GFS run. Usage: trudy_brief_named.py SCRATCH TDIR OUT.html"""
import json, sys, math, os, datetime as dt
S, T, OUT = sys.argv[1:4]; O = 'file://' + T + '/out'; GA = 'file://' + S + '/gfsanim'
M = json.load(open(T + '/models.json')); C = json.load(open(T + '/climo.json')); CH = json.load(open(T + '/chances.json')); SC = json.load(open(T + '/scenarios.json'))
GT = json.load(open(S + '/gfsanim/gfs_tracks.json'))
SM = M['summary']; TR = M['tracks']; W = M['simon_err']; NHC = CH['nhc']
LATEST, PREV, ENSC = CH['latest'], CH['prev'], CH['ensc']
T5, T5P = SM[LATEST]['top5'], SM[PREV]['top5']
EC, AI, GE = SM[ENSC['ecens']]['ecens'], SM[ENSC['aiens']]['aiens'], SM[ENSC['gefs']]['gefs']
C5 = C['500']; n5 = C5['n']
def get(c, t): return next((r for r in TR if r['cycle'] == c and r['tech'] == t), None)
def comp(b): return ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'][int((b + 11.25) // 22.5) % 16]
def cat(v): return 'tropical storm' if v < 64 else 'category-1 hurricane' if v < 83 else 'category-2 hurricane' if v < 96 else 'category-3 hurricane' if v < 113 else 'category-4 hurricane' if v < 137 else 'category-5 hurricane'
def lt(s): return s.replace(' 00:00', ' midnight').replace(' 12:00', ' noon')
def lfl(t): return lt((dt.datetime.strptime(t, '%Y-%m-%d %HZ') - dt.timedelta(hours=6)).strftime('%a %d %b %H:%M'))
def short(s): return s.replace(' Oct', '')
def cap(t): return t[0].upper() + t[1:]
def hz(c): return c[-2:] + 'Z'
def pct(n, d): return round(100 * n / d)
def of5(p): return {0: 'none of the five', 20: 'one of the five', 40: 'two of the five', 60: 'three of the five', 80: 'four of the five', 100: 'all five'}.get(p, f'{p}%')
BASE = {'GDMI': 'GDMN', 'GDM2': 'GDMN', 'CEMI': 'CEMN', 'CEM2': 'CEMN', 'AEMI': 'AEMN', 'AEM2': 'AEMN', 'AIFI': 'AIFS'}
NM = {'GDMN': 'Google DeepMind cyclone model', 'AIFS': 'ECMWF AIFS', 'TVCN': 'track consensus TVCN', 'CEMN': 'Canadian ensemble mean', 'AEMN': 'GEFS ensemble mean'}
def nm(t): return NM[BASE.get(t, t)]
FIVE = sorted(T5['members'], key=lambda m: m['cpa_km']); PREVB = {BASE.get(m['tech'], m['tech']): m for m in T5P['members']}
L, K, NH, Wc = SC['least'], SC['likely'], SC['nhc'], SC['worst']
for _x in (L, K, Wc): _x['name'] = _x['name'].replace('Track consensus', 'track consensus')
of = get(LATEST, 'OFCL'); hc = get(LATEST, 'HCCA'); av = sorted([r for r in TR if r['tech'] == 'AVNO'], key=lambda r: r['cycle'])[-1]; ecm = sorted([r for r in TR if r['tech'] == 'ECMO'], key=lambda r: r['cycle'])[-1]
# NHC-grounded city wind: exceedance curve from the wind-speed probabilities (log-linear between 34 and 50 kt)
p34, p50, p64 = NHC['p34'] / 100, NHC['p50'] / 100, NHC['p64'] / 100
slope = (math.log(p50) - math.log(p34)) / 16; v_med = 34 + (math.log(0.5) - math.log(p34)) / slope if p34 < 0.5 else 34 + (math.log(0.5) - math.log(p34)) / slope
EXPO = {'amapas': (math.sqrt(0.93 / 1.18), 1.40), 'ezapata': (math.sqrt(0.70 / 1.18), 1.45), 'pitillal': (math.sqrt(0.57 / 1.18), 1.45)}
def bw(kt, k): f, g = EXPO[k]; return round(kt * 1.852 * f), round(kt * 1.852 * f * g)
SITES = [('amapas', 'D Terrace, Amapas, 8th floor'), ('ezapata', 'Casa Francisca, Emiliano Zapata, 3rd floor'), ('pitillal', 'El Pitillal house, street level')]
def scell(s, k): x = s['sites'][k]; return f"<b>{x['kmh']}</b> km/h, gusts {x['gust_kmh']}<br><span class=small>{lt(x['t'])}, wind from the {comp(x['frm'])}</span>"
def ncell(k): a, ag = bw(v_med, k); b, bg = bw(50, k); return f"<b>{a}</b> km/h, gusts {ag}<br><span class=small>1 in 10: {b} km/h, gusts {bg}</span>"
def win(s, k): w = s['windows'][k]; return f"{lt(w[0])} → {lt(w[1])}" if w else '—'
def d8(b): return ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'][int((b + 22.5) // 45) % 8]
five_rows = '\n'.join(
    f"<tr><td class=nw><b>{cap(nm(m['tech']))}</b>{' †' if m['ivcn'] else ''}</td><td class=num>{W[BASE.get(m['tech'], m['tech'])]}</td>"
    f"<td class=num><b>{m['cpa_km']}</b></td><td>{comp(m['cpa_brg'])}</td><td class=nw>{short(lt(m['cpa_local']))}</td><td class=num>{m['cpa_v']}</td><td class=num>{m['peak_v']}</td>"
    f"<td>{(m['landfall']['region'] + ', ' + short(lfl(m['landfall']['t']))) if m['landfall'] else 'stays offshore'}</td>"
    f"<td class=num>{PREVB[BASE.get(m['tech'], m['tech'])]['cpa_km']} {comp(PREVB[BASE.get(m['tech'], m['tech'])]['cpa_brg'])}</td>"
    f"<td class=num>{m['sites']['amapas']['kmh']}</td><td class=num>{m['sites']['ezapata']['kmh']}</td><td class=num>{m['sites']['pitillal']['kmh']}</td><td class=num>{m['rain_mm']}</td></tr>" for m in FIVE)
def aid_rows(cycle, techs):
    out = []
    for t in techs:
        r = get(cycle, t)
        if not r: continue
        lf = f"{r['landfall']['region']}, {short(lfl(r['landfall']['t']))}, {r['landfall']['v']} kt" if r['landfall'] else '—'
        out.append(f"<tr><td>{r['name']}{' †' if r['ivcn'] else ''}</td><td class=num>{r['cpa_km']}</td><td>{comp(r['cpa_brg'])}</td><td class=nw>{short(lt(r['cpa_local']))}</td><td class=num>{r['cpa_v'] or '—'}</td><td class=num>{r['peak_v'] or '—'}</td><td class=num>{r['rain_mm']}</td><td>{lf}</td></tr>")
    return '\n'.join(out)
rowsL = aid_rows(LATEST, ['OFCL', 'GDMI', 'AIFI', 'TVCN', 'CEM2', 'AEMI', 'HCCA', 'AVNI', 'UKX2', 'NVGI', 'CMC2', 'HFAI', 'HFBI', 'HWFI', 'HMNI', 'CTCI', 'CLP5'])
rowsP = aid_rows(PREV, ['GDMN', 'AIFS', 'TVCN', 'CEMI', 'AEMN', 'HCCA', 'AVNO', 'UKXI', 'NVGM', 'HFSA', 'HFSB', 'HWRF', 'HMON', 'CTCX', 'CLP5'])
clim_rows = '\n'.join(f"<tr><td>{s['year']} {s['name'].title()}</td><td class=num>{s['cpa_km']}</td><td>{s['cpa_t'][:10]} (+{s['cpa_days']} d)</td><td class=num>{s['v_cpa'] or '—'}</td><td class=num>{s['vmax']}</td><td>{s['region']}</td></tr>" for s in C5['storms'] if s['cpa_km'] <= 125)
LATE = GT['late']; lpk = min(LATE, key=lambda x: x[3]); lcl = min(LATE, key=lambda x: math.hypot(x[1] - 20.61, (x[2] + 105.2345) * math.cos(math.radians(20))))
def gl(h): return (dt.datetime(2026, 10, 13, 12) + dt.timedelta(hours=h)).strftime('%a %d %b, %-I %p').replace('AM', 'am').replace('PM', 'pm')
gr = GT['pv']['rain']; gw = GT['pv']['wind']
trudy_end = GT['trudy'][-1]
html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Trudy and Puerto Vallarta: advisory {NHC['adv']}</title>
<style>
__FONTS__
@page {{ size: Letter; margin: 17mm 16mm 18mm 16mm; }}
:root {{ --ink: #0b0b0b; --ink2: #3d3c39; --mute: #6b6a66; --line: #dcdad4; --accent: #1c5cab; --panel: #f3f2ee; --warn: #b3410f; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: #fff; color: var(--ink); font-family: "Red Hat Text", "DejaVu Sans", Arial, sans-serif; font-size: 10.2pt; line-height: 1.42; }}
h1, h2, h3 {{ font-family: "Red Hat Display", "DejaVu Sans", Arial, sans-serif; line-height: 1.15; margin: 0; }}
h1 {{ font-size: 23pt; font-weight: 800; letter-spacing: -0.01em; }}
h2 {{ font-size: 15pt; font-weight: 800; margin: 16pt 0 6pt; padding-top: 6pt; border-top: 2px solid var(--ink); break-after: avoid; }}
h3 {{ font-size: 11.3pt; font-weight: 700; margin: 10pt 0 4pt; break-after: avoid; }}
p {{ margin: 0 0 6pt; }} ul {{ margin: 0 0 6pt 16pt; padding: 0; }} li {{ margin: 0 0 3pt; }}
.kicker {{ font-family: "Red Hat Mono", monospace; color: var(--accent); font-size: 9pt; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 8pt; }}
.sub {{ font-size: 12pt; color: var(--ink2); margin: 8pt 0 10pt; line-height: 1.35; }}
.meta {{ font-family: "Red Hat Mono", monospace; font-size: 8.4pt; color: var(--mute); margin-bottom: 12pt; }}
.box {{ background: var(--panel); border-left: 4px solid var(--warn); padding: 8pt 11pt; margin: 8pt 0 10pt; break-inside: avoid; }} .box h3 {{ margin-top: 0; }}
.small {{ font-size: 8.6pt; color: var(--mute); }}
figure {{ margin: 8pt 0 10pt; break-inside: avoid; }} figure img {{ display: block; width: 100%; height: auto; }}
figure.w90 img {{ width: 90%; margin: 0 auto; }} figure.w80 img {{ width: 80%; margin: 0 auto; }}
figcaption {{ font-size: 8.6pt; color: var(--ink2); margin-top: 4pt; line-height: 1.35; }} figcaption b {{ color: var(--ink); }}
table {{ width: 100%; border-collapse: collapse; font-size: 8.6pt; margin: 6pt 0 10pt; }}
th, td {{ text-align: left; vertical-align: top; padding: 3.5pt 4.5pt; border-bottom: 1px solid var(--line); }}
th {{ font-weight: 700; font-size: 8.2pt; color: var(--ink2); border-bottom: 1.5px solid var(--ink); }}
td.num, th.num {{ text-align: right; font-family: "Red Hat Mono", monospace; white-space: nowrap; }} td.nw {{ white-space: nowrap; }}
table.app, table.five {{ font-size: 7.9pt; }} table.app td, table.app th, table.five td, table.five th {{ padding: 2.8pt 3.4pt; }} table.five {{ break-inside: avoid; }}
tr {{ break-inside: avoid; }}
.tiles {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 7pt; margin: 8pt 0 10pt; break-inside: avoid; }}
.tile {{ background: var(--panel); border-radius: 6pt; padding: 8pt 9pt; }}
.tile .n {{ font-family: "Red Hat Display", sans-serif; font-size: 18pt; font-weight: 800; line-height: 1.1; }}
.tile .l {{ font-size: 8.2pt; color: var(--ink2); margin-top: 2pt; line-height: 1.3; }}
.pb {{ break-before: page; }}
.foot {{ font-size: 8.2pt; color: var(--mute); border-top: 1px solid var(--line); padding-top: 6pt; margin-top: 14pt; }}
table.scen {{ font-size: 8.2pt; }} table.scen td:first-child {{ font-weight: 700; width: 15%; }} table.scen th {{ width: 21%; }}
table.out {{ font-size: 8.3pt; break-inside: avoid; }} table.out td:first-child {{ width: 30%; }}
</style></head><body>

<div class="kicker">Tropical Storm Trudy · NHC advisory {NHC['adv']} · Puerto Vallarta · the five best Simon models</div>
<h1>Trudy: realistic chances for Puerto Vallarta, the path, and what it means at three addresses</h1>
<p class="sub">The NHC's forecast and wind probabilities, the five best position forecasters of Simon (Google DeepMind's cyclone model, the ECMWF AIFS, the track consensus, the Canadian and GEFS ensemble means), three ensembles and 77 years of climatology. Least, most likely and worst cases with timing at D Terrace in Amapas, Casa Francisca in Emiliano Zapata and the house in El Pitillal. At the end, the GFS run out to 384 hours.</p>
<p class="meta">Tuesday 13 October 2026, 9 pm Vallarta time (14 Oct 03Z) · NHC advisory {NHC['adv']} · model runs of {hz(PREV)} and {hz(LATEST)} early versions · not an official forecast</p>

<div class="box"><h3>Bottom line</h3>
<ul>
<li><b>The NHC now forecasts a major hurricane at the Jalisco–Colima coast on Saturday, then north across Jalisco.</b> Advisory {NHC['adv']}: Trudy is a 40-kt tropical storm at 11.2N 97.0W moving northwest at 17 km/h, forecast to be a hurricane by Wednesday night and a major hurricane by Friday, reaching 19.0N 104.4W (the coast near Manzanillo) at 6 pm Saturday at 115 kt and 21.0N 106.0W (off Nayarit, northwest of the bay) at 6 pm Sunday at 75 kt. That line passes about {of['cpa_km']} km {d8(of['cpa_brg'])} of Puerto Vallarta around {lt(of['cpa_local']).split(' ', 3)[-1] if False else lt(of['cpa_local'])}. No watches or warnings yet; the NHC says watches will likely be needed Wednesday.</li>
<li><b>NHC wind probabilities for Puerto Vallarta (the number to use):</b> tropical-storm wind (≥ 63 km/h) <b>{NHC['p34']}%</b>, 50 kt (≥ 93 km/h) <b>{NHC['p50']}%</b>, hurricane wind (≥ 119 km/h) <b>{NHC['p64']}%</b>, all between Friday night and Sunday night. Manzanillo: 64%, 39% and 24%.</li>
<li><b>The five best Simon models agree with a close pass.</b> Their newest lines pass {', '.join(f"{nm(m['tech'])} {m['cpa_km']} km" for m in FIVE)}, all to the southwest, Sunday morning to Monday early. {of5(T5['within']['100']).capitalize()} within 100 km, {of5(T5['within']['200'])} within 200 km, {of5(T5['within']['300'])} within 300 km; {of5(T5['pv34'])} give tropical-storm wind in the city. The GFS and the ECMWF IFS are the outliers: the GFS kills Trudy over Michoacán, the IFS is two days slower.</li>
<li><b>Our reading:</b> about <b>4 in 5</b> that the center passes within 300 km (rain bands, big surf, gusty wind), about <b>1 in 3</b> within 100 km, about <b>1 in 3</b> for tropical-storm wind in the city, about <b>1 in 10</b> for 93 km/h winds, and low (NHC: {NHC['p64']}%) for hurricane wind, because the official line crosses the Sierra before it reaches the bay.</li>
<li><b>When:</b> swell from Friday; rain bands from Saturday afternoon; the worst Saturday night to Sunday afternoon; easing Sunday night to Monday.</li>
<li><b>Most likely at the buildings</b> (NHC probabilities, median): Amapas {bw(v_med,'amapas')[0]} km/h gusting {bw(v_med,'amapas')[1]}, Casa Francisca {bw(v_med,'ezapata')[0]} gusting {bw(v_med,'ezapata')[1]}, Pitillal {bw(v_med,'pitillal')[0]} gusting {bw(v_med,'pitillal')[1]}; 100–200 mm of rain, more on the slopes. <b>Worst case among the five</b> ({Wc['name']}): center {Wc['cpa_km']} km {d8(Wc['cpa_brg'])} at {lt(Wc['cpa_local'])}; Amapas {Wc['sites']['amapas']['kmh']} km/h gusting {Wc['sites']['amapas']['gust_kmh']}; about {Wc['rain_mm']} mm before the mountains add theirs; Pitillal and Cuale rivers in flood.</li>
<li><b>What to do now:</b> prepare as for a storm on Sunday: water, food and medicine for three days, phones charged, documents in a bag, the car parked on high ground in Pitillal by Saturday afternoon, balcony items in at Amapas by Saturday. Watch for the Wednesday watches.</li>
</ul></div>

<div class="tiles">
<div class="tile"><div class="n">{NHC['p34']}%</div><div class="l">NHC: tropical-storm wind (≥ 63 km/h) in Puerto Vallarta, Friday night to Sunday night</div></div>
<div class="tile"><div class="n">{of['cpa_km']} km</div><div class="l">closest approach of the NHC line, {lt(of['cpa_local'])}, after landfall near Manzanillo</div></div>
<div class="tile"><div class="n">{T5['within']['100']}%</div><div class="l">of the five best Simon models within 100 km ({T5['within']['300']}% within 300 km)</div></div>
<div class="tile"><div class="n">Sat–Sun</div><div class="l">rain bands from Saturday afternoon; worst Saturday night to Sunday afternoon</div></div>
</div>

<h2>1. NHC advisory {NHC['adv']}</h2>
<p>Discussion 3 (Mahoney): Trudy has a large circulation but a compact core, with tropical-storm winds only in the northern semicircle and within 60 n mi of the center; the center was hard to place. The track "is difficult and uncertain, with higher than normal spread in the guidance from 72 h onward", as Trudy reaches weak steering between a retreating ridge and a trough over the western United States. "The deterministic global models are significantly slower than the HFIP Corrected Consensus Aid (HCCA), Google DeepMind (GDMI), the European Centre's AIFS, and the AI-GFS. The new track forecast closely follows HCCA and GDMI, which have been the best-performing track forecast aids this season." Rapid intensification is forecast. "For this cycle, the GFS track is unrealistic." Key message: "Trudy is forecast to be a major hurricane as it approaches the coast of southwestern and west-central Mexico late this week and into the weekend… watches could be required for a portion of these areas on Wednesday."</p>
<table style="break-inside: avoid"><tr><th>Valid (local)</th><th>Position</th><th class=num>Wind, kt</th><th>Strength</th></tr>
<tr><td>Tue 9 pm (now)</td><td>11.2N 97.0W</td><td class=num>40</td><td>tropical storm</td></tr>
<tr><td>Wed 6 pm</td><td>12.6N 100.0W</td><td class=num>65</td><td>category-1 hurricane</td></tr>
<tr><td>Thu 6 pm</td><td>14.3N 101.5W</td><td class=num>100</td><td>category 3</td></tr>
<tr><td>Fri 6 pm</td><td>16.3N 102.5W</td><td class=num>115</td><td>category 4</td></tr>
<tr><td>Sat 6 pm</td><td>19.0N 104.4W (coast near Manzanillo)</td><td class=num>115</td><td>category 4</td></tr>
<tr><td>Sun 6 pm</td><td>21.0N 106.0W (off Nayarit)</td><td class=num>75</td><td>category 1</td></tr></table>
<p class="small">Average NHC track errors are about 100 n mi (185 km) at day 4 and 125 n mi (230 km) at day 5, and about 15 kt in intensity. Puerto Vallarta's probabilities: 34 kt {NHC['p34']}% (14% Friday night to Saturday night, 20% Saturday night to Sunday night), 50 kt {NHC['p50']}%, 64 kt {NHC['p64']}%. Barra de Navidad 44 / 22 / 9%, San Blas 38 / 13 / 6%, Islas Marías 39 / 17 / 8%.</p>

<h2>2. The five best Simon models</h2>
<p>The five best position forecasters of Simon's last two days, leaving out the NHC's own products and the climatology baseline (12–36 h mean error in km in the second column). Their {hz(LATEST)} early versions, with the {hz(PREV)} runs for comparison. The NHC corrected consensus, excluded here, passes {hc['cpa_km']} km {comp(hc['cpa_brg'])} at {lt(hc['cpa_local'])}.</p>
<table class="five"><tr><th>Model</th><th class=num>Simon km</th><th class=num>Closest km</th><th>Side</th><th>When</th><th class=num>kt then</th><th class=num>Peak kt</th><th>Landfall</th><th class=num>{hz(PREV)}</th><th class=num>Amapas km/h</th><th class=num>E. Zapata</th><th class=num>Pitillal</th><th class=num>Rain mm</th></tr>
{five_rows}</table>
<p class="small">Closest approach to 20.61N 105.23W, Vallarta time. Building winds: sustained, if the center followed that line exactly, from the parametric field of the Simon graphics with the Simon exposure factors and no weakening over land; not probabilities. Rain: R-CLIPER-type total at the city, no terrain. † intensity from the NHC intensity consensus. The AIFS early version is the {hz(PREV)} AIFS run moved to the {hz(LATEST)} center by the NHC's own rule.</p>
<figure><img src="{O}/t1_tracks.png" alt="Track map"><figcaption><b>Figure 1.</b> The NHC forecast (black and yellow, with local day and strength), the five best Simon models (thick: {hz(LATEST)}; thin dashed: {hz(PREV)}), the other aids, the three ensembles, and Simon's NHC forecast (orange dashed).</figcaption></figure>
<figure class="w90"><img src="{O}/t4_intensity.png" alt="Intensity"><figcaption><b>Figure 2.</b> Intensity. The NHC forecasts a peak of 115 kt; DeepMind {next(m for m in FIVE if BASE.get(m['tech']) == 'GDMN')['peak_v']} kt; the ensemble means are smeared and weak by construction.</figcaption></figure>

<h2>3. The chances</h2>
<figure><img src="{O}/t3_chances.png" alt="Chances"><figcaption><b>Figure 3.</b> NHC probability of tropical-storm wind (black), the share of the five lines (purple) and of ensemble members and analog storms (grey) that bring the center within 100, 200 and 300 km or give tropical-storm wind in the city.</figcaption></figure>
<table class="out"><tr><th>Outcome</th><th class=num>NHC</th><th class=num>Five, {hz(LATEST)}</th><th class=num>Five, {hz(PREV)}</th><th class=num>AIFS ens. / ECMWF ens. / GEFS / climo</th><th>Our reading</th></tr>
<tr><td>Center within 300 km</td><td class=num>—</td><td class=num>{T5['within']['300']}%</td><td class=num>{T5P['within']['300']}%</td><td class=num>{AI['within']['300']} / {EC['within']['300']} / {GE['within']['300']} / {pct(C5['within']['300'], n5)}%</td><td>about 4 in 5</td></tr>
<tr><td>Center within 100 km</td><td class=num>—</td><td class=num>{T5['within']['100']}%</td><td class=num>{T5P['within']['100']}%</td><td class=num>{AI['within']['100']} / {EC['within']['100']} / {GE['within']['100']} / {pct(C5['within']['100'], n5)}%</td><td>about 1 in 3</td></tr>
<tr><td>Tropical-storm wind (≥ 63 km/h) in the city</td><td class=num>{NHC['p34']}%</td><td class=num>{T5['pv34']}%</td><td class=num>{T5P['pv34']}%</td><td class=num>{AI['pv34']} / {EC['pv34']} / {GE['pv34']} / {pct(C5['ts_within200'], n5)}%</td><td>about 1 in 3</td></tr>
<tr><td>Strong tropical-storm wind (≥ 93 km/h)</td><td class=num>{NHC['p50']}%</td><td class=num colspan=3>—</td><td>about 1 in 10</td></tr>
<tr><td>Hurricane wind (≥ 119 km/h) in the city</td><td class=num>{NHC['p64']}%</td><td class=num colspan=3>—</td><td>low</td></tr></table>
<p class="small">Climatology: {n5} storms since 1949 passed within 500 km of Trudy's position between 12 September and 11 November; {C5['within']['300']} came within 300 km of Vallarta, {C5['within']['100']} within 100 km. The closest: {', '.join(f"{s['name'].title()} {s['year']} ({s['cpa_km']} km)" for s in C5['storms'] if s['cpa_km'] <= 125)}.</p>

<h2 class="pb">4. The three addresses</h2>
<p>Four columns. Least, most likely and worst are lines from the five best Simon models ("most likely" is their median by closest approach; "worst" the line with the strongest wind at the terrace). The NHC column turns the advisory's wind probabilities for Puerto Vallarta into a median and a 1-in-10 wind, times the same exposure factors (0.89 for the Amapas terrace with a land wind, 0.77 for the sheltered mid floor, 0.70 for the street-level house); its timing is from the official line. Times are Vallarta time.</p>
<table class="scen">
<tr><th></th><th>Least<br><span class=small>{L['name']}: {L['cpa_km']} km {d8(L['cpa_brg'])} at {lt(L['cpa_local'])}, {L['cpa_v']} kt</span></th>
<th>Most likely (five)<br><span class=small>{K['name']}: {K['cpa_km']} km {d8(K['cpa_brg'])} at {lt(K['cpa_local'])}, {K['cpa_v']} kt</span></th>
<th>NHC advisory {NHC['adv']}<br><span class=small>landfall near Manzanillo Saturday evening; center {of['cpa_km']} km {d8(of['cpa_brg'])} at {lt(of['cpa_local'])}</span></th>
<th>Worst (five)<br><span class=small>{Wc['name']}: {Wc['cpa_km']} km {d8(Wc['cpa_brg'])} at {lt(Wc['cpa_local'])}, {Wc['cpa_v']} kt after a {Wc['peak_v']}-kt peak</span></th></tr>
<tr><td>Swell on the coast</td><td>{win(L,'swell')}</td><td>{win(K,'swell')}</td><td>{win(NH,'swell')}</td><td>{win(Wc,'swell')}</td></tr>
<tr><td>Rain bands</td><td>{win(L,'bands')}</td><td>{win(K,'bands')}</td><td>{win(NH,'bands')}</td><td>{win(Wc,'bands')}</td></tr>
<tr><td>Tropical-storm wind in the city</td><td>{win(L,'ts')}</td><td>{win(K,'ts')}</td><td>{NHC['p34']}% chance, {win(NH,'ts')} if on the line</td><td>{win(Wc,'ts')}</td></tr>
<tr><td>Rain at the city (before terrain)</td><td>{L['rain_mm']} mm</td><td>{K['rain_mm']} mm</td><td>{NH['rain_mm']} mm on the line</td><td>{Wc['rain_mm']} mm</td></tr>
<tr><td>D Terrace, Amapas, 8th floor</td><td>{scell(L,'amapas')}</td><td>{scell(K,'amapas')}</td><td>{ncell('amapas')}</td><td>{scell(Wc,'amapas')}</td></tr>
<tr><td>Casa Francisca, Emiliano Zapata, 3rd floor</td><td>{scell(L,'ezapata')}</td><td>{scell(K,'ezapata')}</td><td>{ncell('ezapata')}</td><td>{scell(Wc,'ezapata')}</td></tr>
<tr><td>El Pitillal house, street level</td><td>{scell(L,'pitillal')}</td><td>{scell(K,'pitillal')}</td><td>{ncell('pitillal')}</td><td>{scell(Wc,'pitillal')}</td></tr>
<tr><td>What it means</td><td>Big surf and a wet Sunday; nothing more.</td><td>A hurricane passing offshore to the southwest on Sunday evening. Heavy rain Sunday, gusty wind, high surf on the open coast and the Malecón. Ordinary storm precautions.</td><td>A weakening hurricane crossing the Sierra and passing close to the bay on Sunday. Wind most likely below storm force in town but gusty; 1 in 10 for damaging gusts near 100 km/h on the exposed terrace; heavy rain on the slopes; river flooding likely in Pitillal; power cuts likely.</td><td>A hurricane 60–70 km southwest on Sunday morning. Tropical-storm wind from midnight to mid-afternoon Sunday, gusts near 100 km/h on the terrace, power and water cuts; {Wc['rain_mm']} mm plus terrain puts the Pitillal and Cuale rivers in flood and risks slides on the Amapas and Conchas Chinas slopes. Pitillal: on higher ground by Saturday night.</td></tr></table>
<figure><img src="{O}/t5_timeline.png" alt="Timeline"><figcaption><b>Figure 4.</b> Timing of swell, rain bands and tropical-storm wind at the city on the NHC line and three of the five. The NHC row's wind bar assumes the center follows the line exactly; the NHC's own chance for that wind is {NHC['p34']}%.</figcaption></figure>

<h2>5. The GFS, out to 384 hours</h2>
<p>The GFS run of 6 pm Monday (18Z) is the outlier for Trudy: it makes landfall in Michoacán on Saturday as a 90-kt hurricane and has it fall apart inland by Sunday ({trudy_end[1]:.1f}N {abs(trudy_end[2]):.1f}W, hour {trudy_end[0]}); the NHC calls this track unrealistic. The "turn" seen on GFS maps later in the run is a second storm, not Trudy: it forms south of Mexico near {LATE[0][1]:.0f}N {abs(LATE[0][2]):.0f}W around {gl(LATE[0][0])}, moves west-northwest, then turns north, peaks at {lpk[3]:.0f} hPa (about {lpk[4]:.0f} kt) {round(math.hypot(lpk[1] - 20.61, (lpk[2] + 105.2345) * math.cos(math.radians(20))) * 111, -1):.0f} km southwest of Vallarta around {gl(lpk[0])}, and crosses the coast just north of the bay that night. In that run, Puerto Vallarta gets about {gr['348'] - gr['300']:.0f} mm of rain between 26 and 28 October and a peak wind of {max(gw.values()):.0f} km/h at the grid point. That is one run at 13–15 days, a storm that does not exist yet; at that range the GFS's skill for a specific storm is close to none. Treat it as a reminder that the season is not over, not as a forecast.</p>
<figure class="w90"><img src="{GA}/frame_330.png" alt="GFS frame"><figcaption><b>Figure 5.</b> One frame of the animation (sent separately as a video): the GFS second storm off Cabo Corrientes on 26–27 October. Colours: 10-m wind; lines: sea-level pressure; bottom strip: the run's wind and rain at Puerto Vallarta.</figcaption></figure>

<h2>6. When we will know</h2>
<ul>
<li><b>Wednesday:</b> NHC advisories at 3 am, 9 am, 3 pm and 9 pm Vallarta time; hurricane or tropical-storm watches for parts of the coast are likely. Watch the Puerto Vallarta line of the wind-speed probabilities.</li>
<li><b>Thursday:</b> about 72 hours out; NHC track errors drop to about 140 km. If the line still crosses the coast near Manzanillo and heads for the bay, prepare for the NHC column above; if it bends east inland or west offshore, the numbers fall.</li>
<li><b>Friday:</b> warnings 36 hours before tropical-storm winds. Simon's lesson: even inside 24 hours the line can shift 100 km; read the probabilities, not the line.</li>
</ul>
<p class="small">Simon, meanwhile (advisory 27): a tiny 95-kt hurricane 200 km west of Cabo Corrientes, re-intensifying and drifting west at 4 km/h, forecast to move near Las Islas Marías on Thursday and weaken; a Hurricane Watch is in effect for Las Islas Marías; the NHC's confidence is low. Its swell continues on the coast.</p>

<h2 class="pb">Appendix. Every aid</h2>
<h3>A1. {hz(LATEST)} cycle (official forecast and early versions)</h3>
<table class="app"><tr><th>Aid</th><th class=num>Closest, km</th><th>Side</th><th>When (local)</th><th class=num>kt then</th><th class=num>Peak kt</th><th class=num>Rain mm</th><th>Landfall</th></tr>
{rowsL}</table>
<h3>A2. {hz(PREV)} runs</h3>
<table class="app"><tr><th>Aid</th><th class=num>Closest, km</th><th>Side</th><th>When (local)</th><th class=num>kt then</th><th class=num>Peak kt</th><th class=num>Rain mm</th><th>Landfall</th></tr>
{rowsP}</table>
<p class="small">† intensity from the NHC intensity consensus. ECMWF IFS {hz(ecm['cycle'])}: {ecm['cpa_km']} km {comp(ecm['cpa_brg'])} at {lt(ecm['cpa_local'])}. Ensembles: GEFS {hz(ENSC['gefs'])} ({GE['n']} members), ECMWF {hz(ENSC['ecens'])} ({EC['n']} members tracked as disturbance 71E), AIFS {hz(ENSC['aiens'])} ({AI['n']} members). Method as in the earlier Trudy brief: hourly interpolation, Natural Earth land, parametric wind with model radii where available, R-CLIPER rain, Simon exposure factors. Climatology: HURDAT2 1949–2025 centred on 11.0N 96.7W.</p>
<div class="foot">Code and data: hurricane-simon/trudy in branch claude/hourly-forecast-animation-m4v1bj of the vallarta-weather repository. Not an official forecast. Follow the SMN, the NHC and Protección Civil. Emergencies: 911.</div>
</body></html>"""
open(OUT, 'w').write(html); print('brief html', len(html), 'v_med', round(v_med, 1))
