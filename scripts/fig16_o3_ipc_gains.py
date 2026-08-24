#!/usr/bin/env python3
"""
Fig 16: O3 IPC gain (%) for all 24 workloads, sorted descending.
Replaces Table 3. Colors: Class A (red) = TLB-bottlenecked interference-driven; Class B (blue) = capacity-driven; gray = not TLB-bottlenecked.
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
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "figs"
OUT  = FIGS / "fig16_o3_ipc_gains.pdf"

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
gains  = [r['gain'] for r in rows]
colors = [COLOR[r['cls']] for r in rows]
x = np.arange(len(rows))

fig, ax = plt.subplots(figsize=figsize(10, 3.2))

bars = ax.bar(x, gains, color=colors, edgecolor='none', width=0.75)

ax.axhline(0, color='black', linewidth=0.7, linestyle='--', alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=55, ha='right', fontsize=6.5)
ax.set_ylabel('O3 IPC Gain over Baseline (%)', fontsize=9)
ax.set_title('O3 IPC Gain per Workload', fontsize=9)
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.6)
ax.tick_params(axis='y', labelsize=8)

# Annotate the two significant bars
for i, r in enumerate(rows):
    if abs(r['gain']) > 3.0:
        ax.text(i, r['gain'] + (1.5 if r['gain'] > 0 else -2.5),
                f"{r['gain']:+.0f}%", ha='center', va='bottom',
                fontsize=7, color=COLOR[r['cls']], fontweight='bold')

patches = [
    mpatches.Patch(color=COLOR['A'],       label='TLB-sensitive: Class A (2 workloads)'),
    mpatches.Patch(color=COLOR['B'],       label='TLB-sensitive: Class B (7 workloads)'),
    mpatches.Patch(color=COLOR['neutral'], label='Not TLB-sensitive (15 workloads)'),
]
ax.legend(handles=patches, fontsize=7.5, loc='upper right', ncol=3)

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
