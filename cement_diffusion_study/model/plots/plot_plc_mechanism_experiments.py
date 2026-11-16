#!/usr/bin/env python3
"""Combined PLC mechanism intervention figure from existing five-seed runs."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--root",
    type=Path,
    default=Path("outputs/simple_abm/PLC_mechanism_experiments"),
)
args = parser.parse_args()

ROOT = args.root
SEEDS = range(42, 47)

EXPERIMENTS = [
    ("Manufacturer market response",
     ["no_mfr_market", "no_market_response", "no_mfr_market_response"]),
    ("Company-wide production priority",
     ["no_corporate_priority", "no_company_priority"]),
    ("Manufacturer peer influence",
     ["no_mfr_peer"]),
    ("RMX peer influence",
     ["no_rmx_peer"]),
    ("DOT purchasing response",
     ["no_dot_response", "no_dot_purchasing"]),
]

COLORS = [
    "#c0392b",
    "#e67e22",
    "#8e44ad",
    "#2980b9",
    "#16a085",
]

BASE_COLOR = "#202c39"


def find_folder(names):
    for name in names:
        p = ROOT / name
        if p.is_dir():
            return p
    raise FileNotFoundError(
        f"Cannot find experiment among {names}. "
        f"Available: {[p.name for p in ROOT.iterdir() if p.is_dir()]}"
    )


def read_seed(folder, seed):
    path = folder / f"seed_{seed}" / "national_month_market_share.csv"
    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(df["yyyy_mm"])
    df["share"] = df["market_share"].astype(float) * 100

    return df.set_index("date")["share"].sort_index()


def load_ensemble(folder):
    data = pd.concat(
        [read_seed(folder, seed).rename(str(seed)) for seed in SEEDS],
        axis=1,
    )

    return pd.DataFrame({
        "mean": data.mean(axis=1),
        "low": data.min(axis=1),
        "high": data.max(axis=1),
    })


def main():
    baseline_folder = ROOT / "baseline"
    baseline = load_ensemble(baseline_folder)

    interventions = []
    summary = []

    for (label, aliases), color in zip(EXPERIMENTS, COLORS):
        folder = find_folder(aliases)
        curve = load_ensemble(folder)

        effects = []

        for seed in SEEDS:
            b = read_seed(baseline_folder, seed).loc["2024-12-01"]
            i = read_seed(folder, seed).loc["2024-12-01"]
            effects.append(i - b)

        effects = np.array(effects)

        interventions.append((label, curve, color))

        summary.append({
            "mechanism": label,
            "mean_effect_pp": effects.mean(),
            "min_effect_pp": effects.min(),
            "max_effect_pp": effects.max(),
        })

        print(
            f"{label}: {effects.mean():+.2f} pp "
            f"[{effects.min():+.2f}, {effects.max():+.2f}]"
        )

    fig = plt.figure(figsize=(13, 9.2))

    gs = GridSpec(
        2, 1,
        height_ratios=[3.2, 1.15],
        hspace=0.37,
        left=0.11,
        right=0.96,
        top=0.96,
        bottom=0.10,
    )

    ax = fig.add_subplot(gs[0])

    # Out-of-sample evaluation period
    ax.axvspan(
        pd.Timestamp("2023-01-01"),
        pd.Timestamp("2024-12-31"),
        color="#e9edf1",
        alpha=0.8,
        zorder=0,
    )

    # Baseline
    ax.plot(
        baseline.index,
        baseline["mean"],
        color=BASE_COLOR,
        lw=2.8,
        label="Baseline",
        zorder=10,
    )

    # Five interventions on the SAME axes
    for label, curve, color in interventions:
        ax.plot(
            curve.index,
            curve["mean"],
            color=color,
            lw=1.9,
            label=f"No {label.lower()}",
            alpha=0.95,
        )

    ax.set_xlim(
        pd.Timestamp("2010-01-01"),
        pd.Timestamp("2024-12-31"),
    )
    ax.set_ylim(bottom=0)

    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.set_ylabel("National PLC market share (%)", fontsize=11)
    ax.set_xlabel("Year", fontsize=10)

    ax.grid(alpha=0.18)
    ax.set_axisbelow(True)

    ax.legend(
        loc="upper left",
        fontsize=9,
        frameon=False,
        ncol=2,
    )

    ax.set_title(
        "A  National PLC diffusion under mechanism interventions",
        loc="left",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )

    # Effect summary: horizontal bars
    ax2 = fig.add_subplot(gs[1])

    names = [r["mechanism"] for r in summary]
    reductions = [-r["mean_effect_pp"] for r in summary]

    y = np.arange(len(names))

    ax2.barh(
        y,
        reductions,
        color=COLORS,
        height=0.62,
        alpha=0.9,
    )

    ax2.set_yticks(y)
    ax2.set_yticklabels(names, fontsize=9)
    ax2.invert_yaxis()

    ax2.set_xlim(0, max(reductions) * 1.18)
    ax2.set_xlabel(
        "Reduction in national PLC market share (percentage points)",
        fontsize=10,
    )

    ax2.set_title(
        "B  Mean intervention effect, December 2024",
        loc="left",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )

    for idx, value in enumerate(reductions):
        ax2.text(
            value + 0.25,
            idx,
            f"{value:.2f} pp",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    ax2.grid(axis="x", alpha=0.15)
    ax2.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax2.spines[spine].set_visible(False)


    fig.text(
        0.5,
        0.035,
        "Lines: five-seed means (42–46)  |  "
        "Shaded period: 2023–2024 evaluation  |  "
        "Effects: paired differences relative to baseline",
        ha="center",
        fontsize=8.5,
    )

    out = ROOT / "Figure_2_PLC_combined_mechanisms"

    fig.savefig(
        out.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        out.with_suffix(".pdf"),
        bbox_inches="tight",
    )

    pd.DataFrame(summary).to_csv(
        ROOT / "mechanism_effects_dec2024.csv",
        index=False,
    )

    plt.close(fig)

    print(f"\nSaved: {out.with_suffix('.png')}")
    print(f"Saved: {out.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
