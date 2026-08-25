"""Shared figure width scale for IISWC 2026 paper plots."""

import matplotlib

# Embed text as real (Type 42 / TrueType) fonts instead of matplotlib's
# default Type 3 bitmap fonts, which trip PDF/A font-type checks on
# submission portals.
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

FIG_W_SCALE = 1.03
COLUMN_W_IN = 3.375 * FIG_W_SCALE  # 1:1 with LaTeX \\figwidth


def figsize(w_in, h_in):
    """Return (width, height) with width scaled by FIG_W_SCALE."""
    return (w_in * FIG_W_SCALE, h_in)
