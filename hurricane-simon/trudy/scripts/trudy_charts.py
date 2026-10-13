"""Charts for the EP93 (Trudy) Puerto Vallarta brief. Usage: trudy_charts.py SCRATCH"""
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
def get(cycle, tech): return next((r for r in TR if r['cycle'] == cycle and r['tech'] == tech), None)
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

# ---------- F1: track map ----------
EXT = (-113.5, 3.5, -86.5, 27.5)
fig, ax = plt.subplots(figsize=(8.4, 7.1))
draw_land(ax, EXT); ax.set_xlim(EXT[0], EXT[2]); ax.set_ylim(EXT[1], EXT[3]); ax.set_aspect(1 / math.cos(math.radians(16)))
for km, lab, ang in ((100, '100 km', 225), (200, '200 km', 240), (300, '300 km', 250)):
    ring(ax, *PV, km, color=INK2, linewidth=0.7, linestyle=(0, (2, 2)), zorder=4)
    a = math.radians(ang); ax.text(PV[1] + km / (111.32 * math.cos(math.radians(PV[0]))) * math.cos(a), PV[0] + km / 110.57 * math.sin(a), lab, fontsize=6, color=INK2, ha='center', va='center', zorder=6,
                                   bbox=dict(facecolor=SURF, edgecolor='none', pad=0.6))
# ensembles first (thin)
for grp, col, lw, al in (('gefs', '#9a9a9a', 0.5, 0.55), ('aiens', '#c9a9e8', 0.5, 0.6), ('ecens', '#86b8ee', 0.6, 0.7)):
    for r in TR:
        if r['cycle'] == '2026101212' and r['group'] == grp:
            ax.plot([p[2] for p in r['track']], [p[1] for p in r['track']], color=col, linewidth=lw, alpha=al, zorder=2)
STYLE = {'GDMN': ('Google DeepMind (12Z)', P[6], 2.6, '-'), 'HCCA': ('NHC corrected consensus (12Z)', INK, 2.2, '-'), 'TVCN': ('Track consensus (12Z)', INK, 1.4, (0, (4, 2))),
         'AVNO': ('GFS', P[0], 1.5, '-'), 'UKX': ('UKMET', '#1b9e9e', 1.5, '-'), 'CEMN': ('Canadian ens. mean', '#3d7d3d', 1.5, '-'), 'NVGM': ('NAVGEM', '#7c8c3a', 1.5, '-'),
         'HFSA': ('HAFS-A', P[1], 1.5, '-'), 'HFSB': ('HAFS-B', '#c2410c', 1.5, (0, (4, 2))), 'HWRF': ('HWRF', P[3], 1.5, '-'), 'HMON': ('HMON', '#b58900', 1.5, (0, (4, 2))), 'CTCX': ('COAMPS-TC', P[7], 1.5, '-'),
         'CLP5': ('Climatology-persistence', MUTE, 1.3, (0, (1, 2)))}
for tech, (lab, col, lw, ls) in STYLE.items():
    r = get('2026101212', tech)
    if not r: continue
    ax.plot([p[2] for p in r['track']], [p[1] for p in r['track']], color=col, linewidth=lw, linestyle=ls, zorder=3 if lw < 2 else 4, solid_capstyle='round')
for tech, lab, col in (('GDMI', 'Google DeepMind (18Z)', P[6]), ('HCCA', 'NHC corrected consensus (18Z)', INK), ('TVCN', 'Track consensus (18Z)', INK)):
    r = get('2026101218', tech)
    if r: ax.plot([p[2] for p in r['track']], [p[1] for p in r['track']], color=col, linewidth=2.0 if tech != 'TVCN' else 1.3, linestyle=(0, (1, 1.2)), zorder=4)
# day marks along DeepMind 12Z
r = get('2026101212', 'GDMN')
for h, lab in ((48, 'Wed'), (96, 'Fri'), (144, 'Sun')):
    p = next((p for p in r['track'] if p[0] == h), None)
    if p: ax.plot(p[2], p[1], 'o', color=P[6], markersize=5, markeredgecolor=SURF, zorder=5); ax.text(p[2] + 0.3, p[1] + 0.25, lab + ' 6 am', fontsize=6.5, color=P[6], zorder=6, bbox=dict(facecolor=SURF, edgecolor='none', pad=0.5, alpha=0.85))
places(ax)
b = D['tracks'][0]['track'][0]; ax.plot(-93.9, 8.1, 'o', color=INK, markersize=6, zorder=6, markeredgecolor=SURF); ax.text(-93.6, 7.3, 'EP93, Mon 12 Oct 6 pm', fontsize=7, color=INK)
handles = [Line2D([], [], color=c, linewidth=lw, linestyle=ls, label=lab) for tech, (lab, c, lw, ls) in STYLE.items()]
handles += [Line2D([], [], color=P[6], linewidth=2, linestyle=(0, (1, 1.2)), label='DeepMind / consensus, 18Z runs (dotted)'),
            Line2D([], [], color='#86b8ee', linewidth=1.2, label='ECMWF ensemble, 51 members (12Z)'), Line2D([], [], color='#c9a9e8', linewidth=1.2, label='ECMWF AIFS ensemble, 51 members (AI, 12Z)'),
            Line2D([], [], color='#9a9a9a', linewidth=1.2, label='GEFS, 31 members (12Z)')]
ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.0, -0.06), ncol=3, fontsize=6.6, handlelength=2.2, borderaxespad=0)
ax.set_title('EP93 (future Trudy): where the models take it, runs of Monday 12 October (12Z and 18Z)', loc='left', fontsize=10, fontweight='bold')
ax.set_xticks(range(-112, -86, 4)); ax.set_xticklabels([f'{-x}°W' for x in range(-112, -86, 4)], fontsize=7); ax.set_yticks(range(4, 28, 4)); ax.set_yticklabels([f'{y}°N' for y in range(4, 28, 4)], fontsize=7); ax.tick_params(length=0); ax.grid(True, color=GRID, linewidth=0.6)
fig.text(0.01, 0.005, 'Rings: 100, 200 and 300 km from Puerto Vallarta. Dynamical and AI aids from the NHC ATCF a-deck; ECMWF ensembles from the ECMWF open-data track files (disturbance 71E). Times UTC−6.', color=MUTE, fontsize=6.3)
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(O + '/t1_tracks.png', dpi=200); plt.close(fig)

# ---------- F1b: analogs ----------
A = C['500']['storms']
fig, ax = plt.subplots(figsize=(8.4, 6.4)); EXT2 = (-118, 3.5, -86.5, 30)
draw_land(ax, EXT2); ax.set_xlim(EXT2[0], EXT2[2]); ax.set_ylim(EXT2[1], EXT2[3]); ax.set_aspect(1 / math.cos(math.radians(16)))
ring(ax, 8.1, -93.9, 500, color=INK2, linewidth=0.8, linestyle=(0, (2, 2))); ax.text(-93.9, 3.9, '500 km around EP93', fontsize=6.5, color=INK2, ha='center')
for km in (100, 300): ring(ax, *PV, km, color=INK2, linewidth=0.7, linestyle=(0, (2, 2)), zorder=4)
cols = [P[6], P[1], P[0], P[2], P[3], P[7]]; k = 0
for s in sorted(A, key=lambda s: s['cpa_km']):
    xs = [p[1] for p in s['track']]; ys = [p[0] for p in s['track']]
    if s['cpa_km'] <= 300:
        ax.plot(xs, ys, color=cols[k % 6], linewidth=2, zorder=4, label=f"{s['year']} {s['name'].title()}: {s['cpa_km']} km, {s['v_cpa']} kt, {s['cpa_days']} d"); ax.plot(xs[0], ys[0], 'o', color=cols[k % 6], markersize=4, zorder=5); k += 1
    else: ax.plot(xs, ys, color='#b9b6ae', linewidth=0.9, zorder=2)
places(ax, small=True)
ax.legend(loc='upper left', bbox_to_anchor=(0, -0.05), ncol=3, fontsize=6.8, title=f'{len(A)} storms since 1949 passed within 500 km of EP93 between 12 Sep and 11 Nov (grey). The 6 that came within 300 km of Vallarta: closest pass, strength then, days from the analog point.', title_fontsize=6.8, borderaxespad=0)
ax.set_title('Analog climatology (HURDAT2, 1949–2025): storms that were where EP93 is now, in this season', loc='left', fontsize=10, fontweight='bold')
ax.set_xticks(range(-116, -86, 4)); ax.set_xticklabels([f'{-x}°W' for x in range(-116, -86, 4)], fontsize=7); ax.set_yticks(range(4, 30, 4)); ax.set_yticklabels([f'{y}°N' for y in range(4, 30, 4)], fontsize=7); ax.tick_params(length=0); ax.grid(True, color=GRID, linewidth=0.6)
fig.tight_layout(rect=(0.01, 0.0, 1, 1)); fig.savefig(O + '/t2_analogs.png', dpi=200); plt.close(fig)

# ---------- F2: chances ----------
n5 = C['500']['n']; w5 = C['500']['within']
rows = [('GEFS ensemble, 31 members (12Z)', SM['2026101212']['gefs'], 'ens'),
        ('ECMWF ensemble, 51 members (12Z)', SM['2026101212']['ecens'], 'ens'),
        ('ECMWF AIFS ensemble (AI), 51 members (12Z)', SM['2026101212']['aiens'], 'ens'),
        ('Dynamical + AI aids, equal weight (18Z, %d aids)' % SM['2026101218']['aids']['n'], dict(within=SM['2026101218']['aids']['within_unweighted'], pv34=SM['2026101218']['aids']['pv34_unweighted']), 'aid'),
        ('Same aids weighted by their Simon skill (18Z)', dict(within=SM['2026101218']['aids']['within'], pv34=SM['2026101218']['aids']['pv34']), 'aid'),
        ('Analog climatology, %d storms since 1949' % n5, dict(within={k: round(100 * w5[k] / n5) for k in ('100', '200', '300')}, pv34=round(100 * C['500']['ts_within200'] / n5)), 'clim')]
cats = [('100', 'Center within 100 km\n(direct hit or near miss)'), ('200', 'Center within 200 km'), ('300', 'Center within 300 km\n(bands, swell, some wind)'), ('pv34', 'Tropical-storm wind\nin the city (≥ 63 km/h)')]
blend = {k: round(sum((r[1]['within'][k] if k != 'pv34' else r[1]['pv34']) for r in rows) / len(rows)) for k, _ in cats}
spread = {k: (min((r[1]['within'][k] if k != 'pv34' else r[1]['pv34']) for r in rows), max((r[1]['within'][k] if k != 'pv34' else r[1]['pv34']) for r in rows)) for k, _ in cats}
json.dump(dict(blend=blend, spread=spread, rows=[(r[0], r[1]['within'], r[1]['pv34']) for r in rows]), open(T + '/chances.json', 'w'))
fig, axs = plt.subplots(1, 4, figsize=(11.2, 3.9), sharey=True)
labels = [r[0] for r in rows] + ['Simple average of the six']
for ax, (k, title) in zip(axs, cats):
    vals = [(r[1]['within'][k] if k != 'pv34' else r[1]['pv34']) for r in rows] + [blend[k]]
    ys = list(range(len(vals)))[::-1]
    colors = [{'ens': P[0], 'aid': P[1], 'clim': P[2]}[r[2]] for r in rows] + [INK]
    ax.barh(ys, vals, color=colors, height=0.62, zorder=3)
    for y, v in zip(ys, vals): ax.text(v + 1.5, y, f'{v}%', va='center', fontsize=7.5, color=INK)
    ax.set_xlim(0, 100); ax.set_title(title, fontsize=8.2, loc='left', fontweight='bold'); ax.grid(True, axis='x', color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(['0', '25', '50', '75', '100%'], fontsize=7)
    ax.spines['left'].set_visible(False)
axs[0].set_yticks(list(range(len(labels)))[::-1]); axs[0].set_yticklabels(labels, fontsize=7.4)
fig.suptitle('Chances for Puerto Vallarta from each source (runs of Monday 12 October)', x=0.01, ha='left', fontsize=10.5, fontweight='bold')
fig.text(0.01, 0.01, 'Ensembles: share of members. Aids: share of deterministic and AI tracks (early versions of the 18Z cycle; the weighted line uses the inverse square of each model’s 12–36 h Simon position error). Climatology: share of analog storms. Wind: parametric field on each track with climatological radii.', color=MUTE, fontsize=6.2)
fig.tight_layout(rect=(0, 0.04, 1, 0.94)); fig.savefig(O + '/t3_chances.png', dpi=200); plt.close(fig)

# ---------- F3: intensity ----------
fig, ax = plt.subplots(figsize=(8.4, 4.4))
c12 = cyc('2026101212')
def xs_of(r): return [local(r['cycle'], p[0]) for p in r['track']]
for grp, col, lab in (('ecens', '#86b8ee', 'ECMWF ensemble members'), ('gefs', '#c5c5c5', 'GEFS members'), ('aiens', '#d9c3ee', 'AIFS ensemble members')):
    for r in TR:
        if r['cycle'] == '2026101212' and r['group'] == grp: ax.plot(xs_of(r), [p[3] for p in r['track']], color=col, linewidth=0.5, alpha=0.7, zorder=1)
for tech, (lab, col, lw, ls) in STYLE.items():
    r = get('2026101212', tech)
    if not r or tech in ('CLP5', 'TVCN'): continue
    ax.plot(xs_of(r), [p[3] for p in r['track']], color=col, linewidth=lw, linestyle=ls, zorder=3, label=lab)
r = get('2026101218', 'HCCA'); ax.plot(xs_of(r), [p[3] for p in r['track']], color=INK, linewidth=2, linestyle=(0, (1, 1.2)), zorder=4, label='NHC corrected consensus (18Z)')
r = get('2026101218', 'GDMI'); ax.plot(xs_of(r), [p[3] for p in r['track']], color=P[6], linewidth=2, linestyle=(0, (1, 1.2)), zorder=4, label='Google DeepMind (18Z)')
for v, lab in ((34, 'TS'), (64, 'Cat 1'), (83, 'Cat 2'), (96, 'Cat 3'), (113, 'Cat 4'), (137, 'Cat 5')):
    ax.axhline(v, color=GRID, linewidth=0.8, zorder=0); ax.text(local('2026101212', 179), v + 1.5, lab, fontsize=6.5, color=MUTE, ha='right')
ax.set_ylim(0, 150); ax.set_ylabel('Max sustained wind (kt)'); ax.set_xlim(local('2026101212', 0), local('2026101212', 180))
days = [local('2026101212', 6) + dt.timedelta(days=i) for i in range(8)]
ax.set_xticks(days); ax.set_xticklabels([d.strftime('%a %d') for d in days], fontsize=7.5); tidy(ax)
ax.legend(loc='upper left', ncol=4, fontsize=6.6, handlelength=2); ax.set_title('How strong: intensity forecasts from the Monday 12Z and 18Z runs', loc='left', fontsize=10, fontweight='bold')
fig.text(0.01, 0.005, 'Thin lines: ensemble members (ECMWF blue, GEFS grey, AIFS lilac). Gridded AI models under-forecast intensity by construction, as they did for Simon. Times UTC−6.', color=MUTE, fontsize=6.3)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(O + '/t4_intensity.png', dpi=200); plt.close(fig)

# ---------- F4: scenario timeline ----------
def windows(r):
    tr = r['track']; c = r['cycle']
    def span(cond):
        hh = [p[0] for p in tr if cond(p)]
        return (local(c, hh[0]), local(c, hh[-1] + 6)) if hh else None
    return dict(swell=span(lambda p: p[4] <= 700 and p[3] >= 50), bands=span(lambda p: p[4] <= 350 and p[3] >= 30),
                ts=(local(c, r['pv34'][0]), local(c, r['pv34'][1] + 1)) if r['pv34'] else None, hu=(local(c, r['pv64'][0]), local(c, r['pv64'][1] + 1)) if r['pv64'] else None,
                cpa=local(c, r['cpa_h']), peak=local(c, r['cpa_h']))
ec = [r for r in TR if r['cycle'] == '2026101212' and r['group'] == 'ecens']
med = sorted(ec, key=lambda r: abs(r['cpa_km'] - SM['2026101212']['ecens']['cpa_median']))[0]
SCEN = [('A · Most likely (middle of the ECMWF ensemble, GFS family, climatology)\npasses about 300 km or more to the west or southwest, or weakens before arriving: swell and showers, no damaging wind', med),
        ('B · Close pass to the west as a hurricane (Google DeepMind 18Z; about 1 in 5 ECMWF members)\ncenter 90 km west on Sunday afternoon: tropical-storm wind, heavy rain', get('2026101218', 'GDMI')),
        ('C · Worst case (NHC corrected consensus 18Z): category-4 landfall at Manzanillo before dawn Sunday,\nthen north across Jalisco, center 75 km east of the bay Sunday afternoon', get('2026101218', 'HCCA'))]
json.dump({k: dict(tech=r['tech'], cycle=r['cycle'], cpa_km=r['cpa_km'], cpa_local=r['cpa_local'], cpa_v=r['cpa_v'], peak_v=r['peak_v'], pv34=r['pv34'], pv64=r['pv64'], rain_mm=r['rain_mm'], sites=r['sites'], landfall=r['landfall'],
                   windows={a: ([x.strftime('%a %d %b %H:%M') for x in b] if isinstance(b, tuple) else b.strftime('%a %d %b %H:%M') if b else None) for a, b in windows(r).items()})
           for k, r in zip('ABC', [s[1] for s in SCEN])}, open(T + '/scenarios.json', 'w'), indent=1)
fig, ax = plt.subplots(figsize=(10.4, 4.3))
x0, x1 = dt.datetime(2026, 10, 15, 0), dt.datetime(2026, 10, 20, 12)
for i, (lab, r) in enumerate(SCEN):
    y = 2 - i; w = windows(r)
    for key, col, h, txt in (('swell', '#bfe0f5', 0.62, 'swell on the coast'), ('bands', '#5aa9e6', 0.62, 'rain bands'), ('ts', P[1], 0.62, 'tropical-storm wind'), ('hu', P[7], 0.62, 'hurricane wind')):
        if w[key]:
            a, b = w[key]; ax.barh(y, (b - a).total_seconds() / 86400, left=a, height=h, color=col, zorder=3 + (key != 'swell'))
            if key == 'ts' or (key == 'bands' and not w['ts']): ax.text(a + (b - a) / 2, y + 0.38, txt, ha='center', fontsize=6.5, color=INK2)
    ax.plot(w['cpa'], y, 'v', color=INK, markersize=7, zorder=6); ax.text(w['cpa'], y - 0.45, f"closest {r['cpa_km']} km, {r['cpa_local'][-5:]}", ha='center', fontsize=6.5, color=INK)
    ax.text(x0 + dt.timedelta(hours=2), y + 0.33, lab, fontsize=6.9, va='bottom', color=INK, zorder=7)
ax.set_ylim(-0.7, 3.2); ax.set_yticks([]); ax.set_xlim(x0, x1)
for d in range(6):
    t = x0 + dt.timedelta(days=d); ax.axvline(t, color=GRID, linewidth=0.8, zorder=0); ax.text(t + dt.timedelta(hours=1), -0.62, t.strftime('%a %d Oct'), fontsize=7.5, color=INK2)
ax.axvline(dt.datetime(2026, 10, 15, 12), color=P[6], linewidth=1.2, linestyle=(0, (3, 2)), zorder=1); ax.text(dt.datetime(2026, 10, 15, 13), 3.0, 'Thu noon: ~72 h out, the point by which the\ntrack should be clear (Simon’s lesson)', fontsize=6.5, color=P[6])
ax.set_xticks([]); ax.spines['left'].set_visible(False); ax.spines['bottom'].set_visible(False)
ax.set_title('When: three scenarios for Puerto Vallarta, local time (UTC−6)', loc='left', fontsize=10, fontweight='bold')
ax.legend(handles=[Patch(color='#bfe0f5', label='swell (hurricane within 700 km)'), Patch(color='#5aa9e6', label='rain bands (center within 350 km)'), Patch(color=P[1], label='tropical-storm wind at the city (≥ 63 km/h)'), Patch(color=P[7], label='hurricane wind'), Line2D([], [], marker='v', color=INK, linestyle='', label='closest approach')],
          loc='upper left', bbox_to_anchor=(0, -0.02), ncol=5, fontsize=6.6, borderaxespad=0)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(O + '/t5_timeline.png', dpi=200); plt.close(fig)
print('charts ok', blend, spread, {k: (r['tech'], r['cpa_km'], r['cpa_local']) for k, r in zip('ABC', [s[1] for s in SCEN])})
