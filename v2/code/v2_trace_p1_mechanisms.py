#!/usr/bin/env python3
"""P1 diagnostics, read-only: inspect supply network and plant event timings.
Run from v2/code: python ../v2_trace_p1_mechanisms.py
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'code'))
import numpy as np
import pandas as pd
from config import RESULTS, MONTHS
from data import ModelData
from model import simulate
from validate import predictive_sets

STATES=['DE','NM','CA','NV','PA','TX']
YEARS=[2022,2023,2025]
OUT=RESULTS/'audit_p1_mechanisms';OUT.mkdir(parents=True,exist_ok=True)
d=ModelData()
P=d.plants.copy()
print(f'Model: {d.J} plants, {d.R} RMXs, {d.F} firms; tracing {STATES}',flush=True)
# Demand-weighted exposure to supplying plants: each connected operating supplier
# gets 1/n equal-share allocation for each RMX, consistent with basic network weights.
rows=[]
for state in STATES:
    ridx=np.where(d.rstate==state)[0]
    if not len(ridx):continue
    for year in YEARS:
        tidx=np.where(MONTHS.year==year)[0]
        demand=d.D[tidx][:,ridx].sum(0)
        A=d.A[ridx,:].tocsr()
        degree=np.asarray(A.sum(1)).ravel()
        total=demand.sum()
        no_link=demand[degree==0].sum()/total if total else np.nan
        # Attribution is diagnostic: equal allocation among potential suppliers,
        # not simulated material flows or actual deliveries.
        weights=np.divide(demand,degree,out=np.zeros_like(demand,dtype=float),where=degree>0)
        byplant=np.asarray(A.T@weights).ravel()
        for j,wt in enumerate(byplant):
            if wt<=0:continue
            rows.append(dict(state=state,year=year,mfr_src_id=d.pid[j],parent=d.plants.iloc[j].get('parent_2020_22',''),plant_state=d.pstate[j],potential_demand_t=wt,
                             state_share_of_demand=wt/total if total else np.nan,capacity_tpm=d.cap[j],
                             eligible=bool(d.eligible[j]),type_iiv=bool(d.iiv[j]),operating_months=int(d.op[j,tidx].sum()),
                             unlinked_demand_fraction=no_link,rmx_count=len(ridx)))
links=pd.DataFrame(rows)
links.to_csv(OUT/'potential_supplier_exposure.csv',index=False)
# Run original validation parameter sets and seeds, no changes to behavioral model.
ps=predictive_sets(); n=len(ps)*5
keep_states=np.isin(d.pstate,STATES)
plant_ids=set(links.mfr_src_id)
tracked=np.array([j for j,pid in enumerate(d.pid) if pid in plant_ids],int)
events=[]
for k,p in enumerate(ps):
    for s in range(5):
        seed=10000+100*k+s
        o=simulate(d,p,seed=seed)
        for j in tracked:
            events.append(dict(seed=seed,mfr_src_id=d.pid[j],intro_month=int(o['intro'][j]),withdrawal_month=int(o['wd'][j]),
                               firm_start_month=int(o['fconv'][d.plant_firm[j]]) if d.plant_firm[j]>=0 else -1))
    print(f'Completed parameter set {k+1}/{len(ps)}',flush=True)
E=pd.DataFrame(events)
T=len(MONTHS)
for field,prefix in [('intro_month','plc_available'),('withdrawal_month','opc_withdrawn')]:
    for year in YEARS:
        end=np.where(MONTHS.year==year)[0][-1]
        E[f'{prefix}_by_{year}']=(E[field]<=end).astype(int)
summary=E.groupby('mfr_src_id').agg({**{f'{p}_by_{y}':'mean' for p in ['plc_available','opc_withdrawn'] for y in YEARS},'intro_month':'median','withdrawal_month':'median'}).reset_index()
summary['median_intro_date']=summary.intro_month.map(lambda t:str(MONTHS[int(t)]) if t<T else 'not by model end')
summary['median_withdrawal_date']=summary.withdrawal_month.map(lambda t:str(MONTHS[int(t)]) if t<T else 'not by model end')
summary.to_csv(OUT/'plant_event_probabilities.csv',index=False)
joined=links.merge(summary,on='mfr_src_id',how='left')
joined.to_csv(OUT/'state_supplier_mechanisms.csv',index=False)
# Approximate fraction of demand exposed to plants that offer PLC / withdraw OPC,
# using fixed potential-supplier weights; not the actual modeled purchasing share.
agg=[]
for (state,year),g in joined.groupby(['state','year']):
    w=g.state_share_of_demand.to_numpy()
    agg.append(dict(state=state,year=year,potential_link_coverage=float(w.sum()),
                    exposure_to_plc_available=float(np.sum(w*g[f'plc_available_by_{year}'])),
                    exposure_to_opc_withdrawn=float(np.sum(w*g[f'opc_withdrawn_by_{year}'])),
                    exposure_to_type_iiv=float(np.sum(w*g.type_iiv)),
                    suppliers=int(len(g)),unlinked_demand_fraction=float(g.unlinked_demand_fraction.iloc[0])))
agg=pd.DataFrame(agg).sort_values(['state','year'])
agg.to_csv(OUT/'state_mechanism_summary.csv',index=False)
print('\n'+agg.to_string(index=False,float_format=lambda x:f'{x:.3f}'))
print('\nSaved files to',OUT)
print('IMPORTANT: potential supplier exposures are diagnostics, NOT deliveries or causal attributions.')
