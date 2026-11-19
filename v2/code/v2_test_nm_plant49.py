#!/usr/bin/env python3
"""Paired V2 diagnostic: block OPC withdrawal at mfr_src_id=49, leave PLC introduction intact.
Run from v2/code: python ../v2_test_nm_plant49.py
Does not modify repository code or original results. Experiment is NOT a historical claim.
"""
from pathlib import Path
import sys, types, json
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent / 'code'))
import model
from data import ModelData
from validate import predictive_sets
from config import RESULTS, MONTHS
from targets import annual_state, usgs_targets

OUT=RESULTS/'audit_nm_plant49'
OUT.mkdir(parents=True,exist_ok=True)
d=ModelData()
match=np.flatnonzero(d.pid==49)
if len(match)!=1: raise RuntimeError(f'Expected exactly one plant ID 49; found {len(match)}')
j=int(match[0]); print('Target plant:',d.plants.iloc[j].to_dict(),flush=True)

# Compile a separate function from the current model source. The ONLY added behavior
# is preventing this plant from entering the OPC withdrawal candidate set.
source=Path(model.__file__).read_text()
needle='        if cand.any():\n'
if source.count(needle)!=1: raise RuntimeError('Model source changed: cannot locate unique withdrawal decision block')
source_cf=source.replace(needle,'        cand[_audit_plant_index] = False  # diagnostic: keep OPC at plant 49\n'+needle,1)
namespace=dict(vars(model));namespace['_audit_plant_index']=j
exec(compile(source_cf, str(model.__file__)+' [experiment]', 'exec'),namespace)
sim_cf=namespace['simulate']

# First five validation seeds, from the first calibrated parameter set.
# For more robustness, increase NSETS to 20 after the initial diagnostic.
NSETS=1
ps=predictive_sets()[:NSETS]
tidx={year:np.where(MONTHS.year==year)[0] for year in [2022,2023,2024,2025]}
rows=[];plant=[]
for k,p in enumerate(ps):
    for s in range(5):
        seed=10000+100*k+s
        for condition,fn in [('baseline',model.simulate),('keep_opc_49',sim_cf)]:
            o=fn(d,p,seed=seed)
            nat,states= model.national_after_imports(d,o['A_st'])
            annual=annual_state(d.states,states)
            for year in tidx:
                rows.append(dict(condition=condition,seed=seed,year=year,
                                 NM=float(annual.loc['NM',year]),
                                 national=float(np.mean(nat[tidx[year]]))))
            plant.append(dict(condition=condition,seed=seed,
                              intro_month=int(o['intro'][j]),withdrawal_month=int(o['wd'][j])))
        print('Finished seed',seed,flush=True)
R=pd.DataFrame(rows);R.to_csv(OUT/'paired_state_shares.csv',index=False)
P=pd.DataFrame(plant);P.to_csv(OUT/'plant49_events.csv',index=False)
wide=R.pivot(index=['seed','year'],columns='condition',values=['NM','national'])
D=pd.DataFrame({'year':[i[1] for i in wide.index],
                'delta_NM':[float(v) for v in (wide['NM']['keep_opc_49']-wide['NM']['baseline'])],
                'delta_national':[float(v) for v in (wide['national']['keep_opc_49']-wide['national']['baseline'])]})
D.groupby('year').agg(['median','min','max']).to_csv(OUT/'paired_effect_summary.csv')
print('\nMedian effects (experiment minus baseline, percentage points):')
print((100*D.groupby('year')[['delta_NM','delta_national']].median()).round(2).to_string())
print('\n2025 baseline and experiment NM share:')
print(R[R.year==2025].groupby('condition')[['NM','national']].median().round(4).to_string())
print('\nPlant events:');print(P.to_string(index=False))
print('\nFiles:',OUT)
print('NOTE: disabling a withdrawal can alter subsequent RNG consumption; use effects as a controlled structural diagnostic, not a fully common-random-number causal estimate.')
