#!/usr/bin/env python3
"""
Fig 7: 2MB page speedup — normalized IPC improvement (2MB / 4KB baseline)
for all TLB-sensitive workloads (Class A and B).
Shows that expanding TLB reach eliminates the bottleneck for Class B workloads;
validates reach-limited root cause.
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
import matplotlib.ticker
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA  = ROOT / "data" / "ipc_2mb.csv"
FIGS  = ROOT / "figs"
OUT   = FIGS / "fig07_2mb_ipc_speedup.pdf"

COLOR = {'A': '#d62728', 'B': '#1f77b4'}

NAME_MAP = {
    'polybench-atax_NX2048_NY2048':                 'atax',
    'polybench-mvt_N2048':                          'mvt',
    'polybench-bicg_NX2048_NY2048':                 'bicg',
    'polybench-gesummv_N2024':                      'gesummv',
    'nw-rodinia-3.1_2048_10':                       'nw',
    'lonestar-dmr_data_25k_10':                     'dmr',
    'kmeans-rodinia-3.1_28k_4x_features':           'kmeans',
    'lonestar-sssp_data_r4_2e20_gr':                'sssp',
    'lonestar-mst_2d_2e20_sym_gr':                  'mst',
}

rows = []
with open(DATA) as f:
    for r in csv.DictReader(f):
        cls  = r['class']
        ipc4 = float(r['ipc_4kb_base']) if r['ipc_4kb_base'] else None
        ipc2 = float(r['ipc_2mb_base']) if r['ipc_2mb_base'] else None
        if ipc4 and ipc2 and cls in ('A', 'B'):
            rows.append({
                'wl':      r['workload'],
                'cls':     cls,
                'speedup': ipc2 / ipc4,
            })

# Sort: Class A first, then B; within each class sort by speedup descending
order = {'A': 0, 'B': 1}
rows.sort(key=lambda r: (order[r['cls']], -r['speedup']))

labels = [NAME_MAP.get(r['wl'], r['wl']) for r in rows]
n = len(rows)
x = np.arange(n)
w = 0.55

fig, ax = plt.subplots(figsize=figsize(6.5, 3.2))

bars = ax.bar(x, [r['speedup'] for r in rows], w,
              color=[COLOR[r['cls']] for r in rows],
              edgecolor='none', alpha=0.88)

max_speedup = max(r['speedup'] for r in rows)

# 1× reference line
ax.axhline(1.0, color='black', linewidth=0.8, linestyle='--', alpha=0.6, label='1× (4 KB baseline)')

# Class divider
n_A = sum(1 for r in rows if r['cls'] == 'A')
if 0 < n_A < n:
    ax.axvline(n_A - 0.5, color='black', linestyle=':', linewidth=0.9, alpha=0.5)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=22, ha='right', fontsize=11)
ax.set_ylabel('Speedup over 4 KB Baseline\n(log scale)', fontsize=12)
ax.yaxis.set_label_coords(-0.08, 0.42)
ax.set_yscale('log')
ax.set_ylim(bottom=0.5, top=max_speedup * 2.4)

# Annotate speedup value above each bar (use multiplicative offset for log scale)
for i, r in enumerate(rows):
    ax.text(i, r['speedup'] * 1.08,
            f"{r['speedup']:.0f}×",
            ha='center', va='bottom', fontsize=9.5, fontweight='bold',
            color=COLOR[r['cls']])
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda v, _: f'{v:.0f}×' if v >= 1 else f'{v:.1f}×'))
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.6)
ax.tick_params(axis='y', labelsize=11)

# Class labels (slightly below original top placement)
ylim = ax.get_ylim()
ypos = ylim[1] * 0.75
if n_A > 0:
    ax.text((n_A - 1) / 2, ypos, 'Class A',
            ha='center', va='top', fontsize=11, style='italic',
            alpha=0.75, color='black')
if n_A < n:
    ax.text(n_A + (n - n_A - 1) / 2, ypos, 'Class B',
            ha='center', va='top', fontsize=11, style='italic',
            alpha=0.75, color='black')

patches = [
    mpatches.Patch(color='#d62728', label='Class A (interference-driven)'),
    mpatches.Patch(color='#1f77b4', label='Class B (capacity-driven)'),
]
fig.subplots_adjust(bottom=0.30, top=0.92)
fig.canvas.draw()
fig.legend(handles=patches, loc='upper center', ncol=2, fontsize=10.5,
           bbox_to_anchor=(0.5, 0.14), bbox_transform=fig.transFigure,
           frameon=False, columnspacing=0.8, handletextpad=0.4)

plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.03)
print(f"Saved: {OUT}")
