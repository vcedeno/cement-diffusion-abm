# PLC Manufacturer Evidence

## Purpose
This research module summarizes publicly available evidence about Portland-limestone cement (PLC) at 100 represented U.S. cement plants. The objective is to establish an empirical foundation for future agent-based modeling of endogenous manufacturer behavior.

## Data
`data/mfr_plc_public_evidence_audit_completed.xlsx`
The workbook contains plant identifiers, locations, evidence descriptions, dates, source references, and interpretations. The original evidence records are preserved.

## Analysis
The script groups records into three evidence-coverage categories:
- Plant-specific evidence
- Broader company evidence
- No plant-specific evidence found

These categories describe the scope of the public evidence. They do not establish actual first-production dates or historical nonavailability.

## Reproduce figures
From the repository root:
```bash
python research/01_manufacturer_availability/scripts/plot_plc_evidence.py
```
