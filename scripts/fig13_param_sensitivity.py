#!/usr/bin/env python3
"""
Fig 13: Parameter sensitivity — protect-cycles sweep (R12) and Bloom-bits sweep (R13).
Both sweeps are flat, demonstrating O3 robustness to parameter choice.
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
OUT  = FIGS / "fig13_param_sensitivity.pdf"

# Only plot TLB-sensitive workloads (MPKI > 5 from workload_stats)
SENSITIVE_WLS = set()
with open(ROOT / "data" / "workload_stats.csv") as f:
    for row in csv.DictReader(f):
        if row['mpki'] and float(row['mpki']) >= 0.9:
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

X_SP = 1.30  # horizontal spacing between x tick positions


def _xlim(x_arr):
    if len(x_arr) == 0:
        return 0.5
    if len(x_arr) == 1:
        return (x_arr[0] - 0.35, x_arr[0] + 0.35)
    span = x_arr[-1] - x_arr[0]
    pad = max(0.04 * span, 0.08)
    return (x_arr[0] - pad, x_arr[-1] + pad)

all_gains = []
for d in pc_data.values():
    all_gains.extend(d.values())
for d in bb_data.values():
    all_gains.extend(d.values())
y_lo = min(all_gains) if all_gains else -10
y_hi = max(all_gains) if all_gains else 10
y_pad = 0.10 * (y_hi - y_lo)
Y_LIM = (int((y_lo - y_pad) // 10) * 10 - 5, int((y_hi + y_pad) // 10) * 10 + 15)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize(8.5, 4.2))

# --- Left: protect-cycles sweep ---
cycles_vals = sorted(next(iter(pc_data.values())).keys()) if pc_data else []
x_cycles = np.arange(len(cycles_vals)) * X_SP
cmap = matplotlib.colormaps.get_cmap('tab10').resampled(max(len(pc_data), 1))

for i, (wl, d) in enumerate(sorted(pc_data.items())):
    gains = [d.get(c, 0) for c in cycles_vals]
    sn = NAME_MAP.get(wl, wl.split('-')[-1][:8])
    ax1.plot(x_cycles, gains, marker='o', markersize=4, linewidth=1.2,
             color=cmap(i), label=sn)

ax1.set_xticks(x_cycles)
ax1.set_xticklabels([f"{c//1000}K" if c < 1_000_000 else f"{c//1_000_000}M"
                     for c in cycles_vals], fontsize=14.5)
ax1.set_xlabel('Protection Window W (cycles)', fontsize=15)
ax1.set_ylabel('DEPOT IPC Gain over Baseline (%)', fontsize=15, y=0.48)
ax1.set_title('Protect-Cycles Sweep', fontsize=15)
ax1.set_xlim(_xlim(x_cycles))
ax1.margins(x=0)
ax1.set_ylim(Y_LIM)
ax1.set_yticks(np.arange(Y_LIM[0], Y_LIM[1] + 1, 20))
ax1.axhline(0, color='black', linewidth=0.6, linestyle='--')
ax1.grid(linestyle=':', linewidth=0.4, alpha=0.6)
ax1.tick_params(labelsize=14)
ax1.margins(y=0)

# --- Right: bloom-bits sweep ---
bits_vals = sorted(next(iter(bb_data.values())).keys()) if bb_data else []
x_bits = np.arange(len(bits_vals)) * X_SP

for i, (wl, d) in enumerate(sorted(bb_data.items())):
    gains = [d.get(b, 0) for b in bits_vals]
    sn = NAME_MAP.get(wl, wl.split('-')[-1][:8])
    ax2.plot(x_bits, gains, marker='s', markersize=4, linewidth=1.2,
             color=cmap(i), label=sn)

ax2.set_xticks(x_bits)
ax2.set_xticklabels([str(b) for b in bits_vals], fontsize=14.5)
ax2.set_xlabel('Bloom Filter Size (bits)', fontsize=15)
ax2.set_title('Bloom Filter Size Sweep', fontsize=15)
ax2.set_xlim(_xlim(x_bits))
ax2.margins(x=0)
ax2.set_ylim(Y_LIM)
ax2.set_yticks(np.arange(Y_LIM[0], Y_LIM[1] + 1, 20))
ax2.tick_params(axis='y', left=True, labelsize=14)
ax2.axhline(0, color='black', linewidth=0.6, linestyle='--')
ax2.grid(linestyle=':', linewidth=0.4, alpha=0.6)
ax2.tick_params(axis='x', labelsize=13)
ax2.margins(y=0)

handles, labels = ax1.get_legend_handles_labels()
n_leg = len(labels)
ncol_leg = (n_leg + 1) // 2 if n_leg else 1  # two rows

plt.tight_layout()
fig.subplots_adjust(wspace=0.19, bottom=0.24)
fig.legend(
    handles, labels,
    loc='upper center',
    bbox_to_anchor=(0.5, 0.10),
    ncol=ncol_leg,
    fontsize=15.5,
    frameon=True,
    columnspacing=1.0,
    handletextpad=0.4,
)
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
