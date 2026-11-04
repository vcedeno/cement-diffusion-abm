#!/usr/bin/env python3
"""Analyze observed USGS cement shipments, 2010–2024."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/usgs_all_state_type_month.csv"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
df["year"] = pd.to_datetime(df["YYYY_MM"]).dt.year
df = df[df["year"].between(2010, 2024)].copy()

df["TYPE"] = df["TYPE"].astype(str).str.strip()

types = ["Portland", "Blended"]
df = df[df["TYPE"].isin(types)]

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

def save(fig, name):
    fig.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Created:", name)

national = (
    df.groupby(["year", "TYPE"])["TONS"]
    .sum()
    .unstack(fill_value=0)
    .reindex(columns=types, fill_value=0)
)

fig, ax = plt.subplots(figsize=(10, 4.5))

for cement_type in types:
    ax.plot(
        national.index,
        national[cement_type] / 1e6,
        linewidth=2,
        label=cement_type,
    )

ax.set_xlabel("Year")
ax.set_ylabel("Shipments (million tons)")
ax.set_title("U.S. cement shipments, 2010–2024")
ax.legend(frameon=False)
ax.set_xticks(range(2010, 2025, 2))

fig.tight_layout()
save(fig, "usgs_national_shipments")

state = (
    df.groupby(["STATE", "TYPE"])["TONS"]
    .sum()
    .unstack(fill_value=0)
    .reindex(columns=types, fill_value=0)
)

state["total"] = state.sum(axis=1)
state["blended_share"] = (
    state["Blended"] / state["total"].replace(0, float("nan"))
)

state = state.sort_values("total", ascending=False)

fig, ax = plt.subplots(
    figsize=(10, max(8, len(state) * 0.28))
)

ax.barh(
    state.index,
    state["Portland"] / 1e6,
    label="Portland",
)

ax.barh(
    state.index,
    state["Blended"] / 1e6,
    left=state["Portland"] / 1e6,
    label="Blended",
)

ax.invert_yaxis()
ax.set_xlabel("Total shipments, 2010–2024 (million tons)")
ax.set_title("Cement shipments by state")
ax.legend(frameon=False)

fig.tight_layout()
save(fig, "usgs_state_shipments")

print("\nYears:", df["year"].min(), "to", df["year"].max())
print("States:", df["STATE"].nunique())
print("Records:", len(df))
print("\nPASS: Empirical USGS shipment figures generated.")
