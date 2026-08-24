#!/usr/bin/env python3
"""
Average eviction-to-reaccess distance (cycles) per TLB-sensitive workload,
with DEPOT's default 500K-cycle protection window marked. Makes visible that
average reuse distance sits well under the window across all nine workloads,
connecting the dead-entry characterization to the mechanism's parameter choice
(a commitment from the original rebuttal, never previously plotted).
Source: log_files/results_0709_R1-burst_bigmem72/, commit d4e4e88 fix.
dmr/mst/sssp were partial snapshots when collected (direction reliable).
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

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "reuse_distance.csv"
FIGS = ROOT / "figs"
OUT = FIGS / "fig_reuse_distance.pdf"

COLOR = {'A': '#d62728', 'B': '#1f77b4'}
WINDOW = 500_000

rows = []
with open(DATA) as f:
    for row in csv.DictReader(f):
        rows.append({'wl': row['workload'], 'cls': row['class'],
                      'delta': int(row['avg_delta_cycles'])})

rows.sort(key=lambda r: r['delta'], reverse=True)

fig, ax = plt.subplots(figsize=figsize(3.4, 2.6))

x = range(len(rows))
colors = [COLOR[r['cls']] for r in rows]
ax.bar(x, [r['delta'] / 1000 for r in rows], color=colors, width=0.65, zorder=3)
ax.axhline(WINDOW / 1000, color='black', linestyle='--', linewidth=1.0, zorder=4)
ax.text(0.3, WINDOW / 1000 + 15, 'DEPOT window (500K)',
        ha='left', va='bottom', fontsize=7.5)
ax.set_ylim(top=WINDOW / 1000 * 1.18)

ax.set_xticks(list(x))
ax.set_xticklabels([r['wl'] for r in rows], rotation=35, ha='right', fontsize=8)
ax.set_ylabel('Avg. eviction$\\to$reaccess\ndistance (K cycles)', fontsize=8.5)
ax.tick_params(axis='y', labelsize=8)
ax.grid(axis='y', linestyle=':', linewidth=0.4, alpha=0.6)

patches = [mpatches.Patch(color=COLOR['A'], label='Class A'),
           mpatches.Patch(color=COLOR['B'], label='Class B')]
ax.legend(handles=patches, fontsize=7.5, loc='center right')

plt.tight_layout()
plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.03)
print(f"Saved: {OUT}")
