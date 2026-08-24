#!/usr/bin/env python3
"""
Fig 9: O3 IPC gain (%) for all 24 workloads, sorted descending.
Colors: Class A (red) = TLB-sensitive, interference-driven; Class B (blue) = capacity-driven; gray = not TLB-sensitive.
Demonstrates both Class-A gains and graceful near-zero degradation everywhere else.
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
import matplotlib.transforms as mtransforms
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "figs"
OUT  = FIGS / "fig09_o3_ipc_gains.pdf"

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

COLOR = {'A': '#d62728', 'B': '#1f77b4', 'neutral': '#7f7f7f'}

def pct_to_axis(pct):
    """
    Piecewise map % gain to axis units with equal tick spacing:
      [-10%, 0%] -> [-1, 0],  [0%, 10%] -> [0, 1],  [10%, 100%] -> [1, 2].
    Compresses 10%–100% like 0%–10% (unlike true log10(speedup)).
    """
    if pct <= 0:
        return max(pct / 10.0, -1.0)
    if pct <= 10:
        return pct / 10.0
    return 1.0 + min((pct - 10.0) / 90.0, 1.0)

def fmt_bar_val(g):
    if abs(g) < 0.05:
        return '0'
    if abs(g) < 10:
        return f'{g:+.1f}'
    return f'{g:+.0f}'

# Evenly spaced tick positions; labels are true % values (no '+' on positives)
Y_TICK_PCT = [-10, 0, 10, 100]
Y_TICK_POS = [-1.0, 0.0, 1.0, 2.0]
Y_TICK_LBL = ['-10', '0', '10', '100']

rows = []
with open(ROOT / "data" / "ipc_comparison.csv") as f:
    for r in csv.DictReader(f):
        base = float(r['R1-burst']) if r['R1-burst'] else None
        o3   = float(r['R2-clean']) if r['R2-clean'] else None
        if base and o3 and base > 0:
            gain_pct = (o3 - base) / base * 100.0
        else:
            gain_pct = 0.0
        rows.append({
            'wl':   r['workload'],
            'cls':  r['class'],
            'gain': gain_pct,
        })

# Sort descending by gain
rows.sort(key=lambda r: r['gain'], reverse=True)

labels = [NAME_MAP.get(r['wl'], r['wl']) for r in rows]
heights = [pct_to_axis(r['gain']) for r in rows]
colors = [COLOR[r['cls']] for r in rows]
x = np.arange(len(rows))

n = len(rows)
fig, ax = plt.subplots(figsize=figsize(7.8, 3.9))

ax.bar(x, heights, color=colors, edgecolor='none', width=0.82)
ax.set_xlim(-0.62, n - 0.38)
ax.margins(x=0)

ax.axhline(0, color='black', linewidth=0.7, linestyle='--', alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=10.5)
ylab = ax.set_ylabel(
    'DEPOT IPC Gain over Baseline (%)\n(nonlinear scale, dashed = 0%)', fontsize=14)
ax.yaxis.set_label_coords(-0.075, 0.42)
# Tighter letter spacing; clip off so ')' is not cut at figure edge
ylab.set_clip_on(False)
ylab.set_transform(mtransforms.Affine2D().scale(0.84, 1.0) + ylab.get_transform())
ax.set_ylim(-1.08, 2.12)
ax.set_yticks(Y_TICK_POS, Y_TICK_LBL)
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.6, which='major')
ax.tick_params(axis='both', labelsize=12)

# % label on every bar (true linear gain, not axis units)
for i, r in enumerate(rows):
    g = r['gain']
    h = heights[i]
    pad = 0.05 if abs(h) > 0.08 else 0.035
    if g >= 0:
        y, va = (h + pad, 'bottom') if g > 0.05 else (pad, 'bottom')
    else:
        y, va = (h - pad, 'top')
    fs = 9.5 if abs(g) >= 3 else 8.5
    fw = 'bold' if abs(g) >= 3 else 'normal'
    ax.text(i, y, fmt_bar_val(g), ha='center', va=va,
            fontsize=fs, color=COLOR[r['cls']], fontweight=fw)

patches = [
    mpatches.Patch(color=COLOR['A'],       label='TLB-sensitive: Class A (2 workloads)'),
    mpatches.Patch(color=COLOR['B'],       label='TLB-sensitive: Class B (7 workloads)'),
    mpatches.Patch(color=COLOR['neutral'], label='Not TLB-sensitive (15 workloads)'),
]
ax.legend(handles=patches, fontsize=12, loc='upper right', ncol=1,
          bbox_to_anchor=(1.0, 0.97), framealpha=0.92, borderaxespad=0.4)

plt.tight_layout()
fig.subplots_adjust(left=0.12)
plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.08)
print(f"Saved: {OUT}")
