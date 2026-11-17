"""Estimate the parent-firm start hazard (leaders/followers) from the firm-month record, 2012-01 .. 2022-12.

    logit h_f(t) = a0 + aG * member_f * 1[t >= GCCA]                     (leaders respond to the GCCA statement)
                      + aP * member_f * 1[t >= roadmap]                  (and to the PCA roadmap)
                      + aS * member_f * 1[t >= GCCA] * size_f            (larger members respond sooner)
                      + aF * (1 - member_f) * pull_f(t - 1)              (followers respond to their customers' market)

  member_f  GCCA membership (new_data/firm_attributes.csv)
  size_f    standardised log capacity share
  pull_f    customer-state-weighted 3-month mean of the observed net PLC share (USGS), lagged one month
  a0        pinned so that S0 firms would start alone over 2012-01 .. 2020-08 (S0 = 0.15, 0.5, 1.5; record: 0)

Fitted by maximum likelihood on firm-months at risk (a firm leaves the risk set after its start month).
Writes results/firm_hazard.json (coefficients, covariance, a0 for each S0) and results/firm_month_panel.csv.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from config import RESULTS, T_OBS, T_DEM, midx, GCCA_DATE, ROADMAP_DATE
from data import ModelData
from targets import monthly_state_net


def build_panel(d: ModelData) -> pd.DataFrame:
    sm3 = pd.DataFrame(monthly_state_net(d.states)).T.rolling(3, min_periods=1).mean().T.to_numpy()
    Wf = d.firm_customer_weights(d.D[:T_DEM].mean(0))       # customer-state weights from the demand file period (2010-24)
    recs = []
    for f in range(d.F):
        for t in range(midx("2012-01"), T_OBS):
            if d.f_obs[f] < t:
                break
            recs.append(dict(firm=d.fname[f], f=f, t=t, y=int(d.f_obs[f] == t), member=int(d.member[f]),
                             pull=float(Wf[f] @ sm3[:, t - 1]), logcap=float(np.log(d.fcap_share[f]))))
    return pd.DataFrame(recs)


def fit(P: pd.DataFrame, S0: float, size=True) -> dict:
    P = P[(P.t >= midx("2012-01")) & (P.t <= midx("2022-12"))].copy()
    P["xg"] = P.member * (P.t >= midx(GCCA_DATE))
    P["xp"] = P.member * (P.t >= midx(ROADMAP_DATE))
    P["xf"] = (1 - P.member) * P.pull
    fl = P.groupby("firm").logcap.first()
    P["xs"] = P.xg * P.firm.map((fl - fl.mean()) / fl.std(ddof=0))
    npre = int((P.t < midx(GCCA_DATE)).sum())
    a0 = float(np.log((S0 / npre) / (1 - S0 / npre)))
    names = ["mem_g", "mem_p"] + (["mem_size"] if size else []) + ["non_pull"]
    X = P[["xg", "xp"] + (["xs"] if size else []) + ["xf"]].to_numpy(); y = P.y.to_numpy()
    nll = lambda b: float(np.sum(np.logaddexp(0, a0 + X @ b) - y * (a0 + X @ b)))
    r = minimize(nll, np.array([4.0, 2.0] + ([0.0] if size else []) + [20.0]), method="BFGS")
    p = 1 / (1 + np.exp(-(a0 + X @ r.x)))
    cov = np.linalg.inv((X * (p * (1 - p))[:, None]).T @ X)
    return dict(a0=a0, coef=dict(zip(names, map(float, r.x))), cov=cov.tolist(), se=dict(zip(names, np.sqrt(np.diag(cov)).tolist())),
                nll=float(r.fun), events=int(y.sum()), firm_months=len(P))


if __name__ == "__main__":
    d = ModelData()
    P = build_panel(d)
    P.to_csv(RESULTS / "firm_month_panel.csv", index=False)
    out = dict(members=[n for n, m in zip(d.fname, d.member) if m], window="2012-01..2022-12",
               fits={f"{k}": fit(P, s) for k, s in (("lo", 0.15), ("mid", 0.5), ("hi", 1.5))})
    json.dump(out, open(RESULTS / "firm_hazard.json", "w"), indent=1)
    for k, v in out["fits"].items():
        print(k, round(v["a0"], 3), {a: round(b, 3) for a, b in v["coef"].items()}, "se", {a: round(b, 3) for a, b in v["se"].items()})
