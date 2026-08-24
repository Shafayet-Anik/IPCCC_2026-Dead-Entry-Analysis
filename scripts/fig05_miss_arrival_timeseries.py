#!/usr/bin/env python3
"""
Fig 5: MissArrivalTimeSeries + DE fraction over time for bicg and atax.
Two-panel: top = total miss arrival rate, bottom = dead-entry fraction.
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
DATA = ROOT / "data" / "miss_arrival_timeseries.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig05_miss_arrival_timeseries.pdf"

# Load data
time_steps = []
bicg_total, bicg_dead = [], []
atax_total, atax_dead = [], []

with open(DATA) as f:
    reader = csv.DictReader(f)
    for row in reader:
        t  = int(row['time_step'])
        bt = int(row['bicg_total_misses'])
        bd = int(row['bicg_dead_misses'])
        at = int(row['atax_total_misses'])
        ad = int(row['atax_dead_misses'])
        time_steps.append(t)
        bicg_total.append(bt)
        bicg_dead.append(bd)
        atax_total.append(at)
        atax_dead.append(ad)

# Interval is 1000 cycles — x axis in millions of cycles
x = np.array(time_steps) * 1000 / 1e6  # → units of Mcycles

# Downsample for clarity (every 10 points)
STEP = max(1, len(x) // 1000)
x_ds       = x[::STEP]
bt_ds      = np.array(bicg_total)[::STEP]
bd_ds      = np.array(bicg_dead)[::STEP]
at_ds      = np.array(atax_total)[::STEP]
ad_ds      = np.array(atax_dead)[::STEP]

# Dead fraction (avoid div-by-zero)
def safe_frac(dead, total):
    arr = np.array(dead, dtype=float)
    tot = np.array(total, dtype=float)
    mask = tot > 0
    result = np.zeros_like(arr)
    result[mask] = arr[mask] / tot[mask] * 100
    return result

bicg_frac = safe_frac(bd_ds, bt_ds)
atax_frac = safe_frac(ad_ds, at_ds)

LEGEND_KW = dict(fontsize=10.5, loc='lower left', bbox_to_anchor=(0.08, 0.02))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize(6, 4.5), sharex=True)

# Panel 1: Miss arrival rate
ax1.plot(x_ds, bt_ds, color='#1f77b4', lw=0.65, label='bicg total')
ax1.plot(x_ds, at_ds, color='#d62728', lw=0.65, linestyle='--', label='atax total')
ax1.set_ylabel('L2 TLB Misses\nper 1K cycles', fontsize=10)
ax1.legend(**LEGEND_KW)
ax1.grid(linestyle=':', linewidth=0.4, alpha=0.6)
ax1.tick_params(labelsize=10)

# Panel 2: Dead-entry fraction
ax2.plot(x_ds, bicg_frac, color='#1f77b4', lw=0.65, label='bicg DE%')
ax2.plot(x_ds, atax_frac, color='#d62728', lw=0.65, linestyle='--', label='atax DE%')
ax2.set_ylabel('Dead-Entry Fraction (%)', fontsize=10)
ax2.set_xlabel('Simulation Time (M cycles)', fontsize=11)
ax2.set_ylim(-5, 105)
ax2.legend(**LEGEND_KW)
ax2.grid(linestyle=':', linewidth=0.4, alpha=0.6)
ax2.tick_params(labelsize=10)

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight')
print(f"Saved: {OUT}")
