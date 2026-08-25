#!/usr/bin/env python3
"""
Average eviction-to-reaccess distance (cycles) per workload, log scale,
with DEPOT's default 500K-cycle protection window marked. All 21 workloads
with usable L2DeadEntryDeltaHistogram data (3 of 24 -- bfs, gaussian,
parboil-bfs -- have none in this run). Connects the dead-entry
characterization to the mechanism's parameter choice (a commitment from
the original rebuttal, never previously plotted).
Source: log_files/results_0709_R1-burst_bigmem72/, commit d4e4e88 fix,
re-extracted directly from L2DeadEntryDeltaAvgCycles/Histogram (final
cumulative stat per log); cross-checked against incline's independent
extraction for the 10 confirmed-complete non-TLB-sensitive workloads
(9/10 matched within rounding). mri-gridding uses incline's full-trace
rerun.
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
import matplotlib.ticker as mticker

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "reuse_distance.csv"
FIGS = ROOT / "figs"
OUT = FIGS / "fig_reuse_distance.pdf"

COLOR = {'A': '#d62728', 'B': '#1f77b4', 'N': '#7f7f7f'}
WINDOW = 500_000

rows = []
with open(DATA) as f:
    for row in csv.DictReader(f):
        rows.append({'wl': row['workload'], 'cls': row['class'],
                      'delta': int(row['avg_delta_cycles'])})

rows.sort(key=lambda r: r['delta'], reverse=True)

fig, ax = plt.subplots(figsize=figsize(3.4, 1.85))

x = range(len(rows))
colors = [COLOR[r['cls']] for r in rows]
for xi, r, c in zip(x, rows, colors):
    val = max(r['delta'], 30)  # floor for log-scale visibility (2mm=293 already fine)
    ax.bar(xi, val, color=c, width=0.7, zorder=3)
ax.axhline(WINDOW, color='black', linestyle='--', linewidth=0.9, zorder=4)
ax.text(20.6, WINDOW * 0.72, 'DEPOT window (500K)', ha='right', va='top', fontsize=6)

ax.set_yscale('log')
ax.set_ylim(bottom=20, top=1.4e7)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{v/1e6:g}M' if v >= 1e6 else (f'{v/1e3:g}K' if v >= 1e3 else f'{v:g}')))

ax.set_xticks(list(x))
ax.set_xticklabels([r['wl'] for r in rows], rotation=55, ha='right', fontsize=5.8)
ax.set_ylabel('Avg. eviction-reaccess dist. (cyc.)', fontsize=6.8)
ax.tick_params(axis='y', labelsize=6, pad=1)
ax.tick_params(axis='x', pad=1)
ax.grid(axis='y', which='major', linestyle=':', linewidth=0.3, alpha=0.6)

patches = [mpatches.Patch(color=COLOR['A'], label='Class A'),
           mpatches.Patch(color=COLOR['B'], label='Class B'),
           mpatches.Patch(color=COLOR['N'], label='Non-TLB-sens.')]
leg = ax.legend(handles=patches, fontsize=5.6, loc='upper center', ncol=3,
                 handlelength=1.1, handletextpad=0.35, borderpad=0.3, labelspacing=0.25,
                 columnspacing=0.9, bbox_to_anchor=(0.50, 0.99), frameon=False)

plt.tight_layout(pad=0.3)
plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.02)
print(f"Saved: {OUT}")
