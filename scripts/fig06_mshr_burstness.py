#!/usr/bin/env python3
"""
Fig 6: MSHRDeadSlotsTimeSeries — atax (bursty, Class A) vs. bicg (flat, Class B).
Shows MSHR dead-slot occupancy over time as the key class discriminator.
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
DATA = ROOT / "data" / "mshr_dead_slots_timeseries.csv"
FIGS = ROOT / "figs"
OUT  = FIGS / "fig06_mshr_burstness.pdf"

time_steps = []
bicg_dead, bicg_live = [], []
atax_dead, atax_live = [], []

with open(DATA) as f:
    reader = csv.DictReader(f)
    for row in reader:
        time_steps.append(int(row['time_step']))
        bicg_dead.append(int(row['bicg_dead_slots']))
        bicg_live.append(int(row['bicg_live_slots']))
        atax_dead.append(int(row['atax_dead_slots']))
        atax_live.append(int(row['atax_live_slots']))

# MSHR occupancy interval is 100 cycles → x in Mcycles
x = np.array(time_steps) * 100 / 1e6

# Downsample
STEP = max(1, len(x) // 2000)
x_ds    = x[::STEP]
b_dead  = np.array(bicg_dead)[::STEP]
b_live  = np.array(bicg_live)[::STEP]
a_dead  = np.array(atax_dead)[::STEP]
a_live  = np.array(atax_live)[::STEP]

fig, axes = plt.subplots(1, 2, figsize=figsize(7, 3.0), sharey=True)

# Left panel: atax (Class A — bursty)
ax = axes[0]
ax.fill_between(x_ds, a_dead, alpha=0.5, color='#d62728', label='Dead-entry slots')
ax.fill_between(x_ds, a_live, alpha=0.2, color='#1f77b4', label='Other live slots')
ax.set_title('atax (Class A: interference-driven)', fontsize=12)
ax.set_xlabel('Simulation Time (M cycles)', fontsize=12)
ax.set_ylabel('MSHR Dead-Entry Slots', fontsize=12)
ax.grid(linestyle=':', linewidth=0.4, alpha=0.5)
ax.tick_params(labelsize=11.5)
ax.margins(x=0.02, y=0.03)

# Right panel: bicg (Class B — flat)
ax = axes[1]
ax.fill_between(x_ds, b_dead, alpha=0.5, color='#1f77b4')
ax.fill_between(x_ds, b_live, alpha=0.2, color='#aaaaaa')
ax.set_title('bicg (Class B: capacity-driven)', fontsize=12)
ax.set_xlabel('Simulation Time (M cycles)', fontsize=12)
ax.grid(linestyle=':', linewidth=0.4, alpha=0.5)
ax.tick_params(labelsize=11.5, labelleft=False)
ax.margins(x=0.02, y=0.03)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', ncol=2, fontsize=13,
           bbox_to_anchor=(0.5, 0.13), bbox_transform=fig.transFigure,
           frameon=False, columnspacing=0.8, handletextpad=0.4)

fig.canvas.draw()
fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.26, wspace=0.04)
plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.03)
print(f"Saved: {OUT}")
