#!/usr/bin/env python3
"""Training-only calibration (2010-2022) of simplified PLC ABM.

Requires: pip install optuna pandas numpy matplotlib
Run from ABM repository root. The simulator is not modified.
Parameter selection and reporting use only the 2010-2022 USGS target. Run evaluation separately.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

TRAIN_MONTHS = 156  # January 2010 through December 2022 inclusive
EVAL_MONTHS = 24   # January 2023 through December 2024 inclusive


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def usgs_series(path):
    d = pd.read_csv(path)
    required = {'YYYY_MM', 'TYPE', 'TONS', 'STATE'}
    if not required.issubset(d.columns):
        raise ValueError(f'USGS input missing: {required - set(d.columns)}')
    d['yyyy_mm'] = pd.to_datetime(d['YYYY_MM'].astype(str).str[:7]).dt.strftime('%Y-%m')
    d['type'] = d['TYPE'].astype(str).str.strip().str.lower()
    d['tons'] = pd.to_numeric(d['TONS'].astype(str).str.replace(',', '', regex=False), errors='raise')
    d = d[d.yyyy_mm.between('2010-01', '2024-12') & d.type.isin(['portland', 'blended'])]
    national = d.STATE.astype(str).str.strip().str.lower().isin(['united states', 'us', 'u.s.', 'total', 'national'])
    if national.any():
        d = d[national]
    g = d.groupby(['yyyy_mm', 'type']).tons.sum().unstack()
    if not {'blended', 'portland'}.issubset(g.columns):
        raise ValueError('USGS must contain blended and portland types')
    s = (g['blended'] / (g['blended'] + g['portland'])).sort_index()
    expected = pd.period_range('2010-01', '2024-12', freq='M').astype(str)
    if len(s) != 180 or not s.index.equals(pd.Index(expected)) or s.isna().any():
        raise ValueError('USGS target must contain 180 complete months, 2010-01 through 2024-12')
    return s.rename('observed')


def simulated_series(path, months):
    d = pd.read_csv(path)
    if not {'yyyy_mm', 'A'}.issubset(d.columns):
        raise ValueError(f'{path} missing yyyy_mm or A')
    s = d.set_index('yyyy_mm')['A'].astype(float)
    if s.index.has_duplicates or not set(months).issubset(s.index):
        raise ValueError('Missing/duplicated model months')
    s = s.reindex(months)
    if not np.isfinite(s).all() or ((s < 0) | (s > 1)).any():
        raise ValueError('Invalid model adoption values')
    return s


def first_crossing(y, threshold):
    indices = np.flatnonzero(y >= threshold)
    return int(indices[0]) if len(indices) else None


def evaluate(pred, obs):
    """All terms dimensionless; lower is better. Annual growth dampens monthly noise."""
    a = np.asarray(pred, float)
    y = np.asarray(obs, float)
    err = a - y
    # Normalization fixed a priori: 10 pp level, 10 pp/year growth,
    # 12 months crossing timing, 10 pp endpoint. Avoid domination by early flat years.
    level = float(np.mean((err / .10) ** 2))
    da = a[12:] - a[:-12]
    dy = y[12:] - y[:-12]
    growth = float(np.mean(((da - dy) / .10) ** 2))
    timing_terms = []
    crossings = {}
    for c in (.10, .20, .40, .50):
        target_t = first_crossing(y, c)
        pred_t = first_crossing(a, c)
        if target_t is None:
            continue
        # A missing crossing is penalized by months to end plus 12 extra.
        penalty_months = ((len(a) + 12 - target_t) if pred_t is None else (pred_t - target_t))
        timing_terms.append((penalty_months / 12.0) ** 2)
        crossings[f'crossing_{int(c*100)}_months'] = None if pred_t is None else int(pred_t - target_t)
    timing = float(np.mean(timing_terms)) if timing_terms else 0.0
    endpoint = float((err[-1] / .10) ** 2)
    objective = .40 * level + .30 * growth + .20 * timing + .10 * endpoint
    return dict(objective=float(objective), E_level=level, E_growth=growth,
                E_transition=timing, E_endpoint=endpoint,
                rmse_full=float(np.sqrt(np.mean(err**2))),
                endpoint_error=float(err[-1]), **crossings)


def write_summary(study, out):
    rows = []
    for t in study.trials:
        r = dict(number=t.number, state=t.state.name, objective=t.value)
        r.update(t.params)
        r.update(t.user_attrs)
        rows.append(r)
    pd.DataFrame(rows).to_csv(out / 'trials.csv', index=False)
    completed = [t for t in study.trials if t.state.name == 'COMPLETE']
    if completed:
        best = min(completed, key=lambda t: t.value)
        (out / 'best.json').write_text(json.dumps(dict(trial=best.number, objective=best.value,
                                  params=best.params, metrics=best.user_attrs), indent=2, default=str))


def plot_curves(out, obs, candidates):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = pd.to_datetime(obs.index)
    ax.plot(x, obs.values, lw=2.5, label='USGS blended shipments (proxy)')
    for label, s in candidates.items():
        ax.plot(x, s.values, lw=1.8, label=label)
    ax.set(xlabel='Year', ylabel='Share (0–1)', title='PLC calibration (2010–2022); evaluation withheld')
    ax.grid(alpha=.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / 'calibrated_curves.png', dpi=190)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--empirical_dir', required=True)
    p.add_argument('--capacity_file', required=True)
    p.add_argument('--evidence_file', required=True)
    p.add_argument('--usgs', required=True)
    p.add_argument('--simulator', default='model/run_plc_simplified.py')
    p.add_argument('--out', required=True)
    p.add_argument('--trials', type=int, default=500, help='ADDITIONAL trials; resume by rerunning')
    p.add_argument('--timeout', type=int, default=900, help='Max seconds per ABM run')
    p.add_argument('--seed', type=int, default=42, help='Single screening seed')
    p.add_argument('--confirm', type=int, default=0, help='Confirm best N configurations across 5 seeds; 0 skips')
    p.add_argument('--keep-all', action='store_true', help='Retain full facility/month files for every run (large)')
    args = p.parse_args()
    if args.trials < 0 or args.confirm < 0:
        p.error('--trials and --confirm must be nonnegative')
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    runs = out / 'runs'
    runs.mkdir(exist_ok=True)
    sim = Path(args.simulator).resolve()
    empirical_dir = Path(args.empirical_dir).resolve()
    capacity_file = Path(args.capacity_file).resolve()
    evidence_file = Path(args.evidence_file).resolve()
    if not sim.exists():
        raise FileNotFoundError(f'Missing simulator: {sim}')
    obs = usgs_series(args.usgs)
    if len(obs) != TRAIN_MONTHS + EVAL_MONTHS:
        raise ValueError('Expected exactly 156 training and 24 evaluation months')
    required_inputs = ['rmx_month_demand_exposure.csv', 'mfr_rmx_pairs.csv', 'rmx_peer_pairs.csv', 'dot_monthly_state.csv']
    for name in required_inputs:
        if not (empirical_dir / name).is_file():
            raise FileNotFoundError(empirical_dir / name)
    ev = pd.read_csv(evidence_file)
    dated = ev['model_evidence_class'].eq('plant_dated_availability_boundary') & ev['supported_month_if_dated'].notna()
    if (ev.loc[dated, 'supported_month_if_dated'].astype(str).str[:7] > '2022-12').any():
        raise ValueError('Calibration evidence contains post-2022 enforceable boundaries')
    demand_months = pd.read_csv(empirical_dir / 'rmx_month_demand_exposure.csv', usecols=['yyyy_mm'])['yyyy_mm'].astype(str).unique()
    if sorted(demand_months) != list(obs.index):
        raise ValueError('Empirical demand must cover exactly 2010-01 through 2024-12')
    # Lock study definition across resumptions; don't accidentally mix objectives/input versions.
    provenance = {'simulator': str(sim), 'simulator_sha256': sha256(sim),
                  'usgs_sha256': sha256(args.usgs),
                  'empirical_dir': str(empirical_dir),
                  'empirical_input_sha256': {name: sha256(empirical_dir / name) for name in required_inputs},
                  'capacity_file': str(capacity_file), 'capacity_sha256': sha256(capacity_file),
                  'evidence_file': str(evidence_file), 'evidence_sha256': sha256(evidence_file),
                  'screen_seed': args.seed, 'objective_version': 'v3_train_2010_2022_annual_growth_normalized',
                  'objective_weights': [.40, .30, .20, .10],
                  'training': '2010-01..2022-12',
                  'search_bounds': {'T_A': [3,36], 'kappa': [4,24], 'B0': [.5,3],
                                    'theta_M': [.01,.20], 'H_M': [1,12], 'T_M': [1,36]}}
    manifest = out / 'calibration_manifest.json'
    if manifest.exists():
        if json.loads(manifest.read_text()) != provenance:
            raise RuntimeError('Existing study manifest differs; use a new --out directory')
    else:
        manifest.write_text(json.dumps(provenance, indent=2))

    try:
        import optuna
    except ImportError as e:
        raise SystemExit('Install dependency in your environment: python -m pip install optuna') from e
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    storage = 'sqlite:///' + str(out / 'optuna.sqlite3')
    study = optuna.create_study(study_name='plc_locked_2010_2022', direction='minimize',
                                storage=storage, load_if_exists=True,
                                sampler=optuna.samplers.TPESampler(seed=20261009, n_startup_trials=40))
    # Baseline K12 evaluated first in new study, so optimizer never loses reference.
    if not study.trials:
        initial = {'T_A': 24, 'kappa': 12, 'B0': 1.5, 'theta_M': .05, 'H_M': 3, 'T_M': 6}
        study.enqueue_trial(initial)

    def sample(trial):
        v = {'T_A': trial.suggest_int('T_A', 3, 36),
             'kappa': trial.suggest_float('kappa', 4, 24),
             'B0': trial.suggest_float('B0', .5, 3),
             'theta_M': trial.suggest_float('theta_M', .01, .20, log=True),
             'H_M': trial.suggest_int('H_M', 1, 12),
             'T_M': trial.suggest_int('T_M', 1, 36)}
        return v

    def simulate(params, run_dir, seed):
        run_dir.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(sim),
               '--empirical_dir', str(empirical_dir), '--capacity_file', str(capacity_file),
               '--evidence_file', str(evidence_file), '--out_dir', str(run_dir),
               '--seed', str(seed)]
        for k, v in params.items():
            cmd.extend(['--' + k, str(v)])
        (run_dir / 'command.json').write_text(json.dumps(cmd, indent=2))
        with (run_dir / 'run.log').open('w') as log:
            subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
        return simulated_series(run_dir / 'national_month_adoption.csv', obs.index)

    def objective(trial):
        params = sample(trial)
        run_dir = runs / f'trial_{trial.number:05d}'
        try:
            a = simulate(params, run_dir, args.seed)
            metrics = evaluate(a.values[:TRAIN_MONTHS], obs.values[:TRAIN_MONTHS])
            for k, v in metrics.items():
                trial.set_user_attr(k, v)
            trial.set_user_attr('run_dir', str(run_dir))
            if not args.keep_all:
                for filename in ('rmx_monthly_states.csv', 'mfr_monthly_states.csv', 'state_month_adoption.csv'):
                    (run_dir / filename).unlink(missing_ok=True)
            print(f"trial {trial.number}: objective={metrics['objective']:.4f}, "
                  f"training RMSE={metrics['rmse_full']:.4f}", flush=True)
            return metrics['objective']
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
            trial.set_user_attr('error', str(e))
            print(f'trial {trial.number} FAILED: {e}; see {run_dir / "run.log"}', flush=True)
            raise

    if args.trials:
        try:
            study.optimize(objective, n_trials=args.trials, catch=(subprocess.CalledProcessError,
                           subprocess.TimeoutExpired, ValueError, FileNotFoundError), gc_after_trial=True)
        finally:
            write_summary(study, out)
    else:
        write_summary(study, out)
    completed = sorted((t for t in study.trials if t.state.name == 'COMPLETE'), key=lambda t: t.value)
    if not completed:
        raise RuntimeError('No successful runs; inspect runs/trial_*/run.log')
    best = completed[0]
    best_series = simulated_series(Path(best.user_attrs['run_dir']) / 'national_month_adoption.csv', obs.index)
    train_metrics = evaluate(best_series.values[:TRAIN_MONTHS], obs.values[:TRAIN_MONTHS])
    (out / 'selected_training_metrics.json').write_text(json.dumps(
        {'selected_trial':best.number, 'train_2010_2022':train_metrics}, indent=2))
    curves = {'best screening seed': best_series.loc['2010-01':'2022-12']}
    plot_curves(out, obs.loc['2010-01':'2022-12'], curves)
    pd.DataFrame({'yyyy_mm': obs.index[:TRAIN_MONTHS], 'observed': obs.values[:TRAIN_MONTHS],
                  'best_screening_seed': best_series.values[:TRAIN_MONTHS]}).to_csv(out / 'best_training_curves.csv', index=False)

    if args.confirm:
        seeds = (42, 123, 456, 789, 2026)
        confirmation = []
        confirmed_curves = {}
        for t in completed[:args.confirm]:
            for seed in seeds:
                r = out / 'confirmation' / f'trial_{t.number:05d}' / f'seed_{seed}'
                try:
                    f = r / 'national_month_adoption.csv'
                    s = simulated_series(f, obs.index) if f.exists() else simulate(t.params, r, seed)
                    train = evaluate(s.values[:TRAIN_MONTHS], obs.values[:TRAIN_MONTHS])
                    confirmation.append(dict(trial=t.number, seed=seed, **t.params,
                                             **{'train_'+k:v for k,v in train.items()}))
                    confirmed_curves.setdefault(t.number, []).append(s.values[:TRAIN_MONTHS])
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
                    confirmation.append(dict(trial=t.number, seed=seed, error=str(e)))
                pd.DataFrame(confirmation).to_csv(out / 'confirmation_metrics.csv', index=False)
        for number, trajectories in confirmed_curves.items():
            if len(trajectories) == len(seeds):
                curves[f'confirmed trial {number} mean'] = pd.Series(np.mean(trajectories, axis=0), index=obs.index[:TRAIN_MONTHS])
        plot_curves(out, obs.loc['2010-01':'2022-12'], curves)
    print(f'Completed trials: {len(completed)}; best trial: {best.number}; objective: {best.value:.5f}')
    print(f'Outputs: {out / "best.json"}, {out / "trials.csv"}, {out / "calibrated_curves.png"}')


if __name__ == '__main__':
    main()
