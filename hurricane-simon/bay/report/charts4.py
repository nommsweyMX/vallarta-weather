import sys, datetime as dt
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
S = sys.argv[1]
INK, INK2, MUTE, GRID, SURF = '#0b0b0b', '#52514e', '#7a7975', '#e6e4df', '#fcfcfb'
P = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': GRID, 'axes.linewidth': 1, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2, 'text.color': INK,
                 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'legend.frameon': False})
def tidy(ax): ax.grid(True, axis='y', color=GRID, linewidth=1); ax.set_axisbelow(True); ax.tick_params(length=0)
T = lambda s: dt.datetime.strptime(s, '%Y-%m-%d %H:%M')   # CST
# ---------- F12: the headline wind for the Amapas building, product by product, against the outcome ----------
# (issue time CST, label, sustained lo, sustained hi, gust lo, gust hi, NHC TS-force probability at that advisory, kind)
prods = [
    ('2026-10-10 03:00', 'Hour-by-hour maps\nadv. 12 · Sat 3 am', 144, 144, 185, 185, 73, 'num'),
    ('2026-10-10 17:36', 'Model snapshot\nadv. 14 · Sat 5:36 pm', 69, 108, None, None, 63, 'num'),
    ('2026-10-10 20:30', 'Risk video\nadv. 15 · Sat 8:30 pm', 63, 93, None, None, 75, 'cat'),
    ('2026-10-10 21:00', 'Hour-by-hour table\nadv. 15 · Sat 9 pm', None, None, None, None, 75, 'cat2'),
    ('2026-10-11 09:10', 'Building set\nadv. 17 · Sun 9:10 am', 60, 60, 83, 83, 56, 'num'),
    ('2026-10-11 13:00', 'Corrected set\nadv. 17 · Sun 1 pm', 60, 60, 83, 83, 56, 'num'),
    ('2026-10-11 15:00', 'Building set\nadv. 18 · Sun 3 pm', 43, 43, 61, 61, 8, 'num'),
    ('2026-10-12 08:10', 'Building set\nadv. 20A · Mon 8:10 am', 34, 34, 47, 47, 0, 'num'),
]
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(7.6, 5.2), gridspec_kw={'height_ratios': [3.2, 1]}, sharex=True)
x0, x1 = T('2026-10-09 22:00'), T('2026-10-12 12:00')
ax.axvspan(T('2026-10-11 23:00'), T('2026-10-12 01:00'), color=GRID, alpha=.6, linewidth=0); ax.text(T('2026-10-12 00:00'), 104, 'closest\npass\n120 km', ha='center', va='top', fontsize=6.4, color=INK2)
for cat, lab in ((63, 'tropical-storm force'), (93, '50 kt'), (119, 'hurricane force')):
    ax.axhline(cat, color=GRID, linewidth=1, linestyle=(0, (3, 2))); ax.text(1.005, cat, lab, transform=ax.get_yaxis_transform(), ha='left', va='center', fontsize=6.4, color=MUTE, clip_on=False)
ax.axhline(7, color=INK, linewidth=2); ax.text(x0 + dt.timedelta(hours=1), 11, 'what the airport measured: 7 km/h, no gusts', fontsize=7, color=INK, va='bottom')
for k, (t, lab, slo, shi, glo, ghi, pp, kind) in enumerate(prods):
    x = T(t); num = str(k + 1)
    if kind == 'num':
        if slo == shi: ax.plot([x], [slo], 'o', color=P[0], markersize=6, zorder=5)
        else: ax.plot([x, x], [slo, shi], '-', color=P[0], linewidth=5, solid_capstyle='round', zorder=5)
        if glo is not None: ax.plot([x], [glo], 's', color=P[1], markersize=5.5, zorder=5); ax.plot([x, x], [slo if slo == shi else shi, glo], ':', color=P[1], linewidth=1)
        ax.text(x, (ghi or shi) + 6, num, ha='center', va='bottom', fontsize=8, fontweight='bold', color=INK)
    elif kind == 'cat':
        ax.plot([x, x], [slo, shi], '-', color=P[6], linewidth=5, alpha=.55, solid_capstyle='round', zorder=4); ax.text(x, shi + 6, num, ha='center', va='bottom', fontsize=8, fontweight='bold', color=INK)
    else:
        ax.plot([x], [128], 'v', color=P[7], markersize=7, zorder=5); ax.text(x, 134, num, ha='center', va='bottom', fontsize=8, fontweight='bold', color=INK)
ax.plot([], [], 'o', color=P[0], label='sustained wind given (bar: a range was given)'); ax.plot([], [], 's', color=P[1], label='gust given'); ax.plot([], [], 's', color=P[6], alpha=.55, markersize=8, label='category only'); ax.plot([], [], 'v', color=P[7], label='class only (no number)')
ax.legend(loc='lower left', bbox_to_anchor=(0.0, 0.1), fontsize=6.6, ncol=1); ax.set_ylim(0, 200)
key = ['1  Hour-by-hour maps · adv. 12 · Sat 3 am · Calle Cafeto house, Amapas', '2  Model snapshot · adv. 14 · Sat 5:36 pm · Francisca Rodríguez ref., 7th floor', '3  Risk video · adv. 15 · Sat 8:30 pm · Amapas 8th floor (tropical-storm force)', '4  Hour-by-hour table · adv. 15 · Sat 9 pm · El Pitillal (top class "no salir")', '5  Building set · adv. 17 · Sun 9:10 am · Amapas 8th floor', '6  Corrected set · adv. 17 · Sun 1 pm · Amapas 8th floor', '7  Building set · adv. 18 · Sun 3 pm · Amapas 8th floor', '8  Building set · adv. 20A · built Mon 8:10 am · Amapas 8th floor']
ax.text(0.995, 0.975, '\n'.join(key), transform=ax.transAxes, ha='right', va='top', fontsize=6.3, color=INK2, linespacing=1.35, bbox=dict(boxstyle='round,pad=0.4', facecolor='#f3f2ee', edgecolor='none')); ax.set_ylabel("km/h at each product's own reference address", fontsize=8); tidy(ax)
ax.set_title('Every product for the city, by issue time: the headline wind it gave', loc='left', fontsize=9.4, fontweight='bold')
ax2.step([T(t) for t, *_ in prods] + [x1], [pp for *_, pp, _ in prods] + [prods[-1][6]], where='post', color=P[2], linewidth=2)
prev = None
for t, lab, slo, shi, glo, ghi, pp, kind in prods:
    ax2.plot([T(t)], [pp], 'o', color=P[2], markersize=4)
    if prev is not None and prev[1] == pp and (T(t) - prev[0]).total_seconds() < 5 * 3600: prev = (T(t), pp); continue
    txt = ('%d%%' % pp) if pp else 'under 3%'; drop = prev is not None and pp < prev[1]
    if drop and pp > 20: ax2.text(T(t) + dt.timedelta(hours=2), pp - 4, txt, ha='left', va='top', fontsize=7, color=INK2)
    elif drop: ax2.text(T(t) + dt.timedelta(hours=2), pp + 7, txt, ha='left', va='bottom', fontsize=7, color=INK2)
    else: ax2.text(T(t), pp + 7, txt, ha='center', va='bottom', fontsize=7, color=INK2)
    prev = (T(t), pp)
ax2.set_ylim(0, 100); ax2.set_ylabel('NHC odds of\nTS-force wind (%)', fontsize=7.5); tidy(ax2)
ax2.set_title('NHC probability of tropical-storm-force wind in Puerto Vallarta at the advisory each product used', loc='left', fontsize=8.4, fontweight='bold')
ax2.set_xlim(x0, x1); ticks = [T('2026-10-10 00:00'), T('2026-10-10 12:00'), T('2026-10-11 00:00'), T('2026-10-11 12:00'), T('2026-10-12 00:00'), T('2026-10-12 12:00')]
ax2.set_xticks(ticks); ax2.set_xticklabels(['Sat 10 Oct\nmidnight', 'Sat\nnoon', 'Sun 11 Oct\nmidnight', 'Sun\nnoon', 'Mon 12 Oct\nmidnight', 'Mon\nnoon'], fontsize=7)
fig.text(0.01, 0.012, 'Sources: the products themselves (Appendix A0 and A1–A4). Product 1 gave 90 mph (144 km/h) sustained and 115 mph (185 km/h) gusts for the Calle Cafeto house with the center 9 km south;\nproduct 2 gave a 7th-floor "height-only" range at the Francisca Rodríguez reference (its city-wide NHC median bracket was 63–93 km/h); products 3 and 4 gave categories, not numbers\n(plotted at the tropical-storm band and as a marker). Products 5–8 are plotted at the time each set was built. Airport: METAR MMPR, Sunday 3 pm to Monday 8 am.', fontsize=6.4, color=MUTE, va='bottom')
fig.tight_layout(rect=[0, 0.085, 1, 1]); fig.savefig(S + '/report/f12_products_wind.png', dpi=220); plt.close(fig); print('charts4 ok')
