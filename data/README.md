# Model Data

This directory contains the source datasets and generated network files used to construct the U.S. cement and concrete supply-chain agent-based model.

## Source Datasets

### `manufacturers.csv`
Cement manufacturer locations used to construct manufacturer–RMX supply relationships.

### `readymix_final_for_network.csv`
Georeferenced ready-mix concrete facilities used to construct the supply-chain network (3,761 facilities).

### `dots.csv`
State departments of transportation represented in the model.

### `demand_inter.csv`
Geographic demand nodes used to construct RMX–demand relationships.

## Generated Network

The following files were generated using `model/simple_abm_build_network.py`.

### `simple_abm/us/nodes.csv`
Network nodes representing cement manufacturers, ready-mix concrete facilities, state DOTs, and geographic demand locations.

### `simple_abm/us/edges.csv`
Network relationships constructed using geographic distance rules.

The network construction uses:

- **Manufacturer–RMX:** 150-mile primary radius, with a bounded nearest-manufacturer fallback of 208 miles.
- **RMX–demand:** 15-mile primary radius, with a nearest-facility fallback.
- **Geographic scope:** 50 U.S. states.

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


## PLC Observed-Demand Model Inputs

**Directory:** `data/plc/01_observed_inputs/`

These files provide the empirical inputs for the PLC diffusion model over January 2010–December 2024. They were generated from the supply-chain network, USGS cement shipment data, county population, DOT acceptance records, and manufacturer availability evidence.

**Demand allocation:**
- `state_month_demand.csv` — Monthly state-level cement demand.
- `rmx_demand_weights.csv` — Facility-level demand allocation weights.
- `rmx_month_demand_exposure.csv` — Monthly demand exposure allocated to each RMX facility.

**Supply and peer networks:**
- `mfr_rmx_pairs.csv` — Potential manufacturer–RMX supply relationships.
- `rmx_peer_pairs.csv` — Local RMX peer relationships.
- `rmx_peer_pairs_undirected.csv` — Undirected representation of RMX peer relationships.

**Regulatory and manufacturer evidence:**
- `dot_first_acceptance.csv` — First recorded PLC acceptance by state DOT.
- `dot_monthly_state.csv` — Monthly DOT implementation states.
- `mfr_plc_evidence_constraints.csv` — Manufacturer PLC availability evidence constraints.

**Diagnostics and configuration:**
- `rmx_peer_diagnostics.csv` — Local peer-network diagnostics.
- `rmx_supply_network_diagnostics.csv` — Manufacturer–RMX network diagnostics.
- `reference_specification.csv` — Input-generation configuration.

**Reproducibility:** These files preserve the observed-demand model inputs used in the PLC calibration workflow. They are distinct from the projected-demand inputs used in prospective evaluation scenarios.

## Empirical Source Data for PLC Input Construction

The following datasets support the construction of the PLC model-ready inputs using `model/build_plc_empirical_state_holdout.py`.

### `usgs_all_state_type_month.csv`
Monthly state-level U.S. cement shipment data, including Portland and blended cement categories. Used to construct observed demand and reference adoption trajectories.

### `county_pop.csv`
County population data used to allocate state-level cement demand geographically.

### `dot_adoption.csv`
State DOT acceptance records used to construct monthly regulatory implementation states.

### `mfr_plc_public_evidence_audit_completed.xlsx`
Plant-level public evidence of PLC availability, including documented dates, evidence classifications, source references, and methodological definitions.

The workbook contains three worksheets:
- `Plant Evidence Audit` — Manufacturer-specific evidence records.
- `Coverage Summary` — Summary of evidence coverage.
- `Method & Definitions` — Evidence classification definitions.

The evidence workbook supports the construction of `mfr_plc_evidence_constraints.csv`.

**Reproducibility:** These empirical source datasets are provided alongside the derived PLC model inputs in `data/plc/01_observed_inputs/`. Manufacturer evidence should be interpreted according to its documented date and evidence classification rather than assuming that all records establish an exact availability month.

## PLC Calibration Inputs

The following files are required by `model/calibrate_plc_locked_2010_2022.py`, in addition to the observed-demand inputs documented above.

### `mfr_capacity_for_model.csv`
Manufacturer capacity and operating-period information derived from the manufacturer dataset. Used to normalize manufacturer demand-response signals.

### `plc/evidence/mfr_plc_evidence_through_2022.csv`
Historical manufacturer PLC availability evidence used in the selected calibration. Evidence is restricted to information available through 2022.

**Calibration provenance:** The selected calibration (trial 406) uses the observed-demand inputs in `data/plc/01_observed_inputs/`, manufacturer capacities, historical evidence, and USGS shipment data.

The calibration manifest records SHA-256 hashes of these inputs. The verified historical simulator preserves the evidence treatment used during calibration.
