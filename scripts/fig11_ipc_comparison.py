#!/usr/bin/env python3
"""
Fig 11: IPC — Baseline vs O3 vs LatPC vs LatPC+O3,
all 24 workloads grouped by class. LatPC+O3 composition is the headline result.
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
DATA  = ROOT / "data" / "ipc_comparison.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig11_ipc_comparison.pdf"

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
        rows.append(row)

# Sort: Class A first, B second, neutral last; within group by baseline IPC desc
order = {'A': 0, 'B': 1, 'neutral': 2}
rows.sort(key=lambda r: (order.get(r['class'], 2),
                          -(float(r['R1-burst']) if r['R1-burst'] else 0)))

labels = [NAME_MAP.get(r['workload'], r['workload']) for r in rows]
n = len(rows)
x = np.arange(n)
w = 0.20

def get_ipc(row, key):
    v = row.get(key, '')
    return float(v) if v else None

# Configs: Baseline, O3, LatPC, LatPC+O3
CONFIGS = [
    ('R1-burst',   'Baseline',    '#7f7f7f'),
    ('R2-clean',   'O3',          '#2ca02c'),
    ('R9',         'LatPC',       '#ff7f0e'),
    ('R10',        'LatPC+O3 ★',  '#d62728'),
]

# Normalize IPC to baseline — show speedup.
# Missing R9/R10 values (runs still pending) are rendered as hatched gray bars
# so the figure structure is complete; regenerate once those CSVs are populated.
PENDING_COLOR  = '#cccccc'
PENDING_HATCH  = '//'

fig, ax = plt.subplots(figsize=figsize(12, 3.8))

for i_cfg, (cfg, label, color) in enumerate(CONFIGS):
    speedups  = []
    colors    = []
    hatches   = []
    for r in rows:
        base = get_ipc(r, 'R1-burst')
        val  = get_ipc(r, cfg)
        if base and val and base > 0:
            speedups.append(val / base)
            colors.append(color)
            hatches.append(None)
        else:
            # Data pending — placeholder bar at y=1.0 (baseline level)
            speedups.append(1.0)
            colors.append(PENDING_COLOR)
            hatches.append(PENDING_HATCH)
    offset = (i_cfg - 1.5) * w
    for xi, (sp, c, h) in enumerate(zip(speedups, colors, hatches)):
        ax.bar(x[xi] + offset, sp, w, color=c, edgecolor='#888888',
               linewidth=0.4, hatch=h, alpha=0.88 if h is None else 0.6,
               label=label if xi == 0 else '_nolegend_')

ax.axhline(1.0, color='black', linewidth=0.7, linestyle='--', alpha=0.6)

# Mark class dividers
prev_cls = rows[0]['class']
for i, r in enumerate(rows[1:], 1):
    if r['class'] != prev_cls:
        ax.axvline(i - 0.5, color='black', linestyle=':', linewidth=0.8, alpha=0.4)
        prev_cls = r['class']

# Class region labels
grps = []
prev = rows[0]['class']
start = 0
for i, r in enumerate(rows):
    if r['class'] != prev or i == len(rows)-1:
        end = i if r['class'] != prev else i+1
        grps.append((start, end, prev))
        start = i
        prev = r['class']
grps.append((start, len(rows), prev))

ymax = ax.get_ylim()[1]
for start, end, cls in grps:
    mid = (start + end - 1) / 2
    cls_label = {'A': 'Class A', 'B': 'Class B', 'neutral': 'Not TLB-sensitive'}[cls]
    ax.text(mid, ax.get_ylim()[1] * 0.97, cls_label,
            ha='center', va='top', fontsize=7.5, style='italic', alpha=0.7)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7.5)
ax.set_ylabel('Speedup over Baseline', fontsize=9)
ax.set_ylim(bottom=0)
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.6)
ax.tick_params(axis='y', labelsize=8)
ax.legend(fontsize=8, loc='upper right', ncol=4)

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
