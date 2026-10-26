# Cement Diffusion ABM

##Description:
An empirically grounded agent-based model (ABM) for studying the diffusion of lower-carbon cement technologies across the U.S. cement and concrete supply chain, including calibration, sensitivity analysis, and prospective LC3 scenarios.

##Topics: 
agent-based-modeling, decarbonization, python, simulation, cement, technology-diffusion, climate-tech

The repository supports two applications:

1. **Portland-limestone cement (PLC):** Historical diffusion analysis, calibration, evaluation, and sensitivity experiments for 2010–2024.
2. **Limestone calcined clay cement (LC3):** Prospective diffusion scenarios for 2026–2045, examining manufacturer availability, regulatory acceptance, demand exposure, and local peer effects.

The model represents cement manufacturers, ready-mix concrete facilities (RMX), state departments of transportation (DOTs), and geographically distributed demand.

## Repository structure

```text
cement-diffusion-abm/
├── README.md
├── requirements.txt
├── data/
│   ├── README.md
│   ├── plc/
│   │   ├── 01_observed_inputs/
│   │   └── evidence/
│   ├── simple_abm/
│   │   └── us/
│   └── *.csv
├── model/
│   ├── README.md
│   ├── run_plc_simplified.py
│   ├── run_lc3_announced_projects_05c.py
│   ├── run_lc3_05c_multiseed.py
│   ├── calibrate_plc_locked_2010_2022.py
│   ├── build_plc_empirical_state_holdout.py
│   ├── simple_abm_build_network.py
│   └── plots/
└── outputs/
    ├── plc_final_2026/
    └── lc3_reference_2026_2045/
```

### `data/`

Contains empirical datasets, network inputs, manufacturer capacities, regulatory evidence, and prepared model inputs.

- `data/simple_abm/us/`: Supply-chain network nodes and edges.
- `data/plc/01_observed_inputs/`: Prepared PLC empirical inputs, including monthly RMX demand exposure, supply relationships, peer networks, and DOT acceptance.
- `data/plc/evidence/`: Historical manufacturer PLC availability evidence.
- `data/mfr_capacity_for_model.csv`: Manufacturer capacity information.

See `data/README.md` for individual dataset descriptions.

### `model/`

Contains the agent-based simulation, input preparation, calibration, sensitivity analysis, and plotting scripts.

- `run_plc_simplified.py`: Historical PLC diffusion simulator.
- `run_lc3_announced_projects_05c.py`: Prospective LC3 simulator with scenario-event protection.
- `run_lc3_05c_multiseed.py`: LC3 stochastic robustness experiments.
- `calibrate_plc_locked_2010_2022.py`: PLC parameter calibration.
- `build_plc_empirical_state_holdout.py`: Preparation of PLC empirical inputs.
- `simple_abm_build_network.py`: Construction of supply-chain relationships.
- `plots/`: Visualization scripts for diffusion, sensitivity, and robustness.

See `model/README.md` for additional details.

### `outputs/plc_final_2026/`

Contains the selected PLC calibration, corrected historical evaluation, and sensitivity experiments.

The saved corrected evaluation and the historically reconstructed calibration simulator are retained separately because exact reproduction of the corrected evaluation trajectory from the currently available simulator has not been established.

### `outputs/lc3_reference_2026_2045/`

Contains prepared LC3 scenario inputs, reference simulation outputs, and multiseed results.

The LC3 05C outputs include national and state adoption trajectories and manufacturer-level results. Large RMX-level monthly simulation outputs are excluded from the public repository.

## Installation

Python 3.10 or newer is recommended.

Clone the repository and enter its root directory:

```bash
git clone <repository-url>
cd cement-diffusion-abm

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

All commands below should be executed from the repository root.

## Example 1: Historical PLC diffusion

Run the historical PLC model for January 2010–December 2024 using the selected calibration parameters.

```bash
python3 model/run_plc_simplified.py \
  --empirical_dir data/plc/01_observed_inputs \
  --capacity_file data/mfr_capacity_for_model.csv \
  --evidence_file data/plc/evidence/mfr_plc_evidence_through_2022.csv \
  --out_dir outputs/examples/plc_reference \
  --seed 42 \
  --T_A 5 \
  --kappa 8.439534971412707 \
  --B0 1.6223578864493762 \
  --theta_M 0.19491661627095874 \
  --H_M 10 \
  --T_M 29
```

This example uses the selected parameters from the PLC calibration conducted with observations through December 2022.

The simulator writes national and state adoption trajectories, manufacturer transitions, and run specifications to:

```text
outputs/examples/plc_reference/
```

The historical simulator reproduces the archived selected calibration trajectory. The corrected E01 manuscript evaluation is preserved separately under `outputs/plc_final_2026/18_E01_controlled_corrected/`.

## Example 2: Prospective LC3 diffusion

Run the LC3 05C reference scenario for January 2026–December 2045.

This scenario includes dated manufacturer deployment events, endogenous manufacturer response, local peer effects, and protection of scenario-event manufacturers from premature endogenous activation.

```bash
python3 model/run_lc3_announced_projects_05c.py \
  --empirical_dir outputs/lc3_reference_2026_2045/inputs_lc3_05 \
  --capacity_file data/mfr_capacity_for_model.csv \
  --evidence_file outputs/lc3_reference_2026_2045/inputs_lc3_05/lc3_05_coordinated_deployment_events.csv \
  --out_dir outputs/examples/lc3_reference \
  --seed 42 \
  --protect_scenario_events \
  --exclude_endogenous_mfr 20 21 65 \
  --T_A 5 \
  --kappa 8.439534971412707 \
  --B0 1.6223578864493762 \
  --theta_M 0.19491661627095874 \
  --H_M 10 \
  --T_M 29
```

The scenario uses the selected PLC behavioral and manufacturer-response parameters without recalibrating them to LC3 outcomes.

The simulation writes its results to:

```text
outputs/examples/lc3_reference/
```

The archived LC3 05C reference and multiseed results are available under `outputs/lc3_reference_2026_2045/`.

## Reproducibility notes

- PLC is the historical calibration and evaluation case.
- LC3 is a prospective scenario application, not an empirical validation against observed LC3 diffusion.
- The selected PLC calibration uses 2010–2022 observations; 2023–2024 is the evaluation period.
- The corrected PLC E01 evaluation RMSE is 0.051927 for January 2023–December 2024.
- Exact reproduction of the corrected E01 trajectory from the available historical simulator has not been established.
- The archived sensitivity experiments and LC3 multiseed outputs can be analyzed without rerunning their simulations.
- Some large agent-level outputs are intentionally excluded to keep the repository manageable.
- Scenario inputs and model assumptions should not be interpreted as independently verified forecasts.

## Additional documentation

- `data/README.md`: Dataset descriptions and provenance.
- `model/README.md`: Model scripts, calibration, and sensitivity analyses.
