#!/usr/bin/env python3
"""V2 network feasibility audit: maximum flow from operating plants to RMXs.
Run from repo root: python v2/code/v2_test_network_lp_feasibility.py
No model files or parameters are changed. Uses 2025 monthly demand and capacity.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import linprog
from data import ModelData
from config import MONTHS, RESULTS

d = ModelData()
out = RESULTS / "audit_network_lp_feasibility"
out.mkdir(parents=True, exist_ok=True)
# Same ownership restrictions as the previous capacity-aware experiment.
has_parent = np.asarray(d.Aown.sum(axis=1)).ravel() > 0
effective = (sparse.diags(has_parent.astype(float)) @ d.Aown
             + sparse.diags((~has_parent).astype(float)) @ d.A).tocsr()
r, j = effective.nonzero()
r, j = r.astype(int), j.astype(int)
E = len(r)
# Edge variables: nonnegative cement tonnage on each allowed RMX-plant link.
plant_constraints = sparse.csr_matrix((np.ones(E), (j, np.arange(E))), shape=(d.J, E))
rmx_constraints = sparse.csr_matrix((np.ones(E), (r, np.arange(E))), shape=(d.R, E))
A_ub = sparse.vstack([plant_constraints, rmx_constraints], format="csr")
records, state_records, plant_records = [], [], []
for t, month in enumerate(MONTHS):
    if month.year != 2025:
        continue
    demand = np.maximum(d.D[t], 0)
    cap = np.where(d.op[:, t], np.maximum(d.cap, 0), 0)
    result = linprog(-np.ones(E), A_ub=A_ub, b_ub=np.r_[cap, demand],
                     bounds=(0, None), method="highs")
    if not result.success:
        raise RuntimeError(f"{month}: LP failed: {result.message}")
    flow = np.maximum(result.x, 0)
    served = np.bincount(r, weights=flow, minlength=d.R)
    plant_flow = np.bincount(j, weights=flow, minlength=d.J)
    remaining = np.maximum(demand - served, 0)
    if np.max(plant_flow-cap) > 1e-4 or np.max(served-demand) > 1e-4:
        raise RuntimeError(f"{month}: infeasible LP solution")
    degree = np.asarray(effective @ d.op[:, t].astype(float)).ravel()
    no_source = degree == 0
    records.append(dict(month=str(month), demand_t=demand.sum(),
        lp_allocated_t=served.sum(), lp_unallocated_t=remaining.sum(),
        lp_unallocated_fraction=remaining.sum()/max(demand.sum(), 1),
        demand_no_active_supplier_t=demand[no_source].sum(),
        active_capacity_t=cap.sum()))
    for s, state in enumerate(d.states):
        mask = d.rs == s
        state_records.append(dict(month=str(month), state=state,
            demand_t=demand[mask].sum(), lp_allocated_t=served[mask].sum(),
            lp_unallocated_t=remaining[mask].sum(),
            no_active_supplier_demand_t=demand[mask & no_source].sum()))
    for k in range(d.J):
        plant_records.append(dict(month=str(month), mfr_src_id=d.pid[k],
            plant_state=d.pstate[k], capacity_t=cap[k], lp_allocated_t=plant_flow[k]))
    print(f"{month}: max served {served.sum():,.0f} / {demand.sum():,.0f} t "
          f"({100*served.sum()/max(demand.sum(),1):.1f}%)", flush=True)

summary = pd.DataFrame(records)
states = pd.DataFrame(state_records)
plants = pd.DataFrame(plant_records)
# The prior greedy experiment ran 5 seeds but allocation is independent of seed.
prior = RESULTS / "audit_capacity_experiment" / "monthly_system_feasibility.csv"
if prior.exists():
    g = pd.read_csv(prior).groupby("month", as_index=False).agg(
        greedy_allocated_t=("capacity_allocated_t","mean"),
        greedy_unallocated_t=("unallocated_t","mean"))
    summary = summary.merge(g, on="month", how="left")
    summary["additional_served_by_lp_t"] = summary.lp_allocated_t - summary.greedy_allocated_t
summary.to_csv(out / "monthly_lp_feasibility.csv", index=False)
states.to_csv(out / "state_month_lp_feasibility.csv", index=False)
plants.to_csv(out / "plant_month_lp_allocation.csv", index=False)
annual = states.groupby("state", as_index=False)[
    ["demand_t","lp_allocated_t","lp_unallocated_t","no_active_supplier_demand_t"]].sum()
annual["lp_unallocated_fraction"] = annual.lp_unallocated_t / annual.demand_t.clip(lower=1)
annual.to_csv(out / "state_2025_lp_summary.csv", index=False)
print("\n2025 monthly means:")
print(summary.select_dtypes("number").mean().round(1).to_string())
print("\nSelected states (annual):")
print(annual[annual.state.isin(["NM","DE","CA","NV","PA","TX"])].round(3).to_string(index=False))
print("\nSaved to", out)
print("NOTE: This is a maximum-flow feasibility bound, not a PLC-market-share prediction.")
