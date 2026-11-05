# Module 08 — PLC Evidence Synthesis

## Contents
- `data/cross_module_evidence_matrix.csv`: 311 source-linked observation/aggregate rows. A row is **not** a distinct independent finding; no causal claims or cross-module deduplication are implied.
- `data/usgs_annual_type_aggregates.csv`: annual sums by original USGS TYPE, **not PLC adoption**.
- `data/source_reuse_audit.csv`: repeated URLs, including cross-module reuse.
- `data/module_coverage_audit.csv`: source URL and record coverage.
- `data/evidence_gaps_and_limitations.csv`: interpretive constraints.
- `scripts/build_cross_module_matrix.py`: deterministic regeneration from Modules 01–07.

## Reproduce
From repository root:

```bash
python research/08_evidence_synthesis/scripts/build_cross_module_matrix.py
```

Requires `pandas` and an Excel engine capable of reading `.xlsx`. Inputs are the existing module folders under `research/`.

## Method
The matrix preserves each plant audit row, each state acceptance row, each economic/RMX/DOT observation, and each Module 07 signal. Module 02's 25,299 monthly rows are represented by annual TYPE aggregates with original row counts; this is a **descriptive transformation**, not a finding of PLC-specific adoption. The source URL reuse audit flags shared documentation but does not automatically collapse distinct events. The `verification_status` field is inherited where present; otherwise it explicitly identifies its original module and does **not** claim external source verification.

## Stage 2 — Conservative mechanism synthesis (provisional)

- `data/mechanism_synthesis_spec.csv`: explicitly curated, auditable synthesis statements with supporting Stage 1 IDs. These are not automatically inferred from record counts.
- `data/mechanism_evidence_synthesis.csv`: generated statements with source-module and URL coverage.
- `data/synthesis_evidence_links.csv`: record-by-record provenance and interpretation limits.
- `scripts/build_mechanism_synthesis.py`: validates all IDs and regenerates Stage 2 outputs.

Run from repository root after Stage 1:

```bash
python research/08_evidence_synthesis/scripts/build_cross_module_matrix.py
python research/08_evidence_synthesis/scripts/build_mechanism_synthesis.py
```

**Interpretation:** The synthesis is descriptive, not a causal test. Some supporting records reuse sources; distinct URL counts are not independent corroboration. Dates of public announcements, regulatory permission, observed shipments, and operational availability must remain distinct. The USGS blended series is broader than PLC. External-signal verification statuses are inherited, not independently reverified here. 


## Stage 4 — Historical and evidence-to-model assessment

- `data/evidence_to_model_assessment.csv`: eight model-facing mechanism assessments, with linked Stage 2 and Stage 1 IDs, limitations and unverified assumptions.
- `data/historical_synthesis_phases.csv`: four documented historical phases and inference boundaries.
- `EVIDENCE_SYNTHESIS.md`: descriptive interpretation, methodological boundaries, and model interpretation.
- `scripts/validate_final_synthesis.py`: checks referential integrity against Stages 1–2.


