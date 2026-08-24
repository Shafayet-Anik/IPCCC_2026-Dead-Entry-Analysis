#!/usr/bin/env python3
"""
Fig 12: O3 IPC gain (%) vs. L2 TLB MPKI for all 24 workloads (log x-axis).
Two-regime structure:
  MPKI < 1  → not TLB-sensitive: all cluster near 0% gain (gray triangles)
  MPKI >= 1 → TLB-sensitive: Class A (red circles, large gains)
                              Class B (blue squares, near-zero gain)
All 8 TLB-sensitive workloads are labeled by name.
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
DATA  = ROOT / "data" / "burstness_o3gain.csv"
FIGS  = ROOT / "figs"
OUT   = FIGS / "fig12_o3gain_vs_mpki.pdf"

COLOR  = {'A': '#d62728', 'B': '#1f77b4', 'neutral': '#aaaaaa'}
MARKER = {'A': 'o',       'B': 's',       'neutral': '^'}
SIZE   = {'A': 90,        'B': 65,        'neutral': 30}
ALPHA  = {'A': 0.95,      'B': 0.88,      'neutral': 0.5}

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
    'backprop-rodinia-3.1_65536':                  'backprop',
    'bfs-rodinia-3.1_graph65536':                  'bfs',
    'gaussian-rodinia-3.1_s256':                   'gaussian',
    'hybridsort-rodinia-3.1_500000':               'hybridsort',
    'lud-rodinia-3.1_s2048v':                      'lud',
    'pagerank':                                    'pagerank',
    'parboil-bfs_NY':                              'p-bfs',
    'parboil-mri-gridding_small':                  'mri-grid',
    'parboil-sad':                                 'sad',
    'parboil-sgemm_medium':                        'sgemm',
    'parboil-spmv':                                'spmv',
    'polybench-2mm_NI512_NJ512_NK512_NL512':       '2mm',
    'polybench-fdtd2d_NX2048_NY2048_T25':          'fdtd2d',
    'polybench-gramschmidt':                       'gramschmidt',
    'streamcluster-rodinia-3.1_3_6_16_65536_65536_1000': 'streamcluster',
}

# Label offsets for TLB-sensitive workloads (dx, dy in points)
LABEL_OFFSET = {
    'atax':        ( 5,  4),
    'mvt':         ( 5, -9),
    'bicg':        ( 5,  4),
    'gesummv':     ( 5,  4),
    'nw':          ( 5,  4),
    'dmr':         ( 5, -9),
    'kmeans':      ( 5,  4),
    'sssp':        ( 5,  4),
    'mst':         (-38, 4),
}

rows = []
with open(DATA) as f:
    for r in csv.DictReader(f):
        mpki = float(r['mpki']) if r['mpki'] else 0
        gain = float(r['o3_gain_pct']) if r['o3_gain_pct'] else 0
        rows.append({
            'wl': r['workload'], 'cls': r['class'],
            'mpki': max(mpki, 0.005),   # floor for log scale
            'gain': gain,
            'name': NAME_MAP.get(r['workload'], r['workload'][:8]),
        })

fig, ax = plt.subplots(figsize=figsize(6.5, 3.8))

# Draw neutral first (background), then B, then A (foreground)
for cls in ('neutral', 'B', 'A'):
    pts = [r for r in rows if r['cls'] == cls]
    xs  = [r['mpki'] for r in pts]
    ys  = [r['gain']  for r in pts]
    lbl = {'A': 'Class A (2 workloads)',
           'B': 'Class B (7 workloads)',
           'neutral': 'Not TLB-sensitive (15 workloads)'}[cls]
    ax.scatter(xs, ys, c=COLOR[cls], marker=MARKER[cls], s=SIZE[cls],
               label=lbl, zorder=3 if cls == 'A' else (2 if cls == 'B' else 1),
               edgecolors='white' if cls != 'neutral' else 'none',
               linewidths=0.6, alpha=ALPHA[cls])

# Label all 8 TLB-sensitive workloads
for r in rows:
    if r['cls'] in ('A', 'B'):
        dx, dy = LABEL_OFFSET.get(r['name'], (5, 4))
        ax.annotate(r['name'], (r['mpki'], r['gain']),
                    xytext=(dx, dy), textcoords='offset points',
                    fontsize=7, color=COLOR[r['cls']],
                    fontweight='bold' if r['cls'] == 'A' else 'normal')

# MPKI = 1 threshold
ax.axvline(1.0, color='#555', linestyle='--', linewidth=1.0, alpha=0.6, zorder=0)
ax.text(1.08, 65, 'MPKI = 1\n(TLB-sensitive\nthreshold)', fontsize=6.5,
        color='#555', va='top', alpha=0.8)

ax.axhline(0, color='black', linewidth=0.5, alpha=0.4, zorder=0)

ax.set_xscale('log')
ax.set_xlim(left=0.003)
ax.set_xlabel('L2 TLB MPKI (log scale)', fontsize=9)
ax.set_ylabel('O3 IPC Gain (%)', fontsize=9)
ax.grid(axis='both', linestyle=':', linewidth=0.4, alpha=0.4)
ax.tick_params(labelsize=8)

ax.legend(fontsize=7.5, loc='upper left', framealpha=0.9)

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
