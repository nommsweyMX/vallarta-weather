"""Charts for the EP93 (Trudy) Puerto Vallarta brief, built around the five best Simon performers. Usage: trudy_charts.py SCRATCH"""
import json, sys, math, datetime as dt
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Polygon as MPoly, Patch
from matplotlib.lines import Line2D
from shapely.geometry import shape, box
S = sys.argv[1]; T = S + '/trudy'; O = T + '/out'
D = json.load(open(T + '/models.json')); C = json.load(open(T + '/climo.json'))
INK, INK2, MUTE, GRID, SURF = '#0b0b0b', '#52514e', '#7a7975', '#e6e4df', '#fcfcfb'
P = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': GRID, 'axes.linewidth': 1, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2, 'text.color': INK,
                 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'legend.frameon': False})
PV = (20.61, -105.2345); TZ = -6
def tidy(ax): ax.grid(True, axis='y', color=GRID, linewidth=1); ax.set_axisbelow(True); ax.tick_params(length=0)
def cyc(s): return dt.datetime.strptime(s, '%Y%m%d%H')
def local(c, h): return cyc(c) + dt.timedelta(hours=h + TZ)
TR = D['tracks']; SM = D['summary']
CYS = sorted(c for c in SM if 'top5' in SM[c] and not SM[c]['top5']['carried']); LATEST, PREV = CYS[-1], CYS[-2]
T5 = SM[LATEST]['top5']; T5B = SM[LATEST]['top5b']; T5P = SM[PREV]['top5']
ENSC = {g: max(c for c in SM if g in SM[c]) for g in ('gefs', 'ecens', 'aiens')}
def hz(c): return c[-2:] + 'Z'
BT = []
for line in open(T + '/bdeck_latest.dat'):
    f = [x.strip() for x in line.split(',')]
    if len(f) > 8 and f[4] == 'BEST': BT.append((f[2], int(f[6][:-1]) / 10, -int(f[7][:-1]) / 10))
def get(cycle, tech): return next((r for r in TR if r['cycle'] == cycle and r['tech'] == tech), None)
FIVE = [(m, get(m['cycle'], m['tech'])) for m in T5['members']]; FIVEP = [(m, get(m['cycle'], m['tech'])) for m in T5P['members']]
BASE = {'GDMI': 'GDMN', 'GDM2': 'GDMN', 'CEMI': 'CEMN', 'CEM2': 'CEMN', 'AEMI': 'AEMN', 'AEM2': 'AEMN', 'AIFI': 'AIFS'}
F5STYLE = {'GDMN': ('Google DeepMind cyclone model', P[6], '-'), 'AIFS': ('ECMWF AIFS (AI)', '#d6336c', '-'), 'TVCN': ('Track consensus TVCN', INK, '-'),
           'CEMN': ('Canadian ensemble mean', '#1f7a3a', '-'), 'AEMN': ('GEFS ensemble mean', '#4a7fb5', '-')}
def style(tech): return F5STYLE[BASE.get(tech, tech)]
land = [shape(f['geometry']) for f in json.load(open(T + '/ne/ne_50m_land.geojson'))['features']]
def draw_land(ax, ext):
    bx = box(*ext)
    for g in land:
        gi = g.intersection(bx)
        if gi.is_empty: continue
        for p in ([gi] if gi.geom_type == 'Polygon' else list(gi.geoms) if gi.geom_type == 'MultiPolygon' else []):
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, facecolor='#efece4', edgecolor='#b8b4a9', linewidth=0.6, zorder=1))
def ring(ax, la, lo, km, **kw):
    pts = [(lo + km / (111.32 * math.cos(math.radians(la))) * math.cos(a), la + km / 110.57 * math.sin(a)) for a in [i * math.pi / 90 for i in range(181)]]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], **kw)
def places(ax, small=False):
    for name, la, lo, dx, dy in [('Puerto Vallarta', 20.61, -105.23, 0.25, 0.1), ('Cabo Corrientes', 20.40, -105.69, -0.2, -0.55), ('Islas Marías', 21.6, -106.5, -2.6, 0.1), ('Manzanillo', 19.05, -104.33, 0.2, -0.45),
                                 ('Acapulco', 16.85, -99.9, 0.2, -0.5), ('Mazatlán', 23.2, -106.4, 0.25, 0.05), ('Cabo San Lucas', 22.9, -109.9, -4.4, -0.5), ('Salina Cruz', 16.17, -95.2, 0.2, -0.5), ('Guatemala', 14.6, -90.5, 0.2, 0.2)]:
        if name == 'Puerto Vallarta': ax.plot(lo, la, '*', color=INK, markersize=11, zorder=6, markeredgecolor=SURF)
        else: ax.plot(lo, la, 'o', color=INK2, markersize=2.5, zorder=5)
        ax.text(lo + dx, la + dy, name, fontsize=6.3 if small else 7, color=INK2, zorder=6, fontweight='bold' if name == 'Puerto Vallarta' else 'normal')
def xy(r): return [p[2] for p in r['track']], [p[1] for p in r['track']]

# ---------- F1: track map, the five highlighted ----------
EXT = (-113.5, 3.5, -86.5, 27.5)
fig, ax = plt.subplots(figsize=(8.4, 7.1))
draw_land(ax, EXT); ax.set_xlim(EXT[0], EXT[2]); ax.set_ylim(EXT[1], EXT[3]); ax.set_aspect(1 / math.cos(math.radians(16)))
for km, lab, ang in ((100, '100 km', 40), (200, '200 km', 25), (300, '300 km', 12)):
    ring(ax, *PV, km, color=INK2, linewidth=0.7, linestyle=(0, (2, 2)), zorder=4)
    a = math.radians(ang); ax.text(PV[1] + km / (111.32 * math.cos(math.radians(PV[0]))) * math.cos(a), PV[0] + km / 110.57 * math.sin(a), lab, fontsize=6, color=INK2, ha='center', va='center', zorder=6, bbox=dict(facecolor=SURF, edgecolor='none', pad=0.6))
for grp, col, lw, al in (('gefs', '#9a9a9a', 0.45, 0.45), ('aiens', '#c9a9e8', 0.45, 0.5), ('ecens', '#86b8ee', 0.5, 0.6)):
    for r in TR:
        if r['cycle'] == ENSC[grp] and r['group'] == grp: ax.plot(*xy(r), color=col, linewidth=lw, alpha=al, zorder=2)
five_base = {BASE.get(m['tech'], m['tech']) for m, _ in FIVE}
OTHER = ['AVNO', 'UKXI', 'NVGM', 'HFSA', 'HFSB', 'HWRF', 'HMON', 'CTCX', 'HCCA']
for t in OTHER:
    r = get(PREV, t)
    if r: ax.plot(*xy(r), color='#a9a7a1', linewidth=1.0, zorder=3)
ec = get('2026101212', 'ECMO'); ax.plot(*xy(ec), color='#5c5a55', linewidth=1.4, linestyle=(0, (1, 1.5)), zorder=3)
for m, r in FIVEP:
    lab, col, ls = style(m['tech']); ax.plot(*xy(r), color=col, linewidth=1.1, linestyle=(0, (2, 1.5)), zorder=4, alpha=0.9)
for m, r in FIVE:
    lab, col, ls = style(m['tech']); ax.plot(*xy(r), color=col, linewidth=2.6, linestyle=ls, zorder=5, solid_capstyle='round')
for c, la, lo in BT[-3:]:
    ax.plot(lo, la, 'o', color=INK, markersize=3.5, zorder=7, markeredgecolor=SURF)
r = get(LATEST, 'GDMI')
for h, lab in ((36, 'Wed'), (84, 'Fri'), (132, 'Sun')):
    p = next((p for p in r['track'] if p[0] == h), None)
    if p: ax.plot(p[2], p[1], 'o', color=P[6], markersize=5, markeredgecolor=SURF, zorder=6); ax.text(p[2] + 0.3, p[1] + 0.25, lab + ' 6 am', fontsize=6.5, color=P[6], zorder=6, bbox=dict(facecolor=SURF, edgecolor='none', pad=0.5, alpha=0.85))
places(ax); c, la, lo = BT[-1]; ax.plot(lo, la, 'o', color=INK, markersize=6, zorder=7, markeredgecolor=SURF); ax.text(lo - 1.0, la - 1.6, 'EP93 center, Mon 6 pm\n(small dots: noon and 6 am fixes)', fontsize=6.6, color=INK)
handles = [Line2D([], [], color=style(m['tech'])[1], linewidth=2.6, label=style(m['tech'])[0]) for m, _ in FIVE]
handles += [Line2D([], [], color=INK, linewidth=2.6, label=f'Thick: {hz(LATEST)} early versions (shifted to the 6 pm center)'), Line2D([], [], color=INK, linewidth=1.1, linestyle=(0, (2, 1.5)), label=f'Thin dashed: the same five, {hz(PREV)} runs'),
            Line2D([], [], color='#5c5a55', linewidth=1.4, linestyle=(0, (1, 1.5)), label='ECMWF IFS, not in the five (12Z)'), Line2D([], [], color='#a9a7a1', linewidth=1.0, label=f'Other aids: GFS, UKMET, NAVGEM, HAFS-A/B, HWRF, HMON, COAMPS, NHC consensus ({hz(PREV)})'),
            Line2D([], [], color='#86b8ee', linewidth=1.2, label=f"ECMWF ensemble, {SM[ENSC['ecens']]['ecens']['n']} members ({hz(ENSC['ecens'])})"), Line2D([], [], color='#c9a9e8', linewidth=1.2, label=f"ECMWF AIFS ensemble, {SM[ENSC['aiens']]['aiens']['n']} members ({hz(ENSC['aiens'])})"),
            Line2D([], [], color='#9a9a9a', linewidth=1.2, label=f"GEFS, {SM[ENSC['gefs']]['gefs']['n']} members ({hz(ENSC['gefs'])})")]
ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.0, -0.06), ncol=2, fontsize=6.6, handlelength=2.4, borderaxespad=0)
ax.set_title('EP93 (future Trudy): the five best Simon models, before and after the 6 pm re-fix', loc='left', fontsize=10, fontweight='bold')
ax.set_xticks(range(-112, -86, 4)); ax.set_xticklabels([f'{-x}°W' for x in range(-112, -86, 4)], fontsize=7); ax.set_yticks(range(4, 28, 4)); ax.set_yticklabels([f'{y}°N' for y in range(4, 28, 4)], fontsize=7); ax.tick_params(length=0); ax.grid(True, color=GRID, linewidth=0.6)
fig.text(0.01, 0.005, 'Rings: 100, 200 and 300 km from Puerto Vallarta. Aids from the NHC ATCF a-deck; ECMWF tracks from the ECMWF open-data track files (disturbance 71E). Day marks on the DeepMind line. Black dots: NHC center fixes at 6 am, noon and 6 pm Monday. Times UTC−6.', color=MUTE, fontsize=6.3)
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(O + '/t1_tracks.png', dpi=200); plt.close(fig)

# ---------- F1b: analogs ----------
A = C['500']['storms']
fig, ax = plt.subplots(figsize=(8.4, 6.8)); EXT2 = (-118, 3.5, -86.5, 30)
draw_land(ax, EXT2); ax.set_xlim(EXT2[0], EXT2[2]); ax.set_ylim(EXT2[1], EXT2[3]); ax.set_aspect(1 / math.cos(math.radians(16)))
P0 = C['p0']; ring(ax, P0[0], P0[1], 500, color=INK2, linewidth=0.8, linestyle=(0, (2, 2))); ax.text(P0[1], P0[0] - 4.2, '500 km around EP93', fontsize=6.5, color=INK2, ha='center')
for km in (100, 300): ring(ax, *PV, km, color=INK2, linewidth=0.7, linestyle=(0, (2, 2)), zorder=4)
cols = [P[6], P[1], P[0], P[2], P[3], P[7], '#1b9e9e', '#7c8c3a', '#c2410c', '#4a7fb5', '#b58900']; k = 0
for s in sorted(A, key=lambda s: s['cpa_km']):
    xs = [p[1] for p in s['track']]; ys = [p[0] for p in s['track']]
    if s['cpa_km'] <= 300:
        ax.plot(xs, ys, color=cols[k % len(cols)], linewidth=1.8, zorder=4, label=f"{s['year']} {s['name'].title()}: {s['cpa_km']} km, {s['v_cpa']} kt, {s['cpa_days']} d"); ax.plot(xs[0], ys[0], 'o', color=cols[k % len(cols)], markersize=4, zorder=5); k += 1
    else: ax.plot(xs, ys, color='#b9b6ae', linewidth=0.9, zorder=2)
places(ax, small=True)
ax.legend(loc='upper left', bbox_to_anchor=(0, -0.05), ncol=3, fontsize=6.6, title=f"{len(A)} storms since 1949 passed within 500 km of EP93's 6 pm position between 12 Sep and 11 Nov (grey).\nThe {C['500']['within']['300']} that came within 300 km of Vallarta: closest pass, strength then, days from the analog point.", title_fontsize=6.8, borderaxespad=0)
fig.suptitle('Analog climatology (HURDAT2, 1949–2025): storms that were where EP93 is now, in this season', x=0.01, ha='left', fontsize=10, fontweight='bold')
ax.set_xticks(range(-116, -86, 4)); ax.set_xticklabels([f'{-x}°W' for x in range(-116, -86, 4)], fontsize=7); ax.set_yticks(range(4, 30, 4)); ax.set_yticklabels([f'{y}°N' for y in range(4, 30, 4)], fontsize=7); ax.tick_params(length=0); ax.grid(True, color=GRID, linewidth=0.6)
fig.tight_layout(rect=(0.01, 0.0, 1, 0.96)); fig.savefig(O + '/t2_analogs.png', dpi=200); plt.close(fig)

# ---------- F2: chances ----------
n5 = C['500']['n']; w5 = C['500']['within']
rows = [(f'Top five, {hz(LATEST)} early versions', dict(within=T5['within'], pv34=T5['pv34']), 'top'),
        (f'Top five, {hz(LATEST)}, weighted by Simon skill', dict(within=T5['within_w'], pv34=T5['pv34_w']), 'top'),
        (f'Top five, {hz(PREV)} runs (before the re-fix)', dict(within=T5P['within'], pv34=T5P['pv34']), 'prev'),
        (f'Sensitivity: corrected consensus in, GEFS mean out ({hz(LATEST)})', dict(within=T5B['within'], pv34=T5B['pv34']), 'sens'),
        (f"Context: GEFS members ({SM[ENSC['gefs']]['gefs']['n']}, {hz(ENSC['gefs'])})", SM[ENSC['gefs']]['gefs'], 'ctx'),
        (f"Context: ECMWF ensemble members ({SM[ENSC['ecens']]['ecens']['n']}, {hz(ENSC['ecens'])})", SM[ENSC['ecens']]['ecens'], 'ctx'),
        (f"Context: ECMWF AIFS ensemble members ({SM[ENSC['aiens']]['aiens']['n']}, {hz(ENSC['aiens'])})", SM[ENSC['aiens']]['aiens'], 'ctx'),
        ('Context: analog climatology (%d storms)' % n5, dict(within={k: round(100 * w5[k] / n5) for k in ('100', '200', '300')}, pv34=round(100 * C['500']['ts_within200'] / n5)), 'ctx')]
cats = [('100', 'Center within 100 km\n(direct hit or near miss)'), ('200', 'Center within 200 km'), ('300', 'Center within 300 km\n(bands, swell, some wind)'), ('pv34', 'Tropical-storm wind\nin the city (≥ 63 km/h)')]
json.dump(dict(latest=LATEST, prev=PREV, ensc=ENSC, top5p=dict(within=T5P['within'], within_w=T5P['within_w'], pv34=T5P['pv34'], pv34_w=T5P['pv34_w'], techs=T5P['techs']), top5=dict(within=T5['within'], within_w=T5['within_w'], pv34=T5['pv34'], pv34_w=T5['pv34_w'], techs=T5['techs'], carried=T5['carried'], weights=T5['weights']),
               top5b=dict(within=T5B['within'], pv34=T5B['pv34'], techs=T5B['techs']), rows=[(r[0], r[1]['within'], r[1]['pv34']) for r in rows]), open(T + '/chances.json', 'w'))
fig, axs = plt.subplots(1, 4, figsize=(11.6, 4.3), sharey=True)
labels = [r[0] for r in rows]
for ax, (k, title) in zip(axs, cats):
    vals = [(r[1]['within'][k] if k != 'pv34' else r[1]['pv34']) for r in rows]; ys = list(range(len(vals)))[::-1]
    colors = [{'top': P[6], 'prev': '#9c8be0', 'sens': '#c9bdf0', 'ctx': '#b5b3ad'}[r[2]] for r in rows]
    ax.barh(ys, vals, color=colors, height=0.62, zorder=3)
    for y, v in zip(ys, vals): ax.text(v + 1.5, y, f'{v}%', va='center', fontsize=7.5, color=INK)
    ax.set_xlim(0, 100); ax.set_title(title, fontsize=8.2, loc='left', fontweight='bold'); ax.grid(True, axis='x', color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(['0', '25', '50', '75', '100%'], fontsize=7)
    ax.spines['left'].set_visible(False)
axs[0].set_yticks(list(range(len(labels)))[::-1]); axs[0].set_yticklabels(labels, fontsize=7.4)
fig.suptitle('Chances for Puerto Vallarta: the five best Simon models (purple), six hours apart, with the ensembles and climatology for context (grey)', x=0.01, ha='left', fontsize=10.2, fontweight='bold')
fig.text(0.01, 0.01, 'Top five: share of the five lines that bring the center within the distance, or give tropical-storm wind on the parametric field. Weighted: inverse square of each model’s 12–36 h Simon position error.\nThe early versions are the previous runs moved to the NHC’s 6 pm center, about 100 km west of where those runs expected it. Context rows: share of ensemble members or analog storms.', color=MUTE, fontsize=6.2)
fig.tight_layout(rect=(0, 0.06, 1, 0.94)); fig.savefig(O + '/t3_chances.png', dpi=200); plt.close(fig)

# ---------- F3: intensity ----------
fig, ax = plt.subplots(figsize=(8.4, 4.4))
def xs_of(r): return [local(r['cycle'], p[0]) for p in r['track']]
for grp, col in (('ecens', '#86b8ee'), ('gefs', '#c5c5c5'), ('aiens', '#d9c3ee')):
    for r in TR:
        if r['cycle'] == ENSC[grp] and r['group'] == grp: ax.plot(xs_of(r), [p[3] for p in r['track']], color=col, linewidth=0.5, alpha=0.6, zorder=1)
for t in OTHER:
    r = get(PREV, t)
    if r: ax.plot(xs_of(r), [p[3] for p in r['track']], color='#a9a7a1', linewidth=0.9, zorder=2)
for m, r in FIVE:
    lab, col, ls = style(m['tech']); ax.plot(xs_of(r), [p[3] for p in r['track']], color=col, linewidth=2.4, linestyle=(0, (5, 2)) if m['ivcn'] else '-', zorder=4, label=lab + (' (consensus intensity)' if m['ivcn'] else ''))
for v, lab in ((34, 'TS'), (64, 'Cat 1'), (83, 'Cat 2'), (96, 'Cat 3'), (113, 'Cat 4'), (137, 'Cat 5')):
    ax.axhline(v, color=GRID, linewidth=0.8, zorder=0); ax.text(local('2026101212', 179), v + 1.5, lab, fontsize=6.5, color=MUTE, ha='right')
ax.set_ylim(0, 150); ax.set_ylabel('Max sustained wind (kt)'); ax.set_xlim(local('2026101212', 6), local('2026101212', 180))
days = [local('2026101212', 6) + dt.timedelta(days=i) for i in range(8)]
ax.set_xticks(days); ax.set_xticklabels([d.strftime('%a %d') for d in days], fontsize=7.5); tidy(ax)
ax.legend(handles=ax.get_legend_handles_labels()[0] + [Line2D([], [], color='#a9a7a1', linewidth=0.9, label='Other aids'), Line2D([], [], color='#86b8ee', linewidth=1, label='Ensemble members (ECMWF blue, GEFS grey, AIFS lilac)')], loc='upper left', ncol=2, fontsize=6.6, handlelength=2.4)
ax.set_title(f'How strong: the five best Simon models, {hz(LATEST)} early versions', loc='left', fontsize=10, fontweight='bold')
fig.text(0.01, 0.005, 'Dashed: TVCN carries no intensity and the AIFS 10-m wind runs low (as for Simon); both are given the NHC intensity consensus IVCN of the cycle. Grey: other aids. Times UTC−6.', color=MUTE, fontsize=6.3)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(O + '/t4_intensity.png', dpi=200); plt.close(fig)

# ---------- F4: scenario timeline from the five ----------
def windows(r):
    tr = r['track']; c = r['cycle']
    def span(cond):
        hh = [p[0] for p in tr if cond(p)]
        return (local(c, hh[0]), local(c, hh[-1] + 6)) if hh else None
    return dict(swell=span(lambda p: p[4] <= 700 and p[3] >= 50), bands=span(lambda p: p[4] <= 350 and p[3] >= 30),
                ts=(local(c, r['pv34'][0]), local(c, r['pv34'][1] + 1)) if r['pv34'] else None, hu=(local(c, r['pv64'][0]), local(c, r['pv64'][1] + 1)) if r['pv64'] else None, cpa=local(c, r['cpa_h']))
by_cpa = sorted(FIVE, key=lambda mr: mr[0]['cpa_km'])
likely = by_cpa[len(by_cpa) // 2]; least = by_cpa[-1]
by_wind = sorted([mr for mr in FIVE + FIVEP if not mr[0]['ivcn']], key=lambda mr: -mr[0]['sites']['amapas']['kmh'])
worst = by_wind[0]
def nm(m): return style(m['tech'])[0].split(' (')[0] + f" {hz(m['cycle'])}"
SCEN = [('least', f"Least impact ({nm(least[0])}): passes {least[0]['cpa_km']} km to the {['N','NE','E','SE','S','SW','W','NW'][int((least[0]['cpa_brg']+22.5)//45)%8]} at {least[0]['cpa_local']}, {least[0]['cpa_v']} kt", least),
        ('likely', f"Most likely (median of the five: {nm(likely[0])}): center {likely[0]['cpa_km']} km {['N','NE','E','SE','S','SW','W','NW'][int((likely[0]['cpa_brg']+22.5)//45)%8]} at {likely[0]['cpa_local']}, {likely[0]['cpa_v']} kt", likely),
        ('worst', f"Worst case ({nm(worst[0])}): center {worst[0]['cpa_km']} km {['N','NE','E','SE','S','SW','W','NW'][int((worst[0]['cpa_brg']+22.5)//45)%8]} at {worst[0]['cpa_local']}, {worst[0]['cpa_v']} kt after a {worst[0]['peak_v']}-kt peak", worst)]
json.dump({k: dict(label=lab, tech=m['tech'], name=nm(m), cycle=m['cycle'], cpa_km=m['cpa_km'], cpa_local=m['cpa_local'], cpa_brg=m['cpa_brg'], cpa_v=m['cpa_v'], peak_v=m['peak_v'], own_peak_v=m['own_peak_v'], ivcn=m['ivcn'], pv34=m['pv34'], pv64=m['pv64'] if 'pv64' in m else r['pv64'],
                   rain_mm=m['rain_mm'], sites=m['sites'], landfall=m['landfall'],
                   windows={a: ([x.strftime('%a %d %b %H:%M') for x in b] if isinstance(b, tuple) else b.strftime('%a %d %b %H:%M') if b else None) for a, b in windows(r).items()})
           for k, lab, (m, r) in SCEN}, open(T + '/scenarios.json', 'w'), indent=1)
fig, ax = plt.subplots(figsize=(10.4, 4.3))
x0, x1 = dt.datetime(2026, 10, 15, 0), dt.datetime(2026, 10, 20, 12)
for i, (key, lab, (m, r)) in enumerate(SCEN):
    y = 2 - i; w = windows(r)
    for kk, col, txt in (('swell', '#bfe0f5', 'swell on the coast'), ('bands', '#5aa9e6', 'rain bands'), ('ts', P[1], 'tropical-storm wind'), ('hu', P[7], 'hurricane wind')):
        if w[kk]:
            a, b = w[kk]; ax.barh(y, (b - a).total_seconds() / 86400, left=a, height=0.62, color=col, zorder=3 + (kk != 'swell'))
            if kk == 'ts' or (kk == 'bands' and not w['ts']): ax.text(a + (b - a) / 2, y + 0.38, txt, ha='center', fontsize=6.5, color=INK2)
    ax.plot(w['cpa'], y, 'v', color=INK, markersize=7, zorder=6); ax.text(w['cpa'], y - 0.45, f"closest {m['cpa_km']} km, {m['cpa_local'][-5:]}", ha='center', fontsize=6.5, color=INK)
    if not any(w[kk] for kk in ('swell', 'bands', 'ts', 'hu')): ax.text(x0 + dt.timedelta(hours=30), y, 'no swell, rain bands or wind in the city from this line', fontsize=6.8, color=MUTE, va='center')
    ax.text(x0 + dt.timedelta(hours=2), y + 0.33, lab, fontsize=6.9, va='bottom', color=INK, zorder=7)
ax.set_ylim(-0.7, 3.2); ax.set_yticks([]); ax.set_xlim(x0, x1)
for d in range(6):
    t = x0 + dt.timedelta(days=d); ax.axvline(t, color=GRID, linewidth=0.8, zorder=0); ax.text(t + dt.timedelta(hours=1), -0.62, t.strftime('%a %d Oct'), fontsize=7.5, color=INK2)
ax.axvline(dt.datetime(2026, 10, 15, 12), color=P[6], linewidth=1.2, linestyle=(0, (3, 2)), zorder=1); ax.text(dt.datetime(2026, 10, 15, 13), 3.0, 'Thu noon: ~72 h out, the point by which the\ntrack should be clear (Simon’s lesson)', fontsize=6.5, color=P[6])
ax.set_xticks([]); ax.spines['left'].set_visible(False); ax.spines['bottom'].set_visible(False)
ax.set_title('When: least, most likely and worst of the five, Puerto Vallarta local time (UTC−6)', loc='left', fontsize=10, fontweight='bold')
ax.legend(handles=[Patch(color='#bfe0f5', label='swell (storm of 50 kt+ within 700 km)'), Patch(color='#5aa9e6', label='rain bands (center within 350 km)'), Patch(color=P[1], label='tropical-storm wind at the city (≥ 63 km/h)'), Patch(color=P[7], label='hurricane wind'), Line2D([], [], marker='v', color=INK, linestyle='', label='closest approach')],
          loc='upper left', bbox_to_anchor=(0, -0.02), ncol=5, fontsize=6.6, borderaxespad=0)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(O + '/t5_timeline.png', dpi=200); plt.close(fig)
print('charts ok', T5['within'], T5['within_w'], {k: (m['tech'], m['cpa_km'], m['cpa_local']) for k, _, (m, _) in SCEN})
