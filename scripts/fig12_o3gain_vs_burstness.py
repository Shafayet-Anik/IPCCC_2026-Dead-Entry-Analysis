#!/usr/bin/env python3
"""
Fig 12: O3 IPC gain vs. burstness (peak MSHRDeadSlots) scatter plot.
Burstness, not DE ratio, predicts O3 effectiveness.
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
DATA = ROOT / "data" / "burstness_o3gain.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig12_o3gain_vs_burstness.pdf"

COLOR  = {'A': '#d62728', 'B': '#1f77b4', 'neutral': '#7f7f7f'}
MARKER = {'A': 'o', 'B': 's', 'neutral': '^'}
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
        if row['burstness_peak'] and row['o3_gain_pct']:
            rows.append({
                'wl': row['workload'],
                'cls': row['class'],
                'burst': float(row['burstness_peak']),
                'gain': float(row['o3_gain_pct']),
                'mpki': float(row['mpki']) if row['mpki'] else 0,
            })

# Annotate notable points
ANNOTATE = {'polybench-atax_NX2048_NY2048', 'polybench-bicg_NX2048_NY2048',
            'polybench-gesummv_N2024', 'polybench-mvt_N2048'}

fig, ax = plt.subplots(figsize=figsize(5.5, 4.0))

# Plot all workloads
for r in rows:
    size = max(20, min(150, r['mpki'] * 1.5))  # scale marker by MPKI
    ax.scatter(r['burst'], r['gain'],
               color=COLOR[r['cls']], marker=MARKER[r['cls']],
               s=size, zorder=3, edgecolors='none', alpha=0.85)
    if r['wl'] in ANNOTATE:
        sn = NAME_MAP.get(r['wl'], r['wl'])
        ax.annotate(sn, (r['burst'], r['gain']),
                    fontsize=7.5, xytext=(5, 2), textcoords='offset points')

ax.axhline(0, color='black', linestyle='--', linewidth=0.7, alpha=0.5)
ax.set_xlabel('Burstness (Peak MSHR Dead-Entry Slots)', fontsize=9)
ax.set_ylabel('O3 IPC Gain (%)', fontsize=9)
ax.grid(linestyle=':', linewidth=0.4, alpha=0.6)
ax.tick_params(labelsize=8)

patches = [
    mpatches.Patch(color=COLOR['A'],       label='Class A'),
    mpatches.Patch(color=COLOR['B'],       label='Class B'),
    mpatches.Patch(color=COLOR['neutral'], label='Not TLB-bottlenecked'),
]
ax.legend(handles=patches, fontsize=8, loc='upper left')

# Note: marker size ∝ MPKI
ax.text(0.98, 0.02, 'Marker area ∝ MPKI', transform=ax.transAxes,
        fontsize=6.5, ha='right', va='bottom', color='gray', style='italic')

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
