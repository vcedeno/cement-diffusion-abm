#!/usr/bin/env python3
"""Run from repository v2/code: python /path/to/v2_state_validation_audit.py
Reproduces validation ensemble and compares year-specific vs 2025 state weights.
Does not modify model or overwrite reference results.
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd()))
from config import RESULTS, MONTHS, T_OBS
from data import ModelData
from model import simulate, national_after_imports
from targets import usgs_targets, annual_state
from validate import predictive_sets

outdir = RESULTS / 'audit_state_metrics'
outdir.mkdir(exist_ok=True,parents=True)
d=ModelData(); tg=usgs_targets()
obs=tg['st_net'].reindex(d.states)
all_years=sorted(set(range(2010,2026)) & set(obs.columns))
print('Running predictive ensemble (same parameter sets and seeds as validate.py)...',flush=True)
curves=[]
for k,p in enumerate(predictive_sets()):
    for s in range(5):
        o=simulate(d,p,seed=10000+100*k+s)
        _,A=national_after_imports(d,o['A_st'])
        curves.append(annual_state(d.states,A)[all_years].to_numpy())
curves=np.asarray(curves)
med=np.median(curves,axis=0)
rows=[]
for j,year in enumerate(all_years):
    mask=(MONTHS.year==year)
    demand=np.asarray(d.Sm @ d.D[mask].sum(axis=0)).ravel()
    w=demand/demand.sum()
    d2025=np.asarray(d.Sm @ d.D[MONTHS.year==2025].sum(axis=0)).ravel()
    w2025=d2025/d2025.sum()
    y=obs[year].to_numpy(dtype=float)
    valid=np.isfinite(y)
    residual=med[:,j]-y
    # Match repository fillna(0) convention, plus report valid-only alternative.
    residual_filled=med[:,j]-np.nan_to_num(y,nan=0)
    rows.append(dict(year=year,rmse_year_weighted=float(np.sqrt(np.sum(w*residual_filled**2))),
        rmse_2025_weighted=float(np.sqrt(np.sum(w2025*residual_filled**2))),
        rmse_valid_only=float(np.sqrt(np.sum(w[valid]*residual[valid]**2)/w[valid].sum())) if valid.any() else None,
        missing_states=int((~valid).sum())))
    for i,state in enumerate(d.states):
        pass
pd.DataFrame(rows).to_csv(outdir/'annual_state_rmse_audit.csv',index=False)
records=[dict(state=state,year=year,model=float(med[i,j]),observed=float(obs.loc[state,year]) if pd.notna(obs.loc[state,year]) else np.nan,
              error=float(med[i,j]-obs.loc[state,year]) if pd.notna(obs.loc[state,year]) else np.nan)
    for j,year in enumerate(all_years) for i,state in enumerate(d.states)]
pd.DataFrame(records).to_csv(outdir/'state_annual_predictions.csv',index=False)
print(pd.DataFrame(rows).query('year in [2022,2025]').to_string(index=False))
print('Saved:',outdir)
