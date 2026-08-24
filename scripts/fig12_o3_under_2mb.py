#!/usr/bin/env python3
"""
Fig 13: Three-config IPC comparison for all 8 TLB-sensitive workloads.
Configs: 4KB baseline | 4KB+O3 | 2MB baseline (all normalized to 4KB baseline = 1×).
Key insight:
  Class B: O3 ≈ 1× (no help from mechanism), 2MB = 2–128× (reach is the cure).
  Class A: O3 = 1.04–1.72× (mechanism helps), 2MB = 39–63× (reach helps even more).
  Message: O3 addresses the Class A interference bottleneck at 4KB;
           the Class B bottleneck is reach — only larger pages or TLB help.
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
DATA = ROOT / "data" / "ipc_2mb.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig12_o3_under_2mb.pdf"

NAME_MAP = {
    'polybench-atax_NX2048_NY2048':               'atax',
    'polybench-mvt_N2048':                         'mvt',
    'polybench-bicg_NX2048_NY2048':               'bicg',
    'polybench-gesummv_N2024':                     'gesummv',
    'nw-rodinia-3.1_2048_10':                      'nw',
    'lonestar-dmr_data_25k_10':                    'dmr',
    'kmeans-rodinia-3.1_28k_4x_features':          'kmeans',
    'lonestar-sssp_data_r4_2e20_gr':               'sssp',
    'lonestar-mst_2d_2e20_sym_gr':                 'mst',
}
COLOR_A   = '#d62728'
COLOR_B   = '#1f77b4'
BAR_BASE  = '#aaaaaa'
BAR_O3_A  = '#d62728'
BAR_O3_B  = '#1f77b4'
BAR_2MB_A = '#ff9896'   # light red
BAR_2MB_B = '#aec7e8'   # light blue

rows = []
with open(DATA) as f:
    for r in csv.DictReader(f):
        if r['workload'] not in NAME_MAP:
            continue
        b4  = float(r['ipc_4kb_base']) if r['ipc_4kb_base'] else None
        o3  = float(r['ipc_4kb_o3'])   if r['ipc_4kb_o3']   else None
        b2  = float(r['ipc_2mb_base']) if r['ipc_2mb_base'] else None
        if not (b4 and o3 and b2):
            continue
        rows.append({
            'wl':  r['workload'],
            'cls': r['class'],
            'sp_o3':  o3  / b4,
            'sp_2mb': b2  / b4,
        })

# Sort: Class A first, then Class B by 2MB speedup desc
order = {'A': 0, 'B': 1}
rows.sort(key=lambda r: (order.get(r['cls'], 2), -r['sp_2mb']))

labels = [NAME_MAP[r['wl']] for r in rows]
n = len(rows)
x = np.arange(n)
w = 0.27

fig, ax = plt.subplots(figsize=figsize(8, 3.6))

ax.axhline(1.0, color='black', linewidth=0.8, linestyle='--', alpha=0.6, zorder=2)

# O3 and 2MB speedup bars
o3_colors  = [BAR_O3_A  if r['cls'] == 'A' else BAR_O3_B  for r in rows]
sp2_colors = [BAR_2MB_A if r['cls'] == 'A' else BAR_2MB_B for r in rows]

ax.bar(x - w, [1.0]*n, w, color=BAR_BASE, edgecolor='none', alpha=0.7)
ax.bar(x,     [r['sp_o3']  for r in rows], w, color=o3_colors,  edgecolor='none', alpha=0.9)
ax.bar(x + w, [r['sp_2mb'] for r in rows], w, color=sp2_colors, edgecolor='none', alpha=0.85)

# Annotate 2MB speedup on top
for i, r in enumerate(rows):
    sp = r['sp_2mb']
    ax.text(i + w, sp + 0.5, f"{sp:.0f}×",
            ha='center', va='bottom', fontsize=7, fontweight='bold',
            color=COLOR_A if r['cls'] == 'A' else COLOR_B)

# Class divider
n_A = sum(1 for r in rows if r['cls'] == 'A')
if 0 < n_A < n:
    y_top = ax.get_ylim()[1]
    ax.axvline(n_A - 0.5, color='black', linestyle=':', linewidth=0.9, alpha=0.5)
    ax.text((n_A - 1)/2, y_top * 0.6,
            'Class A', ha='center', fontsize=8.5, style='italic',
            color=COLOR_A, alpha=0.8)
    ax.text(n_A + (n - n_A - 1)/2, y_top * 0.6,
            'Class B', ha='center', fontsize=8.5, style='italic',
            color=COLOR_B, alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=8.5)
ax.set_ylabel('Speedup over 4 KB Baseline', fontsize=9)
ax.set_ylim(bottom=0)
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.5)
ax.tick_params(axis='y', labelsize=8)

patches = [
    mpatches.Patch(color=BAR_BASE,  label='4 KB Baseline (1×)'),
    mpatches.Patch(color='#d62728', alpha=0.9, label='4 KB + O3 (Class A)'),
    mpatches.Patch(color='#1f77b4', alpha=0.9, label='4 KB + O3 (Class B)'),
    mpatches.Patch(color=BAR_2MB_A, label='2 MB Baseline (Class A)'),
    mpatches.Patch(color=BAR_2MB_B, label='2 MB Baseline (Class B)'),
]
ax.legend(handles=patches, fontsize=7, loc='upper right', ncol=2)

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
