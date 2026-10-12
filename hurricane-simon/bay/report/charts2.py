import json, sys, math, datetime as dt
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from PIL import Image
S = sys.argv[1]; H = '/home/user/vallarta-weather/hurricane-simon'
T = json.load(open(S + '/report/trend.json')); LY = json.load(open(H + '/map/data/layers.json'))
INK, INK2, MUTE, GRID, SURF = '#0b0b0b', '#52514e', '#7a7975', '#e6e4df', '#fcfcfb'
P = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
RAMP = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95', '#104281', '#0d366b']
rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': GRID, 'axes.linewidth': 1, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2, 'text.color': INK,
                 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'legend.frameon': False})
def tidy(ax): ax.grid(True, axis='y', color=GRID, linewidth=1); ax.set_axisbelow(True); ax.tick_params(length=0)
PV = (20.61, -105.2345)
def P_(s): return dt.datetime.strptime(s, '%Y-%m-%dT%H:%MZ')
def cst(s): d = P_(s) - dt.timedelta(hours=6); return d.strftime('%a') + ' ' + (str(d.hour % 12 or 12) + (' am' if d.hour < 12 else ' pm'))
# ---------- F7: every NHC forecast track vs what happened ----------
bb = LY['reg']['bbox']; im = Image.open(H + '/map/data/img/reg_base.webp')
fig, ax = plt.subplots(figsize=(7.4, 6.2))
ax.imshow(im, extent=[bb[2], bb[3], bb[1], bb[0]], aspect='auto', alpha=0.95)
sx = (bb[3] - bb[2]) / LY['reg']['w']; sy = (bb[0] - bb[1]) / LY['reg']['h']
ax.scatter([bb[2] + p[0] * sx for p in LY['reg']['coast']], [bb[0] - p[1] * sy for p in LY['reg']['coast']], s=0.6, color='#ffd166', alpha=0.7, linewidths=0)
tr = [t for t in T['trend'] if t['track']]; n = len(tr)
for i, t in enumerate(tr):
    col = RAMP[min(len(RAMP) - 1, int(i / max(1, n - 1) * (len(RAMP) - 1)))]
    pts = [(p[2], p[1]) for p in t['track'] if P_(p[0]) <= P_(t['issued']) + dt.timedelta(hours=72)]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, linewidth=1.6 if i < n - 1 else 2.4, alpha=0.95, solid_capstyle='round', zorder=3)
bt = T['best']; ax.plot([b[2] for b in bt], [b[1] for b in bt], color='#111111', linewidth=3.2, zorder=5, label='What happened (NHC best track to Mon 6 am)')
ax.plot(bt[-1][2], bt[-1][1], '*', color='#111111', markersize=14, markeredgecolor=SURF, zorder=6)
ax.plot(PV[1], PV[0], 'o', color='#e34948', markersize=8, markeredgecolor=SURF, markeredgewidth=1.5, zorder=6); ax.text(PV[1] + 0.12, PV[0] + 0.05, 'Puerto Vallarta', color='#ffffff', fontsize=8.5, fontweight='bold', zorder=6)
circ = plt.Circle((PV[1], PV[0]), 100 / 111.0, fill=False, color='#ffffff', linestyle='--', linewidth=1, alpha=0.8); ax.add_patch(circ); ax.text(PV[1] + 0.55, PV[0] + 0.78, '100 km', color='#ffffff', fontsize=7)
ax.set_xlim(-108.9, -102.3); ax.set_ylim(15.3, 22.0); ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect(1 / math.cos(math.radians(19)))
from matplotlib.lines import Line2D
handles = [Line2D([0], [0], color=RAMP[0], lw=2, label='Advisory 1 (Wed 7 Oct, 9 am)'), Line2D([0], [0], color=RAMP[6], lw=2, label='Advisories 9–12 (Fri–Sat)'), Line2D([0], [0], color=RAMP[12], lw=2.4, label=f"Advisory {tr[-1]['num']} ({cst(tr[-1]['issued'])})"), Line2D([0], [0], color='#111111', lw=3, label='What happened (best track to Mon 6 am)')]
ax.legend(handles=handles, loc='lower left', fontsize=7.5, facecolor='#0b0e13', edgecolor='none', labelcolor='#ffffff', framealpha=0.75)
ax.set_title('Every NHC forecast track for Simon (first 72 h of each), and what happened', loc='left', fontsize=10, fontweight='bold')
fig.tight_layout(); fig.savefig(S + '/report/f7_tracks.png', dpi=220); plt.close(fig)
# ---------- F8: closest approach to Vallarta, advisory by advisory ----------
fig, axs = plt.subplots(2, 1, figsize=(7.4, 5.6), sharex=True, gridspec_kw={'height_ratios': [1.25, 1]})
xs = list(range(len(tr))); labs = [f"#{t['num']}\n{cst(t['issued'])}" for t in tr]
ax = axs[0]; ys = [t['cpa_km'] for t in tr]
ax.axhline(T['actual_cpa']['km'], color=INK, linewidth=2); ax.text(0, T['actual_cpa']['km'] + 5, f"What happened: closest pass {T['actual_cpa']['km']} km ({cst(T['actual_cpa']['t'])}, {T['actual_cpa']['kt']} kt), then a stall", color=INK, fontsize=8, fontweight='bold')
ax.axhspan(0, 15, color=P[7], alpha=0.10, linewidth=0); ax.text(len(xs) - 0.6, 8, 'center over the city', color=INK2, fontsize=7, ha='right', va='center')
ax.plot(xs, ys, color=P[0], linewidth=2, marker='o', markersize=5, markeredgecolor=SURF, markeredgewidth=1.2)
ax.set_ylabel('Forecast closest approach\nto Puerto Vallarta (km)', fontsize=8); ax.set_ylim(0, 150); tidy(ax)
ax.set_title('How close the NHC forecast line came to Vallarta, advisory by advisory', loc='left', fontsize=10, fontweight='bold')
ax = axs[1]; ys = [t['cpa_kt'] for t in tr]
ax.axhline(T['actual_cpa']['kt'], color=INK, linewidth=2); ax.text(0, T['actual_cpa']['kt'] + 4, f"intensity at the real closest pass: {T['actual_cpa']['kt']} kt", color=INK, fontsize=8, fontweight='bold')
for y, lab in [(64, 'cat. 1'), (96, 'cat. 3'), (113, 'cat. 4')]: ax.axhline(y, color=GRID, linewidth=1); ax.text(len(xs) - 0.6, y + 2, lab, color=MUTE, fontsize=7, ha='right')
ax.plot(xs, ys, color=P[1], linewidth=2, marker='o', markersize=5, markeredgecolor=SURF, markeredgewidth=1.2)
ax.set_ylabel('Forecast intensity at that\nclosest approach (kt)', fontsize=8); ax.set_ylim(0, 140); tidy(ax)
ax.set_xticks(xs); ax.set_xticklabels([l.replace('\n', ' ') for l in labs], fontsize=6.5, rotation=45, ha='right'); ax.set_xlabel('NHC advisory number and issue time (Vallarta time)', fontsize=8)
fig.tight_layout(); fig.savefig(S + '/report/f8_cpa_trend.png', dpi=220); plt.close(fig)
# ---------- F9: what the resident graphics said for the three buildings, by version, and what the airport measured ----------
sn = T['snaps']; keys = ['17a', '17b', '18', '20']; names = {'17a': 'Adv. 17\nSun 9:10 am\n(first set)', '17b': 'Adv. 17\nSun 1 pm\n(dry-side rain)', '18': 'Adv. 18\nSun 3 pm', '20': 'Adv. 20\nMon 6 am'}
sites = [('amapas', 'D Terrace (8th floor)', P[3]), ('ezapata', 'Casa Francisca (3rd floor)', P[0]), ('pitillal', 'El Pitillal (house)', P[2])]
fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.8), gridspec_kw={'width_ratios': [1.3, 1]})
ax = axs[0]; w = 0.24
for j, (sid, lab, col) in enumerate(sites):
    vals = [sn[k]['sites'][sid]['peak_gb'] for k in keys]; ax.bar([x + (j - 1) * w for x in range(4)], vals, width=w - 0.03, color=col, linewidth=0, label=lab)
ax.axhline(7, color=INK, linewidth=2, label='Airport, Sun 3 pm to Mon 8 am:\npeak 7 km/h (4 kt), no gusts reported')
ax.set_xticks(range(4)); ax.set_xticklabels([names[k] for k in keys], fontsize=6.6); ax.set_ylabel('Forecast peak gust at the building (km/h)', fontsize=8); ax.set_ylim(0, 125); tidy(ax); ax.legend(fontsize=6.6, loc='upper left', ncol=2)
ax.set_title('Wind: what each version of the building\nsummary said, and what was measured', loc='left', fontsize=9.5, fontweight='bold')
ax = axs[1]
for j, (sid, lab, col) in enumerate(sites):
    vals = [(sn[k]['sites'][sid]['rain'] or {}).get('total_mm') or 0 for k in keys]; ax.bar([x + (j - 1) * w for x in range(4)], vals, width=w - 0.03, color=col, linewidth=0)
ax.set_yscale('symlog', linthresh=10); ax.set_ylim(0, 400); ax.set_yticks([0, 5, 10, 50, 100, 250]); ax.set_yticklabels(['0', '5', '10', '50', '100', '250'])
ax.axhspan(5, 35, color=INK, alpha=0.08, linewidth=0); ax.text(3.45, 18, 'airport overnight: light rain on and off,\n6-hour groups 4–35 mm (inconsistent)', color=INK, fontsize=6.4, ha='right', va='center')
for xi, k in enumerate(keys):
    if all(((sn[k]['sites'][sid]['rain'] or {}).get('total_mm') or 0) < 1 for sid, _, _ in sites): ax.text(xi, 1.2, 'under\n1 mm', ha='center', va='bottom', fontsize=6.4, color=INK2)
ax.set_xticks(range(4)); ax.set_xticklabels([names[k] for k in keys], fontsize=6.6); ax.set_ylabel('Forecast rain total at the building (mm)', fontsize=8); tidy(ax)
ax.set_title('Rain: the first set scaled satellite\nrain to the SMN regional figure;\nthe later sets did not', loc='left', fontsize=9.5, fontweight='bold')
fig.tight_layout(); fig.savefig(S + '/report/f9_buildings.png', dpi=220); plt.close(fig)
print('charts2 ok')
