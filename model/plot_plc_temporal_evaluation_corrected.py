
#!/usr/bin/env python3
"""
Figure S2: Temporal evaluation of PLC diffusion (2010–2024).

Inputs
------
data/usgs_all_state_type_month.csv

outputs/plc_final_2026/03_calibration_2010_2022/
    best_training_curves.csv

outputs/plc_final_2026/04_E01_primary_evaluation/
    national_month_adoption.csv

outputs/plc_final_2026/05_E02_historical_reconstruction/
    national_month_adoption.csv

outputs/plc_final_2026/06_E03_projected_demand/
    national_month_adoption.csv

Outputs
-------
outputs/plc_final_2026/figures/
    Fig1_historical_diffusion.png
    Fig1_historical_diffusion.pdf
    Fig1_historical_diffusion_metrics.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


ROOT = Path("outputs/plc_final_2026")
OUT = ROOT / "figures_corrected"

USGS_FILE = Path("data/usgs_all_state_type_month.csv")

CALIBRATION_FILE = (
    ROOT
    / "03_calibration_2010_2022"
    / "best_training_curves.csv"
)

RUNS = {
    "E01_corrected": (
        ROOT
        / "18_E01_controlled_corrected"
        / "national_month_adoption.csv"
    ),
}

COLORS = {
    "E01_corrected": "#2166AC",
}

LABELS = {
    "E01_corrected": "ABM: demand-weighted RMX adoption",
}

START = pd.Timestamp("2010-01-01")
CAL_END = pd.Timestamp("2022-12-01")
EVAL_START = pd.Timestamp("2023-01-01")
EVAL_END = pd.Timestamp("2024-12-01")


def load_usgs():

    df = pd.read_csv(USGS_FILE)

    required = {"STATE", "YYYY_MM", "TYPE", "TONS"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"Missing USGS columns: {required - set(df.columns)}"
        )

    df["date"] = pd.to_datetime(
        df["YYYY_MM"].astype(str),
        format="%Y-%m",
    )

    df["type"] = (
        df["TYPE"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["TONS"] = pd.to_numeric(
        df["TONS"],
        errors="raise",
    )

    df = df[
        (df["date"] >= START)
        & (df["date"] <= EVAL_END)
    ].copy()

    df = df[
        df["type"].isin(["blended", "portland"])
    ].copy()

    national = (
        df.groupby(["date", "type"])["TONS"]
        .sum()
        .unstack(fill_value=0)
    )

    if not {"blended", "portland"}.issubset(national.columns):
        raise ValueError(
            "USGS data must contain both Blended and Portland."
        )

    denominator = (
        national["blended"] + national["portland"]
    )

    if (denominator <= 0).any():
        raise ValueError(
            "USGS contains months with zero total shipments."
        )

    observed = (
        national["blended"] / denominator
    )

    result = (
        observed
        .rename("observed")
        .reset_index()
        .sort_values("date")
    )

    return result


def load_calibration_target():

    df = pd.read_csv(CALIBRATION_FILE)

    required = {"yyyy_mm", "observed"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"Missing calibration columns: "
            f"{required - set(df.columns)}"
        )

    df["date"] = pd.to_datetime(
        df["yyyy_mm"],
        format="%Y-%m",
    )

    return (
        df[["date", "observed"]]
        .sort_values("date")
        .reset_index(drop=True)
    )


def verify_observed_target(observed):

    calibration = load_calibration_target()

    check = calibration.merge(
        observed,
        on="date",
        how="left",
        suffixes=("_calibration", "_reconstructed"),
        validate="one_to_one",
    )

    if check["observed_reconstructed"].isna().any():
        raise RuntimeError(
            "Some calibration months are missing from USGS."
        )

    differences = np.abs(
        check["observed_calibration"]
        - check["observed_reconstructed"]
    )

    max_difference = differences.max()

    print(
        "Maximum difference between calibration "
        f"and reconstructed USGS target: {max_difference:.10f}"
    )

    if max_difference > 1e-8:
        raise RuntimeError(
            "USGS reconstruction does not match the "
            "calibration target. Check the original "
            "calibration aggregation before plotting."
        )

    print("USGS calibration-target verification: PASSED")


def load_run(path):

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    required = {"yyyy_mm", "A"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"Missing columns in {path}: "
            f"{required - set(df.columns)}"
        )

    df["date"] = pd.to_datetime(
        df["yyyy_mm"],
        format="%Y-%m",
    )

    df["A"] = pd.to_numeric(
        df["A"],
        errors="raise",
    )

    if not df["A"].between(0, 1).all():
        raise ValueError(
            f"Adoption shares outside [0,1] in {path}"
        )

    return (
        df[["date", "A"]]
        .rename(columns={"A": "model"})
        .sort_values("date")
    )


def main():

    OUT.mkdir(parents=True, exist_ok=True)

    # ---------------------------------
    # Observed USGS target
    # ---------------------------------

    observed = load_usgs()

    verify_observed_target(observed)

    merged = observed.copy()

    # ---------------------------------
    # Simulated trajectories
    # ---------------------------------

    for name, path in RUNS.items():

        run = load_run(path)

        run = run.rename(
            columns={"model": name}
        )

        merged = merged.merge(
            run,
            on="date",
            how="inner",
            validate="one_to_one",
        )

    merged = merged[
        (merged["date"] >= START)
        & (merged["date"] <= EVAL_END)
    ].copy()

    if len(merged) != 180:
        raise RuntimeError(
            f"Expected 180 months, found {len(merged)}."
        )

    evaluation = merged[
        (merged["date"] >= EVAL_START)
        & (merged["date"] <= EVAL_END)
    ]

    if len(evaluation) != 24:
        raise RuntimeError(
            f"Expected 24 evaluation months, "
            f"found {len(evaluation)}."
        )

    # ---------------------------------
    # Evaluation metrics
    # ---------------------------------

    metrics = []

    for name in RUNS:

        rmse = np.sqrt(
            np.mean(
                (
                    evaluation[name]
                    - evaluation["observed"]
                ) ** 2
            )
        )

        metrics.append({
            "run": name,
            "rmse_2023_2024": rmse,
            "dec_2022": merged.loc[
                merged["date"] == CAL_END,
                name,
            ].iloc[0],
            "dec_2023": merged.loc[
                merged["date"]
                == pd.Timestamp("2023-12-01"),
                name,
            ].iloc[0],
            "dec_2024": merged.loc[
                merged["date"] == EVAL_END,
                name,
            ].iloc[0],
        })

    metrics_df = pd.DataFrame(metrics)

    metrics_df.to_csv(
        OUT / "Fig1_historical_diffusion_metrics.csv",
        index=False,
    )

    print("\nEvaluation metrics:")
    print(metrics_df.to_string(index=False))

    # ---------------------------------
    # Figure
    # ---------------------------------

    plt.rcParams.update({
        "font.size": 10,
        "axes.labelsize": 11,
        "legend.fontsize": 8.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    fig, ax = plt.subplots(
        figsize=(10, 4.8)
    )

    ax.axvspan(
        EVAL_START,
        EVAL_END,
        color="#EFEFEF",
        alpha=0.65,
        zorder=0,
    )

    ax.plot(
        merged["date"],
        merged["observed"] * 100,
        color="black",
        linewidth=2.3,
        label="USGS blended-cement share",
        zorder=5,
    )

    for name in RUNS:

        ax.plot(
            merged["date"],
            merged[name] * 100,
            color=COLORS[name],
            linewidth=2.0,
            alpha=0.95,
            label=LABELS[name],
        )

    ax.axvline(
        EVAL_START,
        color="0.35",
        linestyle="--",
        linewidth=1.1,
    )

    ax.set_xlim(
        START,
        pd.Timestamp("2025-01-01"),
    )

    ax.set_ylim(bottom=0)

    ax.set_xlabel("Year")
    ax.set_ylabel("National adoption / shipment share (%)")

    ax.xaxis.set_major_locator(
        mdates.YearLocator(2)
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    ax.grid(
        axis="y",
        alpha=0.2,
        linewidth=0.6,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        loc="upper left",
        frameon=False,
    )

    ax.text(
        pd.Timestamp("2023-03-01"),
        0.12,
        "Evaluation\n(2023–2024)",
        transform=ax.get_xaxis_transform(),
        fontsize=9,
        color="0.35",
        va="bottom",
        ha="left",
    )

    fig.tight_layout()

    fig.savefig(
        OUT / "Fig1_historical_diffusion.png",
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        OUT / "Fig1_historical_diffusion.pdf",
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"\nSaved Figure 1 to: {OUT}")


if __name__ == "__main__":
    main()