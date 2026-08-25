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
(9/10 matched within rounding). dmr/mst/sssp/gramschmidt were partial
snapshots when measured (direction reliable, hatched). mri-gridding
uses incline's full-trace rerun: its earlier partial trace stopped
before the benchmark's actual gridding_GPU kernel ever ran, so the
prior number reflected preprocessing only -- this is the corrected,
complete result, not a partial one.
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
PARTIAL = {'dmr', 'mst', 'sssp', 'gramschmidt'}

rows = []
with open(DATA) as f:
    for row in csv.DictReader(f):
        rows.append({'wl': row['workload'], 'cls': row['class'],
                      'delta': int(row['avg_delta_cycles'])})

rows.sort(key=lambda r: r['delta'], reverse=True)

fig, ax = plt.subplots(figsize=figsize(3.4, 1.85))

x = range(len(rows))
colors = [COLOR[r['cls']] for r in rows]
hatches = ['///' if r['wl'] in PARTIAL else None for r in rows]
for xi, r, c, h in zip(x, rows, colors, hatches):
    val = max(r['delta'], 30)  # floor for log-scale visibility (2mm=293 already fine)
    ax.bar(xi, val, color=c, width=0.7, zorder=3,
           hatch=h, edgecolor='black' if h else 'none', linewidth=0.5 if h else 0)
ax.axhline(WINDOW, color='black', linestyle='--', linewidth=0.9, zorder=4)
ax.text(20.6, WINDOW * 1.35, 'DEPOT window (500K)', ha='right', va='bottom', fontsize=6)

ax.set_yscale('log')
ax.set_ylim(bottom=20, top=4e6)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{v/1e6:g}M' if v >= 1e6 else (f'{v/1e3:g}K' if v >= 1e3 else f'{v:g}')))

ax.set_xticks(list(x))
ax.set_xticklabels([r['wl'] for r in rows], rotation=55, ha='right', fontsize=5.8)
ax.set_ylabel('Avg. eviction-reaccess dist. (cyc.)', fontsize=6.8)
ax.tick_params(axis='y', labelsize=6, pad=1)
ax.tick_params(axis='x', pad=1)
ax.grid(axis='y', which='major', linestyle=':', linewidth=0.3, alpha=0.6)

patches = [mpatches.Patch(color=COLOR['A'], label='Class A (TLB-sens.)'),
           mpatches.Patch(color=COLOR['B'], label='Class B (TLB-sens.)'),
           mpatches.Patch(color=COLOR['N'], label='Non-TLB-sensitive'),
           mpatches.Patch(facecolor='white', edgecolor='black', hatch='///',
                           label='Truncated-trace baseline')]
leg = ax.legend(handles=patches, fontsize=5.2, loc='upper right', ncol=1,
                 handlelength=1.2, handletextpad=0.4, borderpad=0.3, labelspacing=0.25,
                 bbox_to_anchor=(1.0, 0.82), framealpha=0.55)
leg.get_frame().set_linewidth(0.5)

plt.tight_layout(pad=0.3)
plt.savefig(OUT, format='pdf', bbox_inches='tight', pad_inches=0.02)
print(f"Saved: {OUT}")
