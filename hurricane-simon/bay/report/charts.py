import json, sys, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
S = sys.argv[1]; H = '/home/user/vallarta-weather/hurricane-simon'
D = json.load(open(S + '/report/data.json')); VF = json.load(open(H + '/bay/data/verify.json')); CS = json.load(open(H + '/bay/data/consensus.json'))
INK, INK2, MUTE, GRID, SURF = '#0b0b0b', '#52514e', '#7a7975', '#e6e4df', '#fcfcfb'
P = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': GRID, 'axes.linewidth': 1, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2, 'text.color': INK,
                 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'legend.frameon': False})
def tidy(ax):
    ax.grid(True, axis='y', color=GRID, linewidth=1, linestyle='-'); ax.set_axisbelow(True); ax.tick_params(length=0)
# ---------- F1: intensity forecasts from the Saturday 6 pm run vs reality ----------
best = {t: v for t, _, _, v, _ in D['best']}
import datetime as dt
T0 = dt.datetime(2026, 10, 11, 0)
act = [((dt.datetime.strptime(t, '%Y-%m-%dT%H:%MZ') - T0).total_seconds() / 3600, v) for t, _, _, v, _ in D['best'] if dt.datetime.strptime(t, '%Y-%m-%dT%H:%MZ') >= T0]
act.append((21, 115))   # advisory 18 position
fig, axs = plt.subplots(1, 2, figsize=(7.4, 4.3), sharey=True)
for ax, title, series in [(axs[0], 'Hurricane-track guidance', [('NHC official', D['intens']['OFCL'], P[0]), ('Google DeepMind cyclone model (AI)', D['intens']['GDMN'], P[4]), ('HAFS-A', D['intens']['HFSA'], P[1]), ('HAFS-B', D['intens']['HFSB'], P[3])]),
                           (axs[1], 'Gridded global models', [('ECMWF IFS', {h: v[0] for h, v in D['grid']['ifs_oper'].items()}, P[0]), ('GFS', {h: v[0] for h, v in D['grid']['gfs'].items()}, P[1]), ('ECMWF AIFS (AI)', {h: v[0] for h, v in D['grid']['aifs_single'].items()}, P[2])])]:
    for y, lab in [(34, 'tropical storm'), (64, 'cat. 1'), (96, 'cat. 3'), (113, 'cat. 4')]:
        ax.axhline(y, color=GRID, linewidth=1); ax.text(48.5, y, lab, color=MUTE, fontsize=7, va='center', ha='left')
    if ax is axs[1]:   # AI archive band: FourCastNet, Pangu, GraphCast, Aurora, AIGFS
        hs = range(0, 49, 6); lo, hi = [], []
        for h in hs:
            vals = [D['grid'][k][str(h)][0] for k in ('fourcastnet', 'pangu', 'graphcast', 'aurora', 'aigfs') if str(h) in D['grid'][k] and D['grid'][k][str(h)][0] is not None]
            lo.append(min(vals) if vals else math.nan); hi.append(max(vals) if vals else math.nan)
        ax.fill_between(list(hs), lo, hi, color=P[4], alpha=0.18, linewidth=0); ax.plot(list(hs), [(a + b) / 2 for a, b in zip(lo, hi)], color=P[4], linewidth=2, label='Five AI models: range and middle\n(FourCastNet, Pangu, GraphCast, Aurora; AIGFS)')
    for lab, d, col in series:
        xs = sorted(int(k) for k in d); ys = [d[str(k)] if str(k) in d else d[k] for k in xs]
        ax.plot(xs, ys, color=col, linewidth=2, solid_joinstyle='round', solid_capstyle='round', label=lab); ax.plot(xs[-1], ys[-1], 'o', color=col, markersize=5, markeredgecolor=SURF, markeredgewidth=1.5)
    ax.plot([a[0] for a in act], [a[1] for a in act], color=INK, linewidth=3, label='What happened (NHC best track + advisory 18)'); ax.plot(21, 115, '*', color=INK, markersize=11, markeredgecolor=SURF)
    ax.set_xlim(0, 48); ax.set_ylim(0, 150); ax.set_xticks(range(0, 49, 12)); ax.set_xticklabels(['Sat\n6 pm', 'Sun\n6 am', 'Sun\n6 pm', 'Mon\n6 am', 'Mon\n6 pm'], fontsize=7.5); ax.set_title(title, loc='left', fontsize=10, color=INK, fontweight='bold'); tidy(ax)
    ax.legend(loc='upper left', bbox_to_anchor=(-0.02, -0.16), fontsize=6.8, handlelength=1.6, borderaxespad=0)
axs[0].set_ylabel('Max sustained wind (kt)'); fig.suptitle('Intensity forecasts from the Saturday 6 pm runs versus what Simon did', x=0.01, ha='left', fontsize=11, fontweight='bold')
fig.text(0.01, 0.005, 'Star: 3 pm Sunday, 115 kt (advisory 18). Gridded models: strongest 10-m wind within 2° of their own low.\nThe four NOAA/CIRA-archive models and NOAA’s AIGFS are all run from GFS analyses.', color=MUTE, fontsize=6.5)
fig.tight_layout(rect=(0, 0.04, 1, 0.95)); fig.savefig(S + '/report/f1_intensity.png', dpi=220); plt.close(fig)
# ---------- F2: position error by lead, every model ----------
rows = [m for m in VF['models'] if m['score'] is not None]
fig, ax = plt.subplots(figsize=(7.4, 7.0))
names = [m['name'][1] + (' ‡' if m['n'] < 1 else '') for m in rows]; ys = list(range(len(rows)))[::-1]
for k, (key, col, mk, lab) in enumerate([('h12', P[0], 'o', '12 h'), ('h24', P[1], 's', '24 h'), ('h36', P[2], '^', '36 h')]):
    xs = [m[key] if m[key] is not None else math.nan for m in rows]; ax.scatter(xs, [y + (k - 1) * 0.0 for y in ys], color=col, marker=mk, s=34, zorder=3, label=lab, edgecolors=SURF, linewidths=1)
for m, y in zip(rows, ys):
    vals = [m[k] for k in ('h12', 'h24', 'h36') if m[k] is not None]; ax.plot([min(vals), max(vals)], [y, y], color=GRID, linewidth=1.2, zorder=1)
    ax.plot(m['score'], y, '|', color=INK, markersize=11, markeredgewidth=1.6, zorder=4)
ax.set_yticks(ys); ax.set_yticklabels(names, fontsize=8); ax.set_xlabel('Mean position error (km), forecasts made in the last 48 h'); ax.set_xlim(0, 300); tidy(ax); ax.grid(True, axis='x', color=GRID); ax.grid(False, axis='y')
ax.legend(loc='upper right', fontsize=8, title='lead time', title_fontsize=8); ax.set_title('Position error by lead time, all models (black tick: 12–36 h mean)', loc='left', fontsize=10, fontweight='bold')
fig.text(0.01, 0.005, '‡ no 36-h verification available (fewer runs in the window), so the mean covers 12–24 h only and is not comparable. Each point averages 1–3 forecasts.', color=MUTE, fontsize=6.5)
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(S + '/report/f2_track_error.png', dpi=220); plt.close(fig)
# ---------- F3: NHC's own odds for Vallarta, advisory by advisory ----------
hist = [(n, iss, pv) for n, iss, pv in D['pv_hist'] if int(n) >= 10 and pv]
fig, ax = plt.subplots(figsize=(7.4, 3.2))
def lab(n, iss):
    t = dt.datetime.strptime(iss.strip(), '%b %d %H%MZ').replace(year=2026) - dt.timedelta(hours=6); h = t.hour % 12 or 12
    return f"#{n}\n{t.strftime('%a')} {h} {'am' if t.hour < 12 else 'pm'}"
xs = list(range(len(hist))); labs = [lab(n, iss.title()) for n, iss, _ in hist]
for key, col, lb in [('34', P[0], 'tropical-storm force (≥ 63 km/h)'), ('50', P[1], '≥ 93 km/h (50 kt)'), ('64', P[2], 'hurricane force (≥ 119 km/h)')]:
    ys = [pv.get(key, 0) for _, _, pv in hist]; ax.plot(xs, ys, color=col, linewidth=2, marker='o', markersize=5, markeredgecolor=SURF, markeredgewidth=1.2, label=lb)
    ax.text(xs[-1] + 0.18, {'34': 30, '50': 21, '64': 12}[key], {'34': f"TS force: {ys[-1]}%", '50': '50 kt: under 3%', '64': 'hurricane: under 1%'}[key], color=INK2, fontsize=7.2, va='center')
    if key == '34': ax.text(xs[-1] + 0.18, 39, 'advisory 18', color=INK, fontsize=7.2, va='center', fontweight='bold')
ax.set_xticks(xs); ax.set_xticklabels(labs, fontsize=7); ax.set_ylim(0, 100); ax.set_ylabel('Chance for Puerto Vallarta (%)'); tidy(ax); ax.legend(loc='upper left', fontsize=7.5)
ax.set_title("The NHC's own odds for Puerto Vallarta, advisory by advisory", loc='left', fontsize=10, fontweight='bold')
ax.set_xlabel('Advisory number and issue time, Vallarta time (Friday 9 to Sunday 11 October)', fontsize=8); ax.set_xlim(-0.4, len(xs) + 1.0)
fig.tight_layout(); fig.savefig(S + '/report/f3_pv_odds.png', dpi=220); plt.close(fig)
# ---------- F4: how uncertain is the next 48 h? ----------
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={'width_ratios': [1.25, 1]})
ax = axs[0]; hs = [c['h'] for c in CS['consensus']]; sp = [c['spread_km'] for c in CS['consensus']]
ax.fill_between(hs, 0, sp, color=P[0], alpha=0.12, linewidth=0); ax.plot(hs, sp, color=P[0], linewidth=2); ax.plot(hs[-1], sp[-1], 'o', color=P[0], markersize=5, markeredgecolor=SURF)
ax.text(hs[-1] - 1, sp[-1] + 6, f"{sp[-1]} km", ha='right', color=INK2, fontsize=8)
ax.set_xticks(range(0, 49, 12)); ax.set_xticklabels(['Sun noon', 'Mon midnight', 'Mon noon', 'Tue midnight', 'Tue noon'], fontsize=7); ax.set_ylabel('Weighted RMS spread of member positions (km)', fontsize=8); ax.set_ylim(0, 110); tidy(ax)
ax.set_title('Spread of the skill-weighted consensus\ngrows with lead time', loc='left', fontsize=9.5, fontweight='bold')
ax = axs[1]; ens = [('GEFS\n(20 trackable of 31)', 11, 20, 100), ('ECMWF ENS\n(51 members)', D['ens_members']['ecmwf']['within100'], D['ens_members']['ecmwf']['n'], D['ens_members']['ecmwf']['median']), ('ECMWF AIFS ens.\n(51 members, AI)', 43, 51, 57)]
vals = [w / n * 100 for _, w, n, _ in ens]; bars = ax.bar(range(3), vals, width=0.5, color=[P[0], P[0], P[4]], linewidth=0)
for b in bars: b.set_capstyle('round')
for i, (lab, w, n, med) in enumerate(ens): ax.text(i, vals[i] + 2, f"{w} of {n}\nmedian {med} km", ha='center', fontsize=7.5, color=INK2)
ax.set_xticks(range(3)); ax.set_xticklabels([e[0] for e in ens], fontsize=7); ax.set_ylim(0, 110); ax.set_xlim(-0.6, 2.6); ax.set_ylabel('Members within 100 km (%)'); tidy(ax)
ax.set_title('Sat 6 pm ensembles: members within\n100 km of the real center, 3 pm Sunday', loc='left', fontsize=9.5, fontweight='bold')
fig.tight_layout(); fig.savefig(S + '/report/f4_uncertainty.png', dpi=220); plt.close(fig)
print('charts ok')
