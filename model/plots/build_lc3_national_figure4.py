#!/usr/bin/env python3
"""Prepare/run/plot four LC3 national regulatory schedules (matched seeds 42-51).

Reference: inputs_lc3_06R24. Only DOT maturity is modified; manufacturer
scenario events and all other input files are copied unchanged.

Staggered: retain existing 14-state DOT trajectories exactly; add 33 states
in three alphabetical (NOT empirical) waves: 2035, 2038, 2040.
"""
from pathlib import Path
import argparse, shutil, subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path('outputs/lc3_reference_2026_2045')
BASE = ROOT / 'inputs_lc3_06R24'
NAMES = {'No DOT implementation':'N0', 'Existing 14-state schedule':'N14',
         'Staggered to 47 states':'NSTAG', '47 states in 2029':'N47'}
COLORS = {'No DOT implementation':'#777777', 'Existing 14-state schedule':'#4C78A8',
          'Staggered to 47 states':'#E69F00', '47 states in 2029':'#009E73'}


def maturity(months, origin):
    p = pd.PeriodIndex(months, freq='M')
    o = pd.Period(origin, freq='M')
    lag = (p.year - o.year)*12 + p.month - o.month
    return np.clip(np.asarray(lag, dtype=float)/24, 0, 1)


def prepare():
    if not BASE.is_dir():
        raise FileNotFoundError(BASE)
    base = pd.read_csv(BASE/'dot_monthly_state.csv', dtype={'state':str, 'yyyy_mm':str})
    assert {'state','yyyy_mm','phi_s'} <= set(base.columns)
    assert not base.duplicated(['state','yyyy_mm']).any()
    states = sorted(base.state.unique())
    assert len(states)==47, f'Expected 47 states, found {len(states)}'
    base['phi_s'] = pd.to_numeric(base.phi_s)
    existing = sorted(base.loc[base.phi_s.gt(0),'state'].unique())
    assert len(existing)==14, f'Expected 14 reference implementing states, found {len(existing)}'
    remaining = sorted(set(states)-set(existing))
    assert len(remaining)==33
    waves = {s:('2035-01' if i<11 else '2038-01' if i<22 else '2040-01')
             for i,s in enumerate(remaining)}
    for label, code in NAMES.items():
        target = ROOT/f'inputs_lc3_{code}'
        target.mkdir(parents=True,exist_ok=True)
        for source in BASE.iterdir():
            if source.is_file():
                shutil.copy2(source,target/source.name)
        dot = base.copy()
        if code=='N0':
            dot['phi_s']=0.0
        elif code=='N47':
            dot['phi_s']=maturity(dot.yyyy_mm,'2029-01')
        elif code=='NSTAG':
            for state, start in waves.items():
                mask=dot.state.eq(state)
                dot.loc[mask,'phi_s']=maturity(dot.loc[mask,'yyyy_mm'],start)
        # N14 retains original values
        assert dot.phi_s.between(0,1).all()
        if code in ('N14','NSTAG'):
            old=base.state.isin(existing)
            np.testing.assert_array_equal(dot.loc[old,'phi_s'],base.loc[old,'phi_s'])
        dot.to_csv(target/'dot_monthly_state.csv',index=False)
        for source in BASE.iterdir():
            if source.is_file() and source.name!='dot_monthly_state.csv':
                assert (target/source.name).read_bytes()==source.read_bytes(), source.name
        print(f'Prepared {label}: {target}')
    pd.DataFrame([{'state':s,'implementation_month':month,'selection_rule':'alphabetical illustrative wave'}
                  for s,month in waves.items()]).to_csv(ROOT/'lc3_national_staggered_wave_assignments.csv',index=False)
    print('Staggered additional states: 11 in 2035, 11 in 2038, 11 in 2040.')
    print('All non-DOT input files verified identical to reference.')


def run():
    runner=Path('model/run_lc3_05c_multiseed.py')
    if not runner.exists(): raise FileNotFoundError(runner)
    for label,code in NAMES.items():
        cmd=['python',str(runner),'--input_dir',str(ROOT/f'inputs_lc3_{code}'),
             '--output_root',str(ROOT/f'LC3_{code}_multiseed')]
        print('RUN:', ' '.join(cmd),flush=True)
        subprocess.run(cmd,check=True)


def plot():
    """Plot existing runs only; use 12-month ratio of summed RMX demand."""
    fig, (ax0, ax1) = plt.subplots(
        2, 1, figsize=(9.3, 7.2), sharex=True,
        gridspec_kw={'height_ratios': [1, 1.55], 'hspace': 0.17}
    )
    summary = []
    handles = []
    labels = []
    for label, code in NAMES.items():
        dot = pd.read_csv(ROOT / f'inputs_lc3_{code}' / 'dot_monthly_state.csv')
        dot['date'] = pd.to_datetime(dot.yyyy_mm + '-01')
        counts = dot.groupby('date').phi_s.apply(lambda x: int((x > 0).sum())).sort_index()
        line, = ax0.step(counts.index, counts.values, where='post',
                         color=COLORS[label], lw=2.2, label=label)
        handles.append(line)
        labels.append(label)

        seed_series = []
        for seed in range(42, 52):
            path = ROOT / f'LC3_{code}_multiseed' / f'seed_{seed}' / 'rmx_monthly_states.csv'
            if not path.exists():
                raise FileNotFoundError(f'Missing simulation output: {path}\nRun with --run first.')
            df = pd.read_csv(path, usecols=['yyyy_mm', 'D_i', 'a_i'])
            df['adopted_demand'] = df['D_i'] * df['a_i']
            monthly = df.groupby('yyyy_mm', sort=True)[['D_i', 'adopted_demand']].sum()
            rolling = monthly.rolling(window=12, min_periods=12).sum()
            a12 = rolling['adopted_demand'] / rolling['D_i']
            seed_series.append(pd.DataFrame({
                'date': pd.to_datetime(a12.index + '-01'),
                'seed': seed, 'A12': a12.to_numpy()
            }))
        combined = pd.concat(seed_series, ignore_index=True).dropna(subset=['A12'])
        grouped = combined.groupby('date').A12.agg(['median', 'min', 'max']).sort_index()
        ax1.plot(grouped.index, 100 * grouped['median'], color=COLORS[label], lw=2.2)
        ax1.fill_between(grouped.index.to_numpy(), 100 * grouped['min'].to_numpy(),
                         100 * grouped['max'].to_numpy(), color=COLORS[label], alpha=.13, lw=0)
        last = grouped.iloc[-1]
        summary.append({'scenario': label, 'median_A_2045_12': last['median'],
                        'min_A_2045_12': last['min'], 'max_A_2045_12': last['max']})

    ax0.set_ylabel('States with DOT\nimplementation')
    ax0.set_ylim(-2, 50)
    ax0.set_yticks([0, 10, 20, 30, 40, 47])
    ax0.set_title('(a) Hypothetical DOT implementation schedules', loc='left', fontsize=11)
    ax1.set_ylabel('National demand-weighted RMX adoption (%)')
    ax1.set_xlabel('Year')
    ax1.set_ylim(bottom=0)
    ax1.set_title('(b) Prospective LC3 adoption: median and seed range (n=10)',
                  loc='left', fontsize=11)
    ax1.xaxis.set_major_locator(mdates.YearLocator(3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    for ax in (ax0, ax1):
        ax.grid(alpha=.18)
        ax.spines[['top', 'right']].set_visible(False)
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.55, .98),
               fontsize=8.5, ncol=2, frameon=False)
    fig.subplots_adjust(left=.13, right=.98, top=.86, bottom=.09)
    out = ROOT / 'figures'
    out.mkdir(exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'lc3_national_regulatory_schedules.{ext}',
                    dpi=250, bbox_inches='tight')
    pd.DataFrame(summary).to_csv(out / 'lc3_national_regulatory_2045_summary.csv', index=False)
    plt.close(fig)
    print('Figure:', out / 'lc3_national_regulatory_schedules.pdf')
    print(pd.DataFrame(summary).to_string(index=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--prepare',action='store_true')
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--plot',action='store_true')
    args=ap.parse_args()
    if not any([args.prepare,args.run,args.plot]):
        args.prepare=args.run=args.plot=True
    if args.prepare:prepare()
    if args.run:run()
    if args.plot:plot()
