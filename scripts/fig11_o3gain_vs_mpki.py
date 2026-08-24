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
OUT   = FIGS / "fig11_o3gain_vs_mpki.pdf"

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

LABEL_DY_BELOW = -19
LABEL_DY_ABOVE = 17
# Above marker (positive dy, va='bottom')
LABEL_ABOVE = {'sssp', 'dmr', 'mvt'}
# Extra distance below / above marker
LABEL_DY_FAR_BELOW = {'bicg': -28, 'kmeans': -28}
LABEL_DY_FAR_ABOVE = {'sssp': 26}

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
    lbl = {'A': 'Class A', 'B': 'Class B', 'neutral': 'Not TLB-sensitive'}[cls]
    ax.scatter(xs, ys, c=COLOR[cls], marker=MARKER[cls], s=SIZE[cls],
               label=lbl, zorder=3 if cls == 'A' else (2 if cls == 'B' else 1),
               edgecolors='white' if cls != 'neutral' else 'none',
               linewidths=0.6, alpha=ALPHA[cls])

# Label all TLB-sensitive workloads (below marker; exceptions above)
for r in rows:
    if r['cls'] in ('A', 'B'):
        if r['name'] in LABEL_DY_FAR_ABOVE:
            dy, va = LABEL_DY_FAR_ABOVE[r['name']], 'bottom'
        elif r['name'] in LABEL_ABOVE:
            dy, va = LABEL_DY_ABOVE, 'bottom'
        elif r['name'] in LABEL_DY_FAR_BELOW:
            dy, va = LABEL_DY_FAR_BELOW[r['name']], 'top'
        else:
            dy, va = LABEL_DY_BELOW, 'top'
        ax.annotate(
            r['name'], (r['mpki'], r['gain']),
            xytext=(0, dy), textcoords='offset points',
            ha='center', va=va,
            fontsize=11, color=COLOR[r['cls']],
            arrowprops=dict(arrowstyle='->', color=COLOR[r['cls']],
                            lw=0.9, shrinkA=0, shrinkB=4, mutation_scale=9),
        )

# MPKI = 1 threshold
ax.axvline(1.0, color='#555', linestyle='--', linewidth=1.0, alpha=0.6, zorder=0)
ax.text(1.08, 73, 'MPKI = 1\n(TLB-sensitive threshold)', fontsize=10.5,
        color='#555', va='top', alpha=0.8)

ax.axhline(0, color='black', linewidth=0.5, alpha=0.4, zorder=0)

ax.set_yticks(np.arange(-15, 91, 15))
ax.set_ylim(-22, 78)

ax.set_xscale('log')
ax.set_xlim(left=0.003)
ax.set_xlabel('L2 TLB MPKI (log scale)', fontsize=12)
ax.set_ylabel('DEPOT IPC Gain (%)', fontsize=12)
ax.yaxis.set_label_coords(-0.06, 0.48)
ax.grid(axis='both', linestyle=':', linewidth=0.4, alpha=0.4)
ax.tick_params(labelsize=11)

ax.legend(fontsize=11.5, loc='upper left', framealpha=0.9,
          handletextpad=0.35, handlelength=1.2, labelspacing=0.45)

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
