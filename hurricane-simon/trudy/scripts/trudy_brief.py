"""Build the EP93 (Trudy) Puerto Vallarta brief (HTML) from the analysis JSON files. Usage: trudy_brief.py SCRATCH OUT.html"""
import json, sys, math, datetime as dt
S, OUT = sys.argv[1:3]; T = S + '/trudy'; O = 'file://' + T + '/out'
M = json.load(open(T + '/models.json')); C = json.load(open(T + '/climo.json')); CH = json.load(open(T + '/chances.json')); SC = json.load(open(T + '/scenarios.json'))
SM = M['summary']; TR = M['tracks']; BL = CH['blend']; SP = CH['spread']
EC, AI, GE = SM['2026101212']['ecens'], SM['2026101212']['aiens'], SM['2026101212']['gefs']; A12, A18 = SM['2026101212']['aids'], SM['2026101218']['aids']
C5 = C['500']; n5 = C5['n']
def get(c, t): return next((r for r in TR if r['cycle'] == c and r['tech'] == t), None)
def comp(b): return ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'][int((b + 11.25) // 22.5) % 16]
def frac(p): return {0: 'none', 100: 'all'}.get(p, f'about 1 in {round(100 / p)}' if p and 100 / p >= 2.5 else f'{p}%')
def cat(v): return 'tropical storm' if v < 64 else 'category 1' if v < 83 else 'category 2' if v < 96 else 'category 3' if v < 113 else 'category 4' if v < 137 else 'category 5'
def lt(s): return s.replace(' 00:00', ' midnight').replace(' 12:00', ' noon')
def lfl(t): return lt((dt.datetime.strptime(t, '%Y-%m-%d %HZ') - dt.timedelta(hours=6)).strftime('%a %d %b %H:%M'))
def short(s): return s.replace(' Oct', '')
ec_close = [r for r in TR if r['cycle'] == '2026101212' and r['group'] == 'ecens' and r['cpa_km'] <= 300]
hrs = sorted(r['cpa_h'] for r in ec_close); c12 = dt.datetime(2026, 10, 12, 12)
def loc(h): return (c12 + dt.timedelta(hours=h - 6)).strftime('%A %d %H:%M').replace(' 00:00', ' midnight')
q25, med, q75 = hrs[len(hrs) // 4], hrs[len(hrs) // 2], hrs[3 * len(hrs) // 4]
import statistics as st
ec_v = round(st.median([r['cpa_v'] for r in ec_close])); ec_brg = sorted(r['cpa_brg'] for r in ec_close)
W = M['simon_err']; A, B, Cc = SC['A'], SC['B'], SC['C']
SITES = [('amapas', 'D Terrace, Amapas (8th floor, faces the bay)'), ('ezapata', 'Casa Francisca, Emiliano Zapata (3rd floor, sheltered)'), ('pitillal', 'El Pitillal house (street level, 160 m from the river)')]
g = get('2026101212', 'GDMN'); gi = get('2026101218', 'GDMI'); hc = get('2026101218', 'HCCA'); tv = get('2026101218', 'TVCN'); av = get('2026101212', 'AVNO')

def aid_rows(cycle, techs):
    out = []
    for t in techs:
        r = get(cycle, t)
        if not r: continue
        lf = f"{r['landfall']['region']}, {short(lfl(r['landfall']['t']))}, {r['landfall']['v']} kt" if r['landfall'] else '—'
        out.append(f"<tr><td>{r['name']}</td><td class=num>{r['cpa_km']}</td><td>{comp(r['cpa_brg'])}</td><td class=nw>{short(lt(r['cpa_local']))}</td><td class=num>{r['cpa_v'] or '—'}</td><td class=num>{r['peak_v'] or '—'}</td>"
                   f"<td class=num>{r['sites']['amapas']['kmh']}</td><td class=num>{r['sites']['ezapata']['kmh']}</td><td class=num>{r['sites']['pitillal']['kmh']}</td><td class=num>{r['rain_mm']}</td><td>{lf}</td></tr>")
    return '\n'.join(out)
rows12 = aid_rows('2026101212', ['GDMN', 'HCCA', 'TVCN', 'AVNO', 'UKX', 'CEMN', 'NVGM', 'AEMN', 'HFSA', 'HFSB', 'HWRF', 'HMON', 'CTCX', 'CLP5'])
rows18 = aid_rows('2026101218', ['GDMI', 'HCCA', 'TVCN', 'AVNI', 'UKXI', 'CEMI', 'NVGI', 'AEMI', 'HFAI', 'HFBI', 'HWFI', 'HMNI', 'CTCI', 'CLP5'])
wrows = '\n'.join(f"<tr><td>{get('2026101218', t)['name'] if get('2026101218', t) else t}</td><td class=num>{W.get({'GDMI': 'GDMN', 'AVNI': 'AVNO', 'UKXI': 'UKX', 'CEMI': 'CEMN', 'NVGI': 'NVGM', 'AEMI': 'AEMN', 'HFAI': 'HFSA', 'HFBI': 'HFSB', 'HWFI': 'HWRF', 'HMNI': 'HMON', 'CTCI': 'CTCX'}.get(t, t), '—')}</td><td class=num>{round(100 * w)}%</td></tr>"
                  for t, w in sorted(A18['weights'].items(), key=lambda x: -x[1]))
clim_rows = '\n'.join(f"<tr><td>{s['year']} {s['name'].title()}</td><td>{s['lat0']:.1f}N {-s['lon0']:.1f}W, {s['t0'][:10]}</td><td class=num>{s['cpa_km']}</td><td>{s['cpa_t'][:10]} (+{s['cpa_days']} d)</td><td class=num>{s['v_cpa'] or '—'}</td><td class=num>{s['vmax']}</td><td>{s['region']}</td></tr>" for s in C5['storms'][:8])
def scen_cell(s, k):
    x = s['sites'][k]; return f"<b>{x['kmh']}</b> km/h, gusts {x['gust_kmh']}<br><span class=small>{lt(x['t'])}, wind from the {comp(x['frm'])}</span>"
def win(s, k): w = s['windows'][k]; return f"{lt(w[0])} → {lt(w[1])}" if w else '—'
html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>EP93 (Trudy) and Puerto Vallarta: chances, path, impacts and timing</title>
<style>
__FONTS__
@page {{ size: Letter; margin: 17mm 16mm 18mm 16mm; }}
:root {{ --ink: #0b0b0b; --ink2: #3d3c39; --mute: #6b6a66; --line: #dcdad4; --accent: #1c5cab; --panel: #f3f2ee; --warn: #b3410f; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: #fff; color: var(--ink); font-family: "Red Hat Text", "DejaVu Sans", Arial, sans-serif; font-size: 10.2pt; line-height: 1.42; }}
h1, h2, h3, h4 {{ font-family: "Red Hat Display", "DejaVu Sans", Arial, sans-serif; line-height: 1.15; margin: 0; }}
h1 {{ font-size: 24pt; font-weight: 800; letter-spacing: -0.01em; }}
h2 {{ font-size: 15pt; font-weight: 800; margin: 16pt 0 6pt; padding-top: 6pt; border-top: 2px solid var(--ink); break-after: avoid; }}
h3 {{ font-size: 11.3pt; font-weight: 700; margin: 10pt 0 4pt; break-after: avoid; }}
p {{ margin: 0 0 6pt; }} ul, ol {{ margin: 0 0 6pt 16pt; padding: 0; }} li {{ margin: 0 0 3pt; }}
.kicker {{ font-family: "Red Hat Mono", monospace; color: var(--accent); font-size: 9pt; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 8pt; }}
.sub {{ font-size: 12.5pt; color: var(--ink2); margin: 8pt 0 10pt; line-height: 1.35; }}
.meta {{ font-family: "Red Hat Mono", monospace; font-size: 8.4pt; color: var(--mute); margin-bottom: 12pt; }}
.box {{ background: var(--panel); border-left: 4px solid var(--accent); padding: 8pt 11pt; margin: 8pt 0 10pt; break-inside: avoid; }}
.box.warn {{ border-left-color: var(--warn); }} .box h3 {{ margin-top: 0; }}
.small {{ font-size: 8.6pt; color: var(--mute); }}
figure {{ margin: 8pt 0 10pt; break-inside: avoid; }} figure img {{ display: block; width: 100%; height: auto; }}
figure.chart img {{ width: 90%; margin: 0 auto; }} figure.w80 img {{ width: 80%; margin: 0 auto; }}
figcaption {{ font-size: 8.6pt; color: var(--ink2); margin-top: 4pt; line-height: 1.35; }} figcaption b {{ color: var(--ink); }}
table {{ width: 100%; border-collapse: collapse; font-size: 8.6pt; margin: 6pt 0 10pt; }}
th, td {{ text-align: left; vertical-align: top; padding: 3.5pt 4.5pt; border-bottom: 1px solid var(--line); }}
th {{ font-weight: 700; font-size: 8.2pt; color: var(--ink2); border-bottom: 1.5px solid var(--ink); }}
td.num, th.num {{ text-align: right; font-family: "Red Hat Mono", monospace; white-space: nowrap; }}
tr {{ break-inside: avoid; }}
.tiles {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 7pt; margin: 8pt 0 10pt; break-inside: avoid; }}
.tile {{ background: var(--panel); border-radius: 6pt; padding: 8pt 9pt; }}
.tile .n {{ font-family: "Red Hat Display", sans-serif; font-size: 18pt; font-weight: 800; line-height: 1.1; }}
.tile .l {{ font-size: 8.2pt; color: var(--ink2); margin-top: 2pt; line-height: 1.3; }}
.pb {{ break-before: page; }}
.foot {{ font-size: 8.2pt; color: var(--mute); border-top: 1px solid var(--line); padding-top: 6pt; margin-top: 14pt; }}
table.scen td:first-child {{ font-weight: 700; width: 20%; }}
td.nw {{ white-space: nowrap; }} table.app {{ font-size: 8pt; }} table.app td, table.app th {{ padding: 3pt 3.5pt; }}
table.scen th {{ width: 26%; }}
</style></head><body>

<div class="kicker">Invest EP93 · the storm that will be Trudy · Puerto Vallarta</div>
<h1>Trudy before it exists: realistic chances for Puerto Vallarta, the path, and what it would mean at three addresses</h1>
<p class="sub">Analog climatology from 77 seasons, the Monday model runs (ECMWF, GFS, UKMET, the US hurricane models, Google DeepMind, the NHC consensus aids and three ensembles) weighted by what each did with Simon, and the resulting most-likely case, worst case and timing for D Terrace in Amapas, Casa Francisca in Emiliano Zapata and the house in El Pitillal.</p>
<p class="meta">Monday 12 October 2026, 7 pm Vallarta time (13 Oct 01Z) · model runs of Monday 12Z and 18Z · NHC outlook of 5 pm PDT · no NHC advisory exists yet for EP93 · not an official forecast</p>

<div class="box warn"><h3>Bottom line</h3>
<ul>
<li><b>It will form.</b> The NHC gives EP93 a near-100% chance of becoming a depression or tropical storm tonight or Tuesday, several hundred miles south-southwest of Guatemala. It will take the name Trudy. Every model that strengthens it makes it a hurricane by Thursday and most make it a major hurricane by Friday or Saturday.</li>
<li><b>Realistic chance for Vallarta, six days out.</b> Averaging six independent sources (three ensembles, the deterministic and AI tracks equal-weighted and Simon-weighted, and the 77-year climatology): <b>{BL['300']}%</b> that the center comes within 300 km (rain bands, swell, some wind), <b>{BL['200']}%</b> within 200 km, <b>{BL['100']}%</b> within 100 km (a direct hit or near miss), and <b>{BL['pv34']}%</b> for tropical-storm wind in the city. The sources disagree widely ({SP['300'][0]}–{SP['300'][1]}% for 300 km): the GFS family sends it far out to sea, the ECMWF ensemble, Google DeepMind and the NHC consensus aids send it toward Jalisco.</li>
<li><b>When.</b> If it comes, the window is <b>Saturday night 17 October to Monday 19 October</b>. Among the ECMWF members that pass within 300 km, the closest approach is at {loc(med)} on the median, with half of them between {loc(q25)} and {loc(q75)}. Swell on the coast from Friday; rain bands from Saturday night.</li>
<li><b>Most likely case:</b> the center passes 250 km or more to the southwest, or weakens before arriving. Swell of several metres on the open coast, showers and a rain band or two, gusts to 50 km/h at the exposed Amapas terrace, nothing damaging. <b>Worst case</b> (the 18Z corrected consensus): a category-4 landfall at Manzanillo before dawn Sunday, then north across Jalisco with the center 75 km east of the bay Sunday afternoon: {Cc['sites']['amapas']['kmh']} km/h sustained and gusts to {Cc['sites']['amapas']['gust_kmh']} on the Amapas terrace, {Cc['rain_mm']} mm of rain before the mountains add theirs, the Pitillal and Cuale rivers in flood. That is a 1-in-10 to 1-in-5 outcome today, not the forecast.</li>
<li><b>What to do now:</b> nothing physical. Note Thursday noon: 72 hours before the window, by which time the ensembles should have chosen a side and the NHC's day-3 line (typical error about 150 km) is worth acting on. Watch for NHC advisory 1 tonight or Tuesday, which will carry the first wind-speed probabilities for Puerto Vallarta; those replace every number in this document.</li>
</ul></div>

<div class="tiles">
<div class="tile"><div class="n">{BL['300']}%</div><div class="l">center within 300 km (six-source average; sources span {SP['300'][0]}–{SP['300'][1]}%)</div></div>
<div class="tile"><div class="n">{BL['100']}%</div><div class="l">center within 100 km (sources span {SP['100'][0]}–{SP['100'][1]}%)</div></div>
<div class="tile"><div class="n">{BL['pv34']}%</div><div class="l">tropical-storm wind in the city, 63 km/h or more (sources span {SP['pv34'][0]}–{SP['pv34'][1]}%)</div></div>
<div class="tile"><div class="n">Sun 18</div><div class="l">most likely day of closest approach, if it comes; window Sat night to Mon</div></div>
</div>

<h2>1. Where EP93 is and what the NHC says</h2>
<p>At 6 pm Monday the disturbance was a broad low near 8.1N 93.9W, roughly 1,900 km southeast of Puerto Vallarta, with 25-kt winds and a pressure of 1008 mb, moving west-northwest at about 10 mph. The 5 pm PDT outlook: "Showers and thunderstorms are beginning to show signs of organization in association with a broad area of low pressure located several hundred miles south-southwest of the coast of Guatemala. This system is gradually becoming better defined, and environmental conditions are forecast to be conducive for further development. A tropical depression or tropical storm is expected to form well south of southern Mexico later tonight or tomorrow." Formation chance through 48 hours and 7 days: near 100 percent.</p>
<p>It is unusually far south and east for a mid-October storm, over warm water, and every track model takes it west-northwest for two to three days before the question of a turn north arises. The ECMWF tracks it as disturbance 71E in its own track files, which is what let the two ECMWF ensembles be read here.</p>

<h2>2. What Simon taught us, applied</h2>
<ul>
<li><b>Which models to trust.</b> Over the two days before Simon's pass, the best position forecasts came from Google DeepMind's cyclone model (mean 12–36 h error 33 km), the NHC corrected consensus HCCA (38 km) and the NHC official line (47 km); the track consensus TVCN scored 51, the Canadian ensemble mean 69, the GFS 67, HWRF 68, UKMET 83, HMON 99, HAFS-A 117, COAMPS-TC 129 and HAFS-B 169. Those scores are the weights in the "Simon-weighted" line below (inverse square of the error), so DeepMind and HCCA together carry about {round(100 * (A18['weights'].get('GDMI', 0) + A18['weights'].get('HCCA', 0)))}% of that estimate. They were earned at 12–36 h on a slow, stalling storm; nothing guarantees they hold at five and six days.</li>
<li><b>Day-5 and day-6 forecasts move.</b> The NHC's own average track error in recent seasons is about 250–300 km at five days and more at six. A line that passes 75 km west of the bay today is, in practice, "somewhere between a landfall on the bay and a 400-km miss". That is why this brief gives chances, not a track.</li>
<li><b>Center winds are not Vallarta's winds.</b> Simon reached category 4 and passed 120 km away; the airport recorded 7 km/h and under 10 mm of rain. The building numbers below are the parametric wind of each model track at each address, with that model's own wind radii where its deck carries them and climatological radii otherwise, multiplied by the same exposure factors as the Simon graphics (1.08 for the Amapas terrace when the wind comes off the bay, 0.89 otherwise; 0.77 for the sheltered mid floor; 0.70 for the street-level house). They say "if the center followed that line"; they are not probabilities. Once the NHC issues advisories, its wind-speed probabilities for Puerto Vallarta are the number to use, as they were for Simon.</li>
<li><b>Small storms and big ones.</b> Simon's gale radii never exceeded 40 nautical miles, which is why a 120-km pass produced nothing. The climatological radii used for the consensus aids here are two to three times larger. If Trudy is compact, the same track gives much less wind in the city; if it is large, more.</li>
<li><b>The split is the forecast.</b> Simon's discussion 22 described a bifurcation between competing ridges; EP93 has its own. The GFS and its ensemble keep it weaker and on a westward heading; the ECMWF, DeepMind and the consensus aids make it a major hurricane that turns north toward Jalisco from Friday. Deeper storms are steered by deeper, more northward flow, so intensity and track are one question here. The ensembles should separate by Thursday.</li>
</ul>

<h2>3. Climatology: storms that were where EP93 is, in this season</h2>
<p>HURDAT2 for the eastern North Pacific, 1949–2025. Of the {n5} storms that passed within 500 km of EP93's position between 12 September and 11 November, {C5['within']['300']} came within 300 km of Puerto Vallarta, {C5['within']['200']} within 200 km and {C5['within']['100']} within 100 km (Priscilla, 1971: 82 km at 70 kt, five and a half days after its analog point). {C5['hurricane']} of the {n5} became hurricanes and {C5['major']} became major hurricanes. The closest passes to Vallarta came {min(C5['days_to_cpa_within300'])}–{sorted(C5['days_to_cpa_within300'])[-2]} days after the analog point, which from Monday evening means Thursday to Sunday; the models are slower than climatology because they keep EP93 on a long westward leg first. Most analogs ended in Central America or Oaxaca ({C5['regions'].get('Central America / Chiapas', 0) + C5['regions'].get('Oaxaca', 0)}), Michoacán–Colima ({C5['regions'].get('Michoacán / Colima', 0)}) or Sinaloa ({C5['regions'].get('Sinaloa', 0)}). Tightening the analog circle to 300 km leaves 8 storms, none of which came within 300 km of Vallarta (Roslyn 1986 came closest at 302 km).</p>
<figure class="w80"><img src="{O}/t2_analogs.png" alt="Analog tracks"><figcaption><b>Figure 1.</b> The {n5} analog storms (grey) and the six that came within 300 km of Vallarta.</figcaption></figure>
<table><tr><th>Storm</th><th>Analog point</th><th class=num>Closest, km</th><th>When</th><th class=num>kt then</th><th class=num>Peak kt</th><th>Region of closest pass</th></tr>
{clim_rows}</table>

<h2 class="pb">4. The models: where they take it</h2>
<figure><img src="{O}/t1_tracks.png" alt="Track map"><figcaption><b>Figure 2.</b> Every track aid of the Monday 12Z cycle, the 18Z early versions of DeepMind and the consensus aids (dotted), and the three ensembles. Google DeepMind (12Z) passes {g['cpa_km']} km {comp(g['cpa_brg'])} of the city at {lt(g['cpa_local'])} as a {cat(g['cpa_v'])} hurricane ({g['cpa_v']} kt, after a {g['peak_v']}-kt peak); its 18Z version passes {gi['cpa_km']} km {comp(gi['cpa_brg'])} at {lt(gi['cpa_local'])}. The 18Z corrected consensus makes landfall at Manzanillo at {lt(lfl(hc['landfall']['t']))} ({hc['landfall']['v']} kt) and crosses Jalisco; the 18Z track consensus passes {tv['cpa_km']} km {comp(tv['cpa_brg'])}. The GFS passes {av['cpa_km']} km to the {comp(av['cpa_brg'])}.</figcaption></figure>
<p><b>Three ensembles, three answers.</b> The GEFS (31 members, 12Z) has {GE['within']['300']}% of members within 300 km of Vallarta and a median closest pass of {GE['cpa_median']} km; it keeps EP93 weak (median peak {GE['peak_median']} kt). The ECMWF ensemble (51 members, 12Z) has {EC['within']['300']}% within 300 km, {EC['within']['200']}% within 200 km and {EC['within']['100']}% within 100 km, with {EC['landfall'].get('Jalisco (Bahía de Banderas)', 0)} members making landfall on Bahía de Banderas itself, {EC['landfall'].get('Michoacán / Colima', 0)} in Michoacán–Colima and {EC['landfall'].get('Sinaloa', 0)} in Sinaloa; its median peak is {EC['peak_median']} kt, a major hurricane, but by the time the close members reach the bay most have weakened (median {ec_v} kt at closest approach), which is why only {EC['pv34']}% of members give tropical-storm wind in the city. The ECMWF AIFS ensemble (AI, 51 members) is the most Vallarta-leaning on track ({AI['within']['300']}% within 300 km, {AI['within']['100']}% within 100 km) and the weakest on intensity (median peak {AI['peak_median']} kt), the same under-forecasting the gridded AI models showed throughout Simon.</p>
<p><b>The deterministic and AI aids</b> of the 12Z cycle (late versions) and 18Z cycle (early versions, the ones the NHC forecaster sees) are tabulated in the appendix. Bearings of the close ECMWF passes cluster between south-southwest and west ({comp(ec_brg[len(ec_brg)//4])} to {comp(ec_brg[3*len(ec_brg)//4])}): the storm passes offshore and turns north, with the city on its right-hand, onshore-wind side. That geometry puts the Amapas terrace, which faces the bay, on the exposed side.</p>
<figure><img src="{O}/t4_intensity.png" alt="Intensity"><figcaption><b>Figure 3.</b> Intensity. DeepMind peaks at {g['peak_v']} kt on {lt(lfl(g['peak_t']))}, the 18Z corrected consensus at {hc['peak_v']} kt, the GFS at {av['peak_v']} kt; the ECMWF members (blue) span tropical storm to category 4; the GEFS (grey) and AIFS (lilac) stay mostly below hurricane strength.</figcaption></figure>

<h2>5. The chances, source by source</h2>
<figure><img src="{O}/t3_chances.png" alt="Chances"><figcaption><b>Figure 4.</b> Share of members, tracks or analog storms that bring the center within 100, 200 and 300 km of Puerto Vallarta, and that give tropical-storm wind in the city. The last row is the plain average of the six sources.</figcaption></figure>
<p>The honest statement is the spread, not the average. The GFS-based sources sit at 0–6%, the European and AI sources at 50–70%, climatology at 26%. The Simon-weighted line is the highest because it concentrates on the two aids that were best for Simon and that happen to be the two closest to Vallarta today; it is one reading, not a verdict. On an ordinary bifurcated six-day forecast, an outcome that half the credible guidance gives and half denies deserves something near one in three, and that is where the 300-km average lands. For the three outcomes that matter to a resident:</p>
<table><tr><th>Outcome</th><th class=num>Six-source average</th><th class=num>Lowest source</th><th class=num>Highest source</th><th>Read it as</th></tr>
<tr><td>Center within 300 km: swell, rain bands, gusty showers, a day or two of disruption</td><td class=num>{BL['300']}%</td><td class=num>{SP['300'][0]}%</td><td class=num>{SP['300'][1]}%</td><td>{frac(BL['300'])}</td></tr>
<tr><td>Center within 200 km: tropical-storm conditions possible on the exposed shore, heavy rain likely</td><td class=num>{BL['200']}%</td><td class=num>{SP['200'][0]}%</td><td class=num>{SP['200'][1]}%</td><td>{frac(BL['200'])}</td></tr>
<tr><td>Center within 100 km: the hurricane itself is a possibility for the bay</td><td class=num>{BL['100']}%</td><td class=num>{SP['100'][0]}%</td><td class=num>{SP['100'][1]}%</td><td>{frac(BL['100'])}</td></tr>
<tr><td>Tropical-storm wind (≥ 63 km/h sustained) in the city</td><td class=num>{BL['pv34']}%</td><td class=num>{SP['pv34'][0]}%</td><td class=num>{SP['pv34'][1]}%</td><td>{frac(BL['pv34'])}</td></tr>
<tr><td>Hurricane wind (≥ 119 km/h sustained) in the city</td><td class=num>&lt; 5%</td><td class=num>0%</td><td class=num>0%</td><td>no track or member gives it today; the worst case below comes close only on the exposed terrace</td></tr></table>

<h2 class="pb">6. The three addresses: most likely, close pass, worst case</h2>
<p>Each scenario is one real model track, run through the same parametric wind field and exposure factors as the Simon graphics, with an R-CLIPER-type rain estimate along the track (no terrain enhancement; the Sierra behind the city can double the total on the slopes). Scenario A is the ECMWF member nearest the ensemble's median closest pass; B is Google DeepMind's 18Z line; C is the NHC corrected consensus 18Z line, the worst coherent case any credible aid gives today. Times are Vallarta time.</p>
<table class="scen">
<tr><th></th><th>A · Most likely<br><span class=small>passes {A['cpa_km']} km to the {comp(get('2026101212','EE50')['cpa_brg'])} at {lt(A['cpa_local'])} as a {cat(A['cpa_v'])} ({A['cpa_v']} kt); about half of all sources</span></th>
<th>B · Close pass to the west<br><span class=small>center {B['cpa_km']} km {comp(gi['cpa_brg'])} at {lt(B['cpa_local'])}, {cat(B['cpa_v'])} ({B['cpa_v']} kt) after a {B['peak_v']}-kt peak; roughly 1 in 5 of ECMWF members, DeepMind's own line</span></th>
<th>C · Worst case<br><span class=small>category-4 landfall at Manzanillo {lt(lfl(Cc['landfall']['t']))} ({Cc['landfall']['v']} kt), center {Cc['cpa_km']} km {comp(hc['cpa_brg'])} of the bay at {lt(Cc['cpa_local'])}; roughly 1 in 10</span></th></tr>
<tr><td>Swell on the coast</td><td>{win(A,'swell')}</td><td>{win(B,'swell')}</td><td>{win(Cc,'swell')}</td></tr>
<tr><td>Rain bands over the bay</td><td>{win(A,'bands')}</td><td>{win(B,'bands')}</td><td>{win(Cc,'bands')}</td></tr>
<tr><td>Tropical-storm wind in the city</td><td>{win(A,'ts')}</td><td>{win(B,'ts')}</td><td>{win(Cc,'ts')}</td></tr>
<tr><td>Rain, storm total (city, before terrain)</td><td>{A['rain_mm']} mm</td><td>{B['rain_mm']} mm</td><td>{Cc['rain_mm']} mm</td></tr>
<tr><td>D Terrace, Amapas, 8th floor</td><td>{scen_cell(A,'amapas')}</td><td>{scen_cell(B,'amapas')}</td><td>{scen_cell(Cc,'amapas')}</td></tr>
<tr><td>Casa Francisca, Emiliano Zapata, 3rd floor</td><td>{scen_cell(A,'ezapata')}</td><td>{scen_cell(B,'ezapata')}</td><td>{scen_cell(Cc,'ezapata')}</td></tr>
<tr><td>El Pitillal house, street level</td><td>{scen_cell(A,'pitillal')}</td><td>{scen_cell(B,'pitillal')}</td><td>{scen_cell(Cc,'pitillal')}</td></tr>
<tr><td>What it means</td><td>A windy, wet Sunday night. Big surf on the south shore and the Malecón; secure balcony items at Amapas as a courtesy, nothing more. Pitillal: puddles, not flood.</td><td>Tropical-storm conditions for most of Sunday. Amapas: wind off the bay at the terrace, salt spray, loose items become projectiles; stay off the balcony. Casa Francisca: sheltered by the hill and the buildings, gusts to {B['sites']['ezapata']['gust_kmh']}, flickering power. Pitillal: {B['rain_mm']} mm or more on the Pitillal basin puts the river up and the low streets under water; move the car before Saturday night.</td><td>Near-hurricane gusts at the terrace from Sunday morning through the night; a day and a half of tropical-storm wind; power and water out for days in parts of the city; {Cc['rain_mm']} mm plus terrain on the Cuale and Pitillal catchments, both rivers in flood, landslides on the Amapas and Conchas Chinas slopes. Pitillal: leave for higher ground on Saturday. This is the case the Hurricane Watch, if one comes on Friday, would be about.</td></tr></table>
<figure><img src="{O}/t5_timeline.png" alt="Timeline"><figcaption><b>Figure 5.</b> The three scenarios in time. The triangle is the closest approach of the center.</figcaption></figure>

<h2>7. When we will know</h2>
<ul>
<li><b>Tonight or Tuesday:</b> NHC advisory 1 on Tropical Depression / Tropical Storm Trudy, with the first official five-day line and wind-speed probabilities. If Puerto Vallarta appears in the 34-kt probability table at all (the threshold is 3%), the Jalisco-leaning scenario is alive in the official forecast.</li>
<li><b>Tuesday 00Z and 12Z runs (available Tuesday morning and evening):</b> the first ECMWF and GEFS ensembles that start from a defined center. Watch whether the GEFS moves toward the ECMWF or the reverse.</li>
<li><b>Thursday noon, about 72 hours out:</b> the decision point. At three days the NHC's average error is about 150 km. If the official line then runs within 150 km of the bay, prepare for scenario B or C; if it runs 400 km or more to the southwest, plan for swell and rain only. Simon's lesson is that even inside 24 hours the line can still shift 100 km; the probabilities, not the line, are what to read.</li>
<li><b>Friday:</b> the SMN and the NHC would issue a Hurricane Watch for the Jalisco coast about 48 hours before hurricane conditions, if scenario B or C is on the table.</li>
</ul>

<h2>8. Simon, meanwhile</h2>
<p>NHC advisory 22A (Monday 6 pm Vallarta time): Simon is a category-2 hurricane with 85-kt winds about 125 km west of Cabo Corrientes, drifting west-northwest at 6 km/h. It is forecast to move slowly away from the bay, then turn northeast and reach the Sinaloa coast as a weakening hurricane around Thursday night or Friday. A Hurricane Warning is in effect for the Islas Marías and a Hurricane Watch from Cabo Corrientes to Bahía Tempehuaya. Puerto Vallarta's wind probabilities are below the 3% display threshold; Mazatlán's 34-kt cumulative probability is 54%. Simon will be inland over Sinaloa, and gone, before Trudy's window opens; the swell it leaves on the Jalisco coast (4–5 m per SMN aviso 40) will have eased by Wednesday, before Trudy's own swell arrives.</p>

<h2>9. Method, sources and caveats</h2>
<ul>
<li><b>Tracks:</b> NHC ATCF a-deck for EP93 (aep932026.dat), cycles 2026101212 (late versions) and 2026101218 (early versions), including the 31 GEFS members; best track bep932026.dat. ECMWF open data, 2026-10-12 12Z, tropical-cyclone track BUFR files for the IFS ensemble and the AIFS ensemble, disturbance 71E, decoded with ecCodes; wind in those files is the model's own 10-m wind, which runs low. Every track was interpolated hourly; closest approach and timing are to 20.61N 105.23W; landfall is the first hour over land in the Natural Earth 50 m land polygons.</li>
<li><b>Wind at the addresses:</b> the parametric wind field of the Simon map page (simon_phys.py) with the model's own 34/50/64-kt radii where present (GEFS, GFS, HAFS, HWRF, HMON, COAMPS, DeepMind 12Z, NAVGEM, UKMET) and climatological radii otherwise (consensus aids, DeepMind 18Z, ECMWF members); exposure factors as in the Simon graphics. No land-decay was applied to model intensities, so the worst-case winds are upper bounds.</li>
<li><b>Rain:</b> R-CLIPER-type profile (Tuleya et al. 2007) integrated hourly at the city; no terrain enhancement.</li>
<li><b>Climatology:</b> HURDAT2 NE Pacific 1949–2025, storms with any 6-hourly fix within 500 km (and 300 km) of 8.1N 93.9W between 12 September and 11 November.</li>
<li><b>Weights:</b> inverse square of each model's mean 12–36 h position error over the last 48 h of Simon's approach (final report, Figure 2); early 18Z versions inherit the late model's score. Weights used: see appendix.</li>
<li><b>Not included:</b> the ECMWF deterministic IFS and AIFS single runs (no track file for EP93 was published for the 12Z cycle); the 00Z Tuesday runs; any NHC advisory, because none exists. This document should be rerun when advisory 1 and the Tuesday ensembles are out.</li>
</ul>

<h2 class="pb">Appendix. Every aid, and the weights</h2>
<h3>A1. Monday 12Z cycle, late versions</h3>
<table class="app"><tr><th>Aid</th><th class=num>Closest, km</th><th>Side</th><th>When (local)</th><th class=num>kt then</th><th class=num>Peak kt</th><th class=num>Amapas km/h</th><th class=num>E. Zapata</th><th class=num>Pitillal</th><th class=num>Rain mm</th><th>Landfall</th></tr>
{rows12}</table>
<h3>A2. Monday 18Z cycle, early versions (what the NHC forecaster sees)</h3>
<table class="app"><tr><th>Aid</th><th class=num>Closest, km</th><th>Side</th><th>When (local)</th><th class=num>kt then</th><th class=num>Peak kt</th><th class=num>Amapas km/h</th><th class=num>E. Zapata</th><th class=num>Pitillal</th><th class=num>Rain mm</th><th>Landfall</th></tr>
{rows18}</table>
<p class="small">Consensus aids carry no intensity (TVCN, CLP5) or no radii (HCCA); their building winds use climatological radii. "kt then" is the model's intensity at closest approach.</p>
<div style="width:55%"><h3>A3. Simon-skill weights (18Z aids)</h3><table><tr><th>Aid</th><th class=num>Simon 12–36 h error, km</th><th class=num>Weight</th></tr>{wrows}</table></div>
<div><h3>A4. Ensemble summaries (12Z)</h3><table class="app"><tr><th></th><th class=num>GEFS</th><th class=num>ECMWF</th><th class=num>AIFS</th></tr>
<tr><td>Members</td><td class=num>{GE['n']}</td><td class=num>{EC['n']}</td><td class=num>{AI['n']}</td></tr>
<tr><td>Within 100 / 200 / 300 km</td><td class=num>{GE['within']['100']} / {GE['within']['200']} / {GE['within']['300']}%</td><td class=num>{EC['within']['100']} / {EC['within']['200']} / {EC['within']['300']}%</td><td class=num>{AI['within']['100']} / {AI['within']['200']} / {AI['within']['300']}%</td></tr>
<tr><td>Median closest pass, km</td><td class=num>{GE['cpa_median']}</td><td class=num>{EC['cpa_median']}</td><td class=num>{AI['cpa_median']}</td></tr>
<tr><td>Median peak intensity, kt</td><td class=num>{GE['peak_median']}</td><td class=num>{EC['peak_median']}</td><td class=num>{AI['peak_median']}</td></tr>
<tr><td>Tropical-storm wind in the city</td><td class=num>{GE['pv34']}%</td><td class=num>{EC['pv34']}%</td><td class=num>{AI['pv34']}%</td></tr>
<tr><td>Landfall on Bahía de Banderas</td><td class=num>{GE['landfall'].get('Jalisco (Bahía de Banderas)', 0)}</td><td class=num>{EC['landfall'].get('Jalisco (Bahía de Banderas)', 0)}</td><td class=num>{AI['landfall'].get('Jalisco (Bahía de Banderas)', 0)}</td></tr>
<tr><td>Landfall Michoacán–Colima / Nayarit / Sinaloa</td><td class=num>{GE['landfall'].get('Michoacán / Colima', 0)} / {GE['landfall'].get('Nayarit', 0)} / {GE['landfall'].get('Sinaloa', 0)}</td><td class=num>{EC['landfall'].get('Michoacán / Colima', 0)} / {EC['landfall'].get('Nayarit', 0)} / {EC['landfall'].get('Sinaloa', 0)}</td><td class=num>{AI['landfall'].get('Michoacán / Colima', 0)} / {AI['landfall'].get('Nayarit', 0)} / {AI['landfall'].get('Sinaloa', 0)}</td></tr>
<tr><td>No landfall within the run</td><td class=num>{GE['no_landfall']}</td><td class=num>{EC['no_landfall']}</td><td class=num>{AI['no_landfall']}</td></tr>
<tr><td>Median city rain, mm (all / 90th pct)</td><td class=num>{GE['rain_median']} / {GE['rain_q90']}</td><td class=num>{EC['rain_median']} / {EC['rain_q90']}</td><td class=num>{AI['rain_median']} / {AI['rain_q90']}</td></tr></table></div>
<div class="foot">Companion to "Hurricane Simon and Puerto Vallarta: models, verification and uncertainty" (final report, 12 October 2026). Code and data: hurricane-simon/trudy in branch claude/hourly-forecast-animation-m4v1bj of the vallarta-weather repository. Not an official forecast. Follow the SMN, the NHC and Protección Civil. Emergencies: 911.</div>
</body></html>"""
open(OUT, 'w').write(html); print('brief html', len(html))
