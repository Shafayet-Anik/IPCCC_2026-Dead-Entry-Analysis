#!/usr/bin/env python3
"""
Fig 3: L2 dead-entry ratio for all 24 workloads, sorted descending, colored by class.
"""
import csv, sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fig_common import figsize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties
import numpy as np

LEGEND_FP = FontProperties(size=15.5, stretch='condensed')

ROOT  = Path(__file__).resolve().parent.parent
DATA  = ROOT / "data" / "workload_stats.csv"
FIGS  = ROOT / "figs"
FIGS.mkdir(exist_ok=True)
OUT   = FIGS / "fig03_de_ratio_bars.pdf"

# Color scheme
COLOR = {'A': '#d62728', 'B': '#1f77b4', 'neutral': '#7f7f7f'}

def short_name(wl):
    """Convert full workload name to short label."""
    name_map = {
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
    return name_map.get(wl, wl.split('-')[-1][:10])

# Load data — all 24 workloads; workloads with no L2 TLB misses get de=0.0
rows = []
with open(DATA) as f:
    reader = csv.DictReader(f)
    for row in reader:
        de = row['de_ratio']
        rows.append({
            'wl':  row['workload'],
            'de':  float(de) if de else 0.0,   # 0 L2 misses → 0% DE ratio
            'cls': row['class'],
        })

# Sort descending by DE ratio
rows.sort(key=lambda r: -r['de'])

labels = [short_name(r['wl']) for r in rows]
vals   = [r['de'] * 100 for r in rows]
colors = [COLOR[r['cls']] for r in rows]

# inches; height sets vertical plot area (LaTeX scales width to \columnwidth)
FIGSIZE = figsize(10, 4.0)
fig, ax = plt.subplots(figsize=FIGSIZE)
x = np.arange(len(rows))

# Draw all bars
for i, r in enumerate(rows):
    ax.bar(x[i], vals[i], color=colors[i], edgecolor='none', width=0.75)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=14.5)
ax.set_ylabel('L2 TLB Dead-Entry\nRatio (%)', fontsize=16)
ax.yaxis.set_label_coords(-0.06, 0.46)
ax.set_ylim(0, 105)
ax.set_xlim(-0.6, len(rows) - 0.4)
ax.grid(axis='y', linestyle=':', linewidth=0.5, alpha=0.7)
ax.tick_params(axis='y', labelsize=15)

patches = [
    mpatches.Patch(color=COLOR['A'],       label='TLB-sensitive: Class A (interference, 2 workloads)'),
    mpatches.Patch(color=COLOR['B'],       label='TLB-sensitive: Class B (capacity, 7 workloads)'),
    mpatches.Patch(color=COLOR['neutral'], label='Not TLB-sensitive (15 workloads)'),
]
fig.subplots_adjust(bottom=0.48, top=0.95)
fig.canvas.draw()
pos = ax.get_position()
leg_cx = (pos.x0 + pos.x1) / 2
leg_y = pos.y0 - 0.28
fig.legend(handles=patches, loc='upper center', ncol=1,
           bbox_to_anchor=(leg_cx, leg_y), bbox_transform=fig.transFigure,
           prop=LEGEND_FP, columnspacing=0.5, handletextpad=0.35,
           labelspacing=0.35, frameon=False)

plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.06)
print(f"Saved: {OUT}")
