# Cement Diffusion: An Agent-Based Study

Reproducible code and data for a geographically explicit, manufacturer-led
agent-based model of Portland-limestone cement (PLC) diffusion in the
United States (2010–2024), followed by conditional limestone calcined
clay cement (LC3) deployment scenarios (2025–2035).

## Setup

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt
```

Run all commands from the `cement_diffusion_study` directory.

## Repository structure

- `model/cement_diffusion_model.py`: PLC agent-based simulator.
- `model/experiments/`: PLC mechanism experiments and LC3 scenarios.
- `model/plots/`: historical evaluation and mechanism figures.
- `data/plc/01_observed_inputs/`: processed DOT, manufacturer, RMX,
  supply-network, peer-network, demand, and PLC evidence inputs.
- `data/mfr_capacity_for_model.csv`: manufacturer capacity inputs.
- `data/usgs_all_state_type_month.csv`: USGS cement shipment observations.
- `data/lc3/lc3_projects_audited_conditional.csv`: conditional LC3 project inputs.
- `figures/`: three reproduced manuscript figures.

The PLC evidence correction log and public evidence audit are included
with the processed inputs for traceability.

## Reproduction

### 1. PLC historical simulation

```bash
python model/cement_diffusion_model.py \
  --empirical-dir data/plc/01_observed_inputs \
  --capacity-file data/mfr_capacity_for_model.csv \
  --evidence-file data/plc/01_observed_inputs/mfr_plc_evidence_constraints_prospective_corrected.csv \
  --observed data/usgs_all_state_type_month.csv \
  --rmx-peer-file data/plc/01_observed_inputs/rmx_peer_pairs.csv \
  --mfr-peer-file data/plc/01_observed_inputs/mfr_peer_pairs.csv \
  --start 2010-01 --end 2024-12 --seed 42 \
  --availability unresolved_possible \
  --integrated-behavior \
  --endogenous-network-capability \
  --future-exogs provided_scenario \
  --production-policy opc_first \
  --announced-conversion-strategy \
  --corporate-rollout-scenario \
  --mfr-alpha0 -7.3300033902879465 \
  --mfr-alpha-market 1.63628618303928 \
  --mfr-alpha-peer 0.22808233636341518 \
  --rmx-beta0 -3.2474584986091823 \
  --rmx-beta-dot 0.21484194767766054 \
  --rmx-beta-peer 0.9471521955379223 \
  --out outputs/PLC_baseline
```

### 2. PLC mechanism experiments

Runs 18 configurations with five random seeds each (90 simulations).
Existing completed runs are skipped.

```bash
python model/experiments/run_plc_mechanism_experiments.py \
  --out outputs/PLC_mechanism_experiments \
  --seeds 42 43 44 45 46 \
  --skip-existing
```

### 3. Figure 1: Historical PLC evaluation

```bash
python model/plots/plot_plc_historical_evaluation.py \
  --run outputs/PLC_mechanism_experiments/baseline/seed_42 \
  --seed-runs \
    outputs/PLC_mechanism_experiments/baseline/seed_42 \
    outputs/PLC_mechanism_experiments/baseline/seed_43 \
    outputs/PLC_mechanism_experiments/baseline/seed_44 \
    outputs/PLC_mechanism_experiments/baseline/seed_45 \
    outputs/PLC_mechanism_experiments/baseline/seed_46 \
  --usgs data/usgs_all_state_type_month.csv \
  --states FL NC VA \
  --out outputs/Figure_1
```

### 4. Figure 2: PLC mechanism experiments

```bash
python model/plots/plot_plc_mechanism_experiments.py \
  --root outputs/PLC_mechanism_experiments
```

### 5. Figure 3: Conditional LC3 deployment

Requires the PLC historical simulation outputs from Step 1.

```bash
python model/experiments/run_lc3_deployment_scenarios.py \
  --plc-output outputs/PLC_baseline \
  --projects data/lc3/lc3_projects_audited_conditional.csv \
  --capacity-file data/mfr_capacity_for_model.csv \
  --peer-file data/plc/01_observed_inputs/rmx_peer_pairs.csv \
  --mfr-peer-file data/plc/01_observed_inputs/mfr_peer_pairs.csv \
  --baseline-month 2024-12 \
  --start 2025-01 --end 2035-12 \
  --extra-plants 5 \
  --candidate-ceiling-fraction 1 \
  --seed 42 \
  --out outputs/LC3_scenarios
```

## Scientific interpretation

USGS blended-cement shipments are an imperfect proxy for PLC market share.

The 2010–2022 period is used for model development; 2023–2024 is the
held-out evaluation period.

Manufacturer evidence dates do not necessarily establish actual PLC
activation dates. Endogenous capability transitions, announced conversions,
and company-wide rollout include modeling assumptions rather than
independently verified historical conversions.

LC3 deployment results are conditional scenarios, not forecasts.
Project commissioning is imposed as a scenario assumption.
PLC behavioral coefficients are transferred to LC3 without independent
LC3 validation. The LC3 scenarios hold 2024 supplier links and total
quantities fixed and assume all states are eligible.

The five-seed ranges in the PLC figures represent minimum–maximum
variation across seeds, not confidence intervals.

## Outputs

The three manuscript figures are included in `figures/`.

Generated simulation outputs are written under `outputs/` and excluded
from version control. They can be regenerated using the commands above.

## Data provenance and preprocessing

This study uses frozen, model-ready empirical inputs. The upstream data
preparation workflow is maintained in the parent repository.

### Geographic supply-chain network

The geographic network is constructed using:

- `../model/simple_abm_build_network.py`

This script builds manufacturer–RMX, RMX–demand, and state DOT relationships
from georeferenced manufacturer, ready-mix, demand, and DOT datasets.

Manufacturer–RMX links use a 150-mile primary radius and a bounded
nearest-manufacturer fallback of 208 miles.

The resulting network is stored in:

- `../data/simple_abm/us/nodes.csv`
- `../data/simple_abm/us/edges.csv`

### Historical PLC empirical inputs

The empirical input-construction workflow is implemented in:

- `../model/build_plc_empirical_state_holdout.py`

It uses the geographic network, USGS shipment data, county population,
DOT acceptance records, and manufacturer PLC evidence to construct
model-ready inputs, including:

- Manufacturer–RMX supply relationships.
- RMX peer relationships within 20 miles.
- Monthly state and RMX demand exposure.
- Monthly state DOT acceptance variables.
- Manufacturer PLC evidence constraints.

The original data sources, processing assumptions, and network
construction commands are documented in `../data/README.md`.

### Final-study input versions

The files under `data/` in this study are the frozen inputs used for
the reproduced manuscript results.

The final manufacturer evidence file incorporates prospective corrections
documented in the accompanying correction log and evidence audit.

The manufacturer peer network is also supplied as a frozen input.

The upstream preprocessing scripts document the construction methodology,
but exact regeneration of every frozen final-study input from raw sources
has not been independently verified.

This distinction does not affect reproduction of the published simulations
from the supplied model-ready inputs.
