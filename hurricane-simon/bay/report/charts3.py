import sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
S = sys.argv[1]
INK, INK2, MUTE, GRID, SURF = '#0b0b0b', '#52514e', '#7a7975', '#e6e4df', '#fcfcfb'
P = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': GRID, 'axes.linewidth': 1, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2, 'text.color': INK,
                 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'legend.frameon': False})
def tidy(ax, axis='y'): ax.grid(True, axis=axis, color=GRID, linewidth=1); ax.set_axisbelow(True); ax.tick_params(length=0)

# ---------- F10: rapid intensification on Mexico's Pacific coast and the official forecast errors (NHC tropical cyclone reports) ----------
# (name, year, kt gained, hours, note on where, mean official intensity error 24 h, 48 h [None if the report gives no number])
storms = [('Kenna', 2002, 100, 42, 'landfall San Blas, Nayarit, 120 kt', 27, 52),
          ('Patricia', 2015, 105, 24, 'landfall Jalisco, 130 kt (peak 185)', 35.0, 57.8),
          ('Roslyn', 2022, 55, 24, 'landfall Nayarit, 105 kt', 9.6, 21.9),
          ('Lidia', 2023, 45, 18, 'landfall 35 n mi SW of Vallarta, 120 kt', 6.4, 7.2),
          ('Otis', 2023, 90, 21, 'landfall Acapulco, 140 kt', 29.5, 51.7),
          ('John', 2024, 65, 24, 'landfall Guerrero, 105 kt', 23.6, 23.0),
          ('Erick', 2025, 55, 24, 'landfall Oaxaca, 110 kt (RI forecast)', 13.1, 25.0),
          ('Simon', 2026, 70, 48, 'no landfall yet; peak 135 kt off Jalisco', None, None)]
fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.7), gridspec_kw={'width_ratios': [1.15, 1]})
ax = axs[0]; xs = range(len(storms))
cols = [P[7] if s[3] <= 24 else P[1] if s[3] <= 42 else P[3] for s in storms]
ax.bar(xs, [s[2] for s in storms], color=cols, width=0.62, linewidth=0)
for i, s in enumerate(storms):
    ax.text(i, s[2] + 2, f'in {s[3]} h', ha='center', va='bottom', fontsize=6.8, color=INK2)
ax.axhline(30, color=INK, linewidth=1, linestyle=(0, (3, 2)), label='rapid-intensification threshold (30 kt in 24 h)'); ax.legend(fontsize=6.6, loc='upper right')
ax.set_xticks(list(xs)); ax.set_xticklabels([f'{s[0]}\n{s[1]}' for s in storms], fontsize=7); ax.set_ylabel('Largest intensification the NHC report records (kt)', fontsize=8); ax.set_ylim(0, 125); tidy(ax)
ax.set_title('Eight storms, one pattern: fast\nstrengthening near Mexico\'s Pacific coast', loc='left', fontsize=9.5, fontweight='bold')
fig.text(0.01, 0.015, 'Left: red = gained in 24 h or less; orange = in 42 h (Kenna); yellow = in 48 h (Simon, operational advisory values; its report is not yet written).\nRight: mean absolute error of the NHC official intensity forecast at 24 h and 48 h over each storm\'s life, from the verification table of its report\n(Tables 4a/5a); one Saffir-Simpson category is roughly 20 kt. Source: NHC tropical cyclone reports for the seven earlier storms; NHC advisories for Simon.', fontsize=6.2, color=MUTE, va='bottom')
ax = axs[1]; w = 0.36
have = [s for s in storms if s[5] is not None]
ax.bar([i - w / 2 for i in range(len(have))], [s[5] for s in have], width=w - 0.04, color=P[0], linewidth=0, label='24-h forecast')
ax.bar([i + w / 2 for i in range(len(have))], [s[6] for s in have], width=w - 0.04, color=P[6], linewidth=0, label='48-h forecast')
for i, s in enumerate(have):
    ax.text(i - w / 2, s[5] + 1, f'{s[5]:.0f}', ha='center', va='bottom', fontsize=6.2, color=INK2); ax.text(i + w / 2, s[6] + 1, f'{s[6]:.0f}', ha='center', va='bottom', fontsize=6.2, color=INK2)
ax.set_xticks(range(len(have))); ax.set_xticklabels([f'{s[0]}\n{s[1]}' for s in have], fontsize=7); ax.set_ylabel('Mean NHC official intensity error (kt)', fontsize=8); ax.set_ylim(0, 70); tidy(ax); ax.legend(fontsize=7, loc='upper right'); ax.tick_params(axis='x', labelsize=6.6)
ax.set_title('The official intensity forecast error\nin each storm (NHC verification tables)', loc='left', fontsize=9.5, fontweight='bold')
fig.tight_layout(rect=[0, 0.1, 1, 1]); fig.savefig(S + '/report/f10_ri_record.png', dpi=220); plt.close(fig)

# ---------- F11: the observing network behind the forecast ----------
fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.9), gridspec_kw={'width_ratios': [1.3, 1]})
ax = axs[0]
rows = [('Weather radars', (4, 13), (6, 8)), ('Automatic weather\nstations (EMA)', (160, 189), (138, 189)), ('Automatic synoptic\nstations (ESIME/ESMA)', (65, 98), (65, 97)), ('Observatories', (75, 77), (76, 76)), ('Radiosonde stations', (14, 15), (15, 15))]
ys = list(range(len(rows)))[::-1]; h = 0.34
for y, (lab, a, b) in zip(ys, rows):
    for dy, (op, tot), col, lab2 in ((h / 2 + 0.02, a, P[1], 'Aug 2019 (Conagua inventory)'), (-h / 2 - 0.02, b, P[0], '2024 (federal audit, ASF)')):
        ax.barh(y + dy, 100, height=h, color=GRID, linewidth=0); ax.barh(y + dy, 100 * op / tot, height=h, color=col, linewidth=0, label=lab2 if y == ys[0] else None)
        ax.text(101, y + dy, f'{op} of {tot}', va='center', fontsize=7, color=INK2)
ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=7.4); ax.set_xlim(0, 125); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(['0', '25', '50', '75', '100%']); tidy(ax, 'x'); hh, ll = ax.get_legend_handles_labels(); fig.legend(hh, ll, loc='lower left', bbox_to_anchor=(0.17, 0.16), ncol=2, fontsize=6.8)
ax.set_title('Share of the national observing\nnetwork (SMN) in operation', loc='left', fontsize=9.5, fontweight='bold')
fig.text(0.01, 0.015, 'Left: the radar totals differ between the inventories (13 radars in 2019, 8 radar stations in the 2024 audit). No SMN radar in Jalisco or Nayarit was found;\nthe nearest known is Cuyutlán (Colima, about 225 km, listed as stand-by); the university radar in Guadalajara detects storms reliably to about 120 km.\nRight: 53rd Weather Reconnaissance Squadron, 2025 season. The US operations plan requires routine aircraft fixes for Atlantic and Gulf storms;\nfor the eastern Pacific it says missions "may be tasked when necessary".', fontsize=6.2, color=MUTE, va='bottom')
ax = axs[1]
cats = ['Atlantic\nstorms', 'E. Pacific\nstorms', 'Hours,\nall basins', 'Hours,\nMelissa\nalone']
vals = [9, 2, 927.9, 170]
ax2 = ax.twinx()
ax.bar([0, 1], vals[:2], color=[P[0], P[1]], width=0.6, linewidth=0); ax2.bar([2, 3], vals[2:], color=[P[0], P[6]], width=0.6, linewidth=0)
for i, v in enumerate(vals): (ax if i < 2 else ax2).text(i, v + (0.2 if i < 2 else 15), f'{v:g}', ha='center', va='bottom', fontsize=7.5, color=INK2)
ax.set_xticks(range(4)); ax.set_xticklabels(cats, fontsize=6.4); ax.set_ylim(0, 12); ax2.set_ylim(0, 1150); ax.set_ylabel('storms', fontsize=7.5); ax2.set_ylabel('hours', fontsize=7.5); ax2.spines['top'].set_visible(False); ax2.tick_params(length=0, labelsize=7); ax.tick_params(labelsize=7); tidy(ax)
ax.set_title('Where the US hurricane\naircraft went in 2025', loc='left', fontsize=9.5, fontweight='bold')
fig.subplots_adjust(left=0.17, right=0.93, top=0.86, bottom=0.3, wspace=0.6); fig.savefig(S + '/report/f11_observing.png', dpi=220); plt.close(fig)
print('charts3 ok')
