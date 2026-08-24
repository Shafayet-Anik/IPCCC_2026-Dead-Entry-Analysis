#!/usr/bin/env python3
"""
Fig 14: Parameter sensitivity — protect-cycles sweep (R12) and Bloom-bits sweep (R13).
Both sweeps are flat, demonstrating DEPOT robustness to parameter choice.
"""
import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fig_common import figsize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "figs"
OUT  = FIGS / "fig14_param_sensitivity.pdf"

# Only plot TLB-sensitive workloads (MPKI > 5 from workload_stats)
SENSITIVE_WLS = set()
with open(ROOT / "data" / "workload_stats.csv") as f:
    for row in csv.DictReader(f):
        if row['mpki'] and float(row['mpki']) > 5:
            SENSITIVE_WLS.add(row['workload'])

# Short names
NAME_MAP = {
    'polybench-atax_NX2048_NY2048':  'atax',
    'polybench-bicg_NX2048_NY2048':  'bicg',
    'polybench-gesummv_N2024':       'gesummv',
    'polybench-mvt_N2048':           'mvt',
    'kmeans-rodinia-3.1_28k_4x_features': 'kmeans',
    'nw-rodinia-3.1_2048_10':        'nw',
    'lonestar-dmr_data_25k_10':      'dmr',
    'lonestar-sssp_data_r4_2e20_gr': 'sssp',
    'lonestar-mst_2d_2e20_sym_gr':   'mst',
}

# Load protect-cycles sweep
pc_data = defaultdict(dict)  # wl -> {cycles -> gain}
with open(ROOT / "data" / "param_sweep_protect_cycles.csv") as f:
    for row in csv.DictReader(f):
        wl = row['workload']
        if wl in SENSITIVE_WLS:
            pc_data[wl][int(row['protect_cycles'])] = float(row['gain_pct'])

# Load bloom-bits sweep
bb_data = defaultdict(dict)
with open(ROOT / "data" / "param_sweep_bloom_bits.csv") as f:
    for row in csv.DictReader(f):
        wl = row['workload']
        if wl in SENSITIVE_WLS:
            bb_data[wl][int(row['bloom_bits'])] = float(row['gain_pct'])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize(8, 3.5))

# --- Left: protect-cycles sweep ---
cycles_vals = sorted(next(iter(pc_data.values())).keys()) if pc_data else []
x_cycles = np.arange(len(cycles_vals))
cmap = matplotlib.colormaps.get_cmap('tab10').resampled(max(len(pc_data), 1))

for i, (wl, d) in enumerate(sorted(pc_data.items())):
    gains = [d.get(c, 0) for c in cycles_vals]
    sn = NAME_MAP.get(wl, wl.split('-')[-1][:8])
    ax1.plot(x_cycles, gains, marker='o', markersize=4, linewidth=1.2,
             color=cmap(i), label=sn)

ax1.set_xticks(x_cycles)
ax1.set_xticklabels([f"{c//1000}K" if c < 1_000_000 else f"{c//1_000_000}M"
                     for c in cycles_vals], fontsize=8.5)
ax1.set_xlabel('Protection Window W (cycles)', fontsize=9)
ax1.set_ylabel('DEPOT IPC Gain over Baseline (%)', fontsize=9)
ax1.set_title('Protect-Cycles Sweep', fontsize=9)
ax1.axhline(0, color='black', linewidth=0.6, linestyle='--')
ax1.grid(linestyle=':', linewidth=0.4, alpha=0.6)
ax1.legend(fontsize=6.5, ncol=2, loc='lower right')
ax1.tick_params(labelsize=8)

# --- Right: bloom-bits sweep ---
bits_vals = sorted(next(iter(bb_data.values())).keys()) if bb_data else []
x_bits = np.arange(len(bits_vals))

for i, (wl, d) in enumerate(sorted(bb_data.items())):
    gains = [d.get(b, 0) for b in bits_vals]
    sn = NAME_MAP.get(wl, wl.split('-')[-1][:8])
    ax2.plot(x_bits, gains, marker='s', markersize=4, linewidth=1.2,
             color=cmap(i), label=sn)

ax2.set_xticks(x_bits)
ax2.set_xticklabels([str(b) for b in bits_vals], fontsize=8.5)
ax2.set_xlabel('Bloom Filter Size (bits)', fontsize=9)
ax2.set_ylabel('DEPOT IPC Gain over Baseline (%)', fontsize=9)
ax2.set_title('Bloom Filter Size Sweep', fontsize=9)
ax2.axhline(0, color='black', linewidth=0.6, linestyle='--')
ax2.grid(linestyle=':', linewidth=0.4, alpha=0.6)
ax2.legend(fontsize=6.5, ncol=2, loc='lower right')
ax2.tick_params(labelsize=8)

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
