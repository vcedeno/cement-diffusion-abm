#!/usr/bin/env python3
"""Plot corrected PLC ±20% one-at-a-time sensitivity envelopes."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


ROOT = Path(
    "outputs/plc_final_2026/robustness/"
    "PLC04_parameter_sensitivity_corrected"
)

OUT = Path("outputs/plc_final_2026/figures_corrected")
OUT.mkdir(parents=True, exist_ok=True)


def load_run(name):
    path = ROOT / name / "national_month_adoption.csv"

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(df["yyyy_mm"] + "-01")

    return df.set_index("date")["A"].sort_index()


reference = load_run("reference")


PARAMETERS = [
    ("B0", r"$B_0$", "#8052A3"),
    ("TA", r"$T_A$", "#2C70C9"),
    ("theta", r"$\theta_M$", "#E58A27"),
    ("TM", r"$T_M$", "#2A9062"),
    ("HM", r"$H_M$", "#A05A54"),
    ("kappa", r"$\kappa$", "#777777"),
]


fig, axes = plt.subplots(
    3,
    2,
    figsize=(12, 10),
    sharex=True,
    sharey=True,
    constrained_layout=True,
)

axes = axes.ravel()


for ax, (parameter, label, color) in zip(axes, PARAMETERS):

    minus = load_run(f"{parameter}_minus20")
    plus = load_run(f"{parameter}_plus20")

    dates = reference.index

    lower = pd.concat([minus, plus], axis=1).min(axis=1)
    upper = pd.concat([minus, plus], axis=1).max(axis=1)

    ax.fill_between(
        dates,
        100 * lower,
        100 * upper,
        color=color,
        alpha=0.25,
        label=r"$\pm20\%$ envelope",
    )

    ax.plot(
        dates,
        100 * reference,
        color="black",
        linewidth=1.8,
        label="Reference",
    )

    ax.plot(
        dates,
        100 * minus,
        color=color,
        linewidth=1,
        linestyle="--",
        alpha=0.8,
    )

    ax.plot(
        dates,
        100 * plus,
        color=color,
        linewidth=1,
        linestyle=":",
        alpha=0.8,
    )

    width = 100 * (upper.iloc[-1] - lower.iloc[-1])

    ax.set_title(
        f"{label} ±20%  |  Dec. 2024 range: {width:.2f} pp",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )

    ax.axvline(
        pd.Timestamp("2023-01-01"),
        color="0.5",
        linestyle=":",
        linewidth=0.9,
        alpha=0.6,
    )

    ax.set_xlim(
        pd.Timestamp("2010-01-01"),
        pd.Timestamp("2024-12-01"),
    )

    ax.set_ylim(0, 100)

    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.grid(axis="y", alpha=0.15)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


for ax in axes[::2]:
    ax.set_ylabel("National RMX adoption (%)")

for ax in axes[-2:]:
    ax.set_xlabel("Year")

axes[0].legend(frameon=False, fontsize=9)

output = OUT / "plc_sensitivity_envelopes.png"

fig.savefig(output, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"Saved: {output}")