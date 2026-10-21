#!/usr/bin/env python3
"""
simple_abm_build_network.py

Build the geographic/institutional network for the simplified ABM.

Approved network rules
----------------------
MFR -> RMX
    - All manufacturers within --mfr_rmx_radius are potential suppliers.
    - No nearest-k restriction is imposed within the primary radius.
    - If no manufacturer lies within the primary radius, the nearest
      represented manufacturer is retained only when it lies within
      --mfr_rmx_fallback_radius.
    - Primary and fallback links are labeled separately.
    - RMX facilities with no represented manufacturer within the fallback
      radius remain network-unresolved.

RMX -> DIM
    - Retains the current downstream representation:
      nearest --rmx_dim_k RMX facility/facilities within --rmx_dim_radius.
    - If no RMX is within the radius, connect to the nearest RMX using a
      separately labeled fallback edge.
    - This rule is retained for now and should be revisited when the
      downstream-demand layer is reviewed.

DOT links
    - DOT -> DIM and RMX -> DOT links are created by state.
    - No DOT peer network is created here.

This script does NOT:
    - create RMX peer edges;
    - create DIM peer edges;
    - create DOT peer edges;
    - assign MFR->RMX purchase shares;
    - assign manufacturer capacity weights;
    - assign material availability.

Inputs
------
manufacturers_csv:
    id,state_code,county_fips,latitude,longitude[,capacity_mmtpa]
readymix_csv:
    id,state_code,county_fips,latitude,longitude
dots_csv:
    id,state_code
demand_inter_csv:
    county_fips,state_code,latitude,longitude[,id]

Outputs
-------
outdir/nodes.csv
outdir/edges.csv
outdir/adjacency_full.npz

Manufacturer capacity
---------------------
If capacity_mmtpa is present, it is converted to:
    capacity_tpm = capacity_mmtpa * 1,000,000 / 12
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, save_npz


REQ_MFR = ["id", "state_code", "county_fips", "latitude", "longitude"]
REQ_RMX = ["id", "state_code", "county_fips", "latitude", "longitude"]
REQ_DOT = ["id", "state_code"]
REQ_DIM = ["county_fips", "state_code", "latitude", "longitude"]


def load_csv(path, required_cols, name):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{name} CSV not found: {p}")

    df = pd.read_csv(p)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df


def norm_state(s):
    return str(s).strip().upper() if pd.notna(s) else ""


def to_float(x):
    try:
        return float(x)
    except Exception:
        return np.nan


def haversine_miles(lat1, lon1, lat2, lon2):
    """Vectorized Haversine distance in miles."""
    radius_km = 6371.0088
    to_rad = np.pi / 180.0

    lat1 = np.asarray(lat1, dtype=float) * to_rad
    lon1 = np.asarray(lon1, dtype=float) * to_rad
    lat2 = np.asarray(lat2, dtype=float) * to_rad
    lon2 = np.asarray(lon2, dtype=float) * to_rad

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    )
    km = 2.0 * radius_km * np.arcsin(np.minimum(1.0, np.sqrt(a)))
    return km * 0.621371


def pairwise_within_radius(src_df, dst_df, radius_mi):
    """Return (src_idx, dst_idx, distance_mi) pairs within radius."""
    if src_df.empty or dst_df.empty:
        return []

    lat1 = src_df["lat"].to_numpy(float)
    lon1 = src_df["lon"].to_numpy(float)
    lat2 = dst_df["lat"].to_numpy(float)
    lon2 = dst_df["lon"].to_numpy(float)

    out = []
    chunk = 2000

    for i0 in range(0, len(lat1), chunk):
        i1 = min(i0 + chunk, len(lat1))
        d = haversine_miles(
            lat1[i0:i1][:, None],
            lon1[i0:i1][:, None],
            lat2[None, :],
            lon2[None, :],
        )
        si, di = np.where(d <= radius_mi)

        for k in range(len(si)):
            out.append((i0 + int(si[k]), int(di[k]), float(d[si[k], di[k]])))

    return out


def main():
    ap = argparse.ArgumentParser(
        description="Build the geographic network for the simplified ABM."
    )
    ap.add_argument("--manufacturers_csv", required=True)
    ap.add_argument("--readymix_csv", required=True)
    ap.add_argument("--dots_csv", required=True)
    ap.add_argument("--demand_inter_csv", required=True)
    ap.add_argument(
        "--states",
        required=True,
        help='Comma-separated state abbreviations, e.g. "VA" or "VA,NC".',
    )
    ap.add_argument("--outdir", required=True)

    # Retained downstream-network settings; to be reviewed separately.
    ap.add_argument("--rmx_dim_radius", type=float, default=15.0)
    ap.add_argument("--rmx_dim_k", type=int, default=1)

    # MFR -> RMX rule: all MFRs within the primary radius; if none exists,
    # retain only the nearest represented MFR when it is within the bounded
    # fallback radius.
    ap.add_argument("--mfr_rmx_radius", type=float, default=150.0)
    ap.add_argument("--mfr_rmx_fallback_radius", type=float, default=208.0)


    args = ap.parse_args()

    if args.rmx_dim_k < 1:
        raise ValueError("--rmx_dim_k must be >= 1")
    if args.rmx_dim_radius <= 0:
        raise ValueError("--rmx_dim_radius must be > 0")
    if args.mfr_rmx_radius <= 0:
        raise ValueError("--mfr_rmx_radius must be > 0")
    if args.mfr_rmx_fallback_radius <= 0:
        raise ValueError("--mfr_rmx_fallback_radius must be > 0")
    if args.mfr_rmx_fallback_radius < args.mfr_rmx_radius:
        raise ValueError(
            "--mfr_rmx_fallback_radius must be >= --mfr_rmx_radius"
        )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    focus_states = [norm_state(s) for s in args.states.split(",") if s.strip()]

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    mfr_raw = load_csv(args.manufacturers_csv, REQ_MFR, "manufacturers")
    rmx_raw = load_csv(args.readymix_csv, REQ_RMX, "ready_mix")
    dots_raw = load_csv(args.dots_csv, REQ_DOT, "dots")
    dim_raw = load_csv(args.demand_inter_csv, REQ_DIM, "demand_intermediaries")

    for df, stcol in [
        (mfr_raw, "state_code"),
        (rmx_raw, "state_code"),
        (dots_raw, "state_code"),
        (dim_raw, "state_code"),
    ]:
        df[stcol] = df[stcol].map(norm_state)

    # Remove the Guam county record incorrectly labeled as Alaska.
    # FIPS 66010 corresponds to Mangilao, Guam and is outside the
    # 50-state model domain.
    dim_fips = (
        dim_raw["county_fips"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(5)
    )

    dim_raw = dim_raw[
        dim_fips != "66010"
    ].copy()

    has_cap = "capacity_mmtpa" in mfr_raw.columns

    mfr = pd.DataFrame(
        {
            "src_id": mfr_raw["id"],
            "type": "MFR",
            "state": mfr_raw["state_code"],
            "county_fips": mfr_raw["county_fips"],
            "lat": mfr_raw["latitude"].map(to_float),
            "lon": mfr_raw["longitude"].map(to_float),
        }
    )

    if has_cap:
        mfr["capacity_tpm"] = mfr_raw["capacity_mmtpa"].map(
            lambda v: to_float(v) * 1_000_000.0 / 12.0
        )
    else:
        mfr["capacity_tpm"] = np.nan

    rmx = pd.DataFrame(
        {
            "src_id": rmx_raw["id"],
            "type": "RMX",
            "state": rmx_raw["state_code"],
            "county_fips": rmx_raw["county_fips"],
            "lat": rmx_raw["latitude"].map(to_float),
            "lon": rmx_raw["longitude"].map(to_float),
            "capacity_tpm": np.nan,
        }
    )

    dot = pd.DataFrame(
        {
            "src_id": dots_raw["id"],
            "type": "DOT",
            "state": dots_raw["state_code"],
            "county_fips": np.nan,
            "lat": np.nan,
            "lon": np.nan,
            "capacity_tpm": np.nan,
        }
    )

    dim = pd.DataFrame(
        {
            "src_id": dim_raw["id"] if "id" in dim_raw.columns else dim_raw["county_fips"],
            "type": "DIM",
            "state": dim_raw["state_code"],
            "county_fips": dim_raw["county_fips"],
            "lat": dim_raw["latitude"].map(to_float),
            "lon": dim_raw["longitude"].map(to_float),
            "capacity_tpm": np.nan,
        }
    )

    # ------------------------------------------------------------------
    # Select focus-state nodes
    # ------------------------------------------------------------------
    in_mfr = mfr[mfr["state"].isin(focus_states)].copy()
    in_rmx = rmx[rmx["state"].isin(focus_states)].copy()
    in_dot = dot[dot["state"].isin(focus_states)].copy()
    in_dim = dim[dim["state"].isin(focus_states)].copy()

    # Expected county-demand population for the 50-state model.
    if len(focus_states) == 50:
        assert len(in_dim) == 3140, (
            f"Expected 3,140 county demand nodes, found {len(in_dim):,}"
    )

    # ------------------------------------------------------------------
    # Model domain
    # ------------------------------------------------------------------
    # The requested state list defines the model domain. Nodes outside that
    # domain (e.g., DC or U.S. territories in a 50-state run) are not added
    # through a geographic halo. Geographic links may cross state boundaries,
    # but both endpoints must belong to the requested model domain.

    # ------------------------------------------------------------------
    # Compose nodes
    # ------------------------------------------------------------------
    nodes = pd.concat(
        [in_mfr, in_rmx, in_dot, in_dim],
        ignore_index=True,
    )

    nodes = (
        nodes.drop_duplicates(subset=["type", "src_id"])
        .reset_index(drop=True)
    )
    nodes["node_id"] = np.arange(len(nodes), dtype=int)

    n_mfr = nodes[nodes["type"] == "MFR"].reset_index(drop=True)
    n_rmx = nodes[nodes["type"] == "RMX"].reset_index(drop=True)
    n_dot = nodes[nodes["type"] == "DOT"].reset_index(drop=True)
    n_dim = nodes[nodes["type"] == "DIM"].reset_index(drop=True)

    edges = []

    # ------------------------------------------------------------------
    # (1) RMX <-> DIM
    # Retained current rule: nearest k within radius; nearest fallback.
    # ------------------------------------------------------------------
    r = n_rmx.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    dnodes = n_dim.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    if not r.empty and not dnodes.empty:
        distances = haversine_miles(
            r["lat"].to_numpy()[:, None],
            r["lon"].to_numpy()[:, None],
            dnodes["lat"].to_numpy()[None, :],
            dnodes["lon"].to_numpy()[None, :],
        )

        for d_idx in range(len(dnodes)):
            dist_to_d = distances[:, d_idx]
            within = np.where(dist_to_d <= args.rmx_dim_radius)[0]

            if len(within) > 0:
                ordered = within[np.argsort(dist_to_d[within])]
                chosen = ordered[: args.rmx_dim_k]
                edge_type_forward = "RMX_DIM"
                edge_type_reverse = "DIM_RMX"
            else:
                chosen = np.array([int(np.argmin(dist_to_d))])
                edge_type_forward = "RMX_DIM_FALLBACK"
                edge_type_reverse = "DIM_RMX_FALLBACK"

            for r_idx in chosen:
                dist = float(dist_to_d[r_idx])
                r_node = int(r.loc[r_idx, "node_id"])
                d_node = int(dnodes.loc[d_idx, "node_id"])

                edges.append(
                    dict(
                        src=r_node,
                        dst=d_node,
                        edge_type=edge_type_forward,
                        distance_mi=dist,
                    )
                )
                edges.append(
                    dict(
                        src=d_node,
                        dst=r_node,
                        edge_type=edge_type_reverse,
                        distance_mi=dist,
                    )
                )

    # ------------------------------------------------------------------
    # (2) MFR <-> RMX
    # RULE:
    #   - retain ALL manufacturers within the primary radius;
    #   - no nearest-k restriction within the primary radius;
    #   - if none is within the primary radius, retain ONLY the nearest
    #     represented manufacturer when it is within the bounded fallback
    #     radius;
    #   - otherwise leave the RMX network-unresolved.
    # Primary and fallback links are labeled separately.
    # ------------------------------------------------------------------
    m = n_mfr.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    r = n_rmx.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    if not m.empty and not r.empty:
        distances = haversine_miles(
            m["lat"].to_numpy()[:, None],
            m["lon"].to_numpy()[:, None],
            r["lat"].to_numpy()[None, :],
            r["lon"].to_numpy()[None, :],
        )

        for r_idx in range(len(r)):
            dist_to_r = distances[:, r_idx]
            within = np.where(dist_to_r <= args.mfr_rmx_radius)[0]

            if len(within) > 0:
                chosen = within[np.argsort(dist_to_r[within])]
                edge_type_forward = "MFR_RMX"
                edge_type_reverse = "RMX_MFR"
            else:
                nearest_idx = int(np.argmin(dist_to_r))
                nearest_dist = float(dist_to_r[nearest_idx])

                if nearest_dist <= args.mfr_rmx_fallback_radius:
                    chosen = np.array([nearest_idx], dtype=int)
                    edge_type_forward = "MFR_RMX_FALLBACK"
                    edge_type_reverse = "RMX_MFR_FALLBACK"
                else:
                    chosen = np.array([], dtype=int)
                    edge_type_forward = None
                    edge_type_reverse = None

            for m_idx in chosen:
                dist = float(dist_to_r[m_idx])
                m_node = int(m.loc[m_idx, "node_id"])
                r_node = int(r.loc[r_idx, "node_id"])

                edges.append(
                    dict(
                        src=m_node,
                        dst=r_node,
                        edge_type=edge_type_forward,
                        distance_mi=dist,
                    )
                )
                edges.append(
                    dict(
                        src=r_node,
                        dst=m_node,
                        edge_type=edge_type_reverse,
                        distance_mi=dist,
                    )
                )

    # ------------------------------------------------------------------
    # (3) DOT links by state
    # No DOT peer edges are created in the simplified network builder.
    # ------------------------------------------------------------------
    if not n_dot.empty:
        dim_groups = n_dim.groupby("state")
        rmx_groups = n_rmx.groupby("state")

        for _, dot_row in n_dot.iterrows():
            state = norm_state(dot_row["state"])

            if state in dim_groups.groups:
                for _, dim_row in dim_groups.get_group(state).iterrows():
                    edges.append(
                        dict(
                            src=int(dot_row["node_id"]),
                            dst=int(dim_row["node_id"]),
                            edge_type="DOT_DIM",
                            distance_mi=np.nan,
                        )
                    )

            if state in rmx_groups.groups:
                for _, rmx_row in rmx_groups.get_group(state).iterrows():
                    edges.append(
                        dict(
                            src=int(rmx_row["node_id"]),
                            dst=int(dot_row["node_id"]),
                            edge_type="RMX_DOT",
                            distance_mi=np.nan,
                        )
                    )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    edges_df = (
        pd.DataFrame(
            edges,
            columns=["src", "dst", "edge_type", "distance_mi"],
        )
        .drop_duplicates()
        .reset_index(drop=True)
    )

    nodes_out = nodes[
        [
            "node_id",
            "type",
            "state",
            "county_fips",
            "lat",
            "lon",
            "src_id",
            "capacity_tpm",
        ]
    ].copy()

    nodes_out.to_csv(outdir / "nodes.csv", index=False)
    edges_df.to_csv(outdir / "edges.csv", index=False)

    n = len(nodes_out)
    rr = edges_df["src"].to_numpy(int)
    cc = edges_df["dst"].to_numpy(int)
    vv = np.ones(len(edges_df), dtype=float)

    adjacency = coo_matrix((vv, (rr, cc)), shape=(n, n)).tocsr()
    save_npz(outdir / "adjacency_full.npz", adjacency)

    print(f"[ok] nodes.csv -> {outdir / 'nodes.csv'} (N={n})")
    print(f"[ok] edges.csv -> {outdir / 'edges.csv'} (E={len(edges_df)})")
    print(f"[ok] adjacency_full.npz -> {outdir / 'adjacency_full.npz'}")
    print()
    print("MFR->RMX rule:")
    print(f"  all MFRs within {args.mfr_rmx_radius:g} miles")
    print(
        "  if none: nearest MFR only when within "
        f"{args.mfr_rmx_fallback_radius:g} miles"
    )
    print("  fallback links are labeled separately")
    print("  no unrestricted nearest-MFR fallback")
    print("  no MFR nearest-k restriction within the primary radius")

    # Report MFR->RMX coverage using forward edges only.
    primary = edges_df[edges_df["edge_type"] == "MFR_RMX"]
    fallback = edges_df[edges_df["edge_type"] == "MFR_RMX_FALLBACK"]
    covered_primary = set(primary["dst"].astype(int))
    covered_fallback = set(fallback["dst"].astype(int))
    all_rmx = set(n_rmx["node_id"].astype(int))
    unresolved = all_rmx - covered_primary - covered_fallback
    print(f"  RMXs with primary MFR connection: {len(covered_primary):,}")
    print(f"  RMXs using bounded fallback: {len(covered_fallback):,}")
    print(f"  network-unresolved RMXs: {len(unresolved):,}")


if __name__ == "__main__":
    main()
