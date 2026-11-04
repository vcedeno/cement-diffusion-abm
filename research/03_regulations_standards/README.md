# PLC DOT Acceptance and Market Transition

## Data

- `dot_first_acceptance.csv`: Reconstructed state-DOT PLC acceptance dates.
- `usgs_all_state_type_month.csv`: USGS cement shipments by state, month, and cement type.

DOT dates were reconstructed from Innis (2018), subsequent announcements, and Tennis et al. (2024). January dates may represent modeling conventions rather than verified acceptance months.

## Analysis

Compares the timing of state-DOT PLC acceptance with the growth of blended-cement shipments during 2010–2024.

All 50 state DOTs accepted PLC by February 2024.

Blended cement is a broader category than PLC. The analysis describes temporal relationships, not causation.

## Reproduce

From the repository root:

python research/03_regulations_standards/scripts/plot_dot_vs_shipments.py

## Outputs

- National comparison (PDF/PNG)
- State-level comparison (PDF/PNG)
- State timing comparison (CSV)
