# Technical Review 04: Geographic Networks and DOT Regulation

## Purpose

Evaluate geographic supply relationships and regulatory
acceptance mechanisms in v2 PLC diffusion model.

The review identifies existing strengths, simplifying
assumptions, and empirically justified diagnostics.

No model modifications are proposed at this stage.

## 1. Geographic supply network

### Current implementation

The model uses manufacturer-RMX supply links from:

v2/original_data/mfr_rmx_pairs.csv

These relationships are represented through a sparse
adjacency matrix.

The network determines which manufacturers are accessible
to each RMX facility.

### Finding N01: Geographic connectivity versus purchasing

Classification: Simplifying assumption.

Geographic relationships determine potential supplier
access, but purchases are generally divided equally
among connected operating suppliers.

Distance does not directly determine purchase volumes
once a supplier connection exists.

### Candidate recommendation

Evaluate the consequences of equal supplier allocation
for state-level PLC market shares.

Use existing geographic and capacity information
to diagnose potential allocation inconsistencies.

Do not assume distance-weighted or capacity-weighted
purchasing is superior without supporting evidence.

Priority: Recommended diagnostic.

## 2. Network completeness

### Finding N02: Missing or limited supply relationships

Classification: Documented limitation.

The model documentation identifies geographic
network limitations, including Minnesota's restricted
supplier coverage and a missing GCC Rapid City link.

These limitations may influence state-level PLC
availability and market-share predictions.

### Candidate recommendation

Conduct a targeted network completeness audit.

Report:

- Accessible cement plants per RMX facility.
- Manufacturer coverage by state.
- States with unusually limited supplier access.
- Documented supply relationships missing from the network.

Prioritize evidence-supported corrections.

Do not introduce hypothetical links solely to
improve historical model fit.

Priority: High.

## 3. DOT acceptance

### Current implementation

State DOT acceptance is represented using documented
historical windows.

Each state has:

- Earliest possible acceptance date.
- Latest documented acceptance date.

The model samples an acceptance month uniformly
within this interval.

### Finding D01: Acceptance-date uncertainty

Classification: Empirically bounded modeling assumption.

Acceptance windows are grounded in historical evidence.

However, the uniform distribution within each window
is a modeling assumption.

### Candidate recommendation

Review the DOT evidence records.

Where a specific historical acceptance date is
documented, consider using that date.

Where only an interval is supported, preserve
the uncertainty and evaluate its consequences.

Priority: Recommended evidence review.

## 4. Regulatory influence on manufacturer decisions

### Finding D02: DOT withdrawal threshold

Classification: Fixed behavioral assumption.

The model permits eligible manufacturer OPC withdrawal
when the demand-weighted DOT acceptance exposure
reaches at least 0.95.

This connects regulatory acceptance to
manufacturer product decisions.

The threshold should not be interpreted as a
documented legal requirement without evidence.

### Candidate recommendation

Clarify the interpretation of the threshold.

Evaluate whether the assumption materially affects
manufacturer withdrawal timing and geographic
PLC market shares.

Distinguish DOT acceptance from manufacturer
product availability and RMX purchasing requirements.

Priority: Recommended.

## 5. Demand-weighted regulatory exposure

### Finding D03

Classification: Strength.

The model calculates regulatory exposure using
customer-market demand rather than simply counting
states where PLC is accepted.

This preserves geographic heterogeneity in
manufacturer exposure.

### Recommendation

Preserve demand-weighted regulatory exposure
unless evidence supports an alternative.

## 6. Preliminary recommendations

N01:
Evaluate the geographic consequences of equal
supplier purchasing.

N02:
Audit supplier-network completeness, especially
documented missing connections and states with
limited supplier coverage.

D01:
Review DOT acceptance dates and distinguish
exact evidence from interval uncertainty.

D02:
Clarify and evaluate the 95% regulatory threshold.

D03:
Preserve demand-weighted regulatory exposure.

These are preliminary recommendations.

No model modifications have been made.

## 7. Source files

- v2/code/data.py
- v2/code/model.py
- v2/code/build_inputs.py
- v2/docs/model_document.md

Relevant documentation:

- Section 2: Agents, states, and network.
- Section 4.2: Manufacturer withdrawal.
- Section 4.4: DOT acceptance.
- Section 5: Parameters.
- Section 6: Assumptions.
- Section 10: Limitations.

## 8. Review status

Geographic network implementation: reviewed.

DOT acceptance implementation: reviewed.

Empirical network completeness: further audit recommended.

DOT evidence verification: pending.

No changes have been made to the model.
