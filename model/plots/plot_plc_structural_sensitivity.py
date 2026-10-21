#!/usr/bin/env python3

from pathlib import Path
import argparse

import pandas as pd
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    panels = [
        ("T_G", r"(a) DOT implementation timescale, $T_G$", " months"),
        ("kappa_A", r"(b) Adoption-propensity sharpness, $\kappa_A$", ""),
        ("T_A", r"(c) RMX adoption-realization timescale, $T_A$", " months"),
    ]

    fig, axes = plt.subplots(
        1, 3,
        figsize=(10.5, 3.3),
        sharex=True,
        sharey=True
    )

    for ax, (parameter, title, suffix) in zip(axes, panels):

        d = df[df["parameter"] == parameter].copy()

        for value in sorted(d["value"].unique()):
            x = d[d["value"] == value].sort_values("year")

            is_ref = bool(x["reference"].iloc[0])

            label = f"{value:g}{suffix}"
            if is_ref:
                label += " (reference)"

            ax.plot(
                x["year"],
                x["A"],
                linewidth=2.4 if is_ref else 1.5,
                linestyle="-" if is_ref else "--",
                label=label,
            )

        ax.set_title(title, fontsize=10)
        ax.set_xlim(2010, 2024)
        ax.set_ylim(0, 0.8)

        ax.set_xticks([2010, 2014, 2018, 2022, 2024])
        ax.tick_params(axis="both", labelsize=8)

        ax.grid(alpha=0.2, linewidth=0.6)

        ax.legend(
            frameon=False,
            fontsize=7.5,
            loc="upper left"
        )

    axes[0].set_ylabel(
        "National demand-weighted RMX adoption, $A(t)$",
        fontsize=9
    )

    for ax in axes:
        ax.set_xlabel("Year", fontsize=9)

    fig.tight_layout()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")

    print(f"WROTE: {out}")
    print(f"WROTE: {out.with_suffix('.png')}")


if __name__ == "__main__":
    main()
