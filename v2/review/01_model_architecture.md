# Technical Review 01: Model Architecture

## Purpose

Document the existing architecture of v2 PLC diffusion
model (v2) before evaluating individual behavioral mechanisms.

This review focuses on understanding the implementation.
It does not propose changes to the model at this stage.

## 1. Model scope

The model simulates the diffusion of portland-limestone cement
(PLC) in the United States.

Temporal resolution: monthly.

Historical period: 2010-2025.
Calibration period: 2010-2022.
Validation period: 2023-2025.

The model can also simulate scenarios through 2035.

## 2. Agents and components

### Parent firms

Parent firms decide when to initiate PLC introduction.

The model distinguishes between industry-coordination leaders
and market-responsive followers.

### Cement plants

Plants introduce PLC following their parent firm's initiation.

Plants may subsequently withdraw OPC, subject to regulatory,
firm-level, and product-class conditions.

### Ready-mix facilities

RMX facilities purchase cement from geographically connected
manufacturers.

Their PLC purchases depend on supplier availability, product
offerings, procurement behavior, and switching constraints.

### State DOTs

State DOT acceptance influences manufacturer OPC withdrawal.

Acceptance dates are sampled within documented historical windows.

### Imports

Imports provide an additional cement supply channel.

The baseline model treats imported cement as OPC.

## 3. Simulation sequence

1. Evaluate parent-firm PLC initiation.
2. Schedule plant-level PLC introduction.
3. Evaluate OPC withdrawal conditions.
4. Update plant product offerings and conversion progress.
5. Calculate RMX purchases from connected suppliers.
6. Aggregate domestic PLC shares by state.
7. Apply import adjustments.
8. Calculate national PLC market share.

## 4. Calibration and validation

The model separates firm-level initiation estimation from
market-layer calibration.

The firm hazard is estimated using historical firm-start records.

The market layer is calibrated using 2010-2022 observations,
with historical firm starts replayed during calibration.

Predictive evaluation uses simulated firm starts and
compares outcomes against 2023-2025 observations.

These procedures require further review before drawing
conclusions about predictive validity.

## 5. Initial architecture assessment

Finding A01:

The model already represents the principal supply-chain
actors and interactions relevant to PLC diffusion.

This includes manufacturer initiation, plant-level product
introduction and withdrawal, RMX purchases, DOT acceptance,
and market-share aggregation.

Implication:

The technical review should prioritize evaluating existing
mechanisms before recommending additional model complexity.

Status: Architecture observation; no code change proposed.

## 6. Questions for subsequent review

- How well are firm initiation decisions supported by evidence?
- How are plant-level availability and production distinguished?
- Are RMX purchases consistent with supply constraints?
- Are cement quantities conserved across the supply network?
- How are geographic relationships used in decisions?
- Are regulatory assumptions consistent with documented evidence?
- How are calibration and validation results interpreted?
- What are the actual plant counts loaded by the runtime?

## 7. Source files

- v2/docs/model_document.md
- v2/code/model.py
- v2/code/data.py
- v2/code/config.py

## 8. Review status

Architecture review: initial assessment completed.
Manufacturer behavior: pending detailed review.
RMX behavior: pending detailed review.
Validation assessment: pending detailed review.

No changes have been made to the model.
