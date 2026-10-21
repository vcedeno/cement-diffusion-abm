# PLC Model and Calibration

This directory contains the Python implementation, calibration, and evaluation workflows for the Portland-limestone cement (PLC) diffusion agent-based model.

## `run_plc_simplified.py`

**Purpose:** Monthly agent-based simulation of PLC diffusion across the U.S. cement supply chain (2010–2024).

**Model:** Represents 100 cement manufacturers and 3,667 network-resolved ready-mix concrete (RMX) facilities. RMX adoption depends on demand pressure, state DOT implementation, local peer adoption, and manufacturer material availability. Manufacturer availability can expand endogenously in response to persistent unmet demand, subject to documented plant-specific evidence.

**Inputs:**
- `rmx_month_demand_exposure.csv` — Monthly RMX demand exposure.
- `mfr_rmx_pairs.csv` — Manufacturer–RMX supply relationships.
- `rmx_peer_pairs.csv` — RMX peer relationships.
- `dot_monthly_state.csv` — State DOT implementation.
- `mfr_capacity_for_model.csv` — Manufacturer capacities and operating periods.
- `mfr_plc_evidence_through_2022.csv` — Manufacturer availability evidence.

**Parameters:** `T_A`, `kappa`, `B0`, `theta_M`, `H_M`, `T_M`, and `seed`.

**Outputs:**
- `national_month_adoption.csv` — Monthly national facility and demand-weighted adoption.
- `mfr_transition_summary.csv` — Manufacturer availability transitions.
- `run_specification.csv` — Simulation parameters.

**Calibration:** Used in the 2010–2022 PLC calibration, with evaluation over 2023–2024 (Supporting Information, Section S10).

**Reproducibility:** The verified historical implementation uses plant-dated manufacturer availability boundaries without assigning monthly transitions to year-only evidence. Reproduction of selected calibration trial 406 (seed 42) produced exact matches for all 180 monthly national adoption records, manufacturer transition summaries, and simulation parameters.

## `calibrate_plc_locked_2010_2022.py`

**Purpose:** Calibrates the PLC agent-based model against observed U.S. blended cement shipment shares for January 2010–December 2022, reserving 2023–2024 for evaluation.

**Method:** Optuna Tree-structured Parzen Estimator (TPE) optimization over six parameters (`T_A`, `kappa`, `B0`, `theta_M`, `H_M`, `T_M`). The objective combines adoption-level error (40%), annual-growth error (30%), transition-timing error (20%), and endpoint error (10%).

**Inputs:** Verified `run_plc_simplified.py`, empirical model inputs, manufacturer capacities and availability evidence, and monthly USGS cement shipment data.

**Configuration:** 500 optimization trials; TPE seed 20261009; simulation screening seed 42. Supports resumable optimization and optional five-seed confirmation.

**Outputs:** `best.json`, `trials.csv`, `calibration_manifest.json`, `selected_training_metrics.json`, `best_training_curves.csv`, and calibration plots. Optional confirmation produces `confirmation_metrics.csv`.

**Reference calibration:** Trial 406, selected using the 2010–2022 training objective (Supporting Information, Section S10).

| Parameter | Selected value |
|---|---:|
| `T_A` | 5 |
| `kappa` | 8.439534971412707 |
| `B0` | 1.6223578864493762 |
| `theta_M` | 0.19491661627095874 |
| `H_M` | 10 |
| `T_M` | 29 |

**Reproducibility:** Records SHA-256 hashes of the simulator and input files. Requires the verified historical simulator implementation; the later year-only manufacturer evidence treatment is not part of the reference calibration.

## Historical PLC Evaluation

**Evaluation period:** January 2023–December 2024.

**Manuscript result:** The corrected E01 evaluation reports a held-out RMSE of **0.051927** (Supporting Information, Section S10).

**Configuration:** Uses the selected trial 406 parameters and simulation seed 42.

**Manufacturer evidence:** The corrected E01 evaluation includes 24 documented availability boundaries, compared with 20 in the historical calibration implementation.

**Reproducibility status:** The corrected E01 trajectory has not been reproduced exactly using the currently available simulator. Differences begin in December 2018 and affect 73 monthly observations. The underlying cause has not been established.

**Interpretation:** The verified calibration run and the corrected manuscript evaluation are distinct simulation results. The reported evaluation RMSE of 0.051927 applies to corrected E01, not to the independently reproduced historical calibration trajectory.

## `simple_abm_build_network.py`

**Purpose:** Constructs the empirical U.S. cement and concrete supply-chain network used by the agent-based model.

**Inputs:**
- `manufacturers.csv` — Cement manufacturer locations.
- `readymix_final_for_network.csv` — Ready-mix concrete facility locations.
- `dots.csv` — State transportation agencies.
- `demand_inter.csv` — Geographic demand nodes.

**Network rules:**
- Manufacturer–RMX: Connects manufacturers within 150 miles of each RMX facility. If none are available, uses the nearest manufacturer within 208 miles.
- RMX–demand: Connects demand nodes to the nearest RMX within 15 miles, with a separately identified nearest-facility fallback.
- Geographic coverage: 50 U.S. states.

**Outputs:**
- `nodes.csv` — Network nodes.
- `edges.csv` — Network relationships, including primary and fallback links.

**Reproducibility:** Network radii and fallback rules are specified through command-line arguments. Network construction does not use observed PLC adoption outcomes.

## `build_plc_empirical_state_holdout.py`

**Purpose:** Constructs the empirical, model-ready inputs for PLC diffusion simulations from the U.S. cement supply-chain network and observed data. Supports observed-demand and projected-demand configurations.

**Inputs:**
- `data/simple_abm/us/nodes.csv` — Supply-chain network nodes.
- `data/simple_abm/us/edges.csv` — Supply-chain network relationships.
- `data/usgs_all_state_type_month.csv` — Monthly USGS cement shipments.
- `data/county_pop.csv` — County population data for demand allocation.
- `data/dot_adoption.csv` — State DOT acceptance records.
- `data/mfr_plc_public_evidence_audit_completed.xlsx` — Manufacturer PLC availability evidence.

**Configuration:** January 2010–December 2024; 50 U.S. states; 20-mile RMX peer radius; 24-month DOT implementation period (`T_G=24`); reference demand `D_ref=1124.5848062887808`.

**Outputs:**
- `state_month_demand.csv` — Monthly state-level cement demand.
- `rmx_demand_weights.csv` — RMX demand allocation weights.
- `rmx_month_demand_exposure.csv` — Monthly RMX demand exposure.
- `mfr_rmx_pairs.csv` — Manufacturer–RMX supply relationships.
- `rmx_peer_pairs.csv` — Local RMX peer relationships.
- `dot_monthly_state.csv` — Monthly DOT implementation.
- `mfr_plc_evidence_constraints.csv` — Manufacturer availability evidence constraints.
- Additional network diagnostics and reference specifications.

**Observed-demand inputs:** `data/plc/01_observed_inputs/` contains the reference empirical inputs used in the PLC calibration workflow.

**Projected-demand inputs:** The script supports a demand holdout beginning in January 2023, with a five-year projection horizon. These inputs are generated separately from the observed-demand configuration.

**Reproducibility:** Input construction uses empirical geographic, demand, regulatory, and manufacturer evidence data. The network and behavioral input parameters are explicitly specified. Observed-demand and projected-demand configurations must remain separate to avoid introducing future observed demand into prospective scenarios.

## `plot_plc_temporal_evaluation_corrected.py`

**Purpose:** Generates the manuscript's historical PLC diffusion figure and evaluates simulated adoption against observed U.S. blended cement shipment shares.

**Inputs:**
- `data/usgs_all_state_type_month.csv` — Observed monthly cement shipments.
- `outputs/plc_final_2026/03_calibration_2010_2022/best_training_curves.csv` — Calibration reference observations.
- `outputs/plc_final_2026/18_E01_controlled_corrected/national_month_adoption.csv` — Corrected E01 simulation trajectory.

**Method:** Reconstructs observed national blended cement shares, verifies consistency with the calibration target, and compares observed and simulated adoption over January 2010–December 2024.

**Evaluation:** Calculates RMSE over the 24 held-out months (January 2023–December 2024).

**Outputs:**
- `Fig1_historical_diffusion.png` — Historical diffusion figure.
- `Fig1_historical_diffusion.pdf` — Publication-quality figure.
- `Fig1_historical_diffusion_metrics.csv` — Evaluation metrics.

Outputs are written to `outputs/plc_final_2026/figures_corrected/`.

**Manuscript result:** Corrected E01 evaluation RMSE = 0.051927.

**Reproducibility:** The script reproduces the evaluation calculation from the saved corrected E01 trajectory. Exact reproduction of that trajectory using the currently available simulator has not been established; this limitation is documented in the Historical PLC Evaluation section above.

## PLC Sensitivity and Robustness Analysis

The repository preserves the sensitivity experiments and robustness analyses used to evaluate the PLC diffusion model.

### Experiment outputs

- `07_stochastic_robustness/`: Simulation results across 30 random seeds (42–71).
- `08_mfr_response_ablation/`: Manufacturer-response ablation experiment.
- `09_parameter_sensitivity/`: Parameter perturbation experiments (±20%).
- `10_TA_TM_interaction/`: Joint variation of the RMX adoption response period and manufacturer expansion delay.

These outputs are stored under `outputs/plc_final_2026/`.

The file `plc_sensitivity_manifest.csv` records experiment identifiers, output paths, file sizes, and SHA-256 hashes.

### Corrected robustness analyses

Additional results are preserved under `outputs/plc_final_2026/robustness/`:

- `PLC03_multiseed/`: Stochastic robustness and peer-effect comparisons.
- `PLC04_parameter_sensitivity_corrected/`: Corrected parameter sensitivity results.
- `PLC05_timescale_interaction_corrected/`: Corrected interaction analysis for the RMX adoption response period and manufacturer expansion delay.

### Analysis and plotting scripts

- `package_plc_sensitivity_results.py`: Packages sensitivity experiment outputs and provenance information.
- `run_plc_behavioral_coefficient_sensitivity.py`: Runs behavioral coefficient sensitivity experiments.
- `plots/plot_plc_sensitivity_envelopes.py`: Generates sensitivity envelopes.
- `plots/plot_plc_structural_sensitivity.py`: Generates structural sensitivity visualizations.
- `plots/plot_plc03_stochastic_robustness.py`: Visualizes PLC03 stochastic robustness results.
- `plots/plot_plc04_plc05_sensitivity_corrected.py`: Visualizes corrected PLC04 and PLC05 sensitivity results.

### Reproducibility

Saved experiment outputs support retrospective analysis without rerunning the simulations. The original experiment results and corrected robustness analyses are retained separately to preserve their provenance.

The scripts and saved outputs have been transferred; their execution dependencies and portability within the public repository have not yet been fully verified.
