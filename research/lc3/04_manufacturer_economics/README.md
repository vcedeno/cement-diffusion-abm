# Module 04 — LC3 Manufacturer Economics (corrected figures)

## Contents
- `data/lc3_manufacturer_economic_evidence.csv`: original evidence table with RMI Plant 1–7 region, fuel, mix, and CAPEX assumptions added to each relevant record, from RMI Exhibits 7–8.
- `data/lc3_clay_sourcing_scenarios.csv`: four **2019 modeled greenfield** cases (flash vs rotary; clay 10 vs 200 km), with raw-clay cost, LC3 production cost, CAPEX, IRR, payback, and primary source.
- `data/lc3_us_project_finance_evidence.csv`: original U.S. project financing evidence; **not** the source of either chart.
- `scripts/plot_manufacturer_economics.py`: generates both figures directly from CSVs.

## Sources and limitations
- RMI (2024), *The Business Case for LC3*, Exhibits 7–8: https://rmi.org/wp-content/uploads/dlm_uploads/2024/12/the_business_case_for_LC3_report.pdf . Plant 7 is the **North American modeled case** ($44/t), not an observed U.S. cement plant. Exhibit 7's CAPEX pertains to the modeled LC3 scenario; Exhibit 8 is the calcined-clay production cost.
- LC3 Project/EPFL (2019), *Financial Attractiveness of LC3*, Table 1 and §7.5: https://lc3.ch/wp-content/uploads/2020/10/2019-LC3FinancialAttractiveness-WEB.pdf . The 10 and 200 km sourcing cases are assumptions, not observations; do not transfer their payback periods directly to U.S. manufacturers.

## Reproduce
From repository root:

```bash
python -m pip install matplotlib
python research/lc3/04_manufacturer_economics/scripts/plot_manufacturer_economics.py
```

## Interpretation
- **RMI:** modeled calcined-clay costs are $21–25/t for six modeled plants; North American Plant 7 is $44/t, which RMI links to raw-clay prices.
- **Clay sourcing:** in the 2019 modeled greenfield case, increasing clay distance from 10 to 200 km raises assumed raw-clay cost ($4 to $17/t clay), LC3 cement cost, and payback (4.4 to 6 years) under either calcination technology.
- Both plots are **published modeled examples**, not plant-specific U.S. observations and not inputs for recalibrating the PLC ABM.
