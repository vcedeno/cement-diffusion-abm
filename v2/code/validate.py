"""Predictive runs: calibrated market layer + estimated firm hazard; calibration fit and 2023-25 forecast.

Parameter sets: the calibration trials within 10% of the best loss (at most 20). Each set is run with
5 seeds (10000 + 100 k + s); the firm-hazard coefficients are drawn from their estimated covariance
in every run. Firm starts are predicted (not the record).

Metrics (medians across the 100 runs)
  fit_rmse_2010_22, forecast_rmse_2023_25   national net share vs USGS
  share_2025, firms_2025                    level in 2025 vs record
  state_rmse_2022 / 2025                    demand-weighted RMSE of annual state shares
  firm timing error                         months; for record dates that are document dates ('started by'),
                                            only a model start later than the record counts as an error
  false_starts_expected                     expected number of firms that start in the model but not in the record
Outputs: results/validation_summary.json, results/curves_validation.npy (2 x runs x T: firm count, national share),
         results/fconv_validation.npy (runs x F firm start months)
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from config import RESULTS, MONTHS, T, T_OBS, CAL_END
from data import ModelData
from model import simulate, national_after_imports
from targets import usgs_targets, annual_state
from config import CAL_FIXED as FIXED, CAL_STRUCTURE as STRUCTURE


def parameter_sets(n=20, tol=1.10) -> list[dict]:
    cal = pd.read_csv(RESULTS / "calibration_trials.csv").sort_values("value")
    keep = cal[cal["value"] <= tol * cal["value"].min()].head(n)
    if len(keep) < n:
        keep = cal.head(n)
    out = []
    for r in keep.itertuples():
        p = {c[7:]: float(getattr(r, c)) for c in keep.columns if c.startswith("params_") and not pd.isna(getattr(r, c))}
        p.update({k: float(v) for k, v in FIXED.items()})
        p.update(STRUCTURE)
        out.append(p)
    return out


def predictive_sets(fit="mid") -> list[dict]:
    hz = json.load(open(RESULTS / "firm_hazard.json"))["fits"][fit]
    return [dict(p, firm_form="lf", lf=hz["coef"], lf_cov=hz["cov"], lf_a0=hz["a0"]) for p in parameter_sets()]


def firm_scores(d: ModelData, FC: np.ndarray, t_end: int) -> tuple[dict, pd.DataFrame]:
    bound = (d.firms["record_basis"] == "started by (document date)").to_numpy()
    p = (FC <= t_end).mean(0)
    rows = []
    for f in range(d.F):
        r = d.f_obs[f]
        if r <= t_end:
            diffs = np.where(FC[:, f] <= t_end, FC[:, f].astype(float) - r, t_end + 12 - r)
            err = np.maximum(diffs, 0) if bound[f] else np.abs(diffs)
            rows.append(dict(firm=d.fname[f], record_bound=bool(bound[f]), err_m=float(np.median(err)), p_start=float(p[f])))
        else:
            rows.append(dict(firm=d.fname[f], record_bound=False, err_m=np.nan, p_start=float(p[f])))
    R = pd.DataFrame(rows)
    st, nev = R.dropna(subset=["err_m"]), R[R.err_m.isna()]
    cap = dict(zip(d.fname, d.fcap_share))
    return dict(firm_err_median_m=float(st.err_m.median()), firm_err_mean_m=float(st.err_m.mean()),
                false_starts_expected=float(nev.p_start.sum()),
                false_start_capacity=float(sum(cap[n] * q for n, q in zip(nev.firm, nev.p_start))),
                missed_expected=float((1 - st.p_start).sum())), R


if __name__ == "__main__":
    d = ModelData()
    tg = usgs_targets()
    y = tg["nat_net"][:T_OBS]
    TR = int((MONTHS <= CAL_END).sum())
    obs_c = np.array([(d.f_obs <= t).sum() for t in range(T)])
    FC, NC, CC, AN = [], [], [], []
    for k, p in enumerate(predictive_sets()):
        for s in range(5):
            o = simulate(d, p, seed=10000 + 100 * k + s)
            nat, A = national_after_imports(d, o["A_st"])
            FC.append(o["fconv"]); NC.append(nat); CC.append([(o["fconv"] <= t).sum() for t in range(T)])
            AN.append(annual_state(d.states, A)[[2022, 2025]].to_numpy())
    FC, NC, CC, AN = np.array(FC), np.array(NC), np.array(CC, float), np.array(AN)
    np.save(RESULTS / "curves_validation.npy", np.stack([CC, NC]))
    np.save(RESULTS / "fconv_validation.npy", FC)
    fit = np.sqrt(((NC[:, :TR] - y[:TR]) ** 2).mean(1))
    fc = np.sqrt(((NC[:, TR:T_OBS] - y[TR:T_OBS]) ** 2).mean(1))
    sc, R = firm_scores(d, FC, T_OBS - 1)
    st_obs = tg["st_net"].reindex(d.states)
    w = np.asarray(d.Sm @ d.D[T_OBS - 12:T_OBS].sum(0)).ravel(); w = w / w.sum()
    med = np.median(AN, 0)
    out = dict(fit_rmse_2010_22=float(np.median(fit)), forecast_rmse_2023_25=float(np.median(fc)),
               share_2025=float(np.median(NC[:, T_OBS - 12:T_OBS].mean(1))), share_2025_obs=float(y[T_OBS - 12:T_OBS].mean()),
               firms_2025=float(np.median(CC[:, T_OBS - 1])), firms_2025_obs=int(obs_c[T_OBS - 1]),
               state_rmse_2022=float(np.sqrt((w * (med[:, 0] - st_obs[2022].fillna(0).to_numpy()) ** 2).sum())),
               state_rmse_2025=float(np.sqrt((w * (med[:, 1] - st_obs[2025].fillna(0).to_numpy()) ** 2).sum())), **sc)
    out["state_2025_model_vs_record"] = {s: [round(float(med[i, 1]), 3), round(float(st_obs.loc[s, 2025]), 3)]
                                         for i, s in enumerate(d.states)}
    out["firms_model_vs_record"] = R.round(3).to_dict(orient="records")
    cal = pd.read_csv(RESULTS / "calibration_trials.csv").sort_values("value")
    out["calibrated_best"] = {c[7:]: round(float(cal.iloc[0][c]), 4) for c in cal.columns if c.startswith("params_")}
    json.dump(out, open(RESULTS / "validation_summary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, (dict, list))}, indent=1))
