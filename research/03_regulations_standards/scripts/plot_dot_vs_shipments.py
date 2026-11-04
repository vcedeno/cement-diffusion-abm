#!/usr/bin/env python3
"""Compare recorded DOT PLC acceptance with USGS blended-cement shipments."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

dot = pd.read_csv(ROOT / "data/dot_first_acceptance.csv")
usgs = pd.read_csv(ROOT / "data/usgs_all_state_type_month.csv")

dot["accept_year"] = pd.to_datetime(dot["t_accept"]).dt.year
usgs["year"] = pd.to_datetime(usgs["YYYY_MM"]).dt.year

usgs = usgs[usgs["year"].between(2010, 2024)]

annual = (
    usgs.groupby(["STATE", "year", "TYPE"])["TONS"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

annual["total"] = annual["Portland"] + annual["Blended"]
annual["blended_share"] = (
    annual["Blended"] / annual["total"].replace(0, float("nan"))
)

national = annual.groupby("year")[["Portland", "Blended"]].sum()
national["blended_share"] = (
    national["Blended"] /
    (national["Portland"] + national["Blended"])
)

years = range(2010, 2025)
accepted = [
    (dot["accept_year"] <= year).sum()
    for year in years
]

fig, ax1 = plt.subplots(figsize=(10, 4.5))

ax1.plot(
    list(years),
    accepted,
    color="tab:blue",
    linewidth=2.5,
    label="States accepting PLC (reconstructed dates)",
)
ax1.set_ylabel("Number of states")
ax1.set_ylim(0, 52)
ax1.set_xlabel("Year")

ax2 = ax1.twinx()
ax2.plot(
    national.index,
    national["blended_share"] * 100,
    color="tab:orange",
    linewidth=2.5,
    label="Blended-cement shipment share",
)
ax2.set_ylabel("Blended shipments (%)")
ax2.set_ylim(0, 100)

ax1.set_title("DOT PLC acceptance and blended-cement shipments")
ax1.set_xticks(range(2010, 2025, 2))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False)

fig.tight_layout()
fig.savefig(OUT / "dot_vs_shipments_national.pdf", bbox_inches="tight")
fig.savefig(OUT / "dot_vs_shipments_national.png", dpi=300, bbox_inches="tight")
plt.close(fig)

first_10 = (
    annual[annual["blended_share"] >= 0.10]
    .groupby("STATE")["year"]
    .min()
    .rename("first_10pct_year")
)

states = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR",
    "California":"CA","Colorado":"CO","Connecticut":"CT",
    "Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI",
    "Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
    "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME",
    "Maryland":"MD","Massachusetts":"MA","Michigan":"MI",
    "Minnesota":"MN","Mississippi":"MS","Missouri":"MO",
    "Montana":"MT","Nebraska":"NE","Nevada":"NV",
    "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM",
    "New York":"NY","North Carolina":"NC","North Dakota":"ND",
    "Ohio":"OH","Oklahoma":"OK","Oregon":"OR",
    "Pennsylvania":"PA","Rhode Island":"RI",
    "South Carolina":"SC","South Dakota":"SD",
    "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT",
    "Virginia":"VA","Washington":"WA","West Virginia":"WV",
    "Wisconsin":"WI","Wyoming":"WY",
}

first_10.index = first_10.index.map(states)

comparison = dot.merge(
    first_10,
    left_on="state",
    right_index=True,
    how="left",
)

comparison = comparison.sort_values("accept_year")

fig, ax = plt.subplots(figsize=(10, 12))

y = range(len(comparison))

ax.scatter(
    comparison["accept_year"],
    y,
    label="Reconstructed DOT acceptance date",
    s=35,
)

ax.scatter(
    comparison["first_10pct_year"],
    y,
    label="First year blended share ≥10%",
    s=35,
)

ax.set_yticks(list(y))
ax.set_yticklabels(comparison["state"])
ax.invert_yaxis()
ax.set_xlabel("Year")
ax.set_title("DOT acceptance and blended-cement shipment transition")
ax.legend(frameon=False)

fig.tight_layout()
fig.savefig(OUT / "dot_vs_shipments_states.pdf", bbox_inches="tight")
fig.savefig(OUT / "dot_vs_shipments_states.png", dpi=300, bbox_inches="tight")
plt.close(fig)

comparison.to_csv(OUT / "dot_shipments_timing.csv", index=False)

print("Created national and state-level figures.")
print("Created state timing comparison.")
print("States reaching 10% blended share:",
      comparison["first_10pct_year"].notna().sum())
