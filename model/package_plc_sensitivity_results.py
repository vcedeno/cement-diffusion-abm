#!/usr/bin/env python3
"""
Package PLC calibration sensitivity experiment results.

Experiments:
    07_stochastic_robustness
    08_mfr_response_ablation
    09_parameter_sensitivity
    10_TA_TM_interaction

Collects:
    national_month_adoption.csv
    mfr_transition_summary.csv
    run_specification.csv

Creates:
    outputs/plc_final_2026/plc_sensitivity_results.zip
    outputs/plc_final_2026/plc_sensitivity_manifest.csv

Usage:
    python model/package_plc_sensitivity_results.py
"""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import csv
import hashlib

ROOT = Path("outputs/plc_final_2026")

EXPERIMENTS = {
    "07_stochastic_robustness": 30,
    "08_mfr_response_ablation": 1,
    "09_parameter_sensitivity": 12,
    "10_TA_TM_interaction": 8,
}

FILES = {
    "national_month_adoption.csv",
    "mfr_transition_summary.csv",
    "run_specification.csv",
}

ZIP_PATH = ROOT / "plc_sensitivity_results.zip"
MANIFEST_PATH = ROOT / "plc_sensitivity_manifest.csv"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ROOT.mkdir(parents=True, exist_ok=True)

    manifest = []
    selected_files = []
    incomplete_runs = []

    for experiment, expected_runs in EXPERIMENTS.items():
        directory = ROOT / experiment

        if not directory.exists():
            raise FileNotFoundError(
                f"Experiment directory not found: {directory}"
            )

        if experiment == "08_mfr_response_ablation":
            run_dirs = [directory]
        else:
            run_dirs = sorted(
                p for p in directory.iterdir()
                if p.is_dir()
            )

        print(
            f"\n{experiment}: "
            f"{len(run_dirs)} runs found "
            f"(expected {expected_runs})"
        )

        if len(run_dirs) != expected_runs:
            raise RuntimeError(
                f"{experiment}: expected {expected_runs} runs, "
                f"found {len(run_dirs)}"
            )

        for run_dir in run_dirs:
            found = {
                p.name: p
                for p in run_dir.iterdir()
                if p.is_file() and p.name in FILES
            }

            missing = FILES - found.keys()

            if missing:
                incomplete_runs.append(
                    (str(run_dir), sorted(missing))
                )
                continue

            for filename in sorted(FILES):
                path = found[filename]

                selected_files.append(path)

                manifest.append({
                    "experiment": experiment,
                    "run": run_dir.name,
                    "file": filename,
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })

    if incomplete_runs:
        print("\nIncomplete runs:")
        for run, missing in incomplete_runs:
            print(f"  {run}: missing {missing}")

        raise RuntimeError(
            "Packaging stopped because some runs are incomplete."
        )

    with MANIFEST_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "experiment",
                "run",
                "file",
                "path",
                "size_bytes",
                "sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest)

    with ZipFile(ZIP_PATH, "w", ZIP_DEFLATED) as zf:
        for path in selected_files:
            zf.write(path, arcname=path.as_posix())

        zf.write(
            MANIFEST_PATH,
            arcname=MANIFEST_PATH.as_posix(),
        )

    print("\nPackaging complete.")
    print(f"Runs: {sum(EXPERIMENTS.values())}")
    print(f"Files: {len(selected_files)}")
    print(f"ZIP: {ZIP_PATH}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"ZIP size: {ZIP_PATH.stat().st_size / 1024**2:.2f} MB")


if __name__ == "__main__":
    main()
