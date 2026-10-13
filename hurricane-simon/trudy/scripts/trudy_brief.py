"""Build the EP93 (Trudy) Puerto Vallarta brief (HTML) around the five best Simon performers, latest cycle versus the previous one.
Usage: trudy_brief.py SCRATCH OUT.html"""
import json, sys, math, datetime as dt
S, OUT = sys.argv[1:3]; T = S + '/trudy'; O = 'file://' + T + '/out'
M = json.load(open(T + '/models.json')); C = json.load(open(T + '/climo.json')); CH = json.load(open(T + '/chances.json')); SC = json.load(open(T + '/scenarios.json'))
SM = M['summary']; TR = M['tracks']; W = M['simon_err']
LATEST, PREV, ENSC = CH['latest'], CH['prev'], CH['ensc']
T5, T5P, T5B = SM[LATEST]['top5'], SM[PREV]['top5'], SM[LATEST]['top5b']
EC, AI, GE = SM[ENSC['ecens']]['ecens'], SM[ENSC['aiens']]['aiens'], SM[ENSC['gefs']]['gefs']
C5 = C['500']; n5 = C5['n']; P0 = C['p0']
BT = []
for line in open(T + '/bdeck_latest.dat'):
    f = [x.strip() for x in line.split(',')]
    if len(f) > 8 and f[4] == 'BEST': BT.append((f[2], int(f[6][:-1]) / 10, -int(f[7][:-1]) / 10, int(f[8]), int(f[9])))
def geo(a, b, c, d): return 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(c - a) / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(math.radians(d - b) / 2) ** 2))
jump = round(geo(BT[-2][1], BT[-2][2], BT[-1][1], BT[-1][2])); pv_km = round(geo(BT[-1][1], BT[-1][2], 20.61, -105.2345), -2)
def get(c, t): return next((r for r in TR if r['cycle'] == c and r['tech'] == t), None)
def comp(b): return ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'][int((b + 11.25) // 22.5) % 16]
def cat(v): return 'tropical storm' if v < 64 else 'category-1 hurricane' if v < 83 else 'category-2 hurricane' if v < 96 else 'category-3 hurricane' if v < 113 else 'category-4 hurricane' if v < 137 else 'category-5 hurricane'
def lt(s): return s.replace(' 00:00', ' midnight').replace(' 12:00', ' noon')
def lfl(t): return lt((dt.datetime.strptime(t, '%Y-%m-%d %HZ') - dt.timedelta(hours=6)).strftime('%a %d %b %H:%M'))
def short(s): return s.replace(' Oct', '')
def cap(t): return t[0].upper() + t[1:]
def hz(c): return c[-2:] + 'Z'
def of5(p): return {0: 'none of the five', 20: 'one of the five', 40: 'two of the five', 60: 'three of the five', 80: 'four of the five', 100: 'all five'}.get(p, f'{p}%')
BASE = {'GDMI': 'GDMN', 'GDM2': 'GDMN', 'CEMI': 'CEMN', 'CEM2': 'CEMN', 'AEMI': 'AEMN', 'AEM2': 'AEMN', 'AIFI': 'AIFS'}
NM = {'GDMN': 'Google DeepMind cyclone model', 'AIFS': 'ECMWF AIFS', 'TVCN': 'track consensus TVCN', 'CEMN': 'Canadian ensemble mean', 'AEMN': 'GEFS ensemble mean', 'HCCA': 'NHC corrected consensus'}
def nm(t): return NM[BASE.get(t, t)]
FIVE = T5['members']; PREVB = {BASE.get(m['tech'], m['tech']): m for m in T5P['members']}
L, K, Wc = SC['least'], SC['likely'], SC['worst']
for _x in (L, K, Wc): _x['name'] = _x['name'].replace('Track consensus', 'track consensus')
NUMW = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'all five'}
hc = get(LATEST, 'HCCA'); hcp = get(PREV, 'HCCA'); ecm = get('2026101212', 'ECMO')
f5 = sorted(FIVE, key=lambda m: m['cpa_km'])
SITES = [('amapas', 'D Terrace, Amapas, 8th floor'), ('ezapata', 'Casa Francisca, Emiliano Zapata, 3rd floor'), ('pitillal', 'El Pitillal house, street level')]
def d8(b): return ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][int((b + 22.5) // 45) % 8]
def line_desc(m): return f"{m['cpa_km']} km {comp(m['cpa_brg'])} at {lt(m['cpa_local'])}"
def aid_rows(cycle, techs):
    out = []
    for t in techs:
        r = get(cycle, t)
        if not r: continue
        lf = f"{r['landfall']['region']}, {short(lfl(r['landfall']['t']))}, {r['landfall']['v']} kt" if r['landfall'] else '—'
        out.append(f"<tr><td>{r['name']}{' †' if r['ivcn'] else ''}</td><td class=num>{r['cpa_km']}</td><td>{comp(r['cpa_brg'])}</td><td class=nw>{short(lt(r['cpa_local']))}</td><td class=num>{r['cpa_v'] or '—'}</td><td class=num>{r['peak_v'] or '—'}</td>"
                   f"<td class=num>{r['sites']['amapas']['kmh']}</td><td class=num>{r['sites']['ezapata']['kmh']}</td><td class=num>{r['sites']['pitillal']['kmh']}</td><td class=num>{r['rain_mm']}</td><td>{lf}</td></tr>")
    return '\n'.join(out)
rowsL = aid_rows(LATEST, ['GDMI', 'AIFI', 'TVCN', 'CEM2', 'AEMI', 'HCCA', 'AVNI', 'UKX2', 'NVG2', 'CMC2', 'HFAI', 'HFBI', 'HWFI', 'HMNI', 'CTCI', 'CLP5'])
rowsP = aid_rows(PREV, ['GDMN', 'AIFS', 'TVCN', 'CEMI', 'AEMN', 'HCCA', 'AVNO', 'UKXI', 'NVGM', 'HFSA', 'HFSB', 'HWRF', 'HMON', 'CTCX', 'CLP5'])
five_rows = '\n'.join(
    f"<tr><td class=nw><b>{cap(nm(m['tech']))}</b>{' †' if m['ivcn'] else ''}</td><td class=num>{W[BASE.get(m['tech'], m['tech'])]}</td><td class=num>{round(100 * T5['weights'][m['tech']])}%</td>"
    f"<td class=num><b>{m['cpa_km']}</b></td><td>{comp(m['cpa_brg'])}</td><td class=nw>{short(lt(m['cpa_local']))}</td><td class=num>{m['cpa_v']}</td><td class=num>{m['peak_v']}</td>"
    f"<td class=num>{PREVB[BASE.get(m['tech'], m['tech'])]['cpa_km']} {comp(PREVB[BASE.get(m['tech'], m['tech'])]['cpa_brg'])}</td>"
    f"<td class=num>{m['sites']['amapas']['kmh']}</td><td class=num>{m['sites']['ezapata']['kmh']}</td><td class=num>{m['sites']['pitillal']['kmh']}</td><td class=num>{m['rain_mm']}</td></tr>" for m in FIVE)
clim_rows = '\n'.join(f"<tr><td>{s['year']} {s['name'].title()}</td><td>{s['lat0']:.1f}N {-s['lon0']:.1f}W, {s['t0'][:10]}</td><td class=num>{s['cpa_km']}</td><td>{s['cpa_t'][:10]} (+{s['cpa_days']} d)</td><td class=num>{s['v_cpa'] or '—'}</td><td class=num>{s['vmax']}</td><td>{s['region']}</td></tr>" for s in C5['storms'] if s['cpa_km'] <= 300)
def scell(s, k): x = s['sites'][k]; return f"<b>{x['kmh']}</b> km/h, gusts {x['gust_kmh']}<br><span class=small>{lt(x['t'])}, wind from the {comp(x['frm'])}</span>"
def win(s, k): w = s['windows'][k]; return f"{lt(w[0])} → {lt(w[1])}" if w else '—'
def pct(n, d): return round(100 * n / d)
close_now = [m for m in FIVE if m['cpa_km'] <= 200]; close_prev = [m for m in T5P['members'] if m['cpa_km'] <= 125]
html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>EP93 (Trudy) and Puerto Vallarta: the five best Simon models</title>
<style>
__FONTS__
@page {{ size: Letter; margin: 17mm 16mm 18mm 16mm; }}
:root {{ --ink: #0b0b0b; --ink2: #3d3c39; --mute: #6b6a66; --line: #dcdad4; --accent: #1c5cab; --panel: #f3f2ee; --warn: #b3410f; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: #fff; color: var(--ink); font-family: "Red Hat Text", "DejaVu Sans", Arial, sans-serif; font-size: 10.2pt; line-height: 1.42; }}
h1, h2, h3, h4 {{ font-family: "Red Hat Display", "DejaVu Sans", Arial, sans-serif; line-height: 1.15; margin: 0; }}
h1 {{ font-size: 23pt; font-weight: 800; letter-spacing: -0.01em; }}
h2 {{ font-size: 15pt; font-weight: 800; margin: 16pt 0 6pt; padding-top: 6pt; border-top: 2px solid var(--ink); break-after: avoid; }}
h3 {{ font-size: 11.3pt; font-weight: 700; margin: 10pt 0 4pt; break-after: avoid; }}
p {{ margin: 0 0 6pt; }} ul, ol {{ margin: 0 0 6pt 16pt; padding: 0; }} li {{ margin: 0 0 3pt; }}
.kicker {{ font-family: "Red Hat Mono", monospace; color: var(--accent); font-size: 9pt; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 8pt; }}
.sub {{ font-size: 12pt; color: var(--ink2); margin: 8pt 0 10pt; line-height: 1.35; }}
.meta {{ font-family: "Red Hat Mono", monospace; font-size: 8.4pt; color: var(--mute); margin-bottom: 12pt; }}
.box {{ background: var(--panel); border-left: 4px solid var(--accent); padding: 8pt 11pt; margin: 8pt 0 10pt; break-inside: avoid; }}
.box.warn {{ border-left-color: var(--warn); }} .box h3 {{ margin-top: 0; }}
.small {{ font-size: 8.6pt; color: var(--mute); }}
figure {{ margin: 8pt 0 10pt; break-inside: avoid; }} figure img {{ display: block; width: 100%; height: auto; }}
figure.w80 img {{ width: 80%; margin: 0 auto; }} figure.w90 img {{ width: 90%; margin: 0 auto; }}
figcaption {{ font-size: 8.6pt; color: var(--ink2); margin-top: 4pt; line-height: 1.35; }} figcaption b {{ color: var(--ink); }}
table {{ width: 100%; border-collapse: collapse; font-size: 8.6pt; margin: 6pt 0 10pt; }}
th, td {{ text-align: left; vertical-align: top; padding: 3.5pt 4.5pt; border-bottom: 1px solid var(--line); }}
th {{ font-weight: 700; font-size: 8.2pt; color: var(--ink2); border-bottom: 1.5px solid var(--ink); }}
td.num, th.num {{ text-align: right; font-family: "Red Hat Mono", monospace; white-space: nowrap; }}
td.nw {{ white-space: nowrap; }} table.app {{ font-size: 7.9pt; }} table.app td, table.app th {{ padding: 2.8pt 3.4pt; }}
table.five {{ font-size: 8pt; break-inside: avoid; }} table.five td, table.five th {{ padding: 3pt 3.5pt; }}
tr {{ break-inside: avoid; }}
.tiles {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 7pt; margin: 8pt 0 10pt; break-inside: avoid; }}
.tile {{ background: var(--panel); border-radius: 6pt; padding: 8pt 9pt; }}
.tile .n {{ font-family: "Red Hat Display", sans-serif; font-size: 18pt; font-weight: 800; line-height: 1.1; }}
.tile .l {{ font-size: 8.2pt; color: var(--ink2); margin-top: 2pt; line-height: 1.3; }}
.pb {{ break-before: page; }}
.foot {{ font-size: 8.2pt; color: var(--mute); border-top: 1px solid var(--line); padding-top: 6pt; margin-top: 14pt; }}
table.scen td:first-child {{ font-weight: 700; width: 19%; }} table.scen th {{ width: 27%; }}
table.out {{ font-size: 8.3pt; break-inside: avoid; }} table.out td:first-child {{ width: 31%; }}
</style></head><body>

<div class="kicker">Invest EP93 · the storm that will be Trudy · Puerto Vallarta · the five best Simon models</div>
<h1>Trudy before it exists: what the five models that got Simon right say for Puerto Vallarta</h1>
<p class="sub">The five best position forecasters of Simon's last two days, leaving out the NHC's own products: Google DeepMind's cyclone model, the ECMWF AIFS, the track consensus, the Canadian ensemble mean and the GEFS ensemble mean. Their newest lines for EP93, how they moved in six hours, the chances they imply for Vallarta, and the least, most likely and worst cases at D Terrace in Amapas, Casa Francisca in Emiliano Zapata and the house in El Pitillal.</p>
<p class="meta">Monday 12 October 2026, 7 pm Vallarta time (13 Oct 01Z) · the five models' Monday {hz(PREV)} runs and their {hz(LATEST)} early versions · NHC outlook of 5 pm PDT · no NHC advisory exists yet for EP93 · not an official forecast</p>

<div class="box warn"><h3>Bottom line</h3>
<ul>
<li><b>The newest numbers moved away from the bay.</b> At 6 pm the NHC placed EP93's center at {BT[-1][1]}N {abs(BT[-1][2])}W, {jump} km west of its noon position and roughly 100 km west of where the five models expected it. Moved to that center (the "early versions" the NHC forecaster works from), the five pass {', '.join(f"{nm(m['tech'])} {m['cpa_km']} km {comp(m['cpa_brg'])}" for m in f5)}. Six hours earlier, {NUMW[len(close_prev)]} of the five passed within {max(m['cpa_km'] for m in close_prev)} km.</li>
<li><b>The chances, read from the five.</b> Newest versions: center within 300 km, <b>{T5['within']['300']}%</b> ({of5(T5['within']['300'])}); within 200 km, <b>{T5['within']['200']}%</b>; within 100 km, <b>{T5['within']['100']}%</b>; tropical-storm wind in the city, <b>{T5['pv34']}%</b>. The {hz(PREV)} runs gave {T5P['within']['300']}%, {T5P['within']['200']}%, {T5P['within']['100']}% and {T5P['pv34']}%. The ECMWF AIFS ensemble ({hz(ENSC['aiens'])}) still puts {AI['within']['100']}% of its members within 100 km, the ECMWF ensemble ({hz(ENSC['ecens'])}) {EC['within']['100']}%, the GEFS {GE['within']['100']}%, climatology {pct(C5['within']['100'], n5)}%.</li>
<li><b>Our reading.</b> The center of a broad low is uncertain by 100 km or more until it tightens, so one re-fix should not erase the earlier runs. Weighting the newest positioning most: <b>about 2 in 3</b> that the center passes within 300 km and brings swell and rain bands, <b>about 1 in 5</b> for tropical-storm wind in the city, <b>about 1 in 10</b> for the center within 100 km.</li>
<li><b>When.</b> Sunday 18 October from midday to Monday 19 morning. Closest approach on the newest lines: Sunday 6 pm (DeepMind, AIFS) to Monday 3 am (track consensus). Swell from Saturday; rain bands from Sunday midday.</li>
<li><b>Most likely</b> (the median of the five, the {K['name']}): center {K['cpa_km']} km {d8(K['cpa_brg'])} at {lt(K['cpa_local'])} as a {cat(K['cpa_v'])}; rain bands {win(K, 'bands').replace(' → ', ' to ')}; {K['sites']['amapas']['kmh']} km/h with gusts to {K['sites']['amapas']['gust_kmh']} on the Amapas terrace; about {K['rain_mm']} mm. <b>Worst case</b> (the {Wc['name']}, before the re-fix): center {Wc['cpa_km']} km {d8(Wc['cpa_brg'])} at {lt(Wc['cpa_local'])} as a {cat(Wc['cpa_v'])}; tropical-storm wind {win(Wc, 'ts').replace(' → ', ' to ')}; {Wc['sites']['amapas']['kmh']} km/h with gusts to {Wc['sites']['amapas']['gust_kmh']} at Amapas; about {Wc['rain_mm']} mm before the mountains add theirs. <b>Least</b> (the {L['name']}): a weak storm {L['cpa_km']} km to the south; nothing here.</li>
<li><b>Outside the five.</b> The NHC corrected consensus, excluded here as an NHC product, moved the other way: its {hz(LATEST)} version passes {hc['cpa_km']} km {comp(hc['cpa_brg'])} at {lt(hc['cpa_local'])} after a {hc['peak_v']}-kt peak. The ECMWF IFS {hz('2026101212')} run makes landfall on Bahía de Banderas. The GFS, HAFS and HWRF send it far out to sea.</li>
<li><b>What to do now:</b> nothing physical. Keep Sunday flexible. NHC advisory 1 is expected tonight or Tuesday; its wind-speed probabilities for Puerto Vallarta replace every number here. Thursday noon, 72 hours out, is the decision point.</li>
</ul></div>

<div class="tiles">
<div class="tile"><div class="n">{T5['within']['300']}%</div><div class="l">center within 300 km: {of5(T5['within']['300'])}, newest versions ({T5P['within']['300']}% six hours earlier)</div></div>
<div class="tile"><div class="n">{T5['within']['200']}%</div><div class="l">center within 200 km: {of5(T5['within']['200'])} ({T5P['within']['200']}% six hours earlier)</div></div>
<div class="tile"><div class="n">{T5['pv34']}%</div><div class="l">tropical-storm wind in the city on the newest five ({T5P['pv34']}% six hours earlier); our reading about 1 in 5</div></div>
<div class="tile"><div class="n">Sun–Mon</div><div class="l">closest approach Sunday 6 pm to Monday 3 am on the newest lines</div></div>
</div>

<h2>1. Where EP93 is and what the NHC says</h2>
<p>NHC best-track fixes on Monday: {BT[-3][1]}N {abs(BT[-3][2])}W at 6 am, {BT[-2][1]}N {abs(BT[-2][2])}W at noon, {BT[-1][1]}N {abs(BT[-1][2])}W at 6 pm, with {BT[-1][3]}-kt winds and {BT[-1][4]} mb at the last fix, about {int(pv_km):,} km southeast of Puerto Vallarta. The {jump}-km move between noon and 6 pm is faster than the motion the outlook describes (about 16 km/h, or 100 km in six hours), which points to the broad center being re-fixed farther west rather than a real jump. The 5 pm PDT outlook: "Showers and thunderstorms are beginning to show signs of organization in association with a broad area of low pressure located several hundred miles south-southwest of the coast of Guatemala. This system is gradually becoming better defined, and environmental conditions are forecast to be conducive for further development. A tropical depression or tropical storm is expected to form well south of southern Mexico later tonight or tomorrow while the system moves generally west-northwestward at around 10 mph." Formation chance through 48 hours and 7 days: near 100 percent. The next name on the 2026 list is Trudy.</p>

<h2>2. The five, and how they moved</h2>
<p>The final Simon report scored every model's position forecasts against the NHC best track over the two days before the pass (mean error at 12, 24 and 36 h, its Figure 2). Leaving out the NHC's own two products (the official forecast, 47 km, and the corrected consensus, 38 km) and the climatology-persistence baseline (53 km, a yardstick rather than a model), the five best were:</p>
<table class="five"><tr><th>Model</th><th class=num>Simon km</th><th class=num>Weight</th><th class=num>{hz(LATEST)}: closest km</th><th>Side</th><th>When</th><th class=num>kt then</th><th class=num>Peak kt</th><th class=num>{hz(PREV)}: closest</th><th class=num>Amapas km/h</th><th class=num>E. Zapata</th><th class=num>Pitillal</th><th class=num>Rain mm</th></tr>
{five_rows}</table>
<p class="small">{hz(LATEST)} columns: the early versions. "Simon km" is the 12–36 h mean position error; the weight is its inverse square, normalised over the five. Closest approach to 20.61N 105.23W, Vallarta time. Building winds are sustained, on the {hz(LATEST)} line. † intensity from the NHC intensity consensus IVCN.</p>
<ul>
<li><b>What an early version is.</b> The NHC cannot wait for a run to finish, so at each cycle it takes the previous run and moves it so that its 6-hour position matches the new center, with the same shift at every hour. The {hz(LATEST)} DeepMind, track consensus and GEFS-mean lines here are the NHC's own; the Canadian mean is a 12-hour-old run moved the same way. No early AIFS exists in the NHC files, so we built one by the same rule from the {hz(PREV)} AIFS run; the shift was 0.5° south and 1.0° west.</li>
<li><b>Two caveats about the five.</b> The track consensus TVCN is computed at the NHC but is a plain average of the GFS, ECMWF, UKMET, HWRF, HMON, HAFS and COAMPS tracks, so it is kept; Figure 4 shows what changes if the corrected consensus is let back in. The AIFS, like every gridded AI model, under-forecasts intensity by construction, and the TVCN has no intensity at all; both carry the NHC intensity consensus IVCN, which is how the NHC uses TVCN.</li>
<li><b>What Simon's scores can and cannot say.</b> They were earned at 12–36 h on a slow, stalling storm near the coast. Nothing guarantees they transfer to a six-day forecast of a storm that has not formed. Five lines cannot resolve a probability finer than 20%; the ensembles and the climatology are the context that keeps the five honest.</li>
<li><b>Center winds are not Vallarta's winds.</b> Simon reached category 4 and passed 120 km away; the airport recorded 7 km/h and under 10 mm. The building numbers say "if the center followed that line"; once they exist, the NHC wind-speed probabilities are the number to use.</li>
</ul>

<h2>3. The lines on the map</h2>
<figure><img src="{O}/t1_tracks.png" alt="Track map"><figcaption><b>Figure 1.</b> The five best Simon models: thick, the {hz(LATEST)} early versions; thin dashed, the same five from the {hz(PREV)} runs. The whole bundle moved about 100 km west with the re-fixed center. Grey: the other aids ({hz(PREV)}); faint: the three ensembles.</figcaption></figure>
<p>The five still split the way all the guidance splits. The GEFS mean and the Canadian mean keep EP93 a weak system heading west; DeepMind, the AIFS and the track consensus make it a hurricane that turns north toward Cabo Corrientes from Friday, then pass it west or southwest of the bay on Sunday. Deeper storms are steered by deeper flow, so intensity and track are one question here. The ECMWF ensemble ({hz(ENSC['ecens'])}) puts {EC['within']['300']}% of 51 members within 300 km and {EC['within']['100']}% within 100 km; the AIFS ensemble ({hz(ENSC['aiens'])}) {AI['within']['300']}% and {AI['within']['100']}%; the GEFS ({hz(ENSC['gefs'])}) {GE['within']['300']}% and {GE['within']['100']}%. None of the three has been moved to the 6 pm center.</p>
<figure class="w90"><img src="{O}/t4_intensity.png" alt="Intensity"><figcaption><b>Figure 2.</b> Intensity on the five newest lines. DeepMind peaks at {next(m for m in FIVE if BASE.get(m['tech']) == 'GDMN')['peak_v']} kt; the intensity consensus carried by the AIFS and the track consensus peaks at {next(m for m in FIVE if m['tech'] == 'TVCN')['peak_v']} kt; the two ensemble means never reach hurricane strength.</figcaption></figure>

<h2>4. Climatology, for context</h2>
<p>Of the {n5} storms since 1949 that passed within 500 km of EP93's 6 pm position between 12 September and 11 November, {C5['within']['300']} came within 300 km of Puerto Vallarta, {C5['within']['200']} within 200 km and {C5['within']['100']} within 100 km. {C5['hurricane']} became hurricanes and {C5['major']} major hurricanes. The closest passes came {min(C5['days_to_cpa_within300'])}–{sorted(C5['days_to_cpa_within300'])[-2]} days after the analog point (one outlier at 16 days), which from Monday evening means Thursday to Monday. Climatology alone puts a 300-km pass at {pct(C5['within']['300'], n5)}% and a 100-km pass at {pct(C5['within']['100'], n5)}%.</p>
<figure class="w80"><img src="{O}/t2_analogs.png" alt="Analog tracks"><figcaption><b>Figure 3.</b> The {n5} analog storms (grey) and the {C5['within']['300']} that came within 300 km of Vallarta.</figcaption></figure>
<table><tr><th>Storm</th><th>Analog point</th><th class=num>Closest, km</th><th>When</th><th class=num>kt then</th><th class=num>Peak kt</th><th>Region of closest pass</th></tr>
{clim_rows}</table>

<h2>5. The chances</h2>
<figure><img src="{O}/t3_chances.png" alt="Chances"><figcaption><b>Figure 4.</b> Share of the five lines that bring the center within 100, 200 and 300 km of Puerto Vallarta and that give tropical-storm wind in the city, newest versions (dark), the {hz(PREV)} runs (mid), and with the corrected consensus swapped in for the GEFS mean (light). Grey: ensembles and climatology.</figcaption></figure>
<table class="out"><tr><th>Outcome</th><th class=num>Five, {hz(LATEST)}</th><th class=num>Weighted</th><th class=num>Five, {hz(PREV)}</th><th class=num>AIFS ens. / ECMWF ens. / GEFS / climo</th><th>Our reading</th></tr>
<tr><td>Center within 300 km: swell, rain bands, gusty showers</td><td class=num>{T5['within']['300']}%</td><td class=num>{T5['within_w']['300']}%</td><td class=num>{T5P['within']['300']}%</td><td class=num>{AI['within']['300']} / {EC['within']['300']} / {GE['within']['300']} / {pct(C5['within']['300'], n5)}%</td><td>about 2 in 3</td></tr>
<tr><td>Center within 200 km: heavy rain likely, tropical-storm gusts possible on the exposed shore</td><td class=num>{T5['within']['200']}%</td><td class=num>{T5['within_w']['200']}%</td><td class=num>{T5P['within']['200']}%</td><td class=num>{AI['within']['200']} / {EC['within']['200']} / {GE['within']['200']} / {pct(C5['within']['200'], n5)}%</td><td>about 1 in 3</td></tr>
<tr><td>Center within 100 km: the hurricane itself could reach the bay</td><td class=num>{T5['within']['100']}%</td><td class=num>{T5['within_w']['100']}%</td><td class=num>{T5P['within']['100']}%</td><td class=num>{AI['within']['100']} / {EC['within']['100']} / {GE['within']['100']} / {pct(C5['within']['100'], n5)}%</td><td>about 1 in 10</td></tr>
<tr><td>Tropical-storm wind (≥ 63 km/h sustained) in the city</td><td class=num>{T5['pv34']}%</td><td class=num>{T5['pv34_w']}%</td><td class=num>{T5P['pv34']}%</td><td class=num>{AI['pv34']} / {EC['pv34']} / {GE['pv34']} / {pct(C5['ts_within200'], n5)}%</td><td>about 1 in 5</td></tr>
<tr><td>Hurricane wind (≥ 119 km/h sustained) in the city</td><td class=num>0%</td><td class=num>0%</td><td class=num>0%</td><td class=num>0 / 0 / 0 / —</td><td>under 5%</td></tr></table>
<p><b>How the reading is made.</b> The newest five give no tropical-storm wind and no 100-km pass. The same five six hours earlier gave three of five for both kinds of close outcome, and the only thing that changed was where the NHC placed a broad, still-forming center. The AIFS ensemble, the best of the three ensembles on Simon's track, still has about a third of its members within 100 km. Climatology sits near 1 in 10 for a 100-km pass. Our reading weights the newest positioning most but does not discard the rest. It is a judgment, rounded on purpose, and it will move with the first NHC advisory.</p>

<h2 class="pb">6. The three addresses: least, most likely, worst</h2>
<p>Each column is one of the five lines, run through the same parametric wind field and exposure factors as the Simon graphics (1.08 for the Amapas terrace when the wind comes off the bay, 0.89 otherwise; 0.77 for the sheltered mid floor; 0.70 for the street-level house), with an R-CLIPER-type rain total along the track (no terrain enhancement; the Sierra behind the city can double the total on the slopes). "Most likely" is the median of the five newest lines by closest approach. "Worst" is the line, from either the newest or the {hz(PREV)} set, with the strongest wind at the terrace among lines that carry their own intensity. Times are Vallarta time.</p>
<table class="scen">
<tr><th></th><th>Least impact<br><span class=small>{L['name']}: {L['cpa_km']} km {d8(L['cpa_brg'])} at {lt(L['cpa_local'])}, {L['cpa_v']} kt</span></th>
<th>Most likely<br><span class=small>{K['name']}: center {K['cpa_km']} km {d8(K['cpa_brg'])} at {lt(K['cpa_local'])}, {cat(K['cpa_v'])} ({K['cpa_v']} kt, consensus intensity)</span></th>
<th>Worst case<br><span class=small>{Wc['name']}: center {Wc['cpa_km']} km {d8(Wc['cpa_brg'])} at {lt(Wc['cpa_local'])}, {cat(Wc['cpa_v'])} ({Wc['cpa_v']} kt) after a {Wc['peak_v']}-kt peak</span></th></tr>
<tr><td>Swell on the coast</td><td>{win(L,'swell')}</td><td>{win(K,'swell')}</td><td>{win(Wc,'swell')}</td></tr>
<tr><td>Rain bands over the bay</td><td>{win(L,'bands')}</td><td>{win(K,'bands')}</td><td>{win(Wc,'bands')}</td></tr>
<tr><td>Tropical-storm wind in the city</td><td>{win(L,'ts')}</td><td>{win(K,'ts')}</td><td>{win(Wc,'ts')}</td></tr>
<tr><td>Rain, storm total (city, before terrain)</td><td>{L['rain_mm']} mm</td><td>{K['rain_mm']} mm</td><td>{Wc['rain_mm']} mm</td></tr>
<tr><td>D Terrace, Amapas, 8th floor</td><td>{scell(L,'amapas')}</td><td>{scell(K,'amapas')}</td><td>{scell(Wc,'amapas')}</td></tr>
<tr><td>Casa Francisca, Emiliano Zapata, 3rd floor</td><td>{scell(L,'ezapata')}</td><td>{scell(K,'ezapata')}</td><td>{scell(Wc,'ezapata')}</td></tr>
<tr><td>El Pitillal house, street level</td><td>{scell(L,'pitillal')}</td><td>{scell(K,'pitillal')}</td><td>{scell(Wc,'pitillal')}</td></tr>
<tr><td>What it means</td><td>A weak storm far to the south. Normal surf; nothing else.</td><td>A hurricane passing well offshore to the southwest overnight Sunday, with the city on its onshore side. Big surf on the open coast and the Malecón from Saturday; a wet, gusty Sunday afternoon and night; balcony items at Amapas worth bringing in. Casa Francisca and Pitillal: ordinary heavy-rain precautions, keep the car off the low streets near the river on Sunday night.</td><td>A {cat(Wc['cpa_v'])} about {round(Wc['cpa_km'], -1)} km {['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'][int((Wc['cpa_brg'] + 22.5) // 45) % 8]} of the bay on Sunday afternoon, moving north. Tropical-storm wind for most of Sunday, gusts to {Wc['sites']['amapas']['gust_kmh']} on the Amapas terrace, power cuts likely; {Wc['rain_mm']} mm plus terrain on the Cuale and Pitillal catchments puts both rivers up and the low streets under water, with slides possible on the Amapas and Conchas Chinas slopes. Pitillal: be on higher ground with the car by Saturday night. A Hurricane Watch on Friday would be about this case.</td></tr></table>
<figure><img src="{O}/t5_timeline.png" alt="Timeline"><figcaption><b>Figure 5.</b> The three cases in time. The triangle is the closest approach of the center.</figcaption></figure>

<h2>7. When we will know</h2>
<ul>
<li><b>Tonight or Tuesday:</b> NHC advisory 1 on Tropical Depression or Tropical Storm Trudy, with the first official five-day line and wind-speed probabilities. If Puerto Vallarta appears in the 34-kt probability table at all (the threshold is 3%), the close cases are alive in the official forecast.</li>
<li><b>Tuesday morning and evening:</b> the {hz(LATEST)} and 12Z model runs, the first that start from the re-fixed center rather than being moved to it. If the five come back east toward the bay, the 6 pm re-fix was the outlier; if they stay west, the most-likely case firms up.</li>
<li><b>Thursday noon, about 72 hours out:</b> the decision point. At three days the NHC's average track error is about 150 km. If the official line then runs within 150 km of the bay, prepare for the worst case; if it runs 250 km or more to the southwest, plan for swell and rain. Simon's lesson is that even inside 24 hours the line can shift 100 km; read the probabilities, not the line.</li>
<li><b>Friday:</b> the SMN and the NHC would issue a Hurricane Watch for the Jalisco coast about 48 hours before tropical-storm winds are expected, if the close cases are still on the table.</li>
</ul>

<h2>8. Simon, meanwhile</h2>
<p>NHC advisory 22A (Monday 6 pm Vallarta time): Simon is a category-2 hurricane with 85-kt winds about 125 km west of Cabo Corrientes, drifting west-northwest at 6 km/h. It is forecast to move slowly away from the bay, then turn northeast and reach the Sinaloa coast as a weakening hurricane around Thursday night or Friday. A Hurricane Warning is in effect for the Islas Marías and a Hurricane Watch from Cabo Corrientes to Bahía Tempehuaya. Puerto Vallarta's wind probabilities are below the 3% display threshold; Mazatlán's 34-kt cumulative probability is 54%. Simon will be inland over Sinaloa before Trudy's window opens; the swell it leaves on the Jalisco coast (4–5 m per SMN aviso 40) should ease by midweek, before Trudy's own swell arrives.</p>

<h2>9. Method, sources and caveats</h2>
<ul>
<li><b>The five:</b> Google DeepMind cyclone model (ATCF aids GDMN {hz(PREV)}, GDMI {hz(LATEST)}), ECMWF AIFS single run (ECMWF open-data tropical-cyclone track files, {hz(PREV)}, disturbance 71E, decoded with ecCodes; the {hz(LATEST)} early version built by the NHC rule), track consensus TVCN, Canadian ensemble mean (CEMI {hz(PREV)}, CEM2 {hz(LATEST)}), GEFS ensemble mean (AEMN {hz(PREV)}, AEMI {hz(LATEST)}).</li>
<li><b>Intensity:</b> each model's own, except the TVCN (none) and the AIFS (model 10-m wind, low by construction), which carry the NHC intensity consensus IVCN of their cycle, interpolated to each hour.</li>
<li><b>Closest approach, timing, landfall, building winds, rain:</b> every track interpolated hourly; distance and timing to 20.61N 105.23W; landfall is the first hour over land in the Natural Earth 50 m polygons; wind from the parametric field of the Simon map page with the model's own 34/50/64-kt radii where the deck carries them and climatological radii otherwise, times the Simon exposure factors, with no decay over land; rain from an R-CLIPER-type profile (after Tuleya et al. 2007) integrated hourly, with no terrain enhancement.</li>
<li><b>Weights:</b> inverse square of each model's 12–36 h mean position error over Simon's last 48 h (final report, Figure 2): DeepMind 33, AIFS 50, TVCN 51, Canadian ensemble mean 54, GEFS mean 57 km.</li>
<li><b>Context:</b> GEFS members and all other aids from the NHC ATCF a-deck (aep932026.dat, as of 01Z on 13 October); best track bep932026.dat; ECMWF IFS ensemble (12Z, 51 members) and AIFS ensemble ({hz(ENSC['aiens'])}) from the ECMWF open-data track files (the {hz(PREV)} IFS files stop at 144 h, short of the window); HURDAT2 NE Pacific 1949–2025 for the analogs, centred on the 6 pm position.</li>
<li><b>Not included:</b> the real {hz(LATEST)} model runs (not yet published); any NHC advisory, because none exists. This document should be rerun when advisory 1 and the Tuesday runs are out.</li>
</ul>

<h2 class="pb">Appendix. Every aid</h2>
<h3>A1. {hz(LATEST)} early versions (what the NHC forecaster sees now)</h3>
<table class="app"><tr><th>Aid</th><th class=num>Closest, km</th><th>Side</th><th>When (local)</th><th class=num>kt then</th><th class=num>Peak kt</th><th class=num>Amapas km/h</th><th class=num>E. Zapata</th><th class=num>Pitillal</th><th class=num>Rain mm</th><th>Landfall</th></tr>
{rowsL}</table>
<h3>A2. {hz(PREV)} runs (late versions where available)</h3>
<table class="app"><tr><th>Aid</th><th class=num>Closest, km</th><th>Side</th><th>When (local)</th><th class=num>kt then</th><th class=num>Peak kt</th><th class=num>Amapas km/h</th><th class=num>E. Zapata</th><th class=num>Pitillal</th><th class=num>Rain mm</th><th>Landfall</th></tr>
{rowsP}</table>
<p class="small">† intensity from the NHC intensity consensus IVCN of the same cycle. Climatology-persistence carries no intensity. Consensus aids and ECMWF tracks use climatological wind radii. "kt then" is the intensity at closest approach. Landfall is the first hour over land in the Natural Earth 50 m polygons.</p>
<h3>A3. Ensemble summaries</h3>
<table class="app"><tr><th></th><th class=num>GEFS ({hz(ENSC['gefs'])})</th><th class=num>ECMWF ({hz(ENSC['ecens'])})</th><th class=num>AIFS ({hz(ENSC['aiens'])})</th></tr>
<tr><td>Members</td><td class=num>{GE['n']}</td><td class=num>{EC['n']}</td><td class=num>{AI['n']}</td></tr>
<tr><td>Within 100 / 200 / 300 km</td><td class=num>{GE['within']['100']} / {GE['within']['200']} / {GE['within']['300']}%</td><td class=num>{EC['within']['100']} / {EC['within']['200']} / {EC['within']['300']}%</td><td class=num>{AI['within']['100']} / {AI['within']['200']} / {AI['within']['300']}%</td></tr>
<tr><td>Median closest pass, km</td><td class=num>{GE['cpa_median']}</td><td class=num>{EC['cpa_median']}</td><td class=num>{AI['cpa_median']}</td></tr>
<tr><td>Median peak intensity, kt</td><td class=num>{GE['peak_median']}</td><td class=num>{EC['peak_median']}</td><td class=num>{AI['peak_median']}</td></tr>
<tr><td>Tropical-storm wind in the city</td><td class=num>{GE['pv34']}%</td><td class=num>{EC['pv34']}%</td><td class=num>{AI['pv34']}%</td></tr>
<tr><td>Landfall on Bahía de Banderas / Michoacán–Colima / Nayarit / Sinaloa</td><td class=num>{GE['landfall'].get('Jalisco (Bahía de Banderas)', 0)} / {GE['landfall'].get('Michoacán / Colima', 0)} / {GE['landfall'].get('Nayarit', 0)} / {GE['landfall'].get('Sinaloa', 0)}</td><td class=num>{EC['landfall'].get('Jalisco (Bahía de Banderas)', 0)} / {EC['landfall'].get('Michoacán / Colima', 0)} / {EC['landfall'].get('Nayarit', 0)} / {EC['landfall'].get('Sinaloa', 0)}</td><td class=num>{AI['landfall'].get('Jalisco (Bahía de Banderas)', 0)} / {AI['landfall'].get('Michoacán / Colima', 0)} / {AI['landfall'].get('Nayarit', 0)} / {AI['landfall'].get('Sinaloa', 0)}</td></tr>
<tr><td>No landfall within the run</td><td class=num>{GE['no_landfall']}</td><td class=num>{EC['no_landfall']}</td><td class=num>{AI['no_landfall']}</td></tr>
<tr><td>Median city rain, mm (all / 90th pct)</td><td class=num>{GE['rain_median']} / {GE['rain_q90']}</td><td class=num>{EC['rain_median']} / {EC['rain_q90']}</td><td class=num>{AI['rain_median']} / {AI['rain_q90']}</td></tr></table>
<div class="foot">Companion to "Hurricane Simon and Puerto Vallarta: models, verification and uncertainty" (final report, 12 October 2026). Code and data: hurricane-simon/trudy in branch claude/hourly-forecast-animation-m4v1bj of the vallarta-weather repository. Not an official forecast. Follow the SMN, the NHC and Protección Civil. Emergencies: 911.</div>
</body></html>"""
open(OUT, 'w').write(html); print('brief html', len(html))
