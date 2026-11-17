"""Calibrate the market layer on 2010-01 .. 2022-12 with firm starts replayed from the record.

Free parameters and search ranges
  sigR  (0, 1)     ready-mix switching away from PLC-only supply while OPC is reachable
  piL   (0, 1)     PLC purchase probability per unit of last month's state PLC share (market norm)
  piD   (0, 0.5)   PLC purchase probability added by the procurement shift
  pi0   (0, 0.05)  base PLC purchase probability from a plant offering both
  kiiv  (0, 1)     product-class constraint for buyers supplied by Type II/V-line plants
Fixed: lC = 1 (leaders' tolerance), H = 18 months (fade of ready-mix switching), sigma = 1.

Loss = mean over months of (national share sim - obs)^2                      (2010-01 .. 2022-12)
     + 0.01 x demand-weighted mean over states and years of (state share sim - obs)^2   (2020, 2021, 2022)
Each trial runs 8 simulations with seeds 0-7 (common random numbers across trials).
Search: Optuna TPE (multivariate, seed 20261107), 1500 trials, three enqueued starting points.

Firm starts are an input here (replay). They are predicted, not replayed, in validate.py.
Output: results/calibration_trials.csv (all completed trials, sorted by loss).
Usage: python calibrate.py [N_TRIALS]
"""
from __future__ import annotations
import sys
import numpy as np
import optuna
from config import RESULTS, MONTHS, CAL_END, CAL_FIXED, CAL_STRUCTURE
from data import ModelData
from model import simulate, national_after_imports
from targets import usgs_targets, annual_state

SPACE = dict(lC=(0.0, 1.0), piL=(0.0, 1.0), piD=(0.0, 0.5), pi0=(0.0, 0.05), sigR=(0.0, 1.0), H=(1.0, 48.0), kiiv=(0.0, 1.0))
FIXED, STRUCTURE = CAL_FIXED, CAL_STRUCTURE
STATE_WEIGHT, STATE_YEARS, N_SIM = 0.01, [2020, 2021, 2022], 8

data = ModelData()
tg = usgs_targets()
TR = int((MONTHS <= CAL_END).sum())
obs_s = tg["nat_net"][:TR]
ST_OBS = tg["st_net"].reindex(data.states)[STATE_YEARS].fillna(0).to_numpy()
_w = np.asarray(data.Sm @ data.D[:TR].sum(0)).ravel()
ST_W = _w / _w.sum()


def make_prm(trial) -> dict:
    prm = {k: (float(FIXED[k]) if k in FIXED else trial.suggest_float(k, lo, hi)) for k, (lo, hi) in SPACE.items()}
    prm.update(STRUCTURE)
    return prm


def objective(trial) -> float:
    prm = make_prm(trial)
    sh, stl = [], []
    for s in range(N_SIM):
        o = simulate(data, prm, seed=s)
        nat, A = national_after_imports(data, o["A_st"])
        sh.append(nat[:TR])
        an = annual_state(data.states, A)[STATE_YEARS].to_numpy()
        stl.append(float((ST_W[:, None] * (an - ST_OBS) ** 2).sum() / len(STATE_YEARS)))
    ls, lst = float(((np.array(sh) - obs_s[None, :]) ** 2).mean()), float(np.mean(stl))
    trial.set_user_attr("loss_share", ls)
    trial.set_user_attr("loss_state", lst)
    return ls + STATE_WEIGHT * lst


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    st = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=20261107, multivariate=True))
    warm = dict(piL=0.1, piD=0.0, pi0=0.0, sigR=0.2, kiiv=0.5)
    for w in (warm, dict(warm, sigR=0.05), dict(warm, piL=0.3, sigR=0.4)):
        st.enqueue_trial(w)
    st.optimize(objective, n_trials=n)
    df = st.trials_dataframe()
    df = df[df["state"] == "COMPLETE"].sort_values("value")
    df.to_csv(RESULTS / "calibration_trials.csv", index=False)
    print("best loss", round(st.best_value, 6), {k: round(v, 3) for k, v in st.best_params.items()})
