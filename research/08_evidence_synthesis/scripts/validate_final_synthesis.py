#!/usr/bin/env python3
"""Validate Module 08 final synthesis references against the existing evidence."""
from pathlib import Path
import pandas as pd


def main():
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    stage1 = pd.read_csv(data / "cross_module_evidence_matrix.csv")
    stage2 = pd.read_csv(data / "mechanism_evidence_synthesis.csv")
    assessment = pd.read_csv(data / "evidence_to_model_assessment.csv")
    phases = pd.read_csv(data / "historical_synthesis_phases.csv")
    known_stage1 = set(stage1["finding_id"].astype(str))
    known_stage2 = set(stage2["synthesis_id"].astype(str))

    def check(frame, column, allowed):
        for row_num, value in enumerate(frame[column].fillna(""), start=2):
            refs = [x.strip() for x in str(value).split(";") if x.strip()]
            missing = set(refs) - allowed
            if missing:
                raise ValueError(f"{column} row {row_num}: unknown IDs {sorted(missing)}")

    check(assessment, "synthesis_ids", known_stage2)
    check(assessment, "stage1_finding_ids", known_stage1)
    check(phases, "synthesis_ids", known_stage2)
    print(f"Validated {len(assessment)} mechanism assessments, {len(phases)} phases, "
          f"{len(stage2)} Stage 2 syntheses and {len(stage1)} Stage 1 records.")


if __name__ == "__main__":
    main()
