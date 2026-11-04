# Cement Diffusion ABM

Agent-based simulations of lower-carbon cement diffusion in the United States: historical Portland-limestone cement (PLC, 2010–2024) and prospective limestone calcined clay cement (LC3, 2026–2045).

## Setup

From the repository root, with Python 3.10+:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## PLC: frozen v1 calibration

The selected PLC calibration is **trial 194**, fitted to January 2010–December 2022 observations (seed 42). January 2023–December 2024 was held out. The training RMSE is **0.0171993**; this is not a held-out RMSE. The empirical target is U.S. blended cement shipment share, not a PLC-only series.

Run the selected simulation:

```bash
python3 model/run_plc_simplified.py \
  --empirical_dir data/plc/01_observed_inputs \
  --capacity_file data/mfr_capacity_for_model.csv \
  --evidence_file data/plc/evidence/mfr_plc_evidence_through_2022.csv \
  --out_dir outputs/examples/plc_frozen_v1 \
  --seed 42 \
  --T_A 7 \
  --kappa 12.105007212733277 \
  --B0 1.4585673452933934 \
  --theta_M 0.18142903019803333 \
  --H_M 10 \
  --T_M 30
```

Selected archived results are in `outputs/plc/`: `best.json`, `best_training_curves.csv`, `national_month_adoption.csv`, `selected_training_metrics.json`, and `calibrated_curves.png`. The simulator and retained PLC inputs were verified against the frozen archive using SHA-256 checksums.

## LC3: four prospective scenarios

The final scenarios use ten matched seeds (42–51), January 2026–December 2045, and the **archived LC3 parameters** (`T_A=5`, `kappa=8.439534971412707`, `B0=1.6223578864493762`, `theta_M=0.19491661627095874`, `H_M=10`, `T_M=29`). These differ from the frozen PLC calibration.

| Scenario | DOT implementation | December 2045 median adoption* | Manufacturer availability |
|---|---|---:|---:|
| `N0` | None | 1.1% | 10 |
| `N14` | 14 states | 51.1% | 14 |
| `NSTAG` | 47 states, staggered | 68.3% | 20 |
| `N47` | 47 states in 2029 | 71.4% | 20 |

*National demand-weighted adoption, trailing 12 months. These are conditional simulations, **not forecasts**.

Archived multiseed summaries and seed-level results are in `outputs/lc3/<SCENARIO>/` as `lc3_05c_multiseed_summary.csv` and `lc3_05c_seed_level_results.csv`.

### Run an LC3 scenario

The runner requires five CSV files in one input directory: four shared inputs under `data/lc3/shared/` and the scenario-specific `dot_monthly_state.csv`.

All four LC3 scenarios use the same demand-exposure input, included in the repository at `data/lc3/shared/rmx_month_demand_exposure.csv`.

Run from the repository root:

```bash
SCENARIO=N47  # N0, N14, NSTAG, or N47
INPUT_DIR="outputs/examples/lc3_inputs_${SCENARIO}"

mkdir -p "$INPUT_DIR"
cp data/lc3/shared/*.csv "$INPUT_DIR/"
cp "data/lc3/${SCENARIO}/dot_monthly_state.csv" "$INPUT_DIR/"

python3 model/run_lc3_05c_multiseed.py \
  --input_dir "$INPUT_DIR" \
  --capacity_file data/mfr_capacity_for_model.csv \
  --output_root "outputs/examples/lc3_${SCENARIO}"
```

The LC3 runner uses the archived scenario configuration, including protection of prescribed manufacturer events and exclusion of manufacturers 20, 21, and 65 from endogenous activation. Manufacturer capacity is held fixed; endogenous response changes material availability.

## Documentation

- [`model/README.md`](model/README.md): Model scripts and simulation details.
- [`data/README.md`](data/README.md): Input data and provenance.
