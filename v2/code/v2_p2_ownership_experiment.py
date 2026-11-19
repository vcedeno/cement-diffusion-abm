#!/usr/bin/env python3
"""Paired V2 ownership-exclusivity experiment, no repository files modified.
Run from repository root: python /path/to/v2_p2_ownership_experiment.py --repo v2 --runs 20
"""
import argparse, json, sys, types
from pathlib import Path
import numpy as np
import pandas as pd

p=argparse.ArgumentParser()
p.add_argument('--repo',type=Path,default=Path('v2'))
p.add_argument('--runs',type=int,default=20,help='Number of predictive parameter sets, 5 seeds each')
p.add_argument('--out',type=Path,default=None)
a=p.parse_args()
root=a.repo.resolve(); code=root/'code'; sys.path.insert(0,str(code))
from data import ModelData
from model import simulate, national_after_imports
from validate import predictive_sets
from targets import usgs_targets, annual_state
from config import MONTHS,T_OBS

source=(code/'model.py').read_text()
# Remove ONLY exclusive-parent purchasing, retaining same geographic network.
# Purchase from all connected operating plants; remove double-counted parent contributions.
old='has_par = np.asarray(d.Aown.sum(1)).ravel() > 0'
new='has_par = np.zeros(R, dtype=bool)'
assert source.count(old)==1
source=source.replace(old,new)
old='Anon_eff = sparse.diags((~has_par).astype(float)) @ d.Anon'
new='Anon_eff = d.A'
assert source.count(old)==1
source=source.replace(old,new)
for old,new in [
    ('+ np.asarray(d.Aown @ frac).ravel()', '+ np.zeros(R)'),
    ('+ np.asarray(d.Aown @ both.astype(float)).ravel()', '+ np.zeros(R)'),
]:
    assert source.count(old)==1, f'Unexpected V2 source layout: {old}'
    source=source.replace(old,new)
module=types.ModuleType('model_p2_all_suppliers');module.__file__=str(code/'model.py')
exec(compile(source,str(code/'model.py'),'exec'),module.__dict__)

out=a.out or root/'results'/'p2_ownership_experiment';out.mkdir(parents=True,exist_ok=True)
d=ModelData(); params=predictive_sets()[:a.runs]; tg=usgs_targets()
obs=tg['st_net'].reindex(d.states)[2025].to_numpy(float)
obs_nat=float(np.mean(tg['nat_net'][T_OBS-12:T_OBS]))
weights=np.asarray(d.Sm @ d.D[T_OBS-12:T_OBS].sum(0)).ravel();weights=weights/weights.sum()
selected=['CA','DE','NM','NH','NV','PA','TX']
rows=[]; state_rows=[]
for k,prm in enumerate(params):
    for s in range(5):
        seed=10000+100*k+s
        b=simulate(d,prm,seed=seed)
        c=module.simulate(d,prm,seed=seed)
        bn,bs=national_after_imports(d,b['A_st']);cn,cs=national_after_imports(d,c['A_st'])
        b25=bs[:,T_OBS-12:T_OBS].mean(axis=1);c25=cs[:,T_OBS-12:T_OBS].mean(axis=1)
        mask=np.isfinite(obs)
        br=np.sqrt(np.sum(weights[mask]*(b25[mask]-obs[mask])**2)/weights[mask].sum())
        cr=np.sqrt(np.sum(weights[mask]*(c25[mask]-obs[mask])**2)/weights[mask].sum())
        rows.append(dict(set=k,seed=seed,baseline_state_rmse=br,all_suppliers_state_rmse=cr,
                         baseline_national=float(bn[T_OBS-12:T_OBS].mean()),
                         all_suppliers_national=float(cn[T_OBS-12:T_OBS].mean()),
                         observed_national=obs_nat,
                         baseline_firm_starts=int((b['fconv']<T_OBS).sum()),
                         all_suppliers_firm_starts=int((c['fconv']<T_OBS).sum())))
        for st in selected:
            if st not in d.states:continue
            i=d.states.index(st)
            state_rows.append(dict(set=k,seed=seed,state=st,observed=obs[i],baseline=b25[i],all_suppliers=c25[i],
                                   baseline_abs_error=abs(b25[i]-obs[i]),all_suppliers_abs_error=abs(c25[i]-obs[i])))
    print(f'Completed parameter set {k+1}/{len(params)}',flush=True)
rr=pd.DataFrame(rows);sr=pd.DataFrame(state_rows)
rr.to_csv(out/'paired_runs.csv',index=False);sr.to_csv(out/'paired_states.csv',index=False)
summary=sr.groupby('state').agg(observed=('observed','median'),baseline=('baseline','median'),all_suppliers=('all_suppliers','median'),baseline_abs_error=('baseline_abs_error','median'),all_suppliers_abs_error=('all_suppliers_abs_error','median')).reset_index()
summary['change_pp']=100*(summary['all_suppliers']-summary['baseline'])
summary['abs_error_change_pp']=100*(summary['all_suppliers_abs_error']-summary['baseline_abs_error'])
summary.to_csv(out/'state_summary.csv',index=False)
print('\nSTATE RESULTS (percentage points):')
print(summary.round(3).to_string(index=False))
print('\nNATIONAL / STATE RMSE (median across paired runs):')
print(rr[['baseline_state_rmse','all_suppliers_state_rmse','baseline_national','all_suppliers_national','observed_national','baseline_firm_starts','all_suppliers_firm_starts']].median().round(4).to_string())
print('\nSaved:',out)
