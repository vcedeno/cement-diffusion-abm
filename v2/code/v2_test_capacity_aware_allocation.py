#!/usr/bin/env python3
"""V2 P1 diagnostic: compare original equal-supplier shares with capacity-limited
allocations using EXACT SAME simulated plant events and per-link PLC propensities.
No model files or parameters are changed. Run: cd v2/code && python ../v2_test_capacity_aware_allocation.py

Capacity is assumed comparable to modeled RMX cement demand; this must be audited.
Allocation is a diagnostic, NOT a calibrated or validated market model.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent/'code'))
import numpy as np
import pandas as pd
from scipy import sparse
import model
from data import ModelData
from validate import predictive_sets
from config import MONTHS, RESULTS

OUT=RESULTS/'audit_capacity_experiment'; OUT.mkdir(parents=True,exist_ok=True)
d=ModelData()
ps=predictive_sets()
NSETS=1  # one parameter set x 5 seeds first; increase only after checking diagnostics
SEEDS=5
YEARS=(2023,2024,2025)
TSET={t for t,m in enumerate(MONTHS) if m.year in YEARS}

has_par=np.asarray(d.Aown.sum(1)).ravel()>0
Aeff=(sparse.diags(has_par.astype(float))@d.Aown+sparse.diags((~has_par).astype(float))@d.A).tocsr()
rr,jj=Aeff.nonzero()
rr=rr.astype(int);jj=jj.astype(int)
N=len(rr)

# Allocation uses original equal-supplier split as a preference, but never exceeds
# each plant's available capacity. Any demand that cannot be routed on existing
# links is explicitly recorded as unallocated (NOT silently renormalized).
def constrained_flow(demand, active, maxiter=500, tol=1e-7):
    cap=np.where(active,d.cap,0.0).astype(float).copy()
    flow=np.zeros(N,float)
    rem=np.maximum(demand,0).astype(float).copy()
    eligible=active[jj] & (cap[jj]>0)
    for _ in range(maxiter):
        possible=eligible & (cap[jj]>tol) & (rem[rr]>tol)
        if not possible.any():break
        degree=np.bincount(rr[possible],minlength=d.R)
        add=np.zeros(N,float)
        add[possible]=rem[rr[possible]]/degree[rr[possible]]
        load=np.bincount(jj,weights=add,minlength=d.J)
        scale=np.minimum(1,np.divide(cap,load,out=np.ones(d.J),where=load>0))
        add*=scale[jj]
        progress=add.sum()
        if progress<=tol:break
        flow+=add
        cap=np.maximum(0,cap-np.bincount(jj,weights=add,minlength=d.J))
        rem=np.maximum(0,rem-np.bincount(rr,weights=add,minlength=d.R))
    return flow,rem

rows=[];plantrows=[];check=[]
current={'seed':None}
def collect(t, opm, frac, both, pi, kap, keep_out, nsrc, share):
    if t not in TSET:return
    demand=d.D[t].astype(float)
    active=opm[jj].astype(bool)
    # Per-link PLC probability follows EXACT V2 purchasing numerators.
    prop=np.where(has_par[rr],frac[jj]+(1-kap[rr])*both[jj].astype(float),
                  frac[jj]*(1-keep_out[rr])+(1-kap[rr])*pi[rr]*both[jj].astype(float))
    prop=np.clip(prop,0,1)*active
    eq=np.divide(demand[rr],nsrc[rr],out=np.zeros(N,float),where=nsrc[rr]>0)*active
    reconstructed=np.bincount(rr,weights=eq*prop,minlength=d.R)/np.maximum(demand,1e-12)
    err=float(np.max(np.abs(reconstructed-share)))
    if err>1e-7:raise RuntimeError(f'Purchasing reconstruction mismatch {MONTHS[t]}: {err:.5g}')
    capflow,unallocated=constrained_flow(demand,opm)
    if (np.bincount(jj,weights=capflow,minlength=d.J)>d.cap+1e-4).any():
        raise RuntimeError('Capacity constraint failed')
    cfshare=np.bincount(rr,weights=capflow*prop,minlength=d.R)/np.maximum(demand,1e-12)
    state_demand=np.bincount(d.rs,weights=demand,minlength=d.S)
    eq_st=np.bincount(d.rs,weights=demand*share,minlength=d.S)/np.maximum(state_demand,1e-12)
    cf_st=np.bincount(d.rs,weights=demand*cfshare,minlength=d.S)/np.maximum(state_demand,1e-12)
    miss_st=np.bincount(d.rs,weights=unallocated,minlength=d.S)/np.maximum(state_demand,1e-12)
    # Apply same import dilution as model.national_after_imports.
    for s,st in enumerate(d.states):
        rows.append(dict(seed=current['seed'],month=str(MONTHS[t]),year=MONTHS[t].year,state=st,
            state_demand_t=state_demand[s],baseline_share=eq_st[s]*(1-d.m_imp[s]),
            capacity_aware_share=cf_st[s]*(1-d.m_imp[s]),
            unallocated_fraction=miss_st[s]))
    for j in np.flatnonzero((np.bincount(jj,weights=eq,minlength=d.J)>0)|(np.bincount(jj,weights=capflow,minlength=d.J)>0)):
        plantrows.append(dict(seed=current['seed'],month=str(MONTHS[t]),mfr_src_id=d.pid[j],
            baseline_implied_t=np.bincount(jj,weights=eq,minlength=d.J)[j],
            capacity_aware_t=np.bincount(jj,weights=capflow,minlength=d.J)[j],capacity_t=d.cap[j]))
    check.append(dict(seed=current['seed'],month=str(MONTHS[t]),max_reconstruction_error=err,
        total_demand_t=demand.sum(),baseline_allocated_t=eq.sum(),capacity_allocated_t=capflow.sum(),
        unallocated_t=unallocated.sum(),total_active_capacity_t=d.cap[opm].sum()))

# Inject a read-only callback at the original model's purchase-share calculation.
source=Path(model.__file__).read_text()
needle='        Dt = d.D[t]\n'
assert source.count(needle)==1,'Unexpected model source version; aborting'
source=source.replace(needle,'        _capacity_audit_callback(t,opm,frac,both,pi,kap,keep_out,nsrc,share)\n'+needle)
ns=dict(vars(model));ns['_capacity_audit_callback']=collect
exec(compile(source,str(model.__file__)+' [capacity audit]','exec'),ns)
sim=ns['simulate']
for k,p in enumerate(ps[:NSETS]):
    for s in range(SEEDS):
        current['seed']=10000+100*k+s
        sim(d,p,seed=current['seed'])
        print('Completed seed',current['seed'],flush=True)
R=pd.DataFrame(rows);P=pd.DataFrame(plantrows);C=pd.DataFrame(check)
R.to_csv(OUT/'monthly_state_comparison.csv',index=False)
P.to_csv(OUT/'plant_allocation_comparison.csv',index=False)
C.to_csv(OUT/'monthly_system_feasibility.csv',index=False)
# Demand-weighted annual shares; annual unallocated share uses the same demand weights.
R['baseline_t']=R.baseline_share*R.state_demand_t
R['capacity_t']=R.capacity_aware_share*R.state_demand_t
R['unallocated_t']=R.unallocated_fraction*R.state_demand_t
A=R.groupby(['seed','year','state'],as_index=False).agg(demand_t=('state_demand_t','sum'),baseline_t=('baseline_t','sum'),capacity_t=('capacity_t','sum'),unallocated_t=('unallocated_t','sum'))
A['baseline_share']=A.baseline_t/A.demand_t
A['capacity_aware_share']=A.capacity_t/A.demand_t
A['unallocated_fraction']=A.unallocated_t/A.demand_t
A['delta_pp']=100*(A.capacity_aware_share-A.baseline_share)
A.to_csv(OUT/'annual_state_comparison.csv',index=False)
print('\n2025 median state changes (percentage points), selected:')
print(A[(A.year==2025)&A.state.isin(['NM','DE','CA','NV','PA','TX'])].groupby('state')[['baseline_share','capacity_aware_share','unallocated_fraction','delta_pp']].median().round(4).to_string())
print('\n2025 system totals (monthly averages):')
print(C[C.month.str.startswith('2025')][['total_demand_t','capacity_allocated_t','unallocated_t','total_active_capacity_t']].mean().round(1).to_string())
print('\nOutputs:',OUT)
print('CAUTION: unallocated demand has zero PLC in this diagnostic, not necessarily OPC in reality. Large unallocated fractions mean the experiment is NOT a defensible market-share prediction.')
