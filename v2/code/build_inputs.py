"""Build the model-ready tables in new_data/derived from original_data and new_data.

Run once before anything else:  python build_inputs.py

Outputs (new_data/derived)
  plants.csv           cement plants: capacity, operating period, parent firm, PLC evidence dates, eligibility
  firms.csv            parent firms: capacity, record start month (first Type IL offered), GCCA membership, record basis
  dot_ranges.csv       state DOT acceptance window (not_before, accepted_by)
  rollout_lags.csv     within-firm lags (months) between a firm's first and later plants, 2020-22 wave
  usgs_state_month.csv state x month shipments of portland and blended cement, 2002-01 .. 2025-12
  import_share_2022.csv state import share of consumption (imported cement treated as ordinary portland)
  rmx_owner.csv        cement-firm owner of each ready-mix plant (blank if independent)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from config import ORIG, NEW, DERIVED

DERIVED.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ plants
cap = pd.read_csv(ORIG / "mfr_capacity_for_model.csv")
ev = pd.read_csv(NEW / "evidence/plant_plc_evidence.csv")
pl = cap[["mfr_src_id", "asset_name", "state_code", "plant_type", "capacity_tpm_model",
          "operating_start", "operating_end"]].merge(
    ev[["mfr_src_id", "parent_2020_22", "first_by", "full_conv"]], on="mfr_src_id", how="left")
pl["capacity_tpm_model"] = pl["capacity_tpm_model"].fillna(1.10e6 / 12)   # median plant capacity where missing
pl["first_t"] = pl["first_by"].astype(str).str[:7].where(pl["first_by"].notna())
pl["prewave"] = pl["first_t"].where(pl["first_t"] < "2020-01")            # PLC documented before 2020 (offered beside OPC)
WHITE = [20, 21]           # white-cement plants (Waco TX, York PA): never gray PLC
SLAG = [79, 80, 81]        # slag-grinding sites: distribution points of their parent in the network
pl["eligible"] = ~pl["mfr_src_id"].isin(WHITE)
pl["role"] = np.where(pl["mfr_src_id"].isin(WHITE), "white",
              np.where(pl["mfr_src_id"].isin(SLAG), "slag_distribution", pl["plant_type"]))
pl.loc[pl["mfr_src_id"] == 52, "operating_end"] = "2021-01"               # Cupertino closure (CARB facility reporting)
pl["observed_wave_first"] = pl["first_t"].where(pl["first_t"] >= "2020-01")
pl.to_csv(DERIVED / "plants.csv", index=False)

# ------------------------------------------------------------------ firms
attr = pd.read_csv(NEW / "firm_attributes.csv").set_index("parent_2020_22")
firms = (pl[pl["eligible"]].groupby("parent_2020_22")
         .agg(n_plants=("mfr_src_id", "size"), capacity=("capacity_tpm_model", "sum"),
              observed_first=("observed_wave_first", "min")).reset_index())
firms["gcca_member"] = firms["parent_2020_22"].map(attr["gcca_member"]).fillna(0).astype(int)
firms["record_basis"] = firms["parent_2020_22"].map(attr["record_basis"])
firms.to_csv(DERIVED / "firms.csv", index=False)

# ------------------------------------------------------------------ DOT windows
dot = pd.read_csv(NEW / "evidence/dot_acceptance_evidence.csv")[["state", "not_before", "accepted_by", "status"]]
dot.to_csv(DERIVED / "dot_ranges.csv", index=False)

# ------------------------------------------------------------------ rollout lags (follow-on plants, 2020-22 wave)
w = pl[pl["observed_wave_first"].between("2020-01", "2022-12")].copy()
w["t"] = pd.PeriodIndex(w["observed_wave_first"], freq="M")
w["f0"] = w.groupby("parent_2020_22")["t"].transform("min")
lags = sorted(l for l in [(a - b).n for a, b in zip(w["t"], w["f0"])] if l > 0)
pd.Series(lags, name="lag_months").to_csv(DERIVED / "rollout_lags.csv", index=False)

# ------------------------------------------------------------------ USGS shipments by state and month
ab = pd.read_csv(ORIG / "dots.csv").set_index("place_name")["state_code"]
ab.index = ab.index.str.title()
d = pd.read_csv(ORIG / "usgs_all_state_type_month.csv")                  # 2002-01 .. 2024-12
d["ym"] = d["YYYY_MM"].astype(str).str[:7]
d["type"] = d["TYPE"].str.strip().str.lower()
d["tons"] = pd.to_numeric(d["TONS"].astype(str).str.replace(",", ""), errors="coerce")
d = d[d["type"].isin(["portland", "blended"])]
d["st"] = d["STATE"].str.title().map(ab)
g = d.groupby(["st", "ym", "type"])["tons"].sum().unstack().fillna(0).reset_index()
g = g[g["ym"] <= "2024-12"]
# 2025 (new_data/usgs_2025): USGS Mineral Industry Surveys, Cement in December 2025, tables 2a and 2b
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
parts = []
for typ in ("portland", "blended"):
    t = pd.read_csv(NEW / f"usgs_2025/{typ}_2025_JanJul.csv").merge(
        pd.read_csv(NEW / f"usgs_2025/{typ}_2025_AugDec.csv"), on="destination")
    t = t[~t["destination"].isin(["Puerto Rico", "Foreign countries", "Total shipments"])]
    t["st"] = t["destination"].str.split(",").str[0].str.title().map(ab)
    long = t.groupby("st")[MON].sum().reset_index().melt(id_vars="st", var_name="mon", value_name=typ)
    long["ym"] = "2025-" + long["mon"].map({m: f"{i + 1:02d}" for i, m in enumerate(MON)})
    parts.append(long[["st", "ym", typ]])
g25 = parts[0].merge(parts[1], on=["st", "ym"])
usgs = pd.concat([g, g25[["st", "ym", "blended", "portland"]]], ignore_index=True).sort_values(["st", "ym"])
usgs.to_csv(DERIVED / "usgs_state_month.csv", index=False)

# ------------------------------------------------------------------ imports (2022 volumes only: no validation-window data)
dist = pd.read_csv(NEW / "imports_by_customs_district.csv")
cons = usgs[usgs["ym"].str[:4] == "2022"].groupby("st")[["blended", "portland"]].sum().sum(axis=1)
CEMENT_SHARE = 0.75                       # cement (not clinker) share of hydraulic-cement-and-clinker imports
imp = pd.Series(0.0, index=cons.index)
for r in dist[dist["included"] == 1].itertuples():
    sts = r.destination_states.split(";")
    wts = cons.reindex(sts).fillna(0)
    if wts.sum() == 0:
        continue
    for s in sts:
        imp[s] += r.imports_2022_kt * 1000 * CEMENT_SHARE * wts[s] / wts.sum()
m = (imp / cons).clip(upper=0.6).rename("import_share")
m.index.name = "st"
m.to_csv(DERIVED / "import_share_2022.csv")

# ------------------------------------------------------------------ ready-mix owners
o = pd.read_csv(NEW / "readymix_owner_assignment.csv")[["id", "owner"]]
o.to_csv(DERIVED / "rmx_owner.csv", index=False)

print(f"plants {len(pl)} (eligible {int(pl.eligible.sum())}) | firms {len(firms)} | lags {len(lags)} | "
      f"usgs {usgs.ym.min()}..{usgs.ym.max()} | import states {int((m > 0).sum())}")
