#!/usr/bin/env python3
"""Build Module 08 Stage 1 provenance matrix from Modules 01–07.

Run from the repository root:
    python research/08_evidence_synthesis/scripts/build_cross_module_matrix.py

Inputs are read only. Outputs are written to research/08_evidence_synthesis/.
"""

from pathlib import Path

import pandas as pd


RESEARCH_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = RESEARCH_ROOT / "08_evidence_synthesis"
DATA_DIR = OUTPUT_DIR / "data"


def input_file(module: str, filename: str) -> Path:
    return RESEARCH_ROOT / module / "data" / filename


def clean(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_url(value) -> str:
    """Normalize for source reuse detection, not for citation or source verification."""
    if pd.isna(value):
        return ""
    url = str(value).strip().lower()
    if not url:
        return ""
    return url.split("?", 1)[0].rstrip("/")


def build_records() -> tuple[pd.DataFrame, pd.DataFrame]:
    records = []

    def add(
        module, record, description, period, scope, evidence_type,
        source_title, source_url, limitation, mechanism="", status="",
        original="", details="",
    ):
        records.append({
            "finding_id": f"SYN{len(records) + 1:04}",
            "source_module": module,
            "source_record_ids": clean(record),
            "documented_finding": clean(description),
            "event_period": clean(period),
            "geographic_scope": clean(scope),
            "mechanism": clean(mechanism),
            "evidence_type": clean(evidence_type),
            "source_title": clean(source_title),
            "source_url": clean(source_url),
            "verification_status": clean(status),
            "interpretation_limit": clean(limitation),
            "original_classification": clean(original),
            "source_detail": clean(details),
        })

    # Module 01: manufacturer evidence; preserve each audited plant record.
    plants = pd.read_excel(
        input_file("01_manufacturer_availability", "mfr_plc_public_evidence_audit_completed.xlsx"),
        sheet_name="Plant Evidence Audit",
    )
    for i, row in plants.iterrows():
        add(
            "01", f'Plant Evidence Audit!row{i + 2}; mfr_src_id={clean(row.get("mfr_src_id"))}',
            row["evidence_description"], row["supported_date"],
            f'{clean(row["plant"])} | {clean(row["state"])}',
            row["evidence_scope"], row["source_title"], row["source_url"],
            row["limitation"], "manufacturer_availability", "as_recorded_in_module01",
            row["evidence_status"],
            f'date_interpretation={clean(row["date_interpretation"])}; '
            f'assumption_supported={clean(row["assumption_supported"])}',
        )

    # Module 02: aggregate the original shipment categories; never equate blended with PLC.
    shipments = pd.read_csv(input_file("02_market_demand", "usgs_all_state_type_month.csv"))
    shipments["year"] = shipments["YYYY_MM"].astype(str).str[:4].astype(int)
    annual = (
        shipments.groupby(["year", "TYPE"], dropna=False)
        .agg(tons=("TONS", "sum"), rows=("TONS", "size"), states=("STATE", "nunique"))
        .reset_index()
    )
    annual.to_csv(DATA_DIR / "usgs_annual_type_aggregates.csv", index=False)
    for i, row in annual.iterrows():
        add(
            "02", f"usgs_annual_type_aggregates.csv:row{i + 2}",
            f"USGS reported {row.tons:,.0f} tons in shipment category {row.TYPE} "
            f"in {int(row.year)} across {int(row.states)} distinct STATE labels "
            f"({int(row.rows)} monthly state records).",
            int(row.year), "USGS reporting states", "reported shipment aggregate",
            "USGS monthly state/type shipment dataset", "",
            "Blended includes materials other than PLC; shipment category is not PLC "
            "adoption. Aggregation sums supplied rows without inferring missing values.",
            "market_shipments", "derived_from_supplied_dataset", row.TYPE,
        )

    # Module 03: state DOT acceptance is permission, not observed use.
    dot = pd.read_csv(input_file("03_regulations_standards", "dot_first_acceptance.csv"))
    for i, row in dot.iterrows():
        add(
            "03", f"dot_first_acceptance.csv:row{i + 2}",
            f"First recorded DOT PLC acceptance date for {row.state}: {row.t_accept}.",
            row.t_accept, row.state, "compiled acceptance date",
            "Module 03 DOT first-acceptance dataset", "",
            "Acceptance is permission, not measured use or purchases. Date precision "
            "is monthly; verify definitions in Module 03 README.",
            "dot_acceptance", "compiled_in_module03",
        )

    # Module 04: manufacturer economics.
    economics = pd.read_csv(input_file("04_manufacturer_economics", "manufacturer_economics_evidence.csv"))
    for i, row in economics.iterrows():
        period = (f"{clean(row.event_start)}–{clean(row.event_end)}"
                  if clean(row.event_end) else row.event_start)
        add(
            "04", f"manufacturer_economics_evidence.csv:row{i + 2}",
            row.evidence_summary, period,
            f"{clean(row.company)} | {clean(row.plant)} | {clean(row.state)}",
            row.source_type, row.source_title, row.source_url,
            row.interpretation_limit, row.economic_mechanism,
            "as_recorded_in_module04", row.evidence_category,
            f"plc_specific={clean(row.plc_specific)}; event_status={clean(row.event_status)}",
        )

    # Module 05: RMX adoption decisions.
    rmx = pd.read_csv(input_file("05_rmx_adoption_decisions", "rmx_adoption_evidence.csv"))
    for i, row in rmx.iterrows():
        add(
            "05", f"rmx_adoption_evidence.csv:row{i + 2}",
            row.evidence_summary, row.event_date,
            f"{clean(row.company)} | {clean(row.facility)} | {clean(row.state)}",
            row.source_type, row.source_title, row.source_url,
            row.interpretation_limit, row.economic_mechanism,
            "as_recorded_in_module05", row.evidence_category,
            f"plc_specific={clean(row.plc_specific)}; "
            f"quantitative_value={clean(row.quantitative_value)} {clean(row.quantitative_unit)}",
        )

    # Module 06: DOT decision factors.
    decisions = pd.read_csv(input_file("06_dot_decision_factors", "dot_decision_evidence.csv"))
    for i, row in decisions.iterrows():
        add(
            "06", f"dot_decision_evidence.csv:row{i + 2}",
            row.documented_fact, row.document_year,
            f"{clean(row.agency)} | {clean(row.state)}",
            row.evidence_type, row.source_title, row.source_url,
            row.interpretation_limit, row.decision_factor, "as_recorded_in_module06",
        )

    # Module 07: external signals; retain original verification labels.
    signals = pd.read_csv(input_file("07_external_signals", "external_signals_master.csv"))
    for _, row in signals.iterrows():
        add(
            "07", f"external_signals_master.csv:signal_id={row.signal_id}",
            row.evidence_summary, row.date, row.geographic_scope,
            row.signal_type, row.source_title, row.source_url,
            row.interpretation_limit, row.category, row.verification_status,
            row.existing_or_new,
            f"event={clean(row.event)}; "
            f"cross_module_reference={clean(row.cross_module_reference)}",
        )

    return pd.DataFrame(records), annual


def write_audits(matrix: pd.DataFrame) -> tuple[int, int]:
    matrix["source_url_normalized"] = matrix["source_url"].map(normalize_url)
    has_url = matrix["source_url_normalized"].ne("")
    sourced = matrix.loc[has_url]

    counts = sourced.groupby("source_url_normalized").size()
    module_counts = sourced.groupby("source_url_normalized")["source_module"].nunique()
    matrix["records_sharing_source_url"] = (
        matrix["source_url_normalized"].map(counts).fillna(0).astype(int)
    )
    matrix["source_reused_across_records"] = matrix["records_sharing_source_url"].gt(1)
    matrix["cross_module_reused_source"] = (
        matrix["source_url_normalized"].map(module_counts).fillna(0).gt(1)
    )
    matrix.to_csv(DATA_DIR / "cross_module_evidence_matrix.csv", index=False)

    reuse = (
        sourced.groupby("source_url_normalized")
        .agg(
            record_count=("finding_id", "size"),
            module_count=("source_module", "nunique"),
            modules=("source_module", lambda s: ";".join(sorted(set(s)))),
            finding_ids=("finding_id", lambda s: ";".join(s)),
        )
        .reset_index()
        .sort_values(["module_count", "record_count"], ascending=False)
    )
    reuse = reuse.loc[reuse["record_count"] > 1]
    reuse.to_csv(DATA_DIR / "source_reuse_audit.csv", index=False)

    coverage = (
        matrix.groupby("source_module")
        .agg(
            records=("finding_id", "size"),
            unique_nonempty_source_urls=(
                "source_url_normalized", lambda s: s[s.ne("")].nunique()
            ),
            records_with_interpretation_limit=(
                "interpretation_limit", lambda s: s.ne("").sum()
            ),
            records_with_source_url=("source_url", lambda s: s.ne("").sum()),
        )
        .reset_index()
    )
    coverage.to_csv(DATA_DIR / "module_coverage_audit.csv", index=False)
    return len(reuse), int(reuse["module_count"].gt(1).sum())


def write_limitations() -> None:
    issues = [
        ("01", "Scheduled conversion dates must not be relabeled as actual operational availability.",
         "Interpret date_interpretation and limitation per plant."),
        ("02", "USGS blended category is not a PLC-specific adoption measure.",
         "Use descriptive shipments only; no PLC market-share inference."),
        ("03", "First acceptance dates are not purchase/adoption dates.",
         "Keep acceptance as an enabling condition."),
        ("04", "Economic evidence is sparse and not a census of retrofit costs.",
         "Avoid national parameter estimates."),
        ("05", "Some RMX evidence concerns low-carbon concrete generally.",
         "Retain plc_specific field in source detail."),
        ("06", "DOT decisions are heterogeneous; documented factors are not causal coefficients.",
         "Do not infer universal motivation."),
        ("07", "Several external signals are not reverified and some are broader than PLC.",
         "Preserve verification_status and source-specific limits."),
        ("ALL", "Repeated source URLs and cross-module observations are not independent corroboration.",
         "Consult source_reuse_audit.csv before counting supporting sources."),
        ("ALL", "USGS annual totals sum rows as supplied; missingness and historical "
         "category comparability are not audited.",
         "Do not infer complete national coverage from aggregates."),
    ]
    pd.DataFrame(
        issues,
        columns=["module", "evidence_gap_or_limitation", "required_interpretation"],
    ).to_csv(DATA_DIR / "evidence_gaps_and_limitations.csv", index=False)


def write_readme(record_count: int) -> None:
    content = f"""# Module 08 — Evidence Synthesis (Stage 1: provenance matrix)

## Status
Stage 1: source-preserving cross-module matrix and reuse/coverage audit.
Interpretive synthesis and figures are **not yet produced**.

## Contents
- `data/cross_module_evidence_matrix.csv`: {record_count} source-linked observations
  or aggregates. A row is **not** an independent finding.
- `data/usgs_annual_type_aggregates.csv`: annual sums by original USGS TYPE,
  **not PLC adoption**.
- `data/source_reuse_audit.csv`: URLs repeated within or across modules.
- `data/module_coverage_audit.csv`: record and source URL coverage.
- `data/evidence_gaps_and_limitations.csv`: interpretation constraints.
- `scripts/build_cross_module_matrix.py`: deterministic regeneration.

## Reproduce
From repository root:

```bash
python research/08_evidence_synthesis/scripts/build_cross_module_matrix.py
```

Requires `pandas` and an Excel reader such as `openpyxl`. The script reads
Modules 01–07 and does not edit their source files.

## Method
The matrix retains each audited plant record, each DOT acceptance record,
manufacturer economics, RMX and DOT decision observations, and external signal.
Module 02's monthly shipments are aggregated by year and original TYPE.
These aggregates are descriptive and do not identify PLC-specific adoption.
Repeated URLs are flagged but distinct observations are not deduplicated.
Verification status is inherited where supplied; otherwise the label indicates
provenance, **not independent verification**.

## Next step
Review cross-module event overlap and date semantics, then construct the
mechanism-level synthesis before generating figures.
"""
    (OUTPUT_DIR / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    matrix, annual = build_records()
    repeated, cross_module = write_audits(matrix)
    write_limitations()
    write_readme(len(matrix))
    print(f"Evidence records: {len(matrix)}")
    print(f"USGS annual category aggregates: {len(annual)}")
    print(f"Repeated source URLs: {repeated}")
    print(f"Cross-module reused URLs: {cross_module}")
    print(f"Outputs: {DATA_DIR}")


if __name__ == "__main__":
    main()
