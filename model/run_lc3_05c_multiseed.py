#!/usr/bin/env python3
"""Run 10-seed LC3-05C robustness experiment and summarize outcomes.
Run from repository root. No model parameter is recalibrated.
"""
import argparse
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd

SEEDS = list(range(42, 52))
ORIGIN = pd.Period('2029-01', freq='M')
THRESHOLDS = (0.05, 0.10, 0.25, 0.50)

def summarize_run(folder, seed):
    n = pd.read_csv(folder / 'national_month_adoption.csv')
    n['month'] = pd.PeriodIndex(n['yyyy_mm'], freq='M')
    n = n.sort_values('month').reset_index(drop=True)
    n['A12'] = n['adopted_demand'].rolling(12, min_periods=12).sum() / n['demand'].rolling(12, min_periods=12).sum()
    row = {'seed': seed, 'A_2045_12': float(n.iloc[-1]['A12']), 'A_2045_month': float(n.iloc[-1]['A'])}
    for threshold in THRESHOLDS:
        hits = n.loc[(n['month'] >= ORIGIN) & (n['A12'] >= threshold)]
        key = f'months_to_{int(threshold*100)}pct'
        row[key] = (int(hits.iloc[0]['month'].ordinal - ORIGIN.ordinal) if len(hits) else np.nan)
    m = pd.read_csv(folder / 'mfr_monthly_states.csv', dtype={'mfr_src_id': str})
    # Count actual first availability, not just scheduled transitions.
    avail = m.loc[m['q_j'].eq(1)].sort_values('yyyy_mm').drop_duplicates('mfr_src_id')
    row['available_mfr_2045'] = int(m.loc[m['yyyy_mm'].eq('2045-12'), 'q_j'].sum())
    row['endogenous_mfr_count'] = int(avail['q_source'].astype(str).str.contains('endogen', case=False).sum())
    if 'q_source' in avail:
        row['endogenous_mfr_ids'] = ','.join(sorted(avail.loc[avail['q_source'].astype(str).str.contains('endogen', case=False), 'mfr_src_id']))
    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--python', default=sys.executable)
    ap.add_argument('--runner', default='model/run_lc3_announced_projects_05c.py')
    ap.add_argument('--input_dir', default='outputs/lc3_reference_2026_2045/inputs_lc3_05')
    ap.add_argument('--capacity_file', default='data/mfr_capacity_for_model.csv')
    ap.add_argument('--output_root', default='outputs/lc3_reference_2026_2045/LC3_05C_multiseed')
    ap.add_argument('--skip_existing', action='store_true')
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    records = []
    for seed in SEEDS:
        out = root / f'seed_{seed}'
        cmd = [args.python, args.runner, '--empirical_dir', args.input_dir,
               '--capacity_file', args.capacity_file,
               '--evidence_file', str(Path(args.input_dir) / 'lc3_05_coordinated_deployment_events.csv'),
               '--out_dir', str(out), '--seed', str(seed), '--T_A', '5',
               '--kappa', '8.439534971412707', '--B0', '1.6223578864493762',
               '--theta_M', '0.19491661627095874', '--H_M', '10', '--T_M', '29',
               '--protect_scenario_events', '--exclude_endogenous_mfr', '20', '21', '65']
        if not (args.skip_existing and (out / 'national_month_adoption.csv').exists()):
            print('Running seed', seed, flush=True)
            subprocess.run(cmd, check=True)
        records.append(summarize_run(out, seed))
    df = pd.DataFrame(records)
    df.to_csv(root / 'lc3_05c_seed_level_results.csv', index=False)
    summary = []
    for key in ['months_to_5pct', 'months_to_10pct', 'months_to_25pct', 'months_to_50pct', 'A_2045_month', 'A_2045_12', 'endogenous_mfr_count']:
        x = df[key].dropna()
        summary.append({'metric': key, 'n_reached_or_valid': len(x), 'n_seeds': len(df),
                        'median': x.median() if len(x) else np.nan,
                        'min': x.min() if len(x) else np.nan,
                        'max': x.max() if len(x) else np.nan})
    pd.DataFrame(summary).to_csv(root / 'lc3_05c_multiseed_summary.csv', index=False)
    print('\n', pd.DataFrame(summary).to_string(index=False))
    print('Saved results in', root)

if __name__ == '__main__':
    main()
