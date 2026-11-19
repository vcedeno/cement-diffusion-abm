#!/usr/bin/env python3
"""P2: Seven-state supplier-coverage audit for V2, 2025.
Run: python v2/code/v2_p2_seven_state_supplier_coverage.py
Descriptive audit only: does not create or validate new supply links.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import sparse
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import ModelData
from config import MONTHS, RESULTS

STATES = ['DE','NM','NH','PA','TX','CA','NV']
d = ModelData()
out = RESULTS / 'audit_p2_supplier_coverage'
out.mkdir(parents=True, exist_ok=True)
# Match V2 ownership priority: RMXs with any parent link only consider parent plants.
all_links = d.A.tocsr().astype(bool).astype(float)
owned_links = d.Aown.tocsr().astype(bool).astype(float)
has_parent = np.asarray(owned_links.sum(axis=1)).ravel() > 0
effective = (sparse.diags(has_parent.astype(float)) @ owned_links +
             sparse.diags((~has_parent).astype(float)) @ all_links).tocsr()
rows, state_rows, detail_rows = [], [], []
for t, month in enumerate(MONTHS):
    if month.year != 2025:
        continue
    operating = d.op[:, t].astype(float)
    total_degree = np.asarray(all_links @ operating).ravel().astype(int)
    eligible_degree = np.asarray(effective @ operating).ravel().astype(int)
    demand = np.maximum(np.asarray(d.D[t], dtype=float), 0)
    for state in STATES:
        mask = np.asarray(d.states)[d.rs] == state
        D = float(demand[mask].sum())
        if D <= 0:
            continue
        row = {'month':str(month), 'state':state, 'demand_t':D,
               'rmx_count':int(mask.sum()),
               'rmx_zero_supplier':int((eligible_degree[mask]==0).sum()),
               'rmx_one_supplier':int((eligible_degree[mask]==1).sum()),
               'rmx_multi_supplier':int((eligible_degree[mask]>=2).sum()),
               'demand_zero_supplier_t':float(demand[mask & (eligible_degree==0)].sum()),
               'demand_one_supplier_t':float(demand[mask & (eligible_degree==1)].sum()),
               'demand_multi_supplier_t':float(demand[mask & (eligible_degree>=2)].sum()),
               'demand_parent_restricted_t':float(demand[mask & has_parent].sum()),
               'demand_parent_restricted_loses_operating_alternative_t':float(
                   demand[mask & has_parent & (total_degree>eligible_degree)].sum()),
               'demand_no_eligible_but_other_operating_link_t':float(
                   demand[mask & (eligible_degree==0) & (total_degree>0)].sum()),
               'demand_no_operating_link_at_all_t':float(
                   demand[mask & (total_degree==0)].sum())}
        state_rows.append(row)
    if month.month == 12:
        for state in STATES:
            ids = np.where(np.asarray(d.states)[d.rs] == state)[0]
            for i in ids:
                suppliers = effective.getrow(i).indices
                active = suppliers[operating[suppliers]>0]
                detail_rows.append({'state':state,'rmx_index':int(i),
                    'dec_2025_demand_t':float(demand[i]),
                    'has_parent_supplier_restriction':bool(has_parent[i]),
                    'all_operating_supplier_count':int(total_degree[i]),
                    'eligible_operating_supplier_count':int(eligible_degree[i]),
                    'eligible_active_plant_ids':';'.join(map(str, d.pid[active]))})
monthly = pd.DataFrame(state_rows)
monthly.to_csv(out/'seven_state_monthly_coverage.csv', index=False)
annual = monthly.groupby('state',as_index=False).agg({
    'demand_t':'sum',
    'demand_zero_supplier_t':'sum', 'demand_one_supplier_t':'sum',
    'demand_multi_supplier_t':'sum', 'demand_parent_restricted_t':'sum',
    'demand_parent_restricted_loses_operating_alternative_t':'sum',
    'demand_no_eligible_but_other_operating_link_t':'sum',
    'demand_no_operating_link_at_all_t':'sum',
    'rmx_count':'mean', 'rmx_zero_supplier':'mean',
    'rmx_one_supplier':'mean','rmx_multi_supplier':'mean'})
for k in ['zero_supplier','one_supplier','multi_supplier','parent_restricted',
          'parent_restricted_loses_operating_alternative',
          'no_eligible_but_other_operating_link_at_all', 'no_operating_link_at_all']:
    col = 'demand_'+k+'_t'
    if col in annual:
        annual[k+'_demand_pct'] = 100*annual[col]/annual.demand_t
annual.to_csv(out/'seven_state_annual_coverage.csv',index=False)
details = pd.DataFrame(detail_rows)
details.to_csv(out/'seven_state_rmx_dec2025.csv',index=False)
print('\n2025 supplier coverage, demand-weighted (%):')
cols = ['state','demand_t','zero_supplier_demand_pct','one_supplier_demand_pct',
        'multi_supplier_demand_pct','parent_restricted_demand_pct',
        'no_operating_link_at_all_demand_pct']
print(annual[cols].round(2).to_string(index=False))
print('\nFiles saved:',out)
print('Interpretation: zero eligible suppliers indicates missing *modeled access*, not a verified missing commercial link.')
print('No network links or PLC market shares have been modified.')
