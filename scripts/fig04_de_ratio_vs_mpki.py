#!/usr/bin/env python3
"""
Fig 4: DE ratio vs. L2 MPKI scatter plot, colored by class.
"""
import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fig_common import figsize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator
import numpy as np

def _arrow_props(cls):
    return dict(arrowstyle='->', color=COLOR[cls], lw=0.75, shrinkA=0, shrinkB=4)
# Label x follows point MPKI (left→right); markers use true CSV coordinates.
# Label at same MPKI as point, offset downward (DE%); stagger if points are close.
ANNOT_BELOW_Y_OFF = {
    'polybench-gesummv_N2024':           20,
    'polybench-atax_NX2048_NY2048':       12,
    'kmeans-rodinia-3.1_28k_4x_features': 14,
    'polybench-bicg_NX2048_NY2048':       22,
}
# log-MPKI multiplier: label left of the point (same DE height); <1 = left
ANNOT_SIDE_XMUL = {
    'polybench-mvt_N2048': (0.65, 'right'),
}

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "workload_stats.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig04_de_ratio_vs_mpki.pdf"

COLOR  = {'A': '#d62728', 'B': '#1f77b4', 'neutral': '#7f7f7f'}
MARKER = {'A': 'o', 'B': 's', 'neutral': '^'}
MARKER_SIZE = {'A': 64, 'B': 80, 'neutral': 80}  # circles slightly smaller than square/triangle

# Short name map (same as fig03)
NAME_MAP = {
    'backprop-rodinia-3.1_65536':                   'backprop',
    'bfs-rodinia-3.1_graph65536':                   'bfs',
    'gaussian-rodinia-3.1_s256':                    'gaussian',
    'hybridsort-rodinia-3.1_500000':                'hybridsort',
    'kmeans-rodinia-3.1_28k_4x_features':           'kmeans',
    'lonestar-dmr_data_25k_10':                     'dmr',
    'lonestar-mst_2d_2e20_sym_gr':                  'mst',
    'lonestar-sssp_data_r4_2e20_gr':                'sssp',
    'lud-rodinia-3.1_s2048v':                       'lud',
    'nw-rodinia-3.1_2048_10':                       'nw',
    'pagerank':                                     'pagerank',
    'parboil-bfs_NY':                               'p-bfs',
    'parboil-mri-gridding_small':                   'mri-grid',
    'parboil-sad':                                  'sad',
    'parboil-sgemm_medium':                         'sgemm',
    'parboil-spmv':                                 'spmv',
    'polybench-2mm_NI512_NJ512_NK512_NL512':        '2mm',
    'polybench-atax_NX2048_NY2048':                 'atax',
    'polybench-bicg_NX2048_NY2048':                 'bicg',
    'polybench-fdtd2d_NX2048_NY2048_T25':           'fdtd2d',
    'polybench-gesummv_N2024':                      'gesummv',
    'polybench-gramschmidt':                        'gramschmidt',
    'polybench-mvt_N2048':                          'mvt',
    'streamcluster-rodinia-3.1_3_6_16_65536_65536_1000': 'streamcluster',
}

rows = []
with open(DATA) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not row['mpki']:
            continue
        # Workloads with no L2 TLB misses have undefined DE ratio → treat as 0%
        rows.append({
            'wl':   row['workload'],
            'de':   float(row['de_ratio']) * 100 if row['de_ratio'] else 0.0,
            'mpki': float(row['mpki']),
            'cls':  row['class'],
        })

fig, ax = plt.subplots(figsize=figsize(7.5, 3.8))
mpkis = [r['mpki'] for r in rows]
xmin, xmax = min(mpkis), max(mpkis)
_x_floor = xmin * 0.5
# p>1 on log10(x): 10^-3→10^-2 is tight; each later decade gets wider (vs. equal log spacing).
LOG_X_EXP = 1.45


def _x_forward(x):
    u = np.log10(np.maximum(np.asarray(x, float), _x_floor * 0.1))
    u0 = np.log10(_x_floor)
    return np.power(np.maximum(u - u0, 0.0), LOG_X_EXP)


def _x_inverse(x):
    u0 = np.log10(_x_floor)
    return np.power(10.0, u0 + np.power(np.maximum(np.asarray(x, float), 0.0), 1.0 / LOG_X_EXP))


def _decade_ticks(lo, hi):
    ticks = []
    v = np.power(10.0, np.floor(np.log10(lo)))
    while v <= hi * 1.05:
        if v >= lo * 0.8:
            ticks.append(v)
        v *= 10.0
    return ticks


def _decade_tick_label(t):
    exp = int(round(np.log10(t)))
    return rf'$10^{{{exp}}}$'

by_wl = {r['wl']: r for r in rows}

for r in rows:
    ax.scatter(r['mpki'], r['de'], color=COLOR[r['cls']],
               marker=MARKER[r['cls']], s=MARKER_SIZE[r['cls']], zorder=3,
               edgecolors='white', linewidths=0.75, alpha=0.85)

for wl, y_off in ANNOT_BELOW_Y_OFF.items():
    r = by_wl[wl]
    cls = r['cls']
    ax.annotate(NAME_MAP[wl], xy=(r['mpki'], r['de']),
                xytext=(r['mpki'], r['de'] - y_off),
                textcoords='data', fontsize=14.5, ha='center', va='top',
                color=COLOR[cls], arrowprops=_arrow_props(cls))

for wl, (xmul, ha) in ANNOT_SIDE_XMUL.items():
    r = by_wl[wl]
    cls = r['cls']
    ax.annotate(NAME_MAP[wl], xy=(r['mpki'], r['de']),
                xytext=(r['mpki'] * xmul, r['de']),
                textcoords='data', fontsize=14.5, ha=ha, va='center',
                color=COLOR[cls], arrowprops=_arrow_props(cls))

ax.set_xlabel('L2 TLB MPKI', fontsize=14)
ax.set_ylabel('L2 TLB Dead-Entry Ratio (%)', fontsize=14)
ax.set_xscale('function', functions=(_x_forward, _x_inverse))
ax.set_xlim(_x_floor, xmax * 1.4)
_xticks = _decade_ticks(_x_floor, xmax * 1.4)
ax.set_xticks(_xticks)
ax.set_xticklabels([_decade_tick_label(t) for t in _xticks])
ax.set_ylim(0, 105)
ax.yaxis.set_major_locator(MultipleLocator(25))
ax.grid(linestyle=':', linewidth=0.5, alpha=0.6)
ax.tick_params(labelsize=13)

patches = [
    mpatches.Patch(color=COLOR['A'],       label='Class A'),
    mpatches.Patch(color=COLOR['B'],       label='Class B'),
    mpatches.Patch(color=COLOR['neutral'], label='Not TLB-sensitive'),
]
ax.legend(handles=patches, fontsize=12, loc='lower right')

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
