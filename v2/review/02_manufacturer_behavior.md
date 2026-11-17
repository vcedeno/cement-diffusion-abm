# Technical Review 02: Manufacturer Behavior

## Purpose

Evaluate manufacturer initiation, plant-level PLC introduction,
and OPC withdrawal in v2 model.

This review identifies existing strengths and potential
improvements. No changes to the implementation are proposed
without examining the supporting evidence.

## 1. Parent-firm initiation

### Current implementation

Parent firms initiate PLC through a probabilistic hazard model.

The model distinguishes:

- Leaders: GCCA members responding to dated industry signals
  and firm size.
- Followers: nonmembers responding to PLC penetration in
  their customers' markets.

The hazard coefficients are estimated using firm-level
observations from 2012-2022.

### Finding M01: Explicit manufacturer decisions

Classification: Strength.

The model represents manufacturer initiation explicitly,
rather than prescribing a national PLC adoption trajectory.

The distinction between leaders and followers introduces
heterogeneity in manufacturer behavior.

### Interpretation

GCCA membership is a modeled behavioral classification.

The statistical relationship does not independently establish
that membership caused PLC introduction.

## 2. Plant-level PLC introduction

### Current implementation

After a parent firm starts, eligible plants introduce PLC
according to a randomized rollout sequence.

The first plant introduces PLC immediately.

Other plants follow delays sampled from observed within-firm
rollout lags.

Documented pre-2020 PLC availability is represented separately.

### Finding M02: Plant rollout ordering

Classification: Potential improvement.

The model uses empirical rollout lags but randomly assigns
plant ordering within a firm.

### Candidate recommendation

Evaluate whether documented plant-specific introduction
dates can constrain rollout ordering where reliable evidence
exists.

Retain the existing stochastic mechanism for unresolved cases.

### Rationale

Plant-specific evidence could improve geographic realism
without introducing additional behavioral parameters.

### Verification needed

Examine the plant evidence table and determine which dates
represent confirmed availability rather than announcements,
document dates, or unresolved evidence.

## 3. OPC withdrawal

### Current implementation

Plants may withdraw OPC after PLC introduction.

Withdrawal depends on:

- Plant eligibility and operation.
- Parent-firm initiation.
- DOT acceptance conditions.
- Leader/follower classification.
- Type II/V product-line constraints.
- Customer-loss tolerance.

In the reported configuration, the customer-loss tolerance
does not impose an additional effective restriction once
the other eligibility conditions are met.

Withdrawal is followed by a conversion period.

### Finding M03: Withdrawal behavior

Classification: Assumption requiring examination.

The reported configuration makes OPC withdrawal depend
primarily on regulatory conditions, firm classification,
and product-class restrictions.

### Candidate recommendation

Compare modeled withdrawal behavior with documented
plant-level production and conversion evidence.

Distinguish:

1. PLC availability.
2. PLC production or production-share changes.
3. OPC withdrawal.

These events should not be assumed equivalent without
supporting evidence.

### Rationale

Manufacturer decisions influence downstream material
availability and therefore RMX purchasing behavior.

### Verification needed

Inspect the conversion evidence and determine which records
support actual OPC withdrawal.

Do not interpret missing evidence as proof of unavailability
or continued OPC production.

## 4. Calibration and validation question

### Finding M04: Demand-weight construction

Classification: Validation question.

The firm-hazard estimation uses customer-market weights
constructed from demand observations extending through 2024.

The firm-hazard outcomes are fitted through 2022.

It remains necessary to determine whether the use of
post-2022 demand information materially affects the
estimated manufacturer behavior.

### Candidate check

Compare the demand-weight construction with a version
restricted to information available by December 2022.

This is a proposed diagnostic, not a confirmed finding
of consequential data leakage.

## 5. Preliminary recommendations

M02:
Examine whether reliable plant-level evidence can constrain
the stochastic rollout ordering.

M03:
Assess the empirical support for OPC withdrawal conditions
and conversion periods.

M04:
Verify the temporal provenance of demand weights used in
manufacturer hazard estimation.

These are candidate recommendations pending evidence review.

## 6. Source files

- v2/code/firm_hazard.py
- v2/code/model.py
- v2/code/data.py
- v2/docs/model_document.md

Relevant model-document sections:

- Section 4.1: Parent-firm initiation.
- Section 4.2: Plant introduction and withdrawal.
- Section 5: Parameters.
- Section 6: Assumptions.
- Section 7: Calibration and validation.

## 7. Review status

Manufacturer implementation: reviewed.

Supporting empirical evidence: further examination needed.

Recommendations: preliminary.

No changes have been made to the model.
