# Technical Review 03: RMX Behavior and Material Flows

## Purpose

Evaluate ready-mix purchasing behavior, supplier allocation,
and material-flow representation in v2 model.

The objective is to identify empirically justified improvements
without introducing unnecessary model complexity.

## 1. Current RMX representation

The model represents RMX behavior through continuous PLC
purchase shares rather than binary adoption states.

RMX facilities purchase from geographically connected,
operating cement plants.

Their purchases depend on:

- Supplier OPC and PLC offerings.
- Manufacturer OPC withdrawal.
- Availability of alternative OPC suppliers.
- Procurement-related purchasing behavior.
- State-level PLC market penetration.
- Product-class constraints.
- Manufacturer ownership of RMX facilities.

Finding R00:

The model already represents manufacturer-led diffusion
through OPC withdrawal and downstream purchasing changes.

Classification: Strength.

Recommendation: Preserve this mechanism.

## 2. Supplier allocation

### Finding R01

Classification: Simplifying assumption.

RMX facilities divide purchases equally among linked,
operating cement plants.

The geographic network identifies potential suppliers,
but does not establish observed purchasing volumes.

### Candidate recommendation

Evaluate the implications of equal supplier allocation
for geographic and state-level market-share results.

Consider whether existing geographic or capacity data
provide evidence for alternative allocation rules.

The model documentation reports that capacity-weighted
purchasing was previously examined and produced worse
forecast performance.

Therefore, capacity weighting should not be assumed
superior without further evidence.

Priority: Recommended diagnostic.

## 3. Transitional purchasing behavior

### Finding R02

Classification: Assumption requiring evidence review.

The model represents temporary switching toward OPC
when buyers encounter PLC-only supply.

This behavior decreases over a fixed qualification
period of 18 months.

### Candidate recommendation

Examine the empirical justification for this duration.

Distinguish documented operational constraints from
modeling assumptions.

Do not replace the existing period with another
unsupported duration.

Priority: Recommended evidence review.

## 4. Material-flow representation

### Finding R03

Classification: Potential structural limitation.

The model calculates RMX PLC purchase shares and
aggregates them using monthly demand.

It does not explicitly allocate shipment quantities
from individual manufacturers to individual RMX
facilities in the reviewed purchasing calculations.

Plant-level production capacity is not enforced
in those calculations.

This does not establish that capacity violations
occur in the reported simulations.

### Candidate recommendation

Evaluate implied manufacturer deliveries against
available plant production capacity.

A diagnostic should determine whether the simplified
purchasing representation produces physically
inconsistent implied deliveries.

Only consider introducing capacity-constrained
allocation if the diagnostic establishes a
meaningful problem.

Priority: High-priority diagnostic.

## 5. Vertical integration

### Finding R04

Classification: Strength.

The model distinguishes cement-owned RMX facilities
from independent facilities.

Owned RMX facilities purchase from their parent
manufacturer's plants when linked supply exists.

### Candidate recommendation

Preserve this mechanism.

Verify ownership assignments and evaluate their
influence on market-share outcomes.

Priority: Verification.

## 6. Summary of recommendations

R01:
Evaluate equal supplier allocation and its
implications for geographic market shares.

R02:
Review evidence supporting the fixed
18-month qualification period.

R03:
Check implied manufacturer deliveries
against production capacity.

R04:
Preserve vertical integration and verify
the underlying ownership assignments.

These recommendations are preliminary.

No model modifications have been made.

## 7. Source files

- v2/code/model.py
- v2/code/data.py
- v2/docs/model_document.md

Relevant documentation:

- Section 4.3: Ready-mix purchases.
- Section 5: Parameters.
- Section 6: Assumptions.
- Section 8: Evidence-to-mechanism mapping.

## 8. Review status

RMX implementation: reviewed.

Material-flow consistency: diagnostic recommended.

Empirical support for purchasing assumptions:
further examination needed.

No changes have been made to the model.
