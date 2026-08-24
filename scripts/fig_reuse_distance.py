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

PARTIAL = {'dmr', 'mst', 'sssp'}

rows = []
with open(DATA) as f:
    for row in csv.DictReader(f):
        rows.append({'wl': row['workload'], 'cls': row['class'],
                      'delta': int(row['avg_delta_cycles'])})

rows.sort(key=lambda r: r['delta'], reverse=True)

fig, ax = plt.subplots(figsize=figsize(2.6, 1.75))

x = range(len(rows))
colors = [COLOR[r['cls']] for r in rows]
hatches = ['///' if r['wl'] in PARTIAL else None for r in rows]
for xi, r, c, h in zip(x, rows, colors, hatches):
    ax.bar(xi, r['delta'] / 1000, color=c, width=0.68, zorder=3,
           hatch=h, edgecolor='black' if h else 'none', linewidth=0.5 if h else 0)
ax.axhline(WINDOW / 1000, color='black', linestyle='--', linewidth=0.9, zorder=4)
ax.text(0.3, WINDOW / 1000 + 18, 'DEPOT window (500K)',
        ha='left', va='bottom', fontsize=6)
ax.set_ylim(top=WINDOW / 1000 * 1.22)

ax.set_xticks(list(x))
ax.set_xticklabels([r['wl'] for r in rows], rotation=40, ha='right', fontsize=6.5)
ax.set_ylabel('Avg. dist. (K cyc.)', fontsize=7)
ax.tick_params(axis='y', labelsize=6.5, pad=1)
ax.tick_params(axis='x', pad=1)
ax.grid(axis='y', linestyle=':', linewidth=0.3, alpha=0.6)

patches = [mpatches.Patch(color=COLOR['A'], label='Class A'),
           mpatches.Patch(color=COLOR['B'], label='Class B'),
           mpatches.Patch(facecolor='white', edgecolor='black', hatch='///',
                           label='Partial')]
ax.legend(handles=patches, fontsize=5.5, loc='center right', handlelength=1.3,
          handletextpad=0.4, borderpad=0.3, labelspacing=0.3)

plt.tight_layout(pad=0.3)
plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.02)
print(f"Saved: {OUT}")
