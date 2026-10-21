#!/usr/bin/env python3
"""One-at-a-time PLC behavioral coefficient sensitivity around calibrated finalist A.

Seven configurations x seeds 1..10 (default). No re-calibration.
Uses the transition-metric definitions from run_plc_multiseed_finalists(1).py.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SPECS = [
    ('reference', 0.5, 0.5, 0.7),
    ('demand_low', 0.3, 0.5, 0.7),
    ('demand_high', 0.7, 0.5, 0.7),
    ('dot_low', 0.5, 0.3, 0.7),
    ('dot_high', 0.5, 0.7, 0.7),
    ('peer_low', 0.5, 0.5, 0.5),
    ('peer_high', 0.5, 0.5, 0.9),
]

def load_evaluation_module(path: Path):
    spec = importlib.util.spec_from_file_location('plc_multiseed_eval', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot import evaluation functions from {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runner', default='model/run_plc_simplified.py')
    ap.add_argument('--evaluation_script', default='model/run_plc_multiseed_finalists.py')
    ap.add_argument('--empirical_dir', required=True)
    ap.add_argument('--capacity_file', required=True)
    ap.add_argument('--evidence_file', required=True)
    ap.add_argument('--usgs_file', required=True)
    ap.add_argument('--out_root', required=True)
    ap.add_argument('--seed_start', type=int, default=1)
    ap.add_argument('--seed_end', type=int, default=10)
    ap.add_argument('--persistence_months', type=int, default=6)
    ap.add_argument('--smooth_months', type=int, default=12)
    ap.add_argument('--skip_existing', action='store_true')
    args = ap.parse_args()
    if args.seed_start < 0 or args.seed_end < args.seed_start:
        ap.error('Invalid seed range')
    for file_path in [args.runner, args.evaluation_script, args.capacity_file,
                      args.evidence_file, args.usgs_file]:
        if not Path(file_path).is_file():
            ap.error(f'File not found: {file_path}')
    if not Path(args.empirical_dir).is_dir():
        ap.error(f'Empirical directory not found: {args.empirical_dir}')

    evalmod = load_evaluation_module(Path(args.evaluation_script).resolve())
    obs, obs_transition = evalmod.load_observed(
        args.usgs_file, args.persistence_months, args.smooth_months)
    root = Path(args.out_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / 'experiment_specification.json').write_text(json.dumps({
        'design': 'one_at_a_time_fixed_reference',
        'specifications': [dict(name=n, beta_d=d, beta_phi=g, beta_peer=p)
                           for n, d, g, p in SPECS],
        'fixed': dict(kappa=7, T_A=3, theta_M=0.20, H_M=12, T_M=6, B0=1),
        'seeds': list(range(args.seed_start, args.seed_end + 1)),
        'runner': str(Path(args.runner).resolve()),
        'evaluation_script': str(Path(args.evaluation_script).resolve()),
        'empirical_dir': str(Path(args.empirical_dir).resolve()),
        'capacity_file': str(Path(args.capacity_file).resolve()),
        'evidence_file': str(Path(args.evidence_file).resolve()),
        'usgs_file': str(Path(args.usgs_file).resolve()),
        'persistence_months': args.persistence_months,
        'smooth_months': args.smooth_months,
    }, indent=2))
    rows, monthly_rows = [], []
    seeds = range(args.seed_start, args.seed_end + 1)
    total = len(SPECS) * len(seeds)
    for index, (name, bd, bg, bp) in enumerate(SPECS):
        for seed in seeds:
            tag = f'{name}_seed{seed:02d}'
            run_dir = root / 'runs' / tag
            nat_path = run_dir / 'national_month_adoption.csv'
            mfr_path = run_dir / 'mfr_transition_summary.csv'
            spec_path = run_dir / 'run_specification.csv'
            print(f'[{index * len(seeds) + seed - args.seed_start + 1}/{total}] {tag}', flush=True)
            # Do not silently reuse outputs from a different parameter specification.
            reuse = False
            if args.skip_existing and nat_path.exists() and mfr_path.exists() and spec_path.exists():
                existing = pd.read_csv(spec_path).set_index('parameter')['value']
                expected = dict(seed=seed, beta_d=bd, beta_phi=bg, beta_peer=bp,
                                kappa=7, T_A=3, H_M=12, theta_M=0.20, T_M=6, B0=1)
                reuse = all(k in existing.index and np.isclose(float(existing[k]), v)
                            for k, v in expected.items())
                if not reuse:
                    raise RuntimeError(f'Existing output has mismatched parameters: {run_dir}')
            if not reuse:
                run_dir.mkdir(parents=True, exist_ok=True)
                cmd = [sys.executable, args.runner,
                       '--empirical_dir', args.empirical_dir,
                       '--capacity_file', args.capacity_file,
                       '--evidence_file', args.evidence_file,
                       '--out_dir', str(run_dir), '--seed', str(seed),
                       '--beta_d', str(bd), '--beta_phi', str(bg), '--beta_peer', str(bp),
                       '--kappa', '7', '--T_A', '3', '--theta_M', '0.20',
                       '--H_M', '12', '--T_M', '6', '--B0', '1']
                subprocess.run(cmd, check=True)
            nat = pd.read_csv(nat_path)
            metrics, _ = evalmod.summarize_run(
                nat, obs, obs_transition, args.persistence_months, args.smooth_months)
            mfr = pd.read_csv(mfr_path)
            n_triggers = int(mfr['trigger_month'].notna().sum())
            n_endo_available = int(mfr['scheduled_availability_month'].notna().sum())
            row = dict(specification=name, seed=seed, beta_D=bd, beta_G=bg,
                       beta_P=bp, kappa_A=7, T_A=3, theta_M=0.20, H_M=12,
                       T_M=6, n_manufacturer_triggers=n_triggers,
                       n_manufacturer_scheduled=n_endo_available,
                       final_A=float(nat.iloc[-1]['A']), **metrics)
            rows.append(row)
            z = nat[['yyyy_mm', 'A']].copy()
            z['specification'], z['seed'] = name, seed
            monthly_rows.append(z)
            pd.DataFrame(rows).to_csv(root / 'per_seed_metrics.csv', index=False)
    results = pd.DataFrame(rows)
    pd.concat(monthly_rows, ignore_index=True).to_csv(root / 'national_monthly_all_seeds.csv', index=False)
    agg = results.groupby(['specification', 'beta_D', 'beta_G', 'beta_P'], as_index=False).agg(
        n_seeds=('seed', 'count'), mean_rmse=('rmse', 'mean'), sd_rmse=('rmse', 'std'),
        mean_mae=('mae', 'mean'), mean_final_A=('final_A', 'mean'),
        sd_final_A=('final_A', 'std'),
        mean_A_2024=('A_2024', 'mean'),
        mean_t25_error_months=('t25_error_months', 'mean'),
        mean_t50_error_months=('t50_error_months', 'mean'),
        mean_growth_timing_error_months=('max_growth_timing_error_months', 'mean'),
        mean_max_growth_12m=('sim_max_growth_12m', 'mean'),
        mean_mfr_triggers=('n_manufacturer_triggers', 'mean'),
    )
    ref = agg.loc[agg.specification.eq('reference')].iloc[0]
    for col in ['mean_rmse', 'mean_final_A', 'mean_A_2024', 'mean_t25_error_months',
                'mean_t50_error_months', 'mean_growth_timing_error_months',
                'mean_max_growth_12m', 'mean_mfr_triggers']:
        agg['delta_' + col] = agg[col] - ref[col]
    agg.to_csv(root / 'coefficient_sensitivity_summary.csv', index=False)
    print('\nSensitivity summary:')
    print(agg[['specification', 'mean_rmse', 'mean_final_A',
               'mean_t25_error_months', 'mean_t50_error_months',
               'mean_mfr_triggers']].to_string(index=False))
    print('\nResults:', root)

if __name__ == '__main__':
    main()
