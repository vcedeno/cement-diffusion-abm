#!/usr/bin/env python3
"""Plot PLC03 stochastic robustness from 20 paired simulation results."""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

ROOT = Path("outputs/plc_final_2026/robustness/PLC03_multiseed")
ANALYSIS = ROOT / "analysis"

paired = pd.read_csv(ANALYSIS / "plc03_multiseed_paired_results.csv")
summary = pd.read_csv(ANALYSIS / "plc03_multiseed_summary.csv").iloc[0]

assert len(paired) == 20
assert set(paired["seed"]) == set(range(101, 121))

# Collect monthly national demand-weighted adoption trajectories.
records = []

for seed in sorted(paired["seed"]):
    for scenario in ("peer_enabled", "peer_disabled"):
        path = ROOT / f"seed_{seed}" / scenario / "national_month_adoption.csv"
        df = pd.read_csv(path)

        df["date"] = pd.to_datetime(df["yyyy_mm"])
        df["adoption_pct"] = 100 * df["A"]
        df["seed"] = seed
        df["scenario"] = scenario

        records.append(df[["date", "seed", "scenario", "adoption_pct"]])

trajectories = pd.concat(records, ignore_index=True)

stats = (
    trajectories
    .groupby(["scenario", "date"])["adoption_pct"]
    .agg(["mean", "std"])
    .reset_index()
)

# Verify that monthly trajectories reproduce the paired endpoint results.
for _, row in paired.iterrows():
    seed = int(row["seed"])

    for scenario, expected in [
        ("peer_enabled", row["adoption_enabled_pct"]),
        ("peer_disabled", row["adoption_disabled_pct"]),
    ]:
        actual = trajectories.loc[
            (trajectories["seed"] == seed)
            & (trajectories["scenario"] == scenario)
            & (trajectories["date"] == pd.Timestamp("2024-12-01")),
            "adoption_pct",
        ].iloc[0]

        assert np.isclose(actual, expected, atol=1e-5), (
            seed, scenario, actual, expected
        )

blue = "#2878a8"
orange = "#df8f32"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(12.5, 4.6),
    gridspec_kw={"width_ratios": [1, 1.25]},
)

# Panel (a): paired endpoint effects.
ax1.scatter(
    paired["seed"],
    paired["peer_effect_pp"],
    color=blue,
    s=34,
    zorder=3,
    label="Paired realizations",
)

mean = float(summary["mean_peer_effect_pp"])
ci_low = float(summary["ci95_mean_low_pp"])
ci_high = float(summary["ci95_mean_high_pp"])

ax1.axhspan(
    ci_low, ci_high,
    color="0.75", alpha=0.35,
    label="95% CI of mean",
)

ax1.axhline(
    mean,
    color="0.2",
    linewidth=1.5,
    label=f"Mean ({mean:.2f} pp)",
)

# No seed-42 reference line.

ax1.set_title("(a) Paired stochastic effects")
ax1.set_xlabel("Random seed")
ax1.set_ylabel("Peer-enabled adoption advantage (pp)")
ax1.set_xlim(100, 121)
ax1.set_xticks([101, 105, 110, 115, 120])
ax1.legend(frameon=False, fontsize=8)

# Panel (b): mean trajectories and ±1 SD.
for scenario, label, color in [
    ("peer_enabled", "Peer enabled", blue),
    ("peer_disabled", "Peer disabled", orange),
]:
    subset = stats.loc[stats["scenario"] == scenario].sort_values("date")

    dates = subset["date"].to_numpy()
    mean_values = subset["mean"].to_numpy()
    sd_values = subset["std"].to_numpy()

    ax2.plot(
        dates, mean_values,
        color=color,
        linewidth=1.8,
        label=label,
    )

    ax2.fill_between(
        dates,
        mean_values - sd_values,
        mean_values + sd_values,
        color=color,
        alpha=0.17,
        linewidth=0,
    )

ax2.set_title("(b) Mean trajectories ± 1 SD")
ax2.set_xlabel("Year")
ax2.set_ylabel("National demand-weighted adoption (%)")
ax2.xaxis.set_major_locator(mdates.YearLocator(2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax2.set_xlim(pd.Timestamp("2010-01-01"), pd.Timestamp("2024-12-01"))
ax2.set_ylim(bottom=0)
ax2.legend(frameon=False, fontsize=9)

for ax in (ax1, ax2):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)

fig.tight_layout()

# Save separately so the original figure remains available.
for ext in ("png", "pdf"):
    path = ANALYSIS / f"plc03_stochastic_robustness_no_reference.{ext}"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"Saved: {path}")

plt.close(fig)

print(f"Mean peer effect: {mean:.4f} pp")
print(f"95% CI: [{ci_low:.4f}, {ci_high:.4f}] pp")
print("All 20 paired endpoint values verified.")
