# Model Reproduction

Run all commands from the repository root after installing `requirements.txt`.

## PLC — Frozen v1 calibration

The selected historical PLC calibration is **trial 194** (seed 42), fitted to 2010–2022 observations. The 2023–2024 period was reserved for evaluation. Training RMSE: **0.0171993**.

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

Compare `outputs/examples/plc_frozen_v1/national_month_adoption.csv` with the archived `outputs/plc/national_month_adoption.csv`. Selected calibration parameters, curves, and metrics are in `outputs/plc/`. The simulator and retained inputs match the frozen v1 archive by SHA-256; a fresh-environment numerical match has not yet been confirmed.

## LC3 — Four scenarios, ten seeds each

The archived LC3 simulations cover 2026–2045, using seeds **42–51**. The scenarios differ in DOT implementation: `N0` (none), `N14` (14 states), `NSTAG` (staggered 47 states), and `N47` (47 states in 2029).

The multiseed runner uses `T_A=5`, `kappa=8.439534971412707`, `B0=1.6223578864493762`, `theta_M=0.19491661627095874`, `H_M=10`, `T_M=29`, scenario-event protection, and endogenous-manufacturer exclusions `20 21 65`. **These are not the frozen v1 PLC parameters.**

Each scenario requires a 2026–2045 `rmx_month_demand_exposure.csv` (approximately 83 MB), which is **not included** in Git. The file must be obtained from the original experiment inputs; its independent generation procedure is not yet documented. Without it, the simulations cannot be rerun from the repository alone.

After obtaining that file, set `DEMAND` to its absolute path and run:

```bash
DEMAND=/absolute/path/to/rmx_month_demand_exposure.csv

for s in N0 N14 NSTAG N47; do
  INPUT="outputs/examples/lc3_inputs_${s}"
  mkdir -p "$INPUT"
  cp data/lc3/shared/*.csv "$INPUT/"
  cp "data/lc3/$s/dot_monthly_state.csv" "$INPUT/"
  cp "$DEMAND" "$INPUT/rmx_month_demand_exposure.csv"

  python3 model/run_lc3_05c_multiseed.py \
    --input_dir "$INPUT" \
    --capacity_file data/mfr_capacity_for_model.csv \
    --output_root "outputs/examples/lc3_${s}"
done
```

The already-computed results are available without rerunning simulations:

- `outputs/lc3/<scenario>/lc3_05c_multiseed_summary.csv`
- `outputs/lc3/<scenario>/lc3_05c_seed_level_results.csv`

The LC3 scenarios are conditional simulations, not forecasts.
