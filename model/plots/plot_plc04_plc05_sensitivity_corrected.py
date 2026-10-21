#!/usr/bin/env python3
"""
Plot corrected PLC04 and PLC05 sensitivity analyses.

PLC04:
    One-at-a-time sensitivity of December 2024 national
    demand-weighted RMX adoption to six calibrated parameters.

PLC05:
    Joint sensitivity to RMX adoption timescale T_A and
    manufacturer response delay T_M.

Inputs
------
outputs/plc_final_2026/robustness/
    PLC04_parameter_sensitivity_corrected/
        plc04_parameter_sensitivity_summary.csv

    PLC05_timescale_interaction_corrected/
        plc05_timescale_interaction_summary.csv

Outputs
-------
outputs/plc_final_2026/figures_corrected/sensitivity/
    S5_parameter_sensitivity_corrected.pdf
    S5_parameter_sensitivity_corrected.png
    S6_timescale_interaction_corrected.pdf
    S6_timescale_interaction_corrected.png

Usage
-----
python model/plots/plot_plc04_plc05_sensitivity_corrected.py
"""

from pathlib import Path
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm


# ============================================================
# Plot configuration
# ============================================================

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 300,
})


PARAMETERS = [
    ("B0", r"$B_0$"),
    ("TA", r"$T_A$"),
    ("theta", r"$\theta_M$"),
    ("TM", r"$T_M$"),
    ("HM", r"$H_M$"),
    ("kappa", r"$\kappa$"),
]


# ============================================================
# Helpers
# ============================================================

def save_figure(fig, out_base):
    out_base.parent.mkdir(parents=True, exist_ok=True)

    pdf_path = out_base.with_suffix(".pdf")
    png_path = out_base.with_suffix(".png")

    fig.savefig(
        pdf_path,
        bbox_inches="tight",
        facecolor="white",
    )

    fig.savefig(
        png_path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    print(f"WROTE: {pdf_path}")
    print(f"WROTE: {png_path}")


# ============================================================
# Figure S5: One-at-a-time parameter sensitivity
# ============================================================

def plot_oat(df, out_base):

    required = {
        "experiment",
        "A_2024_pp",
        "delta_vs_reference_pp",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"PLC04 missing columns: {sorted(missing)}"
        )

    ref = df.loc[
        df["experiment"] == "reference"
    ]

    if len(ref) != 1:
        raise ValueError(
            "Expected exactly one PLC04 reference run"
        )

    reference_adoption = float(
        ref["A_2024_pp"].iloc[0]
    )

    labels = []
    minus_effects = []
    plus_effects = []

    for prefix, latex_label in PARAMETERS:

        minus_name = f"{prefix}_minus20"
        plus_name = f"{prefix}_plus20"

        minus = df.loc[
            df["experiment"] == minus_name,
            "delta_vs_reference_pp",
        ]

        plus = df.loc[
            df["experiment"] == plus_name,
            "delta_vs_reference_pp",
        ]

        if len(minus) != 1 or len(plus) != 1:
            raise ValueError(
                f"Missing or duplicate PLC04 experiment "
                f"for {prefix}"
            )

        labels.append(latex_label)
        minus_effects.append(float(minus.iloc[0]))
        plus_effects.append(float(plus.iloc[0]))

    minus_effects = np.asarray(minus_effects)
    plus_effects = np.asarray(plus_effects)

    # Sort by largest absolute endpoint effect.
    importance = np.maximum(
        np.abs(minus_effects),
        np.abs(plus_effects),
    )

    order = np.argsort(-importance)

    labels = [labels[i] for i in order]
    minus_effects = minus_effects[order]
    plus_effects = plus_effects[order]

    y = np.arange(len(labels))
    height = 0.34

    fig, ax = plt.subplots(figsize=(8.4, 4.5))

    color_minus = "#2878B5"
    color_plus = "#E68635"

    ax.barh(
        y - height / 2,
        minus_effects,
        height=height,
        color=color_minus,
        label=r"Parameter $-20\%$",
    )

    ax.barh(
        y + height / 2,
        plus_effects,
        height=height,
        color=color_plus,
        label=r"Parameter $+20\%$",
    )

    ax.axvline(
        0,
        color="#333333",
        linewidth=0.9,
        zorder=3,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    ax.set_xlabel(
        "Change in December 2024 national adoption "
        "(percentage points)"
    )

    ax.set_ylabel("Calibrated parameter")

    ax.grid(
        axis="x",
        alpha=0.18,
        linewidth=0.6,
    )

    ax.set_axisbelow(True)

    ax.legend(
        loc="lower right",
        frameon=False,
        ncol=2,
    )

    # Add modest horizontal padding.
    all_effects = np.r_[
        minus_effects,
        plus_effects,
    ]

    minimum = min(0, all_effects.min())
    maximum = max(0, all_effects.max())

    span = maximum - minimum
    padding = max(0.8, span * 0.06)

    ax.set_xlim(
        minimum - padding,
        maximum + padding,
    )

    # Remove unnecessary borders.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    save_figure(fig, out_base)

    plt.close(fig)

    print(
        f"PLC04 reference December 2024 adoption: "
        f"{reference_adoption:.4f}%"
    )


# ============================================================
# Figure S6: T_A × T_M interaction heatmap
# ============================================================

def plot_timescale(df, out_base):

    required = {
        "T_A",
        "T_M",
        "A_2024_pct",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"PLC05 missing columns: {sorted(missing)}"
        )

    pivot = df.pivot(
        index="T_A",
        columns="T_M",
        values="A_2024_pct",
    ).sort_index().sort_index(axis=1)

    ta_values = list(pivot.index)
    tm_values = list(pivot.columns)

    if ta_values != [4, 5, 6]:
        raise ValueError(
            f"Unexpected T_A values: {ta_values}"
        )

    if tm_values != [23, 29, 35]:
        raise ValueError(
            f"Unexpected T_M values: {tm_values}"
        )

    values = pivot.to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError(
            "PLC05 heatmap contains missing or invalid values"
        )

    reference = float(pivot.loc[5, 29])

    fig, ax = plt.subplots(figsize=(6.7, 4.9))

    # Sequential colors show absolute adoption levels.
    image = ax.imshow(
        values,
        cmap="viridis",
        aspect="auto",
        interpolation="nearest",
        vmin=np.floor(values.min()),
        vmax=np.ceil(values.max()),
    )

    ax.set_xticks(np.arange(len(tm_values)))
    ax.set_xticklabels(tm_values)

    ax.set_yticks(np.arange(len(ta_values)))
    ax.set_yticklabels(ta_values)

    ax.set_xlabel(
        r"Manufacturer response delay, $T_M$ (months)"
    )

    ax.set_ylabel(
        r"RMX adoption timescale, $T_A$ (months)"
    )

    # Cell values.
    for row in range(len(ta_values)):
        for col in range(len(tm_values)):

            value = values[row, col]

            # Choose text color based on background brightness.
            rgba = image.cmap(
                image.norm(value)
            )

            luminance = (
                0.2126 * rgba[0]
                + 0.7152 * rgba[1]
                + 0.0722 * rgba[2]
            )

            text_color = (
                "black"
                if luminance > 0.55
                else "white"
            )

            is_reference = (
                ta_values[row] == 5
                and tm_values[col] == 29
            )

            label = f"{value:.1f}%"

            if is_reference:
                label += "\n(reference)"

            ax.text(
                col,
                row,
                label,
                ha="center",
                va="center",
                fontsize=10 if is_reference else 11,
                fontweight=(
                    "bold" if is_reference else "normal"
                ),
                color=text_color,
            )

    # Highlight calibrated reference cell.
    from matplotlib.patches import Rectangle

    reference_row = ta_values.index(5)
    reference_col = tm_values.index(29)

    rect = Rectangle(
        (
            reference_col - 0.5,
            reference_row - 0.5,
        ),
        1,
        1,
        fill=False,
        edgecolor="white",
        linewidth=2.0,
    )

    ax.add_patch(rect)

    cbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.045,
        pad=0.04,
    )

    cbar.set_label(
        "December 2024 national adoption (%)"
    )

    fig.tight_layout()

    save_figure(fig, out_base)

    plt.close(fig)

    print(
        f"PLC05 reference December 2024 adoption: "
        f"{reference:.4f}%"
    )


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--root",
        default="outputs/plc_final_2026",
    )

    args = parser.parse_args()

    root = Path(args.root)

    plc04_file = (
        root
        / "robustness"
        / "PLC04_parameter_sensitivity_corrected"
        / "plc04_parameter_sensitivity_summary.csv"
    )

    plc05_file = (
        root
        / "robustness"
        / "PLC05_timescale_interaction_corrected"
        / "plc05_timescale_interaction_summary.csv"
    )

    for path in [plc04_file, plc05_file]:
        if not path.is_file():
            raise FileNotFoundError(path)

    plc04 = pd.read_csv(plc04_file)
    plc05 = pd.read_csv(plc05_file)

    out_dir = (
        root
        / "figures_corrected"
        / "sensitivity"
    )

    plot_oat(
        plc04,
        out_dir / "S5_parameter_sensitivity_corrected",
    )

    plot_timescale(
        plc05,
        out_dir / "S6_timescale_interaction_corrected",
    )

    print("\nBoth corrected sensitivity figures generated.")


if __name__ == "__main__":
    main()
