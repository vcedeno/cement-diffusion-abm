#!/usr/bin/env python3
"""Read-only audit of V2's implied equal-supplier tonnage vs plant capacity.
Run: cd v2/code && python ../v2_audit_implied_capacity.py
Does NOT claim actual shipments: V2 computes purchasing shares, not constrained flows.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'code'))
import numpy as np
import pandas as pd
from scipy import sparse
from config import RESULTS, MONTHS
from data import ModelData

OUT = RESULTS / 'audit_implied_capacity'
OUT.mkdir(parents=True, exist_ok=True)
d = ModelData()
# Match model.py: cement-owned RMXs use parent plants only, others use all linked plants.
has_par = np.asarray(d.Aown.sum(axis=1)).ravel() > 0
Aeff = (sparse.diags(has_par.astype(float)) @ d.Aown +
        sparse.diags((~has_par).astype(float)) @ d.A).tocsr()
# NOTE: model.py nsrc uses d.A for non-owned and d.Aown for owned;
# eligibility is NOT filtered out of denominator, so match it exactly.
plant_rows, state_rows, month_rows = [], [], []
for t, month in enumerate(MONTHS):
    if month.year not in (2022, 2023, 2024, 2025):
        continue
    active = d.op[:, t].astype(float)
    Aactive = Aeff @ sparse.diags(active)
    nsrc = np.asarray(Aactive.sum(axis=1)).ravel()
    demand = d.D[t].astype(float)
    alloc_per_link = np.divide(demand, nsrc, out=np.zeros_like(demand), where=nsrc > 0)
    plant_tons = np.asarray(Aactive.T @ alloc_per_link).ravel()
    unmet = float(demand[nsrc == 0].sum())
    month_rows.append(dict(month=str(month), total_rmx_demand_t=float(demand.sum()),
                           allocated_demand_t=float(plant_tons.sum()),
                           no_operating_supplier_demand_t=unmet,
                           operating_plant_capacity_t=float(np.sum(d.cap * active)),
                           plants_above_capacity=int(np.sum((plant_tons > d.cap + 1e-6) & (active > 0))),
                           excess_t=float(np.maximum(plant_tons - d.cap * active, 0).sum())))
    for j in range(d.J):
        if plant_tons[j] <= 0 and not active[j]:
            continue
        plant_rows.append(dict(month=str(month),year=month.year,mfr_src_id=d.pid[j],
            plant_state=d.pstate[j],parent=d.fname[d.plant_firm[j]] if d.plant_firm[j]>=0 else '',
            operating=bool(active[j]), implied_allocated_t=float(plant_tons[j]),
            capacity_tpm=float(d.cap[j]),
            implied_utilization=float(plant_tons[j]/d.cap[j]) if d.cap[j]>0 else np.nan,
            implied_excess_t=float(max(plant_tons[j]-d.cap[j],0))))
    # State-specific share of each plant's implied deliveries; do not mistake for real deliveries.
    for state in ['NM','DE','CA','NV','PA','TX']:
        mask = d.rstate == state
        weights = np.where(mask, alloc_per_link, 0.0)
        vals = np.asarray(Aactive.T @ weights).ravel()
        total = float(demand[mask].sum())
        for j in np.flatnonzero(vals > 0):
            state_rows.append(dict(month=str(month),state=state,mfr_src_id=d.pid[j],
                plant_state=d.pstate[j],implied_state_t=float(vals[j]),
                share_of_state_rmx_demand=float(vals[j]/total) if total else np.nan))

plants = pd.DataFrame(plant_rows)
states = pd.DataFrame(state_rows)
monthly = pd.DataFrame(month_rows)
plants.to_csv(OUT/'plant_month_implied_allocation.csv',index=False)
states.to_csv(OUT/'state_plant_implied_allocation.csv',index=False)
monthly.to_csv(OUT/'monthly_capacity_summary.csv',index=False)
annual = (plants.groupby(['year','mfr_src_id','plant_state','parent'],dropna=False)
          .agg(implied_annual_t=('implied_allocated_t','sum'),
               annual_capacity_t=('capacity_tpm','sum'),
               peak_month_utilization=('implied_utilization','max'),
               months_above_capacity=('implied_excess_t',lambda x:int((x>1e-6).sum())),
               implied_excess_annual_t=('implied_excess_t','sum')).reset_index())
annual['annual_utilization']=annual.implied_annual_t/annual.annual_capacity_t.replace(0,np.nan)
annual.to_csv(OUT/'annual_plant_capacity.csv',index=False)
print('Saved outputs to',OUT)
print('NOTE: Implied equal-share allocation is NOT observed shipments or a simulated flow.')
print('\nPlant 49 annual:')
print(annual[annual.mfr_src_id==49].to_string(index=False))
print('\n2025 largest implied over-capacity:')
print(annual[annual.year==2025].sort_values('implied_excess_annual_t',ascending=False).head(12).to_string(index=False))
print('\n2025 system totals:')
print(monthly[monthly.month.str.startswith('2025')][['total_rmx_demand_t','allocated_demand_t','no_operating_supplier_demand_t','excess_t']].sum().to_string())
