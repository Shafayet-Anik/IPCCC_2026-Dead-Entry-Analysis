#!/usr/bin/env python3
"""
Fig 10: K5 synthetic validation — sim cycles and DE miss count per kernel,
baseline vs. O3. K1-K4 identical; K5 is the hot/cold probe kernel.
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

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "k5_synthetic.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig10_k5_synthetic.pdf"

rows = {}
with open(DATA) as f:
    reader = csv.DictReader(f)
    for row in reader:
        cfg = row['config']
        k   = row['kernel']
        if cfg not in rows: rows[cfg] = {}
        rows[cfg][k] = {'cycles': int(row['cycles']), 'de': int(row['de_misses'])}

kernels = ['K1', 'K2', 'K3', 'K4', 'K5']
x = np.arange(len(kernels))
w = 0.35

base_cycles = [rows['Baseline'][k]['cycles'] for k in kernels]
o3_cycles   = [rows['O3'][k]['cycles']       for k in kernels]
base_de     = [rows['Baseline'][k]['de']     for k in kernels]
o3_de       = [rows['O3'][k]['de']           for k in kernels]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize(6.5, 3.2))

# Left: cycles per kernel
ax1.bar(x - w/2, base_cycles, w, color='#7f7f7f', label='Baseline')
ax1.bar(x + w/2, o3_cycles,   w, color='#2ca02c', label='O3')
ax1.set_xticks(x); ax1.set_xticklabels(kernels, fontsize=9)
ax1.set_ylabel('Simulation Cycles', fontsize=9)
ax1.set_title('Kernel Execution Cycles', fontsize=9)
ax1.legend(fontsize=8)
ax1.grid(axis='y', linestyle=':', linewidth=0.5, alpha=0.6)
ax1.tick_params(labelsize=8)
# Annotate K5 speedup
k5_idx = kernels.index('K5')
speedup = base_cycles[k5_idx] / o3_cycles[k5_idx]
ax1.annotate(f'{speedup:.1f}×', xy=(x[k5_idx]+w/2, o3_cycles[k5_idx]),
             xytext=(0, 6), textcoords='offset points',
             ha='center', fontsize=8, color='#2ca02c', fontweight='bold')

# Right: dead-entry miss count per kernel
ax2.bar(x - w/2, base_de, w, color='#7f7f7f', label='Baseline')
ax2.bar(x + w/2, o3_de,   w, color='#2ca02c', label='O3')
ax2.set_xticks(x); ax2.set_xticklabels(kernels, fontsize=9)
ax2.set_ylabel('Dead-Entry TLB Misses', fontsize=9)
ax2.set_title('Dead-Entry Miss Count', fontsize=9)
ax2.legend(fontsize=8)
ax2.grid(axis='y', linestyle=':', linewidth=0.5, alpha=0.6)
ax2.tick_params(labelsize=8)
# Annotate K5 reduction
ax2.annotate('512→0', xy=(x[k5_idx]+w/2, 10),
             xytext=(0, 5), textcoords='offset points',
             ha='center', fontsize=7.5, color='#2ca02c')

plt.suptitle('K5 Hot/Cold Synthetic Micro-benchmark', fontsize=9.5, y=1.01)
plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
