# U.S. Cement Market Demand

## Data

`data/usgs_all_state_type_month.csv`

Monthly USGS cement shipment data by state and cement type.

## Analysis

The analysis examines Portland and blended cement shipments
during 2010–2024.

Blended cement is not equivalent to PLC.

USGS data show a substantial increase in blended-cement shipments between 2021 and 2024. Although PLC likely contributed to this growth, the data do not distinguish PLC from other blended cements or identify the factors driving the transition.

## Figures

- `figures/usgs_national_shipments.pdf`
- `figures/usgs_state_shipments.pdf`

PNG versions are also generated.

## Reproduce

From the repository root:

```bash
python research/02_market_demand/scripts/plot_usgs_shipments.py
