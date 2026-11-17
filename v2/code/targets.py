"""Observed targets from USGS shipments and helpers to aggregate model output.

The adoption measure is the blended share of portland + blended cement shipments, net of the 2016-19
baseline (blended cements such as Type IP that existed before the PLC transition). National: monthly.
State: annual, net of each state's own 2016-19 baseline, floored at zero.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from config import DERIVED, MONTHS, OBS_END


def usgs_targets() -> dict:
    g = pd.read_csv(DERIVED / "usgs_state_month.csv")
    g = g[g["ym"].between("2010-01", OBS_END)]
    nat = g.groupby("ym")[["blended", "portland"]].sum()
    nat_share = (nat["blended"] / (nat["blended"] + nat["portland"])).reindex(MONTHS.astype(str)).to_numpy()
    nat_base = np.nanmean(nat_share[(MONTHS.year >= 2016) & (MONTHS.year <= 2019)])
    g["yr"] = g["ym"].str[:4].astype(int)
    ann = g.groupby(["st", "yr"])[["blended", "portland"]].sum()
    ann = (ann["blended"] / (ann["blended"] + ann["portland"])).unstack()
    base = ann.loc[:, 2016:2019].mean(axis=1)
    net = ann.sub(base, axis=0).clip(lower=0)
    return dict(nat_raw=nat_share, nat_net=np.clip(nat_share - nat_base, 0, None), nat_base=nat_base,
                st_raw=ann, st_net=net, st_base=base)


def monthly_state_net(states) -> np.ndarray:
    """S x T_obs monthly state share net of the state's 2016-19 monthly mean (used for the firms' follower pull)."""
    from config import T_OBS
    u = pd.read_csv(DERIVED / "usgs_state_month.csv")
    u = u[u["ym"] <= "2024-12"]                                 # the hazard is estimated on 2012-22; 2025 not needed
    u["sh"] = u.blended / (u.blended + u.portland).replace(0, np.nan)
    piv = u.pivot(index="st", columns="ym", values="sh")
    base = piv.loc[:, "2016-01":"2019-12"].mean(1)
    net = piv.sub(base, axis=0).clip(lower=0).reindex(states)
    return net.reindex(columns=[str(m) for m in MONTHS[:T_OBS]]).fillna(0).to_numpy()


def annual_state(states, A_st: np.ndarray) -> pd.DataFrame:
    """States x years: simple mean of the monthly demand-weighted state shares."""
    df = pd.DataFrame(A_st.T, columns=states)
    df["yr"] = MONTHS.year[:A_st.shape[1]]
    return df.groupby("yr").mean().T
