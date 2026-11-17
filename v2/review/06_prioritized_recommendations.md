# Prioritized Recommendations for the v2 Model

## Purpose

This document consolidates the technical review of the
existing v2 PLC diffusion model.

The objective is to identify focused, empirically supported
opportunities to improve geographic representation,
behavioral interpretation, and predictive validation.

Recommendations distinguish:

1. Findings supported by the implementation or stored results.
2. Diagnostics needed to establish their practical importance.
3. Potential improvements conditional on diagnostic evidence.

No model changes were made during this review.

---

## P1 — Investigate state-level prediction errors

**Priority:** High

**Related findings:** V01, V02, N01, M02

### Verified finding

The model reproduces national PLC diffusion more closely
than individual state-level outcomes.

Reported validation metrics include:

- National RMSE, 2023-2025: 0.0344.
- Demand-weighted state RMSE, 2025: 0.1442.

The stored 2025 results show substantial discrepancies
in several states, including Delaware, New Mexico,
Pennsylvania, and New Hampshire.

The calibration objective emphasizes national monthly
market share, with a coefficient of 0.01 on the
state-level error component.

### Recommended diagnostic

For states with the largest validation errors:

1. Compare observed and simulated annual PLC shares.
2. Identify supplying manufacturers and plants.
3. Examine documented PLC introduction and withdrawal.
4. Check relevant network connections and imports.
5. Determine which modeled mechanism plausibly explains
   each discrepancy.

### Potential improvement

Revise a specific geographic or behavioral assumption
only when the diagnostic identifies a supported cause.

Do not introduce additional calibration parameters
solely to improve aggregate fit.

### Relevant implementation

- code/calibrate.py
- code/validate.py
- code/model.py
- code/data.py
- code/targets.py

### Verification

Compare state-level errors before and after any
evidence-supported change.

Check whether national performance is preserved.

---

## P2 — Audit manufacturer-RMX supply connections

**Priority:** High

**Related findings:** N01, N02, R01

### Verified finding

The model uses a geographic network of potential
manufacturer-to-RMX supply relationships.

Purchasing is distributed equally among linked
operating suppliers, subject to model rules.

The existing documentation identifies limitations
in geographic coverage, including Minnesota.

It also reports that capacity-weighted purchasing
was previously examined and worsened forecast fit.

### Recommended diagnostic

1. Identify states with restricted supplier coverage.
2. Examine plants serving each state's RMX facilities.
3. Compare modeled connections with documented
   supplier relationships where evidence is available.
4. Determine whether missing connections contribute
   to state-level prediction errors.

### Potential improvement

Correct demonstrably missing or inaccurate connections
using traceable geographic or commercial evidence.

Do not add hypothetical supply links merely to
improve calibration.

### Relevant implementation

- original_data/mfr_rmx_pairs.csv
- code/data.py
- code/model.py
- code/build_inputs.py

### Verification

Check changes in geographic coverage and state-level
predictions while preserving the existing purchasing
rules for the initial comparison.

---

## P3 — Evaluate material-flow consistency

**Priority:** High

**Related findings:** R03, N01

### Verified finding

The model calculates RMX PLC purchasing shares
using linked suppliers and modeled product availability.

The reviewed purchasing implementation does not
explicitly allocate physical shipment quantities
from individual manufacturers to RMX facilities
or enforce plant production capacities.

This does not establish that modeled flows exceed
capacity or that market-share predictions are invalid.

### Recommended diagnostic

1. Identify the demand represented by each RMX facility.
2. Examine how supplier purchase shares are calculated.
3. Determine whether implied supplier-level quantities
   can be reconstructed without unsupported assumptions.
4. Compare reconstructed quantities with documented
   plant capacities where meaningful.
5. Report unresolved allocation uncertainty explicitly.

### Potential improvement

If the diagnostic establishes a material inconsistency,
evaluate a minimal, evidence-supported allocation
or capacity constraint.

Avoid introducing arbitrary utilization factors,
production fractions, or delivery assumptions.

### Relevant implementation

- code/model.py
- code/data.py
- original_data/mfr_capacity_for_model.csv
- original_data/rmx_month_demand_exposure.csv.gz

### Verification

Check quantity accounting, supplier-level capacity
consistency, and effects on state and national shares.

---

## P4 — Strengthen plant-level historical evidence

**Priority:** Medium

**Related findings:** M02, M03, V02

### Verified finding

The model represents manufacturer initiation,
plant-level PLC introduction, and OPC withdrawal.

Plant rollout timing uses empirical within-firm
lags, but plant ordering is randomized.

The existing documentation acknowledges that this
approach cannot predict some plant-specific laggards.

OPC withdrawal is governed by additional modeled
conditions, including DOT acceptance and product class.

### Recommended diagnostic

1. Compare simulated introduction timing with
   documented plant-level PLC evidence.
2. Distinguish documented availability from
   actual production and OPC withdrawal.
3. Identify plants with verified later introduction
   or continued OPC production.
4. Examine whether these plants contribute to
   state-level discrepancies.

### Potential improvement

Use verified plant-specific constraints where
the historical evidence supports them.

Preserve unresolved cases as uncertain rather
than treating missing evidence as unavailability.

Do not interpret documentary availability dates
as retrofit or conversion durations.

### Relevant implementation

- code/model.py
- code/data.py
- new_data/evidence/plant_plc_evidence.csv
- new_data/plant_conversion_evidence.csv

### Verification

Compare plant-level timing and geographic market
shares against the documented record.

---

## P5 — Clarify calibration and validation assumptions

**Priority:** Medium

**Related findings:** V01, V03, V04, V05

### Verified finding

The model uses separate manufacturer and market
estimation stages.

The market layer is calibrated through 2022.

Manufacturer starts are predicted during validation.

The 2025 demand input is constructed using observed
2025 shipment ratios.

The observed PLC target is approximated from
USGS blended cement shares net of the
2016-2019 baseline.

Manufacturer validation distinguishes dated starts
from documentary upper bounds.

### Recommended diagnostic

1. Document which inputs are observed during
   the validation period.
2. Distinguish conditional historical evaluation
   from fully prospective forecasting.
3. Examine sensitivity to the national/state
   calibration weighting.
4. Describe uncertainty in the observed PLC proxy.
5. Preserve the treatment of uncertain manufacturer
   initiation dates.

### Potential improvement

Clarify validation claims and, where feasible,
compare results with demand projections based
only on pre-validation information.

Any calibration-objective change should be
evaluated against both national and state outcomes.

### Relevant implementation

- code/calibrate.py
- code/validate.py
- code/targets.py
- code/data.py
- code/firm_hazard.py

### Verification

Report national, state-level, and manufacturer
validation results under clearly defined
information assumptions.

---

## Recommended implementation sequence

The recommendations should be investigated
incrementally.

### First: Diagnose geographic errors

Begin with P1.

Use the largest state-level discrepancies to
identify which mechanisms warrant closer examination.

### Second: Examine network and quantity consistency

Investigate P2 and P3 using existing inputs.

Do not change purchasing rules until the
diagnostics establish a supported reason.

### Third: Examine plant-level evidence

Use P4 to investigate documented rollout
and withdrawal discrepancies.

### Fourth: Clarify validation interpretation

Complete P5 before drawing stronger predictive
claims or comparing alternative model versions.

---

## Principles for future development

1. Preserve the existing manufacturer-led mechanism.
2. Prefer documented evidence over additional parameters.
3. Distinguish PLC capability, production, and delivery.
4. Do not interpret missing evidence as unavailability.
5. Evaluate state-level outcomes alongside national fit.
6. Preserve the separation between calibration and validation.
7. Make one targeted change at a time.
8. Compare each change with the existing reference model.
9. Retain changes only when supported by evidence
   and improved diagnostic performance.

---

## Review scope

This document provides technical recommendations
based on code inspection, documentation, and stored
validation results.

It does not report independently reproduced simulations.

Proposed improvements are conditional on further
diagnostic evidence.

The existing model has not been modified.

## Supporting review documents

- 01_model_architecture.md
- 02_manufacturer_behavior.md
- 03_rmx_behavior.md
- 04_network_and_regulation.md
- 05_validation_assessment.md
