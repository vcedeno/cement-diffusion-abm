#!/usr/bin/env python3
"""Build the empirical state for the simplified historical PLC ABM.

Stage 1 only. This script contains NO RMX adoption behavior, Bernoulli draws,
manufacturer response, or calibration.

Canonical structural inputs
---------------------------
* data/simple_abm/us/nodes.csv
* data/simple_abm/us/edges.csv

The script:
1. validates the 100 MFR / 3,761 RMX / 3,140 DIM / 50 DOT node universe;
2. extracts the forward MFR->RMX supply network from MFR_RMX and
   MFR_RMX_FALLBACK edges only;
3. constructs the 20-mile RMX peer network geometrically among supply-resolved
   RMX facilities;
4. constructs state demand -> RMX demand exposure D_i(t) -> bounded d_i(t);
5. constructs DOT acceptance g_s(t) -> implementation maturity phi_s(t);
6. parses the completed PLC manufacturer public-evidence audit into an evidence
   constraint table WITHOUT inventing monthly q_j(t) histories.

Historical PLC shipment shares are not supplied to agents.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

D_REF_DEFAULT = 1124.5848062887808  # 2010-2019 RMX-month median; 440,040 observations
T_G_DEFAULT = 24
PEER_RADIUS_MILES = 20.0
PRIMARY_SUPPLY = "MFR_RMX"
FALLBACK_SUPPLY = "MFR_RMX_FALLBACK"
SUPPLY_EDGE_TYPES = {PRIMARY_SUPPLY, FALLBACK_SUPPLY}

# Locked manuscript/network diagnostics. Disable with --no_strict_counts only
# when intentionally diagnosing a different geography/network.
EXPECTED = {
    "MFR": 100,
    "RMX": 3761,
    "DIM": 3140,
    "DOT": 50,
    "MFR_RMX_primary_links": 13127,
    "MFR_RMX_fallback_links": 294,
    "MFR_RMX_total_links": 13421,
    "RMX_resolved": 3667,
    "RMX_unresolved": 94,
    "RMX_primary_resolved": 3373,
    "RMX_fallback_resolved": 294,
    "resolved_with_peers": 3256,
    "resolved_zero_peers": 411,
}

STATE_NAME_TO_ABBR = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

def canon_state(x) -> str:
    if x is None or pd.isna(x):
        return ""
    return str(x).strip().upper().split(",")[0].strip()


def to_month_key(x) -> str:
    return str(pd.Period(str(x).strip().replace("_", "-")[:7], freq="M"))


def month_diff(start: str, end: str) -> int:
    return (pd.Period(end, freq="M") - pd.Period(start, freq="M")).n

def find_col(df: pd.DataFrame, candidates: list[str], *, required=True):
    lookup = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lookup:
            return lookup[c.lower()]
    if required:
        raise KeyError(f"None of these columns were found: {candidates}. Available: {list(df.columns)}")
    return None


def haversine_matrix(lat1, lon1, lat2, lon2):
    """Pairwise great-circle distance in miles: (n,) x (m,) -> (n,m)."""
    r = 3958.7613
    lat1 = np.radians(np.asarray(lat1, dtype=float))[:, None]
    lon1 = np.radians(np.asarray(lon1, dtype=float))[:, None]
    lat2 = np.radians(np.asarray(lat2, dtype=float))[None, :]
    lon2 = np.radians(np.asarray(lon2, dtype=float))[None, :]
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.minimum(1.0, np.sqrt(a)))


def load_nodes(path: Path, states: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"src_id": str, "node_id": str})
    required = {"node_id", "type", "state", "src_id", "lat", "lon", "capacity_tpm"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"nodes.csv missing required columns: {sorted(missing)}")
    df["type"] = df["type"].astype(str).str.upper().str.strip().replace({
        "READY_MIX": "RMX", "RMX_PLANT": "RMX", "MANUFACTURER": "MFR",
        "CONTRACTOR": "DIM", "DEVELOPER": "DIM", "PDM": "DIM", "PDN": "DIM",
    })
    df["state"] = df["state"].map(canon_state)
    df["src_id"] = df["src_id"].astype(str).str.strip()
    df["node_id"] = df["node_id"].astype(str).str.strip()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["capacity_tpm"] = pd.to_numeric(df["capacity_tpm"], errors="coerce")
    return df[df["state"].isin(states)].copy()


def load_edges(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"src": str, "dst": str})
    required = {"src", "dst", "edge_type", "distance_mi"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"edges.csv missing required columns: {sorted(missing)}")
    df["src"] = df["src"].astype(str).str.strip()
    df["dst"] = df["dst"].astype(str).str.strip()
    df["edge_type"] = df["edge_type"].astype(str).str.upper().str.strip()
    df["distance_mi"] = pd.to_numeric(df["distance_mi"], errors="coerce")
    return df


def assert_equal(label: str, actual: int, expected: int, strict: bool):
    status = "OK" if actual == expected else "MISMATCH"
    print(f"  {label:<30} {actual:>8,}   expected {expected:>8,}   [{status}]")
    if strict and actual != expected:
        raise RuntimeError(f"{label}: got {actual:,}, expected {expected:,}")


def validate_node_universe(nodes: pd.DataFrame, strict: bool):
    print("\n[NODE UNIVERSE]")
    counts = nodes["type"].value_counts()
    for typ in ["MFR", "RMX", "DIM", "DOT"]:
        assert_equal(typ, int(counts.get(typ, 0)), EXPECTED[typ], strict)
    print(f"  {'TOTAL':<30} {len(nodes):>8,}")


def build_supply_network(nodes: pd.DataFrame, edges: pd.DataFrame, out_dir: Path, strict: bool) -> pd.DataFrame:
    """Extract unique forward MFR->RMX links. Edge endpoints are node_id."""
    node_type = nodes.set_index("node_id")["type"].to_dict()
    node_src = nodes.set_index("node_id")["src_id"].to_dict()

    s = edges[edges["edge_type"].isin(SUPPLY_EDGE_TYPES)].copy()
    s = s[(s["src"].map(node_type) == "MFR") & (s["dst"].map(node_type) == "RMX")].copy()
    s["mfr_src_id"] = s["src"].map(node_src)
    s["rmx_src_id"] = s["dst"].map(node_src)
    s = s.dropna(subset=["mfr_src_id", "rmx_src_id"])
    s = s[["mfr_src_id", "rmx_src_id", "edge_type", "distance_mi"]].drop_duplicates(
        ["mfr_src_id", "rmx_src_id"]
    )

    primary = s[s["edge_type"] == PRIMARY_SUPPLY]
    fallback = s[s["edge_type"] == FALLBACK_SUPPLY]

    rmx = nodes[nodes["type"] == "RMX"][["src_id", "state"]].rename(columns={"src_id": "rmx_src_id"})
    agg = s.groupby("rmx_src_id").agg(
        n_mfr=("mfr_src_id", "nunique"),
        has_primary=("edge_type", lambda x: int((x == PRIMARY_SUPPLY).any())),
        has_fallback=("edge_type", lambda x: int((x == FALLBACK_SUPPLY).any())),
    ).reset_index()
    net = rmx.merge(agg, on="rmx_src_id", how="left")
    for c in ["n_mfr", "has_primary", "has_fallback"]:
        net[c] = net[c].fillna(0).astype(int)
    net["network_resolved"] = (net["n_mfr"] > 0).astype(int)
    net["resolution_type"] = np.select(
        [net["has_primary"].eq(1), net["has_fallback"].eq(1)],
        ["primary", "fallback"], default="unresolved"
    )

    print("\n[SUPPLY NETWORK]")
    assert_equal("MFR_RMX primary links", len(primary), EXPECTED["MFR_RMX_primary_links"], strict)
    assert_equal("MFR_RMX fallback links", len(fallback), EXPECTED["MFR_RMX_fallback_links"], strict)
    assert_equal("MFR_RMX total links", len(s), EXPECTED["MFR_RMX_total_links"], strict)
    assert_equal("RMX resolved", int(net["network_resolved"].sum()), EXPECTED["RMX_resolved"], strict)
    assert_equal("RMX unresolved", int((net["network_resolved"] == 0).sum()), EXPECTED["RMX_unresolved"], strict)
    assert_equal("RMX primary-resolved", int((net["resolution_type"] == "primary").sum()), EXPECTED["RMX_primary_resolved"], strict)
    assert_equal("RMX fallback-resolved", int((net["resolution_type"] == "fallback").sum()), EXPECTED["RMX_fallback_resolved"], strict)

    resolved = net[net["network_resolved"] == 1]
    print(f"  {'Mean potential MFRs/resolved RMX':<30} {resolved['n_mfr'].mean():>8.2f}")

    s.to_csv(out_dir / "mfr_rmx_pairs.csv", index=False)
    net.to_csv(out_dir / "rmx_supply_network_diagnostics.csv", index=False)
    return net


def build_peer_network(nodes: pd.DataFrame, supply_diag: pd.DataFrame, out_dir: Path, radius: float, strict: bool):
    """Build undirected RMX peer pairs geometrically among supply-resolved RMX."""
    resolved_ids = set(supply_diag.loc[supply_diag["network_resolved"] == 1, "rmx_src_id"].astype(str))
    r = nodes[(nodes["type"] == "RMX") & nodes["src_id"].isin(resolved_ids)].copy()
    r = r.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    if len(r) != len(resolved_ids):
        raise RuntimeError(f"Only {len(r)} of {len(resolved_ids)} resolved RMX have valid coordinates")

    # 3,667^2 is small enough (~13.4M distances) for a transparent vectorized calculation.
    dist = haversine_matrix(r["lat"], r["lon"], r["lat"], r["lon"])
    iu, ju = np.where(np.triu((dist <= radius) & (dist > 0), k=1))
    undirected = pd.DataFrame({
        "rmx_a": r.iloc[iu]["src_id"].to_numpy(),
        "rmx_b": r.iloc[ju]["src_id"].to_numpy(),
        "distance_mi": dist[iu, ju],
    })
    directed = pd.concat([
        undirected.rename(columns={"rmx_a": "rmx_src_id", "rmx_b": "peer_src_id"}),
        undirected.rename(columns={"rmx_b": "rmx_src_id", "rmx_a": "peer_src_id"}),
    ], ignore_index=True)

    npeer = directed.groupby("rmx_src_id")["peer_src_id"].nunique().rename("n_peers")
    diag = r[["src_id", "state"]].rename(columns={"src_id": "rmx_src_id"}).copy()
    diag = diag.merge(npeer, on="rmx_src_id", how="left")
    diag["n_peers"] = diag["n_peers"].fillna(0).astype(int)

    print(f"\n[RMX PEER NETWORK: radius <= {radius:g} mi]")
    assert_equal("Resolved RMX with >=1 peer", int((diag["n_peers"] > 0).sum()), EXPECTED["resolved_with_peers"], strict)
    assert_equal("Resolved RMX with zero peers", int((diag["n_peers"] == 0).sum()), EXPECTED["resolved_zero_peers"], strict)
    print(f"  {'Mean peers':<30} {diag['n_peers'].mean():>8.2f}   manuscript ~8.80")
    print(f"  {'Median peers':<30} {diag['n_peers'].median():>8.1f}   manuscript 5")
    q = diag["n_peers"].quantile([.25,.50,.75,.90,.95])
    print("  Peer-count quantiles:", ", ".join(f"p{int(k*100)}={v:.0f}" for k,v in q.items()))

    directed.to_csv(out_dir / "rmx_peer_pairs.csv", index=False)
    undirected.to_csv(out_dir / "rmx_peer_pairs_undirected.csv", index=False)
    diag.to_csv(out_dir / "rmx_peer_diagnostics.csv", index=False)
    return diag


def load_usgs_total_demand(
    path: Path,
    states: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Load monthly state cement demand from USGS.

    D_s(t) = Portland shipments + blended-cement shipments.

    The USGS file uses full state names (e.g., 'Alabama'), whereas the
    ABM uses two-letter abbreviations (e.g., 'AL'). Regional observations,
    if present, are not added on top of statewide observations.
    """
    df = pd.read_csv(path)

    required = {"STATE", "YYYY_MM", "TYPE", "TONS"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(
            f"USGS file missing required columns: {sorted(missing)}"
        )

    # ---------------------------------------------------------------
    # State normalization
    # ---------------------------------------------------------------
    df["state_raw"] = df["STATE"].astype(str).str.strip()

    # Keep the first component in case a regional label appears.
    state_base = (
        df["state_raw"]
        .str.split(",", n=1)
        .str[0]
        .str.strip()
    )

    # USGS uses full state names; model uses abbreviations.
    df["state"] = state_base.map(STATE_NAME_TO_ABBR)

    # Also tolerate files that already contain abbreviations.
    missing_map = df["state"].isna()
    df.loc[missing_map, "state"] = (
        state_base[missing_map]
        .str.upper()
        .where(state_base[missing_map].str.len() == 2)
    )

    df["has_region"] = df["state_raw"].str.contains(",", regex=False)

    # ---------------------------------------------------------------
    # Month
    # ---------------------------------------------------------------
    df["yyyy_mm"] = df["YYYY_MM"].map(to_month_key)

    # ---------------------------------------------------------------
    # Cement type
    # ---------------------------------------------------------------
    typ = df["TYPE"].astype(str).str.strip().str.lower()

    df["cement_type"] = np.select(
        [
            typ.eq("portland"),
            typ.eq("blended"),
        ],
        [
            "portland",
            "blended",
        ],
        default="other",
    )

    # ---------------------------------------------------------------
    # Tons
    # ---------------------------------------------------------------
    df["tons"] = pd.to_numeric(df["TONS"], errors="coerce")

    df = df[
        df["cement_type"].isin(["portland", "blended"])
        & df["state"].isin(states)
        & df["tons"].notna()
    ].copy()

    # ---------------------------------------------------------------
    # Avoid regional double counting.
    #
    # If statewide observations exist for a state-month-type, use them.
    # Otherwise use the available regional observations.
    # ---------------------------------------------------------------
    raw = (
        df.groupby(
            ["state", "yyyy_mm", "cement_type", "has_region"],
            as_index=False,
        )["tons"]
        .sum()
    )

    rows = []

    for (st, ym, cement_type), g in raw.groupby(
        ["state", "yyyy_mm", "cement_type"],
        sort=False,
    ):
        statewide = g.loc[~g["has_region"], "tons"]

        if not statewide.empty:
            tons = float(statewide.sum())
        else:
            tons = float(g["tons"].sum())

        rows.append(
            {
                "state": st,
                "yyyy_mm": ym,
                "cement_type": cement_type,
                "tons": tons,
            }
        )

    x = pd.DataFrame(rows)

    if x.empty:
        raise ValueError(
            "No USGS Portland/blended observations remain after "
            "state normalization and filtering."
        )

    # ---------------------------------------------------------------
    # Model period
    # ---------------------------------------------------------------
    x = x[
        (x["yyyy_mm"] >= start)
        & (x["yyyy_mm"] <= end)
    ].copy()

    # ---------------------------------------------------------------
    # D_s(t) = Portland + blended
    # ---------------------------------------------------------------
    state_month = (
        x.groupby(["state", "yyyy_mm"], as_index=False)["tons"]
        .sum()
        .rename(columns={"tons": "D_s"})
        .sort_values(["state", "yyyy_mm"])
        .reset_index(drop=True)
    )

    if state_month.empty:
        raise ValueError(
            "USGS state-month demand is empty after date filtering."
        )

    missing_states = sorted(
        set(states) - set(state_month["state"].unique())
    )

    if missing_states:
        print(
            "WARNING: states with no USGS demand observations:",
            ", ".join(missing_states),
        )

    print(
        f"\n[USGS STATE DEMAND]\n"
        f"  State-month observations: {len(state_month):,}\n"
        f"  States represented: {state_month['state'].nunique()} / {len(states)}\n"
        f"  Period: {state_month['yyyy_mm'].min()} "
        f"to {state_month['yyyy_mm'].max()}"
    )

    return state_month



def apply_preperiod_seasonal_demand_holdout(
    state_demand: pd.DataFrame,
    states: list[str],
    start: str,
    end: str,
    holdout_start: str,
    n_train_years: int = 5,
) -> pd.DataFrame:
    """
    Replace D_s(t) from holdout_start onward using only pre-holdout data.

    For each state and calendar month m, use the mean D_s over the final
    n_train_years before holdout_start. The same 12-month seasonal profile
    is repeated through the holdout period. No post-holdout USGS demand
    observation contributes to generated D_s(t).
    """
    holdout_start = to_month_key(holdout_start)
    if not (start < holdout_start <= end):
        raise ValueError(
            f"demand_holdout_start must satisfy {start} < holdout_start <= {end}; "
            f"got {holdout_start}"
        )
    if n_train_years < 1:
        raise ValueError("demand_holdout_years must be >= 1")

    x = state_demand.copy()
    x["period"] = pd.PeriodIndex(x["yyyy_mm"], freq="M")
    h = pd.Period(holdout_start, freq="M")
    window_start = h - 12 * int(n_train_years)

    train = x[(x["period"] >= window_start) & (x["period"] < h)].copy()
    train["month_of_year"] = train["period"].dt.month

    seasonal = (
        train.groupby(["state", "month_of_year"], as_index=False)["D_s"]
        .mean()
        .rename(columns={"D_s": "D_s_generated"})
    )

    expected = {(st, m) for st in states for m in range(1, 13)}
    observed = set(zip(seasonal["state"], seasonal["month_of_year"]))
    missing = sorted(expected - observed)
    if missing:
        preview = ", ".join(f"{st}-m{m:02d}" for st, m in missing[:12])
        raise RuntimeError(
            "Cannot construct strict demand holdout; missing pre-holdout "
            f"state-month seasonal cells ({len(missing)}): {preview}"
        )

    pre = x[x["period"] < h][["state", "yyyy_mm", "D_s"]].copy()

    holdout_months = pd.period_range(h, pd.Period(end, freq="M"), freq="M")
    future = pd.MultiIndex.from_product(
        [states, holdout_months],
        names=["state", "period"],
    ).to_frame(index=False)
    future["month_of_year"] = future["period"].dt.month
    future = future.merge(
        seasonal,
        on=["state", "month_of_year"],
        how="left",
        validate="many_to_one",
    )
    future["yyyy_mm"] = future["period"].astype(str)
    future["D_s"] = future["D_s_generated"]

    out = pd.concat(
        [pre, future[["state", "yyyy_mm", "D_s"]]],
        ignore_index=True,
    ).sort_values(["state", "yyyy_mm"]).reset_index(drop=True)

    print(
        "\n[STRICT DEMAND HOLDOUT]\n"
        f"  Observed USGS D_s used through: {str(h - 1)}\n"
        f"  Generated D_s begins: {holdout_start}\n"
        f"  Seasonal reference window: {str(window_start)} to {str(h - 1)}\n"
        f"  Method: state-by-calendar-month mean over final {n_train_years} pre-holdout years\n"
        f"  Generated holdout observations: {len(future):,}"
    )
    return out


def load_population(path: Path) -> pd.DataFrame:
    pop = pd.read_csv(path, dtype=str)
    state_col = find_col(pop, ["state", "STATE"])
    fips_col = find_col(pop, ["county_fips", "fips", "FIPS", "GEOID"])
    pop_col = find_col(pop, ["pop", "population", "POP", "POPULATION"])
    out = pd.DataFrame({
        "state": pop[state_col].map(canon_state),
        "county_fips": pop[fips_col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5),
        "population": pd.to_numeric(pop[pop_col], errors="coerce").fillna(0.0),
    })
    return out.groupby(["state", "county_fips"], as_index=False)["population"].max()


def build_demand_weights(nodes: pd.DataFrame, pop: pd.DataFrame, resolved_ids: set[str]) -> pd.DataFrame:
    """Construct L_i and omega_i for supply-resolved RMX only."""
    work = nodes.copy()
    work["county_fips_norm"] = work["county_fips"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
    rmx = work[(work["type"] == "RMX") & work["src_id"].isin(resolved_ids)].dropna(subset=["lat", "lon"]).copy()
    dim = work[work["type"] == "DIM"].dropna(subset=["lat", "lon"]).copy()
    dim = dim.merge(pop, left_on=["state", "county_fips_norm"], right_on=["state", "county_fips"], how="left")
    dim["population"] = dim["population"].fillna(0.0)

    rows = []
    for st, rg in rmx.groupby("state"):
        dg = dim[(dim["state"] == st) & (dim["population"] > 0)].copy()
        if dg.empty:
            raise RuntimeError(f"No populated demand nodes found for state {st}")
        dist = haversine_matrix(rg["lat"], rg["lon"], dg["lat"], dg["lon"])
        L = (dg["population"].to_numpy(float)[None, :] / (1.0 + dist)).sum(axis=1)
        if not np.isfinite(L).all() or L.sum() <= 0:
            raise RuntimeError(f"Invalid gravity weights for state {st}")
        omega = L / L.sum()
        rows.extend({"rmx_src_id": sid, "state": st, "L_i": float(Li), "omega_i": float(wi)}
                    for sid, Li, wi in zip(rg["src_id"], L, omega))
    out = pd.DataFrame(rows)
    if len(out) != len(resolved_ids):
        raise RuntimeError(f"Demand weights created for {len(out)} RMX; expected {len(resolved_ids)} resolved RMX")
    check = out.groupby("state")["omega_i"].sum()
    if not np.allclose(check.values, 1.0, atol=1e-10):
        raise RuntimeError(f"Demand weights do not sum to 1 by state: {check.to_dict()}")
    return out


def build_monthly_demand(weights, state_demand, d_ref):
    out = state_demand.merge(weights, on="state", how="inner")
    out["D_i"] = out["omega_i"] * out["D_s"]
    out["d_i"] = out["D_i"] / (out["D_i"] + float(d_ref))
    return out[["yyyy_mm", "state", "rmx_src_id", "D_s", "L_i", "omega_i", "D_i", "d_i"]]


def print_demand_diagnostics(monthly: pd.DataFrame, expected_obs: int | None = None):
    x, d = monthly["D_i"].dropna(), monthly["d_i"].dropna()
    w = monthly.drop_duplicates("rmx_src_id")["omega_i"].dropna()
    print("\n[DEMAND EXPOSURE]")
    print(f"  RMX-month observations: {len(x):,}" + (f" (expected {expected_obs:,})" if expected_obs else ""))
    print("  D_i tons/month:")
    print(x.quantile([.01,.05,.10,.25,.50,.75,.90,.95,.99]).to_string())
    print(f"  max={x.max():.3f} CV={x.std(ddof=1)/x.mean():.3f}")
    print("  d_i:")
    print(d.quantile([.25,.50,.75,.90,.95]).to_string())
    print("  omega_i:")
    print(w.quantile([.50,.90,.95,.99]).to_string())
    print(f"  max={w.max():.6f} CV={w.std(ddof=1)/w.mean():.3f}")


def load_dot_acceptance(path: Path, states: list[str], plc_label="PLC") -> dict[str, str]:
    df = pd.read_csv(path)
    if "STATE" in df.columns and "state" not in df.columns: df["state"] = df["STATE"]
    if "YYYY_MM" in df.columns and "yyyy_mm" not in df.columns: df["yyyy_mm"] = df["YYYY_MM"]
    if "BLEND" in df.columns and "blend" not in df.columns: df["blend"] = df["BLEND"]
    allow_col = next((c for c in ["allow", "allow_plc", "adopt"] if c in df.columns), None)
    if not {"state", "yyyy_mm", "blend"}.issubset(df.columns) or allow_col is None:
        raise KeyError("DOT file needs state, yyyy_mm, blend and allow/allow_plc/adopt")
    df["state"] = df["state"].map(canon_state)
    df["yyyy_mm"] = df["yyyy_mm"].map(to_month_key)
    df["blend"] = df["blend"].astype(str).str.upper().str.strip()
    df["allow"] = pd.to_numeric(df[allow_col], errors="coerce").fillna(0.0)
    df = df[df["state"].isin(states) & (df["blend"] == plc_label.upper()) & (df["allow"] > 0)].copy()
    first = df.sort_values("yyyy_mm").groupby("state", as_index=False).first()
    return dict(zip(first["state"], first["yyyy_mm"]))


def build_dot_monthly(states, months, first_accept, T_G):
    rows = []
    for st in states:
        acc = first_accept.get(st)
        for ym in months:
            if acc is None or ym < acc:
                g, phi = 0, 0.0
            else:
                g = 1
                phi = min(1.0, max(0.0, month_diff(acc, ym) / float(T_G)))
            rows.append({"state": st, "yyyy_mm": ym, "t_accept": acc, "g_s": g, "phi_s": phi})
    return pd.DataFrame(rows)


def classify_supported_date(v):
    """Classify evidence date syntax; never manufacture a switch month."""
    if pd.isna(v) or not str(v).strip():
        return "none", None
    s = str(v).strip().lower()
    if s == "current":
        return "current_only", None
    if "or-earlier" in s:
        return "latest_known_bound", None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return "dated_boundary", s[:7]
    if re.fullmatch(r"\d{4}-\d{2}", s):
        return "dated_boundary", s
    if re.fullmatch(r"\d{4}", s):
        return "year_only", None
    return "other_bound", None


def load_mfr_evidence(path: Path, nodes: pd.DataFrame, out_dir: Path):
    df = pd.read_excel(path, sheet_name="Plant Evidence Audit", dtype={"mfr_src_id": str})
    required = {"mfr_src_id", "evidence_status", "supported_date", "date_interpretation",
                "assumption_supported", "limitation"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Manufacturer evidence workbook missing: {sorted(missing)}")
    df["mfr_src_id"] = df["mfr_src_id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    mfr_ids = set(nodes.loc[nodes["type"] == "MFR", "src_id"].astype(str))
    audit_ids = set(df["mfr_src_id"])
    if audit_ids != mfr_ids:
        raise RuntimeError(f"Manufacturer audit IDs do not match node MFR IDs. Missing audit={sorted(mfr_ids-audit_ids)}; extra={sorted(audit_ids-mfr_ids)}")

    classes = df["supported_date"].map(classify_supported_date)
    df["date_evidence_class"] = [x[0] for x in classes]
    df["supported_month_if_dated"] = [x[1] for x in classes]

    status = df["evidence_status"].astype(str)
    direct = status.eq("Direct plant evidence")
    contrary = status.str.contains("contrary|No PLC", case=False, regex=True)
    # This is an evidence classification only, NOT q_j(t).
    df["model_evidence_class"] = "unresolved"
    df.loc[direct & df["date_evidence_class"].eq("dated_boundary"), "model_evidence_class"] = "plant_dated_availability_boundary"
    df.loc[direct & df["date_evidence_class"].eq("latest_known_bound"), "model_evidence_class"] = "plant_latest_known_availability_bound"
    df.loc[direct & df["date_evidence_class"].isin(["current_only", "year_only", "other_bound"]), "model_evidence_class"] = "plant_availability_without_monthly_transition_date"
    df.loc[contrary, "model_evidence_class"] = "current_contrary_evidence"

    print("\n[MANUFACTURER PLC EVIDENCE AUDIT]")
    print(f"  Plants audited: {len(df)}")
    print(df["evidence_status"].value_counts().to_string())
    print("\n  Model evidence classes (not q_j states):")
    print(df["model_evidence_class"].value_counts().to_string())
    print("\n  NOTE: unresolved evidence is NOT converted to q_j=0.")
    print("  NOTE: 'current'/'or-earlier'/year-only bounds are NOT invented as switch months.")

    keep = [c for c in ["mfr_src_id", "company", "plant", "state", "evidence_status", "supported_date",
                         "date_evidence_class", "supported_month_if_dated", "model_evidence_class",
                         "date_interpretation", "evidence_scope", "evidence_description", "source_title",
                         "source_date", "source_url", "assumption_supported", "limitation"] if c in df.columns]
    df[keep].to_csv(out_dir / "mfr_plc_evidence_constraints.csv", index=False)
    return df


def main():
    ap = argparse.ArgumentParser(description="Build Stage-1 empirical state for simplified PLC ABM")
    ap.add_argument("--nodes", required=True)
    ap.add_argument("--edges", required=True)
    ap.add_argument("--usgs", required=True)
    ap.add_argument("--county_pop", required=True)
    ap.add_argument("--dot_adoption", required=True)
    ap.add_argument("--mfr_plc_evidence", required=True)
    ap.add_argument("--states", required=True, help="Comma-separated state abbreviations")
    ap.add_argument("--start", default="2010-01")
    ap.add_argument("--end", default="2024-12")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--d_ref", type=float, default=D_REF_DEFAULT)
    ap.add_argument("--T_G", type=int, default=T_G_DEFAULT)
    ap.add_argument("--peer_radius", type=float, default=PEER_RADIUS_MILES)
    ap.add_argument("--plc_label", default="PLC")
    ap.add_argument(
        "--demand_holdout_start",
        default=None,
        help="First month whose state demand is generated only from pre-holdout data, e.g. 2020-01.",
    )
    ap.add_argument(
        "--demand_holdout_years",
        type=int,
        default=5,
        help="Number of pre-holdout years used for state-by-calendar-month seasonal means.",
    )
    ap.add_argument("--no_strict_counts", action="store_true")
    args = ap.parse_args()

    strict = not args.no_strict_counts
    states = sorted({canon_state(x) for x in args.states.split(",") if x.strip()})
    start, end = to_month_key(args.start), to_month_key(args.end)
    months = [str(x) for x in pd.period_range(start, end, freq="M")]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    nodes = load_nodes(Path(args.nodes), states)
    edges = load_edges(Path(args.edges))
    pop = load_population(Path(args.county_pop))
    print(f"Loaded nodes: {len(nodes):,}; edges: {len(edges):,}; states: {len(states)}")

    validate_node_universe(nodes, strict)
    supply_diag = build_supply_network(nodes, edges, out_dir, strict)
    build_peer_network(nodes, supply_diag, out_dir, args.peer_radius, strict)

    resolved_ids = set(supply_diag.loc[supply_diag["network_resolved"] == 1, "rmx_src_id"].astype(str))
    weights = build_demand_weights(nodes, pop, resolved_ids)
    weights.to_csv(out_dir / "rmx_demand_weights.csv", index=False)

    state_demand = load_usgs_total_demand(Path(args.usgs), states, start, end)

    if args.demand_holdout_start:
        state_demand = apply_preperiod_seasonal_demand_holdout(
            state_demand=state_demand,
            states=states,
            start=start,
            end=end,
            holdout_start=args.demand_holdout_start,
            n_train_years=args.demand_holdout_years,
        )

    state_demand.to_csv(out_dir / "state_month_demand.csv", index=False)
    monthly = build_monthly_demand(weights, state_demand, args.d_ref)
    monthly.to_csv(out_dir / "rmx_month_demand_exposure.csv", index=False)
    print_demand_diagnostics(monthly, expected_obs=len(resolved_ids) * len(months))

    first_accept = load_dot_acceptance(Path(args.dot_adoption), states, args.plc_label)
    dot_monthly = build_dot_monthly(states, months, first_accept, args.T_G)
    dot_monthly.to_csv(out_dir / "dot_monthly_state.csv", index=False)
    pd.DataFrame([{"state": st, "t_accept": first_accept.get(st)} for st in states]).to_csv(
        out_dir / "dot_first_acceptance.csv", index=False)
    print("\n[DOT]")
    print(f"  States with PLC acceptance date: {len(first_accept)} / {len(states)}")

    load_mfr_evidence(Path(args.mfr_plc_evidence), nodes, out_dir)

    pd.DataFrame([
        {"parameter": "D_ref", "value": args.d_ref, "role": "2010-2019 training-only median RMX-month demand exposure (440040 observations)"},
        {"parameter": "T_G", "value": args.T_G, "role": "structural DOT implementation-maturity timescale, months"},
        {"parameter": "R_P", "value": args.peer_radius, "role": "structural RMX peer radius, miles; peers constructed geometrically"},
        {"parameter": "demand_holdout_start", "value": args.demand_holdout_start or "", "role": "first month with pre-period-generated state demand"},
        {"parameter": "demand_holdout_years", "value": args.demand_holdout_years if args.demand_holdout_start else "", "role": "pre-holdout years used for state-by-calendar-month seasonal demand means"},
    ]).to_csv(out_dir / "reference_specification.csv", index=False)

    print("\nWrote Stage-1 empirical state to:", out_dir)
    print("No RMX adoption behavior, Bernoulli draws, manufacturer response, or PLC calibration were run.")


if __name__ == "__main__":
    main()
