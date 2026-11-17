"""Model data: plants, parent firms, ready-mix network, demand, DOT windows, imports and plant attributes.

All tables are read from new_data/derived (built by build_inputs.py) and from original_data
(network and demand files of the cement-diffusion-abm repository, used unchanged).

Indices used throughout
  j  cement plant (J = 81, row order of plants.csv)
  f  parent firm (F = 22, row order of firms.csv)
  r  ready-mix plant (R, sorted ready-mix ids from the demand file)
  s  state (S, sorted state codes of ready-mix plants)
  t  month (config.MONTHS)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import sparse
from config import ORIG, NEW, DERIVED, MONTHS, T, T_OBS, T_DEM, midx, GCCA_DATE, ROADMAP_DATE


class ModelData:
    def __init__(self):
        P = pd.read_csv(DERIVED / "plants.csv")
        Fm = pd.read_csv(DERIVED / "firms.csv")
        dot = pd.read_csv(DERIVED / "dot_ranges.csv").set_index("state")
        self.plants, self.firms = P, Fm
        self.lags = pd.read_csv(DERIVED / "rollout_lags.csv")["lag_months"].to_numpy()   # within-firm rollout lags
        self.signals = [midx(GCCA_DATE), midx(ROADMAP_DATE)]

        # ---- cement plants
        self.J = len(P)
        self.pid = P["mfr_src_id"].to_numpy()
        jix = {j: k for k, j in enumerate(self.pid)}
        self.cap = P["capacity_tpm_model"].to_numpy(float)                  # t per month
        self.eligible = P["eligible"].to_numpy(bool)                        # False: white-cement plants (never PLC)
        self.prewave = np.array([midx(x) for x in P["prewave"]])            # PLC documented before 2020 (offered beside OPC)
        op_s = np.array([max(midx(x), 0) for x in P["operating_start"]])
        op_e = np.array([midx(x) for x in P["operating_end"]])
        tt = np.arange(T)
        self.op = (tt[None, :] >= op_s[:, None]) & (tt[None, :] < op_e[:, None])   # J x T operating
        self.pstate = P["state_code"].to_numpy()

        # ---- parent firms
        self.F = len(Fm)
        self.fname = Fm["parent_2020_22"].tolist()
        fix = {f: k for k, f in enumerate(self.fname)}
        self.plant_firm = np.array([fix.get(f, -1) for f in P["parent_2020_22"]])
        self.plant_firm[~self.eligible] = -1
        fcap = np.zeros(self.F)
        for j in range(self.J):
            if self.plant_firm[j] >= 0:
                fcap[self.plant_firm[j]] += self.cap[j]
        self.fcap_share = fcap / fcap.sum()
        self.f_obs = np.array([midx(x) for x in Fm["observed_first"]])     # record: first Type IL offered (validation target)
        self.member = Fm["gcca_member"].to_numpy(bool)                      # GCCA member (leader)
        ls = np.log(self.fcap_share)
        self.size_z = (ls - ls.mean()) / ls.std(ddof=0)                     # standardised log capacity share (hazard covariate)

        # ---- ready-mix network and demand (original_data, unchanged)
        pairs = pd.read_csv(ORIG / "mfr_rmx_pairs.csv")
        dem = pd.read_csv(ORIG / "rmx_month_demand_exposure.csv.gz", usecols=["yyyy_mm", "state", "rmx_src_id", "D_i"])
        self.rmx = np.sort(dem["rmx_src_id"].unique())
        rix = {r: k for k, r in enumerate(self.rmx)}
        self.R = len(self.rmx)
        rows = pairs["rmx_src_id"].map(rix).to_numpy()
        cols = pairs["mfr_src_id"].map(jix).to_numpy()
        ok = ~(pd.isna(rows) | pd.isna(cols))
        self.A = sparse.csr_matrix((np.ones(ok.sum()), (rows[ok].astype(int), cols[ok].astype(int))),
                                   shape=(self.R, self.J))                  # R x J supply links
        dem["m"] = pd.PeriodIndex(dem["yyyy_mm"].astype(str), freq="M").map(lambda p: (p - MONTHS[0]).n)
        dem["r"] = dem["rmx_src_id"].map(rix)
        self.D = np.zeros((T, self.R))                                      # T x R demand (t cement)
        keep = dem["m"].to_numpy() < T
        self.D[dem["m"].to_numpy()[keep], dem["r"].to_numpy()[keep]] = dem["D_i"].to_numpy()[keep]
        st_of_r = dem.drop_duplicates("rmx_src_id").set_index("rmx_src_id")["state"].reindex(self.rmx).to_numpy()
        if T_OBS > T_DEM:
            # 2025: the 2024 profile of each ready-mix plant scaled by its state's USGS shipment ratio (same month, prior year)
            g = pd.read_csv(DERIVED / "usgs_state_month.csv")
            tot = g.assign(tot=g["blended"] + g["portland"]).pivot(index="st", columns="ym", values="tot")
            for t in range(T_DEM, T_OBS):
                ym, ym0 = str(MONTHS[t]), str(MONTHS[t - 12])
                ratio = (tot[ym] / tot[ym0]).reindex(st_of_r).fillna(1.0).to_numpy()
                self.D[t] = self.D[t - 12] * ratio
        for t in range(T_OBS, T):                                           # scenario years repeat the last 12 months
            self.D[t] = self.D[T_OBS - 12 + (t - T_OBS) % 12]
        self.rstate = st_of_r
        self.states = sorted(set(self.rstate))
        self.S = len(self.states)
        six = {s: k for k, s in enumerate(self.states)}
        self.rs = np.array([six[s] for s in self.rstate])                  # R: state of each ready-mix plant
        self.Sm = sparse.csr_matrix((np.ones(self.R), (self.rs, np.arange(self.R))), shape=(self.S, self.R))

        # ---- DOT acceptance windows (new_data): lower bound defaults to the 2012 standard
        lo_raw = [dot.loc[s, "not_before"] if s in dot.index else None for s in self.states]
        self.dot_lo = np.array([max(midx(x if isinstance(x, str) else "2012-01"), -1) for x in lo_raw])
        self.dot_hi = np.array([max(midx(dot.loc[s, "accepted_by"]), -1) if s in dot.index else -1 for s in self.states])

        # ---- imports: share of state consumption supplied by imported cement (ordinary portland), 2022 volumes
        m = pd.read_csv(DERIVED / "import_share_2022.csv").set_index("st")["import_share"]
        self.m_imp = m.reindex(self.states).fillna(0).to_numpy()

        # ---- weights
        self.dbar = self.D[:T_OBS].mean(0)                                  # R: mean monthly demand
        self.AT = self.A.T.tocsr()
        self.den_cust = np.asarray(self.AT @ self.dbar).ravel()            # J: demand of a plant's customers
        self.Wf = self.firm_customer_weights(self.dbar)                   # F x S: state mix of each firm's customers

        # ---- cement-owned ready-mix (vertical integration): owning parent index, -1 otherwise
        own = pd.read_csv(DERIVED / "rmx_owner.csv").set_index("id")["owner"]
        self.rowner = np.array([fix.get(o, -1) if isinstance(o, str) else -1 for o in own.reindex(self.rmx)])
        Ac = self.A.tocoo()
        own_link = (self.rowner[Ac.row] >= 0) & (self.plant_firm[Ac.col] == self.rowner[Ac.row])
        self.Aown = sparse.csr_matrix((Ac.data[own_link], (Ac.row[own_link], Ac.col[own_link])), shape=self.A.shape)
        self.Anon = (self.A - self.Aown).tocsr()

        # ---- plant attributes from evidence (new_data): conversion speed and Type II/V product line
        ce = pd.read_csv(NEW / "plant_conversion_evidence.csv").set_index("mfr_src_id").reindex(self.pid)
        self.ramp_j = ce["ramp_months"].fillna(12).to_numpy(float)          # months to full PLC after OPC withdrawal
        self.ramp_def = ce["ramp_basis"].fillna("no firm").str.startswith("no firm").to_numpy()   # no firm-level evidence
        self.iiv = ce["type_iiv_line"].fillna(0).to_numpy().astype(bool)    # standard OPC is sulfate-resistant Type II/V
        el = self.eligible.astype(float)
        self.iiv_r = np.asarray(self.A @ (self.iiv & self.eligible).astype(float)).ravel() \
            / np.maximum(np.asarray(self.A @ el).ravel(), 1e-9)              # R: exposure to Type II/V-line supply


    def firm_customer_weights(self, dbar) -> np.ndarray:
        """F x S: capacity-weighted state mix of the demand of each firm's customers (demand weights dbar)."""
        den = np.asarray(self.AT @ dbar).ravel()
        Pf = np.zeros((self.F, self.J))
        for j in range(self.J):
            if self.plant_firm[j] >= 0 and self.eligible[j]:
                Pf[self.plant_firm[j], j] = self.cap[j]
        Pf /= np.maximum(Pf.sum(1, keepdims=True), 1e-12)
        cust_st = np.asarray(self.AT @ (dbar[:, None] * (self.rs[:, None] == np.arange(self.S)[None, :]))) \
            / np.maximum(den[:, None], 1e-12)
        return Pf @ cust_st


def draw_dot(d: ModelData, rng) -> np.ndarray:
    """Acceptance month per state, uniform within its documented window."""
    lo, hi = d.dot_lo, np.maximum(d.dot_hi, d.dot_lo)
    return np.array([rng.integers(a, b + 1) for a, b in zip(lo, hi)])


def gate_share(d: ModelData, acc: np.ndarray) -> np.ndarray:
    """G[j, t]: demand-weighted share of plant j's customers located in states whose DOT has accepted PLC."""
    accepted = (np.arange(T)[:, None] >= acc[d.rs][None, :])             # T x R
    num = (d.A.T @ (d.D * accepted).T)
    den = (d.A.T @ d.D.T)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, 1.0)
