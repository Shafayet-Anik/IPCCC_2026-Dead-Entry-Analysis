#!/usr/bin/env python3
"""
Fig 10: IPC — Baseline vs DEPOT vs LatPC vs LatPC+DEPOT,
all 24 workloads grouped by class. LatPC+DEPOT composition is the headline result.
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
OUT  = FIGS / "fig10_ipc_comparison.pdf"

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
GROUP_SP = 0.68  # spacing between workload groups (<1 = tighter)
x = np.arange(n) * GROUP_SP
w = 0.13

def get_ipc(row, key):
    v = row.get(key, '')
    return float(v) if v else None

# Piecewise y: 0–1× = 16% of axis; 1–5, 5–10, 10–15× = 28% each
Y_BREAKS = [0, 1, 5, 10, 15]
Y_SEG_FRAC = [0.16, 0.28, 0.28, 0.28]
Y_TICK_VALS = Y_BREAKS
_cum = [0.0]
for f in Y_SEG_FRAC:
    _cum.append(_cum[-1] + f)
Y_TICK_POS = _cum

def speedup_to_axis(s):
    s = max(0.0, min(float(s), Y_BREAKS[-1]))
    for i, frac in enumerate(Y_SEG_FRAC):
        lo, hi = Y_BREAKS[i], Y_BREAKS[i + 1]
        if s <= hi:
            t = (s - lo) / (hi - lo) if hi > lo else 0.0
            return Y_TICK_POS[i] + t * frac
    return 1.0

# Paper palette: Class A red, Class B blue, neutral gray; light green for LatPC
C_RED         = '#d62728'
C_BLUE        = '#1f77b4'
C_GRAY        = '#7f7f7f'
C_GREEN_LIGHT = '#98df8a'

# Configs: Baseline, DEPOT, LatPC, LatPC+DEPOT
CONFIGS = [
    ('R1-burst',   'Baseline',      C_GRAY),
    ('R2-clean',   'DEPOT',         C_BLUE),
    ('R9',         'LatPC',         C_GREEN_LIGHT),
    ('R10',        'LatPC+DEPOT',   C_RED),
]

fig, ax = plt.subplots(figsize=figsize(10.5, 3.9))

for i_cfg, (cfg, label, color) in enumerate(CONFIGS):
    speedups = []
    for r in rows:
        base = get_ipc(r, 'R1-burst')
        val  = get_ipc(r, cfg)
        sp = val / base if (base and val and base > 0) else 1.0
        speedups.append(sp)
    offset = (i_cfg - 1.5) * w
    for xi, sp in enumerate(speedups):
        h = speedup_to_axis(sp)
        ax.bar(x[xi] + offset, h, w, color=color, edgecolor='none',
               alpha=0.88,
               label=label if xi == 0 else '_nolegend_')

ax.axhline(speedup_to_axis(1.0), color='black', linewidth=0.7,
           linestyle='--', alpha=0.6)
Y_TOP_PAD = 0.08  # headroom above 15× tick for class region labels
ax.set_ylim(0, 1.0 + Y_TOP_PAD)
ax.set_yticks(Y_TICK_POS, [str(t) for t in Y_TICK_VALS])

# Mark class dividers
prev_cls = rows[0]['class']
for i, r in enumerate(rows[1:], 1):
    if r['class'] != prev_cls:
        ax.axvline((i - 0.5) * GROUP_SP, color='black', linestyle=':',
                   linewidth=0.8, alpha=0.4)
        prev_cls = r['class']

# Class region labels (one label per contiguous class block)
grps = []
start = 0
for i in range(1, n):
    if rows[i]['class'] != rows[i - 1]['class']:
        grps.append((start, i, rows[i - 1]['class']))
        start = i
grps.append((start, n, rows[-1]['class']))

for start, end, cls in grps:
    mid_x = (x[start] + x[end - 1]) / 2
    cls_label = {'A': 'Class A', 'B': 'Class B', 'neutral': 'Not TLB-sensitive'}[cls]
    ax.text(mid_x, 1.0 + Y_TOP_PAD * 0.72, cls_label,
            ha='center', va='top', fontsize=13.5, style='italic', alpha=0.7)

x_pad = 1.5 * w + 0.12
ax.set_xlim(-x_pad, x[-1] + x_pad)
ax.margins(x=0)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=13.5)
ax.set_ylabel('Speedup over Baseline (x)', fontsize=17)
ax.yaxis.set_label_coords(-0.04, 0.42)
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.6)
ax.tick_params(axis='both', labelsize=15)
ax.legend(fontsize=15, loc='upper right', ncol=1, framealpha=0.92,
          bbox_to_anchor=(1.0, 0.90))

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.06)
print(f"Saved: {OUT}")
