# PLC adoption model: code, data and documents

An agent-based model of the US transition from ordinary portland cement to portland-limestone cement (PLC, ASTM C595 Type IL), 2010-2025, built from documented evidence on firms, plants, state DOTs, buyers and imports, and designed for transfer to LC3.

## Contents

| Folder | Content |
|---|---|
| `docs/preliminary_results.md` | Conceptual model, agents and decisions, DOT and firm records, calibration and validation, mechanisms and sensitivity, intervention ideas, LC3 adaptation |
| `docs/model_document.md` | Every equation, variable, parameter and assumption, with evidence links and code locations |
| `docs/evidence_ledger.md` | All evidence used, with full references |
| `docs/figures/` | Figures 1-4 |
| `original_data/` | Input files from the cement-diffusion-abm repository (snapshot 87809f8), unchanged. `rmx_month_demand_exposure.csv.gz` is the original csv compressed with gzip (lossless) |
| `new_data/` | Input files compiled for this model: evidence tables, plant and firm attributes, import volumes, ready-mix ownership, USGS 2025 transcription |
| `new_data/derived/` | Model-ready tables built by `code/build_inputs.py` from the two data folders |
| `code/` | Model code (see the code map in `docs/model_document.md`, section 11) |
| `results/` | Outputs of the reported run: firm-hazard estimates, calibration trials, validation summary and curves, mechanism and sensitivity tables |

### `original_data/` (cement-diffusion-abm repository)

| File | Used for |
|---|---|
| `mfr_capacity_for_model.csv` | Cement plants: capacity, operating period, type |
| `mfr_rmx_pairs.csv` | Supply network: cement plant to ready-mix plant links |
| `rmx_month_demand_exposure.csv.gz` | Monthly ready-mix demand, 2010-2024 |
| `usgs_all_state_type_month.csv` | USGS shipments by state, type and month, 2002-2024 |
| `dots.csv` | State names and codes |
| `readymix_final_for_network.csv` | Ready-mix facility list (basis of the ownership assignment) |

### `new_data/`

| File | Content |
|---|---|
| `evidence/plant_plc_evidence.csv` | Plant-level PLC evidence: first documented date, document type, confidence, note, source; full-conversion notes; later evidence (2026) |
| `evidence/dot_acceptance_evidence.csv` | State DOT acceptance window (not before, accepted by), status, evidence, source |
| `plant_conversion_evidence.csv` | Conversion period by firm and Type II/V product line by plant, with sources |
| `firm_attributes.csv` | GCCA membership; whether the record start is a dated start or a document date |
| `imports_by_customs_district.csv` | Imports of hydraulic cement and clinker by customs district (2022, 2023), destination states, origin |
| `readymix_owner_assignment.csv` | Cement firm owning each ready-mix plant (facility-name match to subsidiary brands) |
| `usgs_2025/` | 2025 monthly shipments by destination (portland, blended), transcribed from USGS MIS December 2025, with source and checks |

## Running

Python 3.11 or later with numpy (2.x), pandas (2.x or 3.x), scipy, optuna, matplotlib. Run from `code/`:

```bash
cd code
python build_inputs.py                          # new_data/derived from original_data and new_data   (seconds)
python firm_hazard.py                           # firm-month panel and start-hazard estimates        (seconds)
python calibrate.py 1500                        # market-layer calibration, 2010-22 (replay)         (about 25 minutes)
python validate.py                              # predictive runs, 2010-25 metrics and curves         (about 15 seconds)
PLC_END=2035-12 python scenarios.py mechanisms  # mechanism tests to 2035                             (minutes)
PLC_END=2035-12 python scenarios.py sensitivity # one-at-a-time sensitivity
python figures.py                               # docs/figures
```

`results/` already contains the reported outputs, so `validate.py`, `scenarios.py` and `figures.py` can be run without repeating the calibration. Running `calibrate.py` overwrites `results/calibration_trials.csv`; with 1,500 trials it reproduces the stored file. Set `PLC_PROCS` to the number of processes for `scenarios.py` (default 2). The example sets `interventions` and `lc3` in `scenarios.py` show how the ideas in `docs/preliminary_results.md` (sections 6 and 7) are implemented; their results are not reported.

## Key results

| Metric | Model | Record |
|---|---|---|
| National share RMSE, calibration 2010-22 | 0.018 | |
| National share RMSE, validation 2023-25 | 0.034 | |
| National PLC share 2025 | 0.60 | 0.62 |
| Parent firms started by Dec 2025 | 20 | 18 |
| Firm start timing error (median) | 3 months | |
