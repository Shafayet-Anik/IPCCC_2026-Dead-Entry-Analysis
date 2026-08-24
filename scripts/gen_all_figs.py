#!/usr/bin/env python3
"""
gen_all_figs.py — Regenerate all data-driven figures for the IISWC 2026 paper.
Run from the paper root:
    python3 scripts/gen_all_figs.py [--data-only] [--figs-only]

Steps:
  1. Extract data from final_results logs → data/*.csv  (unless --figs-only)
  2. Run each per-figure script → figs/*.pdf            (unless --data-only)

Figures 2 (arch diagram) and 9 (DEPOT mechanism diagram) are manual — no script.
"""

import sys, os, subprocess
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIGS    = ROOT / "figs"
FIGS.mkdir(exist_ok=True)

DATA_ONLY = '--data-only' in sys.argv
FIGS_ONLY = '--figs-only' in sys.argv

def run(script, desc):
    print(f"\n{'='*55}")
    print(f"  {desc}")
    print(f"  Running: {script.name}")
    print(f"{'='*55}")
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=False,
    )
    if result.returncode != 0:
        print(f"  ERROR: {script.name} exited with code {result.returncode}")
        return False
    return True

ok = []
fail = []

# Step 1 — Data extraction
if not FIGS_ONLY:
    script = SCRIPTS / "extract_data.py"
    if run(script, "Data extraction → data/*.csv"):
        ok.append("extract_data")
    else:
        fail.append("extract_data")
        print("\nData extraction failed — figure scripts may not work correctly.")

# Step 2 — Figure scripts
if not DATA_ONLY:
    figure_scripts = [
        (SCRIPTS / "fig01_teaser.py",               "Fig 1  — Teaser (DE ratio + DEPOT gain + K5)"),
        (SCRIPTS / "fig03_de_ratio_bars.py",        "Fig 3  — L2 DE ratio, 24 workloads"),
        (SCRIPTS / "fig04_de_ratio_vs_mpki.py",     "Fig 4  — DE ratio vs. MPKI scatter"),
        (SCRIPTS / "fig05_miss_arrival_timeseries.py","Fig 5 — Miss arrival timeseries (atax, bicg)"),
        (SCRIPTS / "fig06_mshr_burstness.py",       "Fig 6  — MSHR dead-slot occupancy (Class A vs B)"),
        (SCRIPTS / "fig07_2mb_ipc_speedup.py",      "Fig 7  — IPC speedup under 2MB pages (Class A/B)"),
        (SCRIPTS / "fig09_o3_ipc_gains.py",         "Fig 9  — DEPOT IPC gain (%) per workload"),
        (SCRIPTS / "fig10_ipc_comparison.py",       "Fig 10 — IPC: Baseline vs DEPOT vs LatPC vs LatPC+DEPOT"),
        (SCRIPTS / "fig11_o3gain_vs_mpki.py",       "Fig 11 — DEPOT gain vs. MPKI scatter (two-regime)"),
        (SCRIPTS / "fig12_o3_under_2mb.py",         "Fig 12 — 3-config comparison for all 9 TLB-sensitive"),
        (SCRIPTS / "fig13_param_sensitivity.py",    "Fig 13 — Parameter sensitivity sweep"),
    ]

    for script, desc in figure_scripts:
        if script.exists():
            if run(script, desc):
                ok.append(script.stem)
            else:
                fail.append(script.stem)
        else:
            print(f"\n  MISSING: {script.name}")
            fail.append(script.stem)

# Summary
print(f"\n{'='*55}")
print(f"  SUMMARY")
print(f"{'='*55}")
print(f"  OK   ({len(ok)}): {', '.join(ok)}")
if fail:
    print(f"  FAIL ({len(fail)}): {', '.join(fail)}")
print()
print("  PDFs in: figs/")
for pdf in sorted(FIGS.glob("*.pdf")):
    print(f"    {pdf.name}")
print()
print("  Manual figures (draw by hand):")
print("    Fig 2  — GPU architecture diagram (no script)")
print("    Fig 9  — DEPOT mechanism diagram     (no script)")
