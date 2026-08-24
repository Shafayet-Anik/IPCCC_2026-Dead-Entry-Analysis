#!/usr/bin/env python3
"""
Fig 1: Teaser — "What predicts DEPOT effectiveness?"
Three scatter plots, same y-axis (DEPOT IPC gain %), progressively better x-axes:
  (a) DE ratio    → no correlation  (atax ≈ bicg at ~99%; yet opposite outcomes)
  (b) MPKI        → necessary but not sufficient  (both are TLB-sensitive; still no split)
  (c) Burstness   → clean separation (atax high, bicg near-zero; Class A vs B)

The canonical pair (atax / bicg) is annotated in every panel so the reader can
track why the two workloads diverge only when burstness is examined.
"""
import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fig_common import COLUMN_W_IN
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

XLABEL_PAD = 2.0   # all panels; re-applied after box_aspect for consistent y
YLABEL_PAD = 2.0   # pad left of (a) y-label (smaller = closer to axis)
YLABEL_Y = 0.44    # vertical position along axis (default 0.5; lower = downward)
LEGEND_FS = 6.5
PANEL_TAG_FS = 7.0
TAG_BELOW_XLABEL_PT = 1.5    # (a)(b)(c) gap below lowest x-label line
TAG_LEGEND_GAP_PT = 2.0      # gap between (a)(b)(c) bottom and legend top
XLABEL_FS = 6.75
XLABEL_FS_C_LINE2 = XLABEL_FS - 1.0   # (c) 2nd line only
XLABEL_C_LINE_GAP_PT = 1.5   # gap below "Burstness" to line-2 top

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "figs"
OUT  = FIGS / "fig01_teaser.pdf"

COLOR  = {'A': '#d62728', 'B': '#1f77b4', 'neutral': '#7f7f7f'}
MARKER = {'A': 'o',       'B': 's',       'neutral': '^'}
# scatter s = area in pt^2 (very small markers for ~1 in panels)
SIZE   = {'A': 16,        'B': 12,        'neutral': 6}
SCATTER_LW = 0.15
ALPHA  = {'A': 0.95,      'B': 0.88,      'neutral': 0.50}

NAME_MAP = {
    'polybench-atax_NX2048_NY2048':                      'atax',
    'polybench-bicg_NX2048_NY2048':                      'bicg',
    'polybench-mvt_N2048':                               'mvt',
    'polybench-gesummv_N2024':                           'gesummv',
}
ANNOTATE = set(NAME_MAP.keys())

WL_ATAX = 'polybench-atax_NX2048_NY2048'
WL_BICG = 'polybench-bicg_NX2048_NY2048'
WL_MVT = 'polybench-mvt_N2048'
WL_GESUMMV = 'polybench-gesummv_N2024'

# (a,b): labels left of markers — (x, y_text, y_arrow), ha='right'
# (c):   labels right of markers — mirror x, ha='left', arrow tail nudged left
LABEL_ANCHOR_X_AB = 0.48   # shared right edge for right-aligned names (a,b)
LABEL_ANCHOR_X_C = 1.0 - LABEL_ANCHOR_X_AB   # shared left edge for left-aligned names (c)
ARROW_GAP_FROM_NAME_AX = 0.012   # arrow tail gap from name (axes fraction)
ARROW_SHRINK_B_PT = 1.0          # gap at marker end (smaller = closer to marker)

# Equal-spaced label rows (axes fraction), top → bottom
LABEL_ANCHOR_Y_TOP = 0.86
LABEL_ANCHOR_Y_STEP = 0.16
_ANCHOR_Y = [LABEL_ANCHOR_Y_TOP - i * LABEL_ANCHOR_Y_STEP for i in range(4)]


def _label_anchors(x_anchor, workload_order):
    """Map workloads to shared y slots: (x, y_text, y_arrow)."""
    return {
        wl: (x_anchor, y, y)
        for wl, y in zip(workload_order, _ANCHOR_Y)
    }


# (a,c): atax, mvt, bicg, gesummv  |  (b): atax, gesummv, mvt, bicg
_ANCHOR_ORDER_A = (WL_ATAX, WL_MVT, WL_BICG, WL_GESUMMV)
_ANCHOR_ORDER_B = (WL_ATAX, WL_GESUMMV, WL_MVT, WL_BICG)
LABEL_ANCHORS = {
    'a': _label_anchors(LABEL_ANCHOR_X_AB, _ANCHOR_ORDER_A),
    'b': _label_anchors(LABEL_ANCHOR_X_AB, _ANCHOR_ORDER_B),
    'c': _label_anchors(LABEL_ANCHOR_X_C, _ANCHOR_ORDER_A),
}


ARROW_LW = 0.65   # workload label arrows (was 0.85)


def _arrow_props_anchor(cls):
    """Arrow from separate (x, y_arrow) anchor toward marker."""
    return dict(arrowstyle='->', color=COLOR[cls], lw=ARROW_LW,
                shrinkA=0, shrinkB=ARROW_SHRINK_B_PT, mutation_scale=10)

# ---- Load data ----
rows = []
with open(ROOT / "data" / "burstness_o3gain.csv") as f:
    for r in csv.DictReader(f):
        de   = float(r['de_ratio'])  * 100 if r['de_ratio']      else None
        mpki = float(r['mpki'])              if r['mpki']          else None
        bst  = float(r['burstness_peak'])    if r['burstness_peak'] else None
        gain = float(r['o3_gain_pct'])       if r['o3_gain_pct']   else None
        if gain is None:
            continue
        rows.append({
            'wl':    r['workload'],
            'cls':   r['class'],
            'de':    de,
            'mpki':  mpki,
            'burst': bst if bst is not None else 0,
            'gain':  gain,
        })

# ---- Figure layout ----
# PDF width = IEEE \columnwidth at 1:1 with LaTeX \figwidth (see fig_common.py)
M_LEFT, M_RIGHT = 0.088, 0.998   # left: room for y-label
M_TOP = 0.995    # top margin above panels
_BOTTOM = 0.34   # room below axes for x-labels + (a)(b)(c) + legend
WSPACE = 0.17   # gap between panels
N_COLS = 3
_ax_w_frac = (M_RIGHT - M_LEFT) / (N_COLS + (N_COLS - 1) * WSPACE)
_ax_h_frac = M_TOP - _BOTTOM
# Plot box aspect = height / width per panel
PANEL_BOX_ASPECT = 1.05   # +5% vertical vs square
FIG_H_IN = COLUMN_W_IN * _ax_w_frac / _ax_h_frac * PANEL_BOX_ASPECT
# Extra figure height (in) so bottom stack is not clipped by savefig
BELOW_AXES_IN = 0.30   # extra figure height so bottom stack is not clipped
FIG_TOTAL_H_IN = FIG_H_IN + BELOW_AXES_IN

fig, axes = plt.subplots(1, 3, figsize=(COLUMN_W_IN, FIG_TOTAL_H_IN), sharey=True)

def draw_panel(ax, key, label, xscale='linear', xlabel='',
               show_ylabel=False, xlabel_fontsize=6.75):
    """Generic scatter for one x-axis choice."""
    # draw order: neutral → B → A (A on top)
    for cls in ('neutral', 'B', 'A'):
        pts = [r for r in rows if r['cls'] == cls and r[key] is not None]
        xs  = [r[key]  for r in pts]
        ys  = [r['gain'] for r in pts]
        ax.scatter(xs, ys,
                   c=COLOR[cls], marker=MARKER[cls],
                   s=SIZE[cls], alpha=ALPHA[cls],
                   edgecolors='white' if cls != 'neutral' else 'none',
                   linewidths=SCATTER_LW,
                   zorder=3 if cls=='A' else (2 if cls=='B' else 1))

    # Annotate workloads: label column + arrow → marker
    for r in rows:
        if r['wl'] not in ANNOTATE or r[key] is None:
            continue
        sn = NAME_MAP[r['wl']]
        cls = r['cls']
        fw = 'bold' if cls == 'A' else 'normal'
        if r['wl'] in LABEL_ANCHORS.get(label, {}):
            tx, ty_text, ty_arrow = LABEL_ANCHORS[label][r['wl']]
            if label in ('a', 'b'):
                ax.text(
                    tx, ty_text, sn, transform=ax.transAxes,
                    ha='right', va='center',
                    fontsize=6, color=COLOR[cls], fontweight=fw,
                    clip_on=False, zorder=5,
                )
                ax.annotate(
                    '', xy=(r[key], r['gain']),
                    xytext=(tx + ARROW_GAP_FROM_NAME_AX, ty_arrow),
                    textcoords='axes fraction', xycoords='data',
                    arrowprops=_arrow_props_anchor(cls),
                    annotation_clip=False, zorder=4,
                )
            else:  # (c): mirror of (a,b) — left-aligned labels, arrow tail left of name
                ax.text(
                    tx, ty_text, sn, transform=ax.transAxes,
                    ha='left', va='center',
                    fontsize=6, color=COLOR[cls], fontweight=fw,
                    clip_on=False, zorder=5,
                )
                ax.annotate(
                    '', xy=(r[key], r['gain']),
                    xytext=(tx - ARROW_GAP_FROM_NAME_AX, ty_arrow),
                    textcoords='axes fraction', xycoords='data',
                    arrowprops=_arrow_props_anchor(cls),
                    annotation_clip=False, zorder=4,
                )

    ax.axhline(0, color='black', lw=0.7, linestyle='--', alpha=0.45)
    if xscale == 'log':
        ax.set_xscale('log')
    ax.set_xlabel(xlabel, fontsize=xlabel_fontsize, labelpad=XLABEL_PAD,
                  linespacing=1.05)
    if show_ylabel:
        ax.set_ylabel('Performance Improvement', fontsize=6.75,
                      labelpad=YLABEL_PAD, y=YLABEL_Y)
    ax.grid(linestyle=':', lw=0.4, alpha=0.45)
    ax.tick_params(labelsize=6.25)
    ax.tick_params(axis='x', length=2, pad=1.5)

# Panel (a): DE ratio — no predictive power
draw_panel(axes[0], key='de',
           label='a',
           xlabel='L2 TLB Dead-Entry\nRatio (%)',
           show_ylabel=True)

# Panel (b): MPKI — separates TLB-sensitive but not Class A vs B
draw_panel(axes[1], key='mpki',
           label='b',
           xscale='log',
           xlabel='L2 TLB MPKI\n(log scale)')

# Panel (c): Burstness — clean separation
draw_panel(axes[2], key='burst',
           label='c',
           xlabel='Burstness')

# Shared y-range; top tick at 80 shown without label
Y_TICKS = [0, 20, 40, 60, 80]
Y_TICK_LABELS = ['0', '20', '40', '60', '80']
_ylo, _yhi = -8, 80
for i, _ax in enumerate(axes):
    _ax.set_ylim(_ylo, _yhi)
    _ax.set_yticks(Y_TICKS)
    _ax.set_yticklabels(Y_TICK_LABELS)
    _ax.tick_params(axis='y', left=True, labelleft=True,
                    pad=0.5, labelsize=6.25, length=2)
    plt.setp(_ax.get_yticklabels(), ha='right', visible=True)

# MPKI = 1 threshold (panel b); label right of dashed line
_MPKI_THRESH_X = 1.0
_MPKI_LABEL_Y = _ylo + 0.78 * (_yhi - _ylo)
axes[1].axvline(_MPKI_THRESH_X, color='#555', linestyle='--', lw=0.9, alpha=0.6)
axes[1].text(_MPKI_THRESH_X * 1.15, _MPKI_LABEL_Y, 'MPKI=1',
             fontsize=5.75, color='#555', va='center', ha='left')

fig.subplots_adjust(left=M_LEFT, right=M_RIGHT, top=M_TOP, bottom=_BOTTOM,
                  wspace=WSPACE)
for _ax in axes:
    _ax.set_box_aspect(PANEL_BOX_ASPECT)

# Re-apply x-labels after box_aspect so (b) and (c) share the same vertical offset
for _ax, _xl in zip(axes[:2], (
    'L2 TLB Dead-Entry\nRatio (%)',
    'L2 TLB MPKI\n(log scale)',
)):
    _ax.set_xlabel(_xl, fontsize=XLABEL_FS, labelpad=XLABEL_PAD, linespacing=1.05)
axes[2].set_xlabel('Burstness', fontsize=XLABEL_FS, labelpad=XLABEL_PAD, linespacing=1.05)
fig.canvas.draw()
_renderer = fig.canvas.get_renderer()
# Line 2 just below "Burstness" (not aligned to (b) block bottom)
_l1_bb = axes[2].xaxis.label.get_window_extent(_renderer)
_cx = (_l1_bb.x0 + _l1_bb.x1) / 2
_y2_disp = _l1_bb.y0 - XLABEL_C_LINE_GAP_PT * fig.dpi / 72.0
_xf, _yf = fig.transFigure.inverted().transform([(_cx, _y2_disp)])[0]
_c_line2_text = fig.text(
    _xf, _yf, '(Peak MSHR Dead Slots)',
    ha='center', va='top', fontsize=XLABEL_FS_C_LINE2,
    transform=fig.transFigure, clip_on=False,
)

# Stack below plots: x-labels → (a)(b)(c) → legend (no overlap)
_pt = fig.dpi / 72.0
_inv = fig.transFigure.inverted()
_xlabel_bottom_disp = min(
    _ax.xaxis.label.get_window_extent(_renderer).y0 for _ax in axes
)
_xlabel_bottom_disp = min(
    _xlabel_bottom_disp, _c_line2_text.get_window_extent(_renderer).y0)
_, _tag_y_fig = _inv.transform([(0, _xlabel_bottom_disp - TAG_BELOW_XLABEL_PT * _pt)])[0]

_tag_artists = []
for _ax, _tag in zip(axes, ('(a)', '(b)', '(c)')):
    _pos = _ax.get_position()
    _cx = (_pos.x0 + _pos.x1) / 2
    _tag_artists.append(fig.text(
        _cx, _tag_y_fig, _tag, ha='center', va='top',
        fontsize=PANEL_TAG_FS, transform=fig.transFigure, clip_on=False,
    ))

fig.canvas.draw()
_renderer = fig.canvas.get_renderer()
_tag_bottom_disp = min(
    _t.get_window_extent(_renderer).y0 for _t in _tag_artists
)

legend_handles = [
    Line2D([0], [0], marker=MARKER['A'], color='w',
           markerfacecolor=COLOR['A'], markeredgecolor='white',
           markeredgewidth=0.15, markersize=4.4, linestyle='None',
           label='Class A (shared VPN)'),
    Line2D([0], [0], marker=MARKER['B'], color='w',
           markerfacecolor=COLOR['B'], markeredgecolor='white',
           markeredgewidth=0.15, markersize=4.0, linestyle='None',
           label='Class B (unique VPNs)'),
    Line2D([0], [0], marker=MARKER['neutral'], color=COLOR['neutral'],
           markerfacecolor=COLOR['neutral'], markersize=3.6, linestyle='None',
           label='Not TLB-sensitive'),
]
_leg_kw = dict(loc='upper center', ncol=3, bbox_transform=fig.transFigure,
              fontsize=LEGEND_FS, columnspacing=0.55, handletextpad=0.28,
              handlelength=0.9, frameon=False, borderaxespad=0)
# Legend top = (a)(b)(c) bottom − 2 pt (display coords → figure anchor)
_leg_top_disp = _tag_bottom_disp - TAG_LEGEND_GAP_PT * _pt
_leg_top_fig = _inv.transform([(0, _leg_top_disp)])[0][1]
fig.legend(handles=legend_handles, bbox_to_anchor=(0.5, _leg_top_fig), **_leg_kw)

# Keep PDF width = COLUMN_W_IN; LaTeX width=\figwidth is then 1:1.
plt.savefig(OUT, format='pdf', bbox_inches=None, pad_inches=0)
_ax_side_in = COLUMN_W_IN * _ax_w_frac
print(f"Saved: {OUT}")
print(f"  figure: {COLUMN_W_IN:.3f} x {FIG_TOTAL_H_IN:.3f} in  |  square panel: "
      f"{_ax_side_in:.3f} x {_ax_side_in:.3f} in")
