#!/usr/bin/env python3
"""
extract_data.py — Parse all final_results logs and write CSVs to data/.
Uses grep-based extraction to handle large log files efficiently.
Run from the paper root: python3 scripts/extract_data.py
"""

import os, re, glob, csv, subprocess
from pathlib import Path
from collections import defaultdict

ROOT  = Path(__file__).resolve().parent.parent
FINAL = ROOT / "scratch" / "final_results"
DATA  = ROOT / "data"
DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Workload class assignment (A = interference/MSHR-merging, B = capacity)
# Empirically determined from O3 IPC gain and burstness analysis
# ---------------------------------------------------------------------------
CLASS_A = {
    "polybench-atax_NX2048_NY2048",
    "polybench-mvt_N2048",
}
CLASS_B = {
    "polybench-bicg_NX2048_NY2048",
    "polybench-gesummv_N2024",
    "nw-rodinia-3.1_2048_10",
    "lonestar-dmr_data_25k_10",
    "kmeans-rodinia-3.1_28k_4x_features",
    "lonestar-sssp_data_r4_2e20_gr",
    "lonestar-mst_2d_2e20_sym_gr",
}

def workload_class(wl):
    if wl in CLASS_A: return "A"
    if wl in CLASS_B: return "B"
    return "neutral"

def get_wl_name(log_path):
    bn = Path(log_path).stem
    return bn.split('_SM86')[0]

# ---------------------------------------------------------------------------
# Fast grep-based log parser — only greps for lines we actually need
# ---------------------------------------------------------------------------
GREP_PATTERN = (
    r'gpu_tot_ipc|^MPKI:|L2DeadEntryMissRatio:|L2DeadEntryMisses:|'
    r'L2DeadEntryMissDenom:|BloomInserts:|BloomHits:|CTFFills:|'
    r'MissArrivalTimeSeries:|DeadEntryArrivalTimeSeries:|'
    r'MSHRDeadSlotsTimeSeries:|MSHRLiveSlotsTimeSeries:|'
    r'MissArrivalInterval:|MSHROccupancyInterval:'
)

def parse_log_fast(path):
    """Extract key stats using grep, return dict."""
    try:
        result = subprocess.run(
            ['grep', '-E', GREP_PATTERN, str(path)],
            capture_output=True, text=True, timeout=30
        )
        lines = result.stdout.splitlines()
    except Exception as e:
        print(f"  WARN: grep failed for {path}: {e}")
        return {}

    r = {}
    # We take LAST occurrence of each stat (= aggregate across all kernels)
    ipcs, mpkis, des, dem, ded = [], [], [], [], []
    bi, bh, cf = [], [], []
    mats_lines, dats_lines, mshrds_lines, mshrls_lines = [], [], [], []
    mais, mois = [], []

    for line in lines:
        line = line.strip()
        if line.startswith('gpu_tot_ipc'):
            m = re.search(r'([\d.]+)\s*$', line)
            if m: ipcs.append(float(m.group(1)))
        elif line.startswith('MPKI:'):
            m = re.search(r'([\d.]+)', line)
            if m: mpkis.append(float(m.group(1)))
        elif 'L2DeadEntryMissRatio:' in line:
            m = re.search(r'L2DeadEntryMissRatio:\s*([\d.]+)', line)
            if m: des.append(float(m.group(1)))
        elif 'L2DeadEntryMisses:' in line and 'Denom' not in line:
            m = re.search(r'L2DeadEntryMisses:\s*(\d+)', line)
            if m: dem.append(int(m.group(1)))
        elif 'L2DeadEntryMissDenom:' in line:
            m = re.search(r'L2DeadEntryMissDenom:\s*(\d+)', line)
            if m: ded.append(int(m.group(1)))
        elif line.startswith('BloomInserts:'):
            m = re.search(r'BloomInserts:\s*(\d+)', line)
            if m: bi.append(int(m.group(1)))
        elif line.startswith('BloomHits:') or 'BloomHits:' in line:
            m = re.search(r'BloomHits:\s*(\d+)', line)
            if m: bh.append(int(m.group(1)))
        elif line.startswith('CTFFills:'):
            m = re.search(r'CTFFills:\s*(\d+)', line)
            if m: cf.append(int(m.group(1)))
        elif line.startswith('MissArrivalTimeSeries:'):
            mats_lines.append(line)
        elif line.startswith('DeadEntryArrivalTimeSeries:'):
            dats_lines.append(line)
        elif line.startswith('MSHRDeadSlotsTimeSeries:'):
            mshrds_lines.append(line)
        elif line.startswith('MSHRLiveSlotsTimeSeries:'):
            mshrls_lines.append(line)
        elif line.startswith('MissArrivalInterval:'):
            m = re.search(r'(\d+)', line)
            if m: mais.append(int(m.group(1)))
        elif line.startswith('MSHROccupancyInterval:'):
            m = re.search(r'(\d+)', line)
            if m: mois.append(int(m.group(1)))

    def parse_ts(line):
        parts = line.split(':', 1)
        if len(parts) > 1:
            return [int(x) for x in parts[1].split() if x.lstrip('-').isdigit()]
        return []

    r['ipc']        = ipcs[-1]  if ipcs  else None
    r['mpki']       = mpkis[-1] if mpkis else None
    r['de_ratio']   = des[-1]   if des   else None
    r['l2_dead_misses'] = dem[-1] if dem else None
    r['l2_dead_denom']  = ded[-1] if ded else None
    r['bloom_inserts']  = bi[-1]  if bi   else None
    r['bloom_hits']     = bh[-1]  if bh   else None
    r['ctf_fills']      = cf[-1]  if cf   else None
    r['miss_arrival_ts']    = parse_ts(mats_lines[-1]) if mats_lines else []
    r['dead_arrival_ts']    = parse_ts(dats_lines[-1]) if dats_lines else []
    r['mshr_dead_ts']       = parse_ts(mshrds_lines[-1]) if mshrds_lines else []
    r['mshr_live_ts']       = parse_ts(mshrls_lines[-1]) if mshrls_lines else []
    r['miss_arrival_interval'] = mais[-1] if mais else 1000
    r['mshr_interval']         = mois[-1] if mois else 100
    return r


def load_run(run_dir):
    logs = sorted(glob.glob(str(run_dir / '*.log')))
    result = {}
    for log in logs:
        wl = get_wl_name(log)
        result[wl] = parse_log_fast(log)
    return result


def burstness(stats):
    ts = stats.get('mshr_dead_ts', [])
    return max(ts) if ts else 0


# ---------------------------------------------------------------------------
# Load all runs
# ---------------------------------------------------------------------------
print("Loading runs...")
RUN_IDS = [
    'R1-burst', 'R2-clean', 'R3', 'R4',
    'R_CTF', 'R_O3CTF', 'R_FP',
    'R12-100K', 'R12-250K', 'R12-500K', 'R12-1M', 'R12-2M',
    'R13-2048', 'R13-4096', 'R13-8192', 'R13-16384',
    'R8', 'R9', 'R10',
]

runs = {}
for run_id in RUN_IDS:
    d = FINAL / run_id
    if d.exists():
        runs[run_id] = load_run(d)
        print(f"  {run_id}: {len(runs[run_id])} workloads")
    else:
        print(f"  {run_id}: MISSING")
        runs[run_id] = {}

WORKLOADS = sorted(runs['R1-burst'].keys())
print(f"\nWorkloads: {len(WORKLOADS)}")


# ---------------------------------------------------------------------------
# CSV 1: workload_stats.csv
# ---------------------------------------------------------------------------
print("\nWriting CSVs...")
with open(DATA / 'workload_stats.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['workload', 'ipc', 'mpki', 'de_ratio', 'burstness_peak', 'class'])
    for wl in WORKLOADS:
        s = runs['R1-burst'][wl]
        w.writerow([wl, s['ipc'], s['mpki'], s['de_ratio'], burstness(s), workload_class(wl)])
print("  workload_stats.csv")

# ---------------------------------------------------------------------------
# CSV 2: ipc_comparison.csv
# ---------------------------------------------------------------------------
configs = ['R1-burst', 'R2-clean', 'R_CTF', 'R_O3CTF', 'R8', 'R9', 'R10']
with open(DATA / 'ipc_comparison.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['workload', 'class'] + configs)
    for wl in WORKLOADS:
        row = [wl, workload_class(wl)]
        for cfg in configs:
            val = runs.get(cfg, {}).get(wl, {}).get('ipc', '')
            row.append(val if val is not None else '')
        w.writerow(row)
print("  ipc_comparison.csv")

# ---------------------------------------------------------------------------
# CSV 3: ipc_2mb.csv
# ---------------------------------------------------------------------------
with open(DATA / 'ipc_2mb.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['workload', 'class', 'ipc_4kb_base', 'ipc_4kb_o3', 'ipc_2mb_base', 'ipc_2mb_o3'])
    for wl in WORKLOADS:
        row = [wl, workload_class(wl)]
        for cfg in ['R1-burst', 'R2-clean', 'R3', 'R4']:
            val = runs.get(cfg, {}).get(wl, {}).get('ipc', '')
            row.append(val if val is not None else '')
        w.writerow(row)
print("  ipc_2mb.csv")

# ---------------------------------------------------------------------------
# CSV 4: de_ratio_comparison.csv
# ---------------------------------------------------------------------------
with open(DATA / 'de_ratio_comparison.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['workload', 'class', 'de_ratio_4kb', 'de_ratio_2mb'])
    for wl in WORKLOADS:
        s1 = runs['R1-burst'].get(wl, {})
        s3 = runs.get('R3', {}).get(wl, {})
        w.writerow([wl, workload_class(wl),
                    s1.get('de_ratio', ''), s3.get('de_ratio', '')])
print("  de_ratio_comparison.csv")

# ---------------------------------------------------------------------------
# CSV 5: miss_arrival_timeseries.csv
# ---------------------------------------------------------------------------
TS_WLS = [
    'polybench-bicg_NX2048_NY2048',
    'polybench-atax_NX2048_NY2048',
]
ts_data = {wl: runs['R1-burst'].get(wl, {}) for wl in TS_WLS}
max_len = max(
    max((len(ts_data[wl].get('miss_arrival_ts', [])) for wl in TS_WLS), default=0),
    1
)
with open(DATA / 'miss_arrival_timeseries.csv', 'w', newline='') as f:
    w = csv.writer(f)
    headers = ['time_step']
    for wl in TS_WLS:
        short = wl.split('-')[1].split('_')[0]
        headers += [f'{short}_total_misses', f'{short}_dead_misses']
    w.writerow(headers)
    for i in range(max_len):
        row = [i]
        for wl in TS_WLS:
            mt = ts_data[wl].get('miss_arrival_ts', [])
            dt = ts_data[wl].get('dead_arrival_ts', [])
            row.append(mt[i] if i < len(mt) else 0)
            row.append(dt[i] if i < len(dt) else 0)
        w.writerow(row)
print("  miss_arrival_timeseries.csv")

# ---------------------------------------------------------------------------
# CSV 6: mshr_dead_slots_timeseries.csv
# ---------------------------------------------------------------------------
max_len2 = max(
    max((len(ts_data[wl].get('mshr_dead_ts', [])) for wl in TS_WLS), default=0),
    1
)
with open(DATA / 'mshr_dead_slots_timeseries.csv', 'w', newline='') as f:
    w = csv.writer(f)
    headers = ['time_step']
    for wl in TS_WLS:
        short = wl.split('-')[1].split('_')[0]
        headers += [f'{short}_dead_slots', f'{short}_live_slots']
    w.writerow(headers)
    for i in range(max_len2):
        row = [i]
        for wl in TS_WLS:
            dt = ts_data[wl].get('mshr_dead_ts', [])
            lt = ts_data[wl].get('mshr_live_ts', [])
            row.append(dt[i] if i < len(dt) else 0)
            row.append(lt[i] if i < len(lt) else 0)
        w.writerow(row)
print("  mshr_dead_slots_timeseries.csv")

# ---------------------------------------------------------------------------
# CSV 7: param_sweep_protect_cycles.csv
# ---------------------------------------------------------------------------
R12_RUNS = {100000: 'R12-100K', 250000: 'R12-250K', 500000: 'R12-500K',
            1000000: 'R12-1M', 2000000: 'R12-2M'}
with open(DATA / 'param_sweep_protect_cycles.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['protect_cycles', 'workload', 'ipc', 'ipc_baseline', 'gain_pct'])
    for cycles, run_id in sorted(R12_RUNS.items()):
        for wl in WORKLOADS:
            ipc  = runs.get(run_id, {}).get(wl, {}).get('ipc')
            base = runs['R1-burst'].get(wl, {}).get('ipc')
            if ipc is not None and base is not None and base > 0:
                w.writerow([cycles, wl, ipc, base, round((ipc-base)/base*100, 3)])
print("  param_sweep_protect_cycles.csv")

# ---------------------------------------------------------------------------
# CSV 8: param_sweep_bloom_bits.csv
# ---------------------------------------------------------------------------
R13_RUNS = {2048: 'R13-2048', 4096: 'R13-4096', 8192: 'R13-8192', 16384: 'R13-16384'}
with open(DATA / 'param_sweep_bloom_bits.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['bloom_bits', 'workload', 'ipc', 'ipc_baseline', 'gain_pct'])
    for bits, run_id in sorted(R13_RUNS.items()):
        for wl in WORKLOADS:
            ipc  = runs.get(run_id, {}).get(wl, {}).get('ipc')
            base = runs['R1-burst'].get(wl, {}).get('ipc')
            if ipc is not None and base is not None and base > 0:
                w.writerow([bits, wl, ipc, base, round((ipc-base)/base*100, 3)])
print("  param_sweep_bloom_bits.csv")

# ---------------------------------------------------------------------------
# CSV 9: k5_synthetic.csv (hardcoded from outline)
# ---------------------------------------------------------------------------
k5_data = [
    ('K1', 'Baseline', 2000,  0),
    ('K2', 'Baseline', 2000,  0),
    ('K3', 'Baseline', 2000,  0),
    ('K4', 'Baseline', 2000,  0),
    ('K5', 'Baseline', 15402, 512),
    ('K1', 'O3',       2000,  0),
    ('K2', 'O3',       2000,  0),
    ('K3', 'O3',       2000,  0),
    ('K4', 'O3',       2000,  0),
    ('K5', 'O3',       5269,  0),
]
with open(DATA / 'k5_synthetic.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['kernel', 'config', 'cycles', 'de_misses'])
    for row in k5_data:
        w.writerow(row)
print("  k5_synthetic.csv")

# ---------------------------------------------------------------------------
# CSV 10: burstness_o3gain.csv
# ---------------------------------------------------------------------------
with open(DATA / 'burstness_o3gain.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['workload', 'class', 'mpki', 'de_ratio', 'burstness_peak',
                'ipc_base', 'ipc_o3', 'o3_gain_pct'])
    for wl in WORKLOADS:
        s1 = runs['R1-burst'].get(wl, {})
        s2 = runs['R2-clean'].get(wl, {})
        ib = s1.get('ipc'); io = s2.get('ipc')
        gain = round((io-ib)/ib*100, 3) if ib and io and ib > 0 else ''
        w.writerow([wl, workload_class(wl), s1.get('mpki',''), s1.get('de_ratio',''),
                    burstness(s1), ib, io, gain])
print("  burstness_o3gain.csv")

# ---------------------------------------------------------------------------
# CSV 11: workload_table.csv (Table I)
# ---------------------------------------------------------------------------
with open(DATA / 'workload_table.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['workload','class','ipc_base','mpki','de_ratio_pct','burstness',
                'ipc_o3','o3_gain_pct','ipc_ctf','ipc_o3ctf',
                'ipc_2mb_base','ipc_2mb_o3'])
    for wl in WORKLOADS:
        s1 = runs['R1-burst'].get(wl, {})
        s2 = runs['R2-clean'].get(wl, {})
        ib = s1.get('ipc'); io = s2.get('ipc')
        gain = round((io-ib)/ib*100, 2) if ib and io and ib > 0 else ''
        de   = s1.get('de_ratio')
        w.writerow([
            wl, workload_class(wl), ib, s1.get('mpki',''),
            round(de*100, 1) if de else '',
            burstness(s1), io, gain,
            runs.get('R_CTF', {}).get(wl,{}).get('ipc',''),
            runs.get('R_O3CTF',{}).get(wl,{}).get('ipc',''),
            runs.get('R3',    {}).get(wl,{}).get('ipc',''),
            runs.get('R4',    {}).get(wl,{}).get('ipc',''),
        ])
print("  workload_table.csv")

print(f"\n=== Done. CSVs in {DATA} ===")
for csv_file in sorted(DATA.glob('*.csv')):
    print(f"  {csv_file.name:45s} {csv_file.stat().st_size:7d} bytes")
