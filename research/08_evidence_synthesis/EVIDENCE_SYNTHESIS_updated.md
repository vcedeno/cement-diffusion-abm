# Module 08 — Evidence-grounded historical interpretation

## Question and scope
What can the compiled Modules 01–07 establish about PLC readiness, regulatory permission, and the early-2020s market transition?

## Historical interpretation

**Before 2012.** Documented field experience and technical evaluation preceded formal Type IL standardization. Selected early use and acceptance are not evidence of nationwide supply or adoption (M08-01, M08-02, M08-05).

**2012–2019.** Type IL standardization and staggered DOT permission preceded the later shipment change. Manufacturer records have different evidence scopes; company announcements, scheduled transitions, and verified plant operations must not be equated (M08-02, M08-03, M08-05).

**2020–2022.** The record contains manufacturer transitions, agency implementation, downstream qualification and supply constraints, and procurement initiatives. Their temporal proximity to shipment changes does not establish that any one caused the change (M08-03, M08-06–M08-11).

**2023–2024.** Additional policy, procurement, and broad DOT acceptance milestones followed the start of the transition. These later milestones cannot be used as explanations for its onset without additional evidence (M08-05, M08-10, M08-11, M08-14).

## What the market series does and does not show
The Module 02 USGS series reports cement shipment categories. The **blended** category contains materials other than PLC, so the sharp increase is not an identified PLC-only adoption curve. The Stage 1 annual aggregates sum supplied rows without a missingness or category-comparability audit.

## Implications for the ABM
See `data/evidence_to_model_assessment.csv` for a mechanism-by-mechanism mapping of observations, evidence limitations, model representation, and unverified behavioral assumptions. A qualitative observation that a constraint exists does not identify its mathematical response function, parameter value, geographic scope, or national prevalence. The mapping was checked against the available model runner and reference specification; it does **not** recalibrate the PLC model.

## Figures
The previous Stage 3 shipment/DOT plot duplicates existing work; the evidence-count heatmap measures **selected record links**, not mechanism importance. Neither is recommended as a manuscript figure. No figures are retained in Module 08.

## Limitations
Source reuse is not independent corroboration. Some Module 07 records were not reverified, and some Module 05 evidence concerns broader low-carbon concrete. The available observational evidence does not identify causal contributions of supply, DOT acceptance, demand, or peer exposure.


## Stage 4 model implementation consistency audit (2026-11-05)

Reviewed `model/run_plc_simplified.py` against the `18_E01_controlled_corrected/run_specification.csv` (seed 42; T_A=5; kappa=8.439534971412707; B0=1.6223578864493762; theta_M=0.19491661627095874; H_M=10; T_M=29). The runner's default arguments differ from the reference values; the reference values must be supplied explicitly to reproduce the run. The uploaded reference specification does not record `rng_mode`, `disable_peer_effect`, or `withhold_future_mfr_evidence`, so their historical invocation cannot be independently verified from that file alone.

**Critical correction:** `phi_s` is an additive DOT acceptance/implementation input in the adoption pressure, **not** a hard DOT eligibility gate. The runner reads `phi_s` from an upstream CSV; the transformation from observed DOT dates is not audited here.

**Other boundaries:** RMX peer pairs and monthly demand exposures are precomputed; this audit cannot verify the 20-mile network construction or the spatial demand-allocation method. Dated plant evidence acts as an availability boundary; year-only evidence is assigned to December. A manufacturer's availability may also become active after the endogenous demand trigger and delay, provided the plant is operating.

No historical evidence sources were reverified and no model was rerun. The model consistency audit is a code-and-specification inspection, not a numerical reproduction or validation of historical fit. See `data/model_consistency_audit.csv`.
