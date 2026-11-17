"""Scenario runner: mechanism tests, one-at-a-time sensitivity, and example intervention / LC3-regime definitions.

Every scenario is a dictionary of overrides applied to each predictive parameter set (validate.predictive_sets),
run with the same seeds as the baseline (paired comparison). The horizon is extended to 2035 with PLC_END.

Override keys
  any simulate() parameter or scenario option (see model.simulate docstring)
  _acc        function(acc_draw, rng) -> DOT acceptance months per state
  _imp_scale  multiply every state's import share
  _imp_spec   'YYYY-MM' from which imports meet the PLC specification
  _scale      (parameter, factor): multiply a calibrated parameter of each set

Usage:  PLC_END=2035-12 python scenarios.py mechanisms|sensitivity|interventions|lc3
Outputs: results/scenarios_<set>_summary.csv, results/scenarios_<set>_runs.csv
Summary columns: y50 (first year the national share reaches 0.5), s2025/s2030/s2035 (annual shares),
  d_y50 (years earlier than baseline, + = faster), d_s2030 (change in 2030 share), never50 (share of runs
  that never reach 0.5), firms_2025.
"""
from __future__ import annotations
import os
import sys
import json
import numpy as np
import pandas as pd
from multiprocessing import Pool
from config import RESULTS, MONTHS, T, midx
from data import ModelData, draw_dot
from model import simulate, national_after_imports
from validate import predictive_sets

D = ModelData()
BASE = predictive_sets()
SEEDS = 5
HZ = json.load(open(RESULTS / "firm_hazard.json"))["fits"]
X = MONTHS.year + (MONTHS.month - 1) / 12
ix = {s: i for i, s in enumerate(D.states)}
nonmem = [i for i in range(D.F) if not D.member[i]]
big3 = [int(f) for f in np.argsort(-D.fcap_share)[:3]]


def lfv(fit, **chg):
    """Firm-hazard variant: intercept variant `fit` (lo/mid/hi); shifted coefficients are applied without draws."""
    c = dict(HZ[fit]["coef"]); c.update(chg)
    return {"lf": c, "lf_cov": None if chg else HZ[fit]["cov"], "lf_a0": HZ[fit]["a0"]}


def se(key):
    return HZ["mid"]["se"][key]


def dot_all(date):
    return lambda a, r: np.minimum(a, midx(date))


C = HZ["mid"]["coef"]
SETS = {
    "mechanisms": [("baseline", {}),
        ("no_industry_signals", {"sig_scale1": 0.0, "sig_scale2": 0.0}),
        ("no_GCCA_effect", {"sig_scale1": 0.0}),
        ("no_roadmap_effect", {"sig_scale2": 0.0}),
        ("no_follower_pull", {"follow_scale": 0.0}),
        ("no_DOT_gate", {"_acc": lambda a, r: np.full_like(a, -1)}),
        ("no_readymix_switching", {"sigR": 0.0}),
        ("no_procurement_response", {"piD": 0.0}),
        ("no_TypeIIV_plant_rule", {"iiv_keep": False}),
        ("no_TypeIIV_buyer_rule", {"kiiv": 0.0}),
        ("no_TypeIIV_rules", {"kiiv": 0.0, "iiv_keep": False}),
        ("no_import_dilution", {"_imp_scale": 0.0}),
        ("followers_convert_fully", {"follower_keep_opc": False}),
        ("no_plant_withdraws_OPC", {"all_keep_opc": True}),
        ("instant_conversion", {"ramp_all": 1}), ("slow_conversion_24m", {"ramp_all": 24})],
    "sensitivity": [("baseline", {}),
        ("solo_rate_low", lfv("lo")), ("solo_rate_high", lfv("hi")),
        ("aG_-1SE", lfv("mid", mem_g=C["mem_g"] - se("mem_g"))), ("aG_+1SE", lfv("mid", mem_g=C["mem_g"] + se("mem_g"))),
        ("aP_-1SE", lfv("mid", mem_p=C["mem_p"] - se("mem_p"))), ("aP_+1SE", lfv("mid", mem_p=C["mem_p"] + se("mem_p"))),
        ("aF_-1SE", lfv("mid", non_pull=C["non_pull"] - se("non_pull"))), ("aF_+1SE", lfv("mid", non_pull=C["non_pull"] + se("non_pull"))),
        ("size_-1SE", lfv("mid", mem_size=C["mem_size"] - se("mem_size"))), ("size_+1SE", lfv("mid", mem_size=C["mem_size"] + se("mem_size"))),
        ("no_size_effect", lfv("mid", mem_size=0.0)),
        ("piD_0.00", {"piD": 0.0}), ("piD_0.10", {"piD": 0.10}), ("piD_0.25", {"piD": 0.25}), ("piD_0.50", {"piD": 0.50}),
        ("sigR_x0.5", {"_scale": ("sigR", .5)}), ("sigR_x1.5", {"_scale": ("sigR", 1.5)}),
        ("H_9", {"H": 9}), ("H_27", {"H": 27}),
        ("imports_x0.5", {"_imp_scale": .5}), ("imports_x1.5", {"_imp_scale": 1.5}),
        ("default_ramp_6", {"ramp_default": 6}), ("default_ramp_18", {"ramp_default": 18}),
        ("dot_windows_latest", {"_acc": lambda a, r: np.maximum(a, D.dot_hi)}),
        ("dot_windows_earliest", {"_acc": lambda a, r: np.minimum(a, np.maximum(D.dot_lo, -1))})],
    # Example definitions (implementation of the ideas in docs/preliminary_results.md, section 6). Not reported.
    "interventions": [("baseline", {}),
        ("signals_8y_earlier", {"signal_shift": 96}),
        ("signals_and_DOT_2012", {"signal_shift": 96, "_acc": dot_all("2012-01")}),
        ("three_largest_start_2016", {"force_conv": {f: midx("2016-01") for f in big3}}),
        ("all_firms_in_club", {"members_extra": nonmem}),
        ("procurement_x2", {"_scale": ("piD", 2.0)}),
        ("imports_meet_spec_2022", {"_imp_spec": "2022-01"}),
        ("followers_supported_to_convert", {"follower_keep_opc": False}),
        ("sulfate_resistant_PLC_qualified_2023", {"iiv_release": "2023-01", "kiiv_release": "2023-01"}),
        ("OPC_sunset_2030", {"sunset": "2030-01"}),
        ("information_push_2024", {"pi_boost": (0.2, "2024-01")})],
    # Example LC3-type regime (docs/preliminary_results.md, section 7): no plant withdraws the incumbent product.
    "lc3": [("baseline", {}),
        ("regime", {"all_keep_opc": True}),
        ("regime_piD_0.25", {"all_keep_opc": True, "piD": 0.25}),
        ("regime_sunset_2030", {"all_keep_opc": True, "sunset": "2030-01"}),
        ("regime_specialty_class_qualifies_2030", {"all_keep_opc": True, "kiiv_release": "2030-01"})],
}


def metrics(nat, fc, A):
    yr = lambda Y: float(nat[(Y - 2010) * 12:(Y - 2009) * 12].mean()) if (Y - 2009) * 12 <= len(nat) else np.nan
    first = lambda q: float(X[np.argmax(nat >= q)]) if (nat >= q).any() else np.nan
    r = dict(y25=first(.25), y50=first(.50), s2025=yr(2025), s2030=yr(2030), s2035=yr(2035),
             firms_2025=int((fc <= midx("2025-12")).sum()))
    for s in ("CA", "AZ", "TX"):
        r[f"{s}_2030"] = float(A[ix[s], (2030 - 2010) * 12:(2031 - 2010) * 12].mean()) if T >= (2031 - 2010) * 12 else np.nan
    return r


def run_one(args):
    name, ov, k, s = args
    p, ov = dict(BASE[k]), dict(ov)
    if "_scale" in ov:
        key, f = ov.pop("_scale"); ov[key] = BASE[k][key] * f
    acc_fn, imp_spec, m_scale = ov.pop("_acc", None), ov.pop("_imp_spec", None), ov.pop("_imp_scale", None)
    p.update(ov)
    seed = 10_000 + 100 * k + s
    acc = acc_fn(draw_dot(D, np.random.default_rng([seed, 1])), np.random.default_rng(seed + 7)) if acc_fn else None
    o = simulate(D, p, seed=seed, acc=acc)
    nat, A = national_after_imports(D, o["A_st"], m_imp=(D.m_imp * m_scale if m_scale is not None else None),
                                    imp_spec_t=(midx(imp_spec) if imp_spec else None))
    return name, k, s, metrics(nat, o["fconv"], A)


def job(a):
    i, k, s = a
    n, ov = SETS[TAG][i]
    return run_one((n, ov, k, s))


TAG = sys.argv[1] if len(sys.argv) > 1 else "mechanisms"

if __name__ == "__main__":
    scen = SETS[TAG]
    jobs = [(i, k, s) for i in range(len(scen)) for k in range(len(BASE)) for s in range(SEEDS)]
    with Pool(int(os.environ.get("PLC_PROCS", 2))) as pool:
        res = pool.map(job, jobs, chunksize=10)
    Rr = pd.DataFrame([dict(scenario=n, k=k, s=s, **m) for n, k, s, m in res])
    Rr.to_csv(RESULTS / f"scenarios_{TAG}_runs.csv", index=False)
    b = Rr[Rr.scenario == "baseline"].set_index(["k", "s"])
    rows = []
    for n, _ in scen:
        g = Rr[Rr.scenario == n].set_index(["k", "s"])
        row = dict(scenario=n, **{c: round(float(g[c].median()), 3) for c in
                                  ("y25", "y50", "s2025", "s2030", "s2035", "firms_2025", "CA_2030", "AZ_2030", "TX_2030")})
        row["d_y50"] = round(float((b["y50"] - g["y50"]).median()), 3)
        row["d_s2030"] = round(float((g["s2030"] - b["s2030"]).median()), 3)
        row["never50"] = round(float(g["y50"].isna().mean()), 2)
        rows.append(row)
    S = pd.DataFrame(rows)
    S.to_csv(RESULTS / f"scenarios_{TAG}_summary.csv", index=False)
    pd.set_option("display.width", 220)
    print(S.to_string(index=False))
