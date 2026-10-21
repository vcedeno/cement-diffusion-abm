#!/usr/bin/env python3
"""Integrated simplified historical PLC ABM.

Uses locked Stage-1 empirical state. No calibration is performed here.
Reference behavior:
  B_i = d_i + phi_s + p_i
  r_i = logistic[4 (B_i - 1)]
  lambda_A = 1-exp(-1/T_A), T_A=6 months
  h_i = x_i lambda_A r_i
  persistent Bernoulli RMX adoption
  Q_i = (1-a_i(t-1))(1-x_i) lambda_A r_i D_i
  Q_j = equal allocation of Q_i over operating potential MFRs
  u_j = Q_j / monthly capacity (equivalent to 12 Q_j / annual capacity)
  ubar_j = H_M-month rolling mean
  if ubar_j >= theta_M, availability is scheduled T_M months later

Dated plant evidence is an availability boundary: q_j=1 from that month forward.
Other evidence classes do not manufacture historical q_j switch dates.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd


def month_add(ym: str, n: int) -> str:
    return str(pd.Period(ym, freq="M") + int(n))


def logistic(z):
    z = np.clip(z, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-z))


def read_csv(path, dtype=None):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    return pd.read_csv(p, dtype=dtype)


def load_inputs(empirical_dir: Path, capacity_file: Path, evidence_file: Path):
    demand = read_csv(empirical_dir / "rmx_month_demand_exposure.csv", {"rmx_src_id": str})
    pairs = read_csv(empirical_dir / "mfr_rmx_pairs.csv", {"mfr_src_id": str, "rmx_src_id": str})
    peers = read_csv(empirical_dir / "rmx_peer_pairs.csv", {"rmx_src_id": str, "peer_src_id": str})
    dot = read_csv(empirical_dir / "dot_monthly_state.csv")
    cap = read_csv(capacity_file, {"mfr_src_id": str})
    evidence = read_csv(evidence_file, {"mfr_src_id": str})

    for df, cols, name in [
        (demand, {"yyyy_mm","state","rmx_src_id","D_i","d_i"}, "demand"),
        (pairs, {"mfr_src_id","rmx_src_id"}, "pairs"),
        (peers, {"rmx_src_id","peer_src_id"}, "peers"),
        (dot, {"state","yyyy_mm","phi_s"}, "DOT"),
        (cap, {"mfr_src_id","capacity_tpm_model"}, "capacity"),
        (evidence, {"mfr_src_id","model_evidence_class","supported_month_if_dated"}, "evidence"),
    ]:
        missing = cols - set(df.columns)
        if missing:
            raise KeyError(f"{name} missing columns: {sorted(missing)}")

    demand["rmx_src_id"] = demand["rmx_src_id"].astype(str).str.strip()
    pairs["rmx_src_id"] = pairs["rmx_src_id"].astype(str).str.strip()
    pairs["mfr_src_id"] = pairs["mfr_src_id"].astype(str).str.strip()
    peers["rmx_src_id"] = peers["rmx_src_id"].astype(str).str.strip()
    peers["peer_src_id"] = peers["peer_src_id"].astype(str).str.strip()
    cap["mfr_src_id"] = cap["mfr_src_id"].astype(str).str.strip()
    evidence["mfr_src_id"] = evidence["mfr_src_id"].astype(str).str.strip()

    demand["D_i"] = pd.to_numeric(demand["D_i"], errors="raise")
    demand["d_i"] = pd.to_numeric(demand["d_i"], errors="raise")
    dot["phi_s"] = pd.to_numeric(dot["phi_s"], errors="raise")
    cap["capacity_tpm_model"] = pd.to_numeric(cap["capacity_tpm_model"], errors="coerce")

    # Simple explicit rule agreed for the current implementation: any remaining
    # missing capacity gets the integrated-plant median proxy, 1.10 Mt/yr.
    miss = cap["capacity_tpm_model"].isna()
    if miss.any():
        print(f"[capacity] {int(miss.sum())} missing value(s): using 1.10 Mt/yr = 91,666.67 t/month")
        cap.loc[miss, "capacity_tpm_model"] = 1.10 * 1_000_000 / 12

    if (cap["capacity_tpm_model"] <= 0).any():
        raise RuntimeError("All model manufacturer capacities must be positive.")

    pairs = pairs.drop_duplicates(["mfr_src_id","rmx_src_id"])
    return demand, pairs, peers, dot, cap, evidence


def main():
    ap = argparse.ArgumentParser(description="Run simplified integrated PLC ABM")
    ap.add_argument("--empirical_dir", required=True)
    ap.add_argument("--capacity_file", required=True)
    ap.add_argument("--evidence_file", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--T_A", type=float, default=6.0)
    ap.add_argument("--H_M", type=int, default=6)
    ap.add_argument("--T_M", type=int, default=6)
    ap.add_argument("--theta_M", type=float, default=0.10)
    ap.add_argument(
        "--disable_endogenous_mfr",
        action="store_true",
        help="Disable Q->u->ubar endogenous manufacturer availability transitions; dated evidence boundaries still apply.",
    )
    ap.add_argument("--kappa", type=float, default=4.0)
    ap.add_argument("--B0", type=float, default=1.5)
    args = ap.parse_args()

    empirical_dir = Path(args.empirical_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    demand, pairs, peers, dot, cap, evidence = load_inputs(
        empirical_dir, Path(args.capacity_file), Path(args.evidence_file)
    )

    months = sorted(demand["yyyy_mm"].astype(str).unique())
    rmx_ids = sorted(demand["rmx_src_id"].unique())
    mfr_ids = sorted(cap["mfr_src_id"].unique())
    rmx_set, mfr_set = set(rmx_ids), set(mfr_ids)

    if set(pairs["rmx_src_id"]) != rmx_set:
        raise RuntimeError("Supply-pair RMX universe does not match demand RMX universe.")
    if not set(pairs["mfr_src_id"]).issubset(mfr_set):
        raise RuntimeError("Supply pairs contain MFR IDs absent from capacity file.")

    lambda_A = 1.0 - np.exp(-1.0 / args.T_A)
    rng = np.random.default_rng(args.seed)

    # Fast structural maps.
    mfrs_by_rmx = pairs.groupby("rmx_src_id")["mfr_src_id"].apply(list).to_dict()
    rmx_by_mfr = pairs.groupby("mfr_src_id")["rmx_src_id"].apply(list).to_dict()
    peers_by_rmx = peers.groupby("rmx_src_id")["peer_src_id"].apply(list).to_dict()
    cap_map = cap.set_index("mfr_src_id")["capacity_tpm_model"].astype(float).to_dict()

    # Operating interval. Blank means unrestricted over modeled period.
    start_map, end_map = {}, {}
    for _, row in cap.iterrows():
        j = row["mfr_src_id"]
        start_map[j] = None if pd.isna(row.get("operating_start")) else str(row.get("operating_start"))[:7]
        end_map[j] = None if pd.isna(row.get("operating_end")) else str(row.get("operating_end"))[:7]

    def operating(j, ym):
        st, en = start_map.get(j), end_map.get(j)
        if st and ym < st:
            return False
        # operating_end is treated as first inactive month (Catskill: 2011-06).
        if en and ym >= en:
            return False
        return True

    # Plant-specific evidence establishes a latest availability boundary.
    # Exact monthly dates are retained; year-only evidence is conservatively
    # assigned to December of the documented year.
    dated = evidence[
        evidence["model_evidence_class"].eq("plant_dated_availability_boundary")
        & evidence["supported_month_if_dated"].notna()
    ].copy()

    evidence_month = dict(zip(
        dated["mfr_src_id"],
        dated["supported_month_if_dated"].astype(str).str[:7],
    ))

    # Persistent states.
    a = {i: 0 for i in rmx_ids}
    q_endo = {j: 0 for j in mfr_ids}
    trigger_month = {j: None for j in mfr_ids}
    scheduled_month = {j: None for j in mfr_ids}
    u_history = {j: deque(maxlen=args.H_M) for j in mfr_ids}

    rmx_rows, mfr_rows = [], []

    print("\n[SIMPLIFIED PLC ABM]")
    print(f"months={months[0]}..{months[-1]}  RMX={len(rmx_ids):,}  MFR={len(mfr_ids):,}")
    print(f"lambda_A={lambda_A:.6f}  theta_M={args.theta_M:.3f}  H_M={args.H_M}  T_M={args.T_M}  seed={args.seed}")
    print(f"dated evidence boundaries={len(evidence_month)}")
    print(f"endogenous MFR response={'OFF' if args.disable_endogenous_mfr else 'ON'}")

    for ym in months:
        dm = demand[demand["yyyy_mm"].astype(str).eq(ym)].set_index("rmx_src_id")
        phi_map = dot[dot["yyyy_mm"].astype(str).eq(ym)].set_index("state")["phi_s"].to_dict()

        # 1. Manufacturer availability at start of month.
        q = {}
        q_source = {}
        for j in mfr_ids:
            op = operating(j, ym)
            ev_on = j in evidence_month and ym >= evidence_month[j]
            endo_on = scheduled_month[j] is not None and ym >= scheduled_month[j]
            if op and (ev_on or endo_on):
                q[j] = 1
                q_source[j] = "evidence" if ev_on and not endo_on else ("endogenous" if endo_on and not ev_on else "evidence+endogenous")
            else:
                q[j] = 0
                q_source[j] = "unavailable" if op else "not_operating"
            if endo_on:
                q_endo[j] = 1

        # 2. Access x_i = equal share of operating potential suppliers available.
        x = {}
        active_mfrs_by_rmx = {}
        for i in rmx_ids:
            active = [j for j in mfrs_by_rmx[i] if operating(j, ym)]
            active_mfrs_by_rmx[i] = active
            x[i] = float(np.mean([q[j] for j in active])) if active else 0.0

        # 3. Prior-month peer exposure.
        p = {}
        for i in rmx_ids:
            ps = peers_by_rmx.get(i, [])
            p[i] = float(np.mean([a.get(k, 0) for k in ps])) if ps else 0.0

        # 4-5. RMX pressure, readiness, hazard, persistent adoption draw.
        month_vals = {}
        a_prev = a.copy()
        for i in rmx_ids:
            row = dm.loc[i]
            state = str(row["state"])
            D_i = float(row["D_i"])
            d_i = float(row["d_i"])
            phi = float(phi_map.get(state, 0.0))
            B = d_i + phi + p[i]
            r = float(logistic(args.kappa*(B-args.B0)))
            h = float(np.clip(x[i]*lambda_A*r, 0.0, 1.0))
            adopted_now = 0
            if a[i] == 0 and rng.random() < h:
                a[i] = 1
                adopted_now = 1

            # 6. Latent demand uses beginning-of-month adoption state, per equation.
            Q_i = (1-a_prev[i]) * (1-x[i]) * lambda_A * r * D_i
            month_vals[i] = (state,D_i,d_i,phi,p[i],x[i],B,r,h,adopted_now,Q_i)

        # 7. Allocate Q_i equally over currently operating potential manufacturers.
        Qj = {j: 0.0 for j in mfr_ids}
        for i, vals in month_vals.items():
            Q_i = vals[-1]
            active = active_mfrs_by_rmx[i]
            if Q_i > 0 and active:
                share = Q_i / len(active)
                for j in active:
                    Qj[j] += share

        # Manufacturer signal + persistent signal.
        uj, ubar = {}, {}
        for j in mfr_ids:
            if operating(j, ym):
                uj[j] = Qj[j] / cap_map[j]
                u_history[j].append(uj[j])
                ubar[j] = float(np.mean(u_history[j])) if len(u_history[j]) == args.H_M else np.nan
            else:
                uj[j] = np.nan
                ubar[j] = np.nan
                u_history[j].clear()

        # 8. Trigger endogenous availability. Scheduling happens after this
        # month's state, preventing same-month circularity.
        # In the ablation, Q/u/ubar are still computed for auditability, but
        # they cannot change q_j.
        if not args.disable_endogenous_mfr:
            for j in mfr_ids:
                if not operating(j, ym) or q[j] == 1 or scheduled_month[j] is not None:
                    continue
                if np.isfinite(ubar[j]) and ubar[j] >= args.theta_M:
                    trigger_month[j] = ym
                    scheduled_month[j] = month_add(ym, args.T_M)

        for i, vals in month_vals.items():
            state,D_i,d_i,phi,peer,x_i,B,r,h,new,Q_i = vals
            rmx_rows.append({
                "yyyy_mm":ym,"state":state,"rmx_src_id":i,"D_i":D_i,"d_i":d_i,
                "phi_s":phi,"p_i":peer,"x_i":x_i,"B_i":B,"r_i":r,"h_i":h,
                "a_prev":a_prev[i],"adopted_this_month":new,"a_i":a[i],"Q_i":Q_i,
            })

        for j in mfr_ids:
            mfr_rows.append({
                "yyyy_mm":ym,"mfr_src_id":j,"operating":int(operating(j,ym)),
                "q_j":q[j],"q_source":q_source[j],"Q_j":Qj[j],"capacity_tpm_model":cap_map[j],
                "u_j":uj[j],"ubar_j":ubar[j],"trigger_month":trigger_month[j],
                "scheduled_availability_month":scheduled_month[j],
                "evidence_boundary_month":evidence_month.get(j),
            })

    rmx_out = pd.DataFrame(rmx_rows)
    mfr_out = pd.DataFrame(mfr_rows)

    # Outcomes: facility prevalence F and demand-weighted adoption A.
    state = rmx_out.groupby(["yyyy_mm","state"], as_index=False).agg(
        F_s=("a_i","mean"),
        demand=("D_i","sum"),
        adopted_demand=("D_i", lambda x: 0.0),
    )
    # compute weighted numerator explicitly
    num_s = (rmx_out.assign(_num=rmx_out["D_i"]*rmx_out["a_i"])
             .groupby(["yyyy_mm","state"],as_index=False)["_num"].sum())
    state = state.drop(columns="adopted_demand").merge(num_s,on=["yyyy_mm","state"])
    state["A_s"] = state["_num"] / state["demand"]
    state = state.drop(columns="_num")

    nat = rmx_out.assign(_num=rmx_out["D_i"]*rmx_out["a_i"]).groupby("yyyy_mm",as_index=False).agg(
        F=("a_i","mean"), demand=("D_i","sum"), adopted_demand=("_num","sum")
    )
    nat["A"] = nat["adopted_demand"] / nat["demand"]

    rmx_out.to_csv(out_dir / "rmx_monthly_states.csv", index=False)
    mfr_out.to_csv(out_dir / "mfr_monthly_states.csv", index=False)
    state.to_csv(out_dir / "state_month_adoption.csv", index=False)
    nat.to_csv(out_dir / "national_month_adoption.csv", index=False)

    # Compact manufacturer transition summary.
    trans = pd.DataFrame({"mfr_src_id":mfr_ids})
    trans["evidence_boundary_month"] = trans["mfr_src_id"].map(evidence_month)
    trans["trigger_month"] = trans["mfr_src_id"].map(trigger_month)
    trans["scheduled_availability_month"] = trans["mfr_src_id"].map(scheduled_month)
    trans.to_csv(out_dir / "mfr_transition_summary.csv", index=False)

    pd.DataFrame([
        {"parameter":"seed","value":args.seed},
        {"parameter":"T_A","value":args.T_A},
        {"parameter":"lambda_A","value":lambda_A},
        {"parameter":"behavioral_pressure","value":"d_i + phi_s + p_i"},
        {"parameter":"disable_endogenous_mfr","value":int(args.disable_endogenous_mfr)},
        {"parameter":"kappa","value":args.kappa},
        {"parameter":"B0","value":args.B0},
        {"parameter":"theta_M","value":args.theta_M},
        {"parameter":"H_M","value":args.H_M},
        {"parameter":"T_M","value":args.T_M},
    ]).to_csv(out_dir / "run_specification.csv", index=False)

    print("\n[FINAL]")
    print(f"RMX adopted: {int(rmx_out[rmx_out.yyyy_mm.eq(months[-1])]['a_i'].sum()):,} / {len(rmx_ids):,}")
    print(f"Final facility prevalence F = {nat.iloc[-1]['F']:.4f}")
    print(f"Final demand-weighted adoption A = {nat.iloc[-1]['A']:.4f}")
    print(f"MFR endogenous triggers = {sum(v is not None for v in trigger_month.values())} / {len(mfr_ids)}")
    print(f"MFR dated evidence boundaries = {len(evidence_month)}")
    print("Wrote outputs to:", out_dir)


if __name__ == "__main__":
    main()
