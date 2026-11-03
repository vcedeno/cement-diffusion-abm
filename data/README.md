# Model Data

This directory contains the source datasets and generated network files used to construct the U.S. cement and concrete supply-chain agent-based model.

## Source Datasets

### `manufacturers.csv`
Dataset of 100 U.S. cement manufacturing plants, including geographic coordinates, plant identifiers, production capacity, ownership, operating status, and production characteristics.

Used to construct manufacturer–RMX supply relationships and as a source for manufacturer capacity inputs.

### `readymix_final_for_network.csv`
Dataset of 3,761 georeferenced ready-mix concrete (RMX) facilities, including facility identifiers, geographic coordinates, addresses, state and county information, and source metadata.

Used to construct manufacturer–RMX and RMX–demand relationships in the supply-chain network.

All facilities have geographic coordinates; 50 records lack county FIPS codes.

### `dots.csv`
Dataset of 50 U.S. state departments of transportation (DOTs), including state identifiers, names, and DOT abbreviations.

Used to represent state-level regulatory agents in the supply-chain network.

### `demand_inter.csv`
Dataset of 3,142 county-level geographic demand nodes, including county identifiers, state codes, and geographic coordinates.

Used to construct RMX–demand relationships in the supply-chain network.

Population and area attributes are incomplete; population data used for demand allocation are provided separately in `county_pop.csv`.

## Generated Network

The following files were generated using `model/simple_abm_build_network.py`.

### `simple_abm/us/nodes.csv`
Generated supply-chain network containing 7,051 nodes: 100 cement manufacturers (MFR), 3,761 ready-mix concrete facilities (RMX), 3,140 geographic demand nodes (DIM), and 50 state departments of transportation (DOT).

Each node includes its type, state, source identifier, and available geographic information. Manufacturer capacity is recorded in tonnes per month where available (90 of 100 manufacturers).

### `simple_abm/us/edges.csv`
Generated network containing 40,023 directed relationships among cement manufacturers (MFR), ready-mix concrete facilities (RMX), county demand nodes (DIM), and state departments of transportation (DOT).

The file records source and destination node identifiers, relationship types, and geographic distances where applicable.

Manufacturer–RMX relationships use a 150-mile primary radius and a nearest-manufacturer fallback bounded at 208 miles.

RMX–DIM relationships use a 15-mile primary radius and a nearest-facility fallback without an equivalent distance bound.

DOT–DIM and RMX–DOT relationships represent state-level regulatory connections and do not include distance values.

## Reproducing the Network

From the repository root, run:

```bash
python3 model/simple_abm_build_network.py \
  --manufacturers_csv data/manufacturers.csv \
  --readymix_csv data/readymix_final_for_network.csv \
  --dots_csv data/dots.csv \
  --demand_inter_csv data/demand_inter.csv \
  --states "AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY" \
  --outdir data/simple_abm/us \
  --rmx_dim_radius 15 \
  --rmx_dim_k 1 \
  --mfr_rmx_radius 150 \
  --mfr_rmx_fallback_radius 208
```

## PLC Observed-Demand Model Inputs

**Directory:** `data/plc/01_observed_inputs/`

These files provide the empirical inputs for the PLC diffusion model over January 2010–December 2024. They were generated from the supply-chain network, USGS cement shipment data, county population, DOT acceptance records, and manufacturer availability evidence.

**Demand allocation:**
- `state_month_demand.csv` — Monthly state-level cement demand (`D_s`) for 50 U.S. states from January 2010 through December 2024 (9,000 state-month records).
- `rmx_demand_weights.csv` — Facility-level demand allocation measures (`L_i`) and normalized weights (`omega_i`) for 3,667 RMX facilities across 47 states. Within each represented state, the allocation weights sum to one.
- `rmx_month_demand_exposure.csv` — Monthly demand exposure for 3,667 RMX facilities over January 2010–December 2024 (660,060 facility-month records). Includes state demand (`D_s`), allocation weights (`omega_i`), allocated facility demand (`D_i`), and normalized demand pressure (`d_i`).

**Supply and peer networks:**
- `mfr_rmx_pairs.csv` — Manufacturer–RMX supply relationships (13,421 pairs), using a 150-mile primary radius and a bounded nearest-manufacturer fallback of 208 miles. Used by the PLC and LC3 simulations.
- `rmx_peer_pairs.csv` — Directed RMX peer relationships (32,178 records) connecting facilities within 20 miles. Used to calculate local peer exposure in the PLC and LC3 simulations.

**Regulatory and manufacturer evidence:**
- `dot_first_acceptance.csv` — First recorded PLC acceptance date (`t_accept`) for each of the 50 state DOTs.
- `dot_monthly_state.csv` — Monthly state-level regulatory variables (`t_accept`, `g_s`, and `phi_s`) used in the PLC diffusion model (9,000 state-month records).
- `mfr_plc_evidence_constraints.csv` — Plant-level PLC availability evidence for 100 cement manufacturers, including evidence classifications, supported dates, source references, assumptions, and limitations. Documented dates do not necessarily establish the exact month when PLC production began.

**Reproducibility:** These files preserve the observed-demand model inputs used in the PLC calibration workflow. They are distinct from the projected-demand inputs used in prospective evaluation scenarios.

## Empirical Source Data for PLC Input Construction

The following datasets are required to reproduce the PLC model-ready inputs using `model/build_plc_empirical_state_holdout.py`.

### `usgs_all_state_type_month.csv`
Monthly state-level U.S. cement shipment data, including Portland and blended cement categories. Used to construct observed demand and reference adoption trajectories.

The USGS blended-cement category is broader than PLC and should not be interpreted as a direct measurement of PLC adoption.

### `county_pop.csv`
County population data used to allocate state-level cement demand geographically.

### `dot_adoption.csv`
State DOT cement acceptance records used to construct monthly regulatory implementation variables.

### `mfr_plc_public_evidence_audit_completed.xlsx`
Plant-level public evidence of PLC availability for 100 cement manufacturers.

The workbook contains three worksheets:
- `Plant Evidence Audit` — Manufacturer-specific evidence records.
- `Coverage Summary` — Summary of evidence coverage.
- `Method & Definitions` — Evidence classification definitions.

The input-construction script reads the `Plant Evidence Audit` worksheet to generate `mfr_plc_evidence_constraints.csv`.

Documented availability dates should be interpreted according to their evidence classification and limitations rather than as exact dates of first PLC production.

## PLC Calibration Inputs

The following files are required by `model/calibrate_plc_locked_2010_2022.py`, in addition to the observed-demand inputs documented above.

### `mfr_capacity_for_model.csv`

Manufacturer capacity and operating-period information for 100 cement facilities, based primarily on the July 2026 Global Cement and Concrete Tracker.

The model uses manufacturer capacity to normalize demand-response signals. One manufacturer has an unresolved numeric capacity.

### `plc/evidence/mfr_plc_evidence_through_2022.csv`

Manufacturer PLC availability evidence used in the selected historical PLC calibration.

The file preserves plant-level evidence classifications, supported dates, and availability constraints. Some records contain later latest-known availability bounds rather than confirmed historical adoption dates.

**Calibration provenance:** The selected PLC calibration (trial 406) uses the observed-demand inputs in `data/plc/01_observed_inputs/`, manufacturer capacity information, historical manufacturer availability evidence, and USGS shipment data.

The calibration manifest records the input files and their SHA-256 hashes. The historical manufacturer evidence file provided in this repository has been verified as byte-for-byte identical to the corresponding archived calibration input.
