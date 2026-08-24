#!/usr/bin/env python3
"""
Fig 7: DE ratio with 4KB vs 2MB pages, grouped by class.
2MB pages collapse Class B DE ratio (reach was the cause);
Class A persists (MSHR interference, not reach).
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
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "de_ratio_comparison.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig07_de_ratio_4kb_vs_2mb.pdf"

COLOR = {'A': '#d62728', 'B': '#1f77b4', 'neutral': '#7f7f7f'}
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
        de4  = float(row['de_ratio_4kb']) * 100 if row['de_ratio_4kb'] else None
        de2  = float(row['de_ratio_2mb']) * 100 if row['de_ratio_2mb'] else None
        rows.append({'wl': row['workload'], 'cls': row['class'], 'de4': de4, 'de2': de2})

# Sort: Class A first, then B, then neutral — within each group by 4KB DE ratio desc
order = {'A': 0, 'B': 1, 'neutral': 2}
rows.sort(key=lambda r: (order[r['cls']], -(r['de4'] or 0)))

labels = [NAME_MAP.get(r['wl'], r['wl']) for r in rows]
x = np.arange(len(rows))
w = 0.38

fig, ax = plt.subplots(figsize=figsize(10, 3.4))

for i, r in enumerate(rows):
    base_color = COLOR[r['cls']]
    de4 = r['de4'] or 0
    de2 = r['de2'] if r['de2'] is not None else 0
    ax.bar(x[i] - w/2, de4, w, color=base_color, alpha=0.9, label='4KB' if i==0 else '')
    ax.bar(x[i] + w/2, de2, w, color=base_color, alpha=0.35, hatch='//',
           edgecolor=base_color, label='2MB' if i==0 else '')

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7.5)
ax.set_ylabel('L2 TLB Dead-Entry Ratio (%)', fontsize=9)
ax.set_ylim(0, 108)
ax.axhline(90, color='black', linestyle='--', linewidth=0.6, alpha=0.4)
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.6)
ax.tick_params(axis='y', labelsize=8)

# Dividers between class groups
bounds = [0]
prev = rows[0]['cls']
for i, r in enumerate(rows[1:], 1):
    if r['cls'] != prev:
        bounds.append(i - 0.5)
        ax.axvline(i - 0.5, color='black', linestyle=':', linewidth=1.0, alpha=0.5)
        prev = r['cls']

# Class labels at top
# Find midpoints
grp_bounds = [0]
prev = rows[0]['cls']
grps = [(0, rows[0]['cls'])]
for i, r in enumerate(rows[1:], 1):
    if r['cls'] != prev:
        grps[-1] = (*grps[-1][:2], i)
        grps.append((i, r['cls']))
        prev = r['cls']
grps[-1] = (*grps[-1][:2], len(rows))

for (start, cls, end) in grps:
    mid = (start + end - 1) / 2
    ax.text(mid, 104, {'A': 'Class A', 'B': 'Class B', 'neutral': 'Not TLB-btl.'}[cls],
            ha='center', va='center', fontsize=7.5, style='italic')

# Legend for bar style
p4 = mpatches.Patch(color='#555555', alpha=0.9, label='4KB pages')
p2 = mpatches.Patch(color='#555555', alpha=0.35, hatch='//', label='2MB pages')
ax.legend(handles=[p4, p2], fontsize=8, loc='lower left')

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
