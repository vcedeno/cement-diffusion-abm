# Technical Review of the v2 Cement Diffusion Model

## Overview

This directory contains a technical review of the existing
v2 agent-based model of Portland-limestone cement (PLC)
diffusion in the United States.

The review examines the model's architecture, manufacturer
behavior, ready-mix purchasing decisions, geographic supply
networks, regulatory representation, and validation.

The objective is to identify evidence-supported opportunities
to strengthen the model's explanatory value, geographic
representation, and predictive performance.

The review does not modify the existing implementation.

## Review Documents

| Document | Content |
|---|---|
| [01 — Model Architecture](01_model_architecture.md) | Model structure, agents, interactions, and overall design |
| [02 — Manufacturer Behavior](02_manufacturer_behavior.md) | Firm initiation, plant introduction, and OPC withdrawal |
| [03 — RMX Behavior](03_rmx_behavior.md) | Purchasing decisions, supplier selection, and material-flow consistency |
| [04 — Networks and Regulation](04_network_and_regulation.md) | Geographic supply connections and DOT acceptance |
| [05 — Validation Assessment](05_validation_assessment.md) | Calibration, validation, state-level errors, and data assumptions |
| [06 — Prioritized Recommendations](06_prioritized_recommendations.md) | Proposed diagnostics and evidence-supported improvements |

## Review Approach

The assessment is based on:

- Inspection of the existing v2 implementation.
- Review of the model documentation and evidence records.
- Examination of stored calibration and validation results.
- Identification of assumptions requiring further verification.

Findings distinguish among:

1. Existing model strengths.
2. Confirmed implementation characteristics.
3. Documented limitations.
4. Questions requiring additional evidence.
5. Potential improvements conditional on diagnostic results.

## Main Areas for Further Investigation

The prioritized recommendations focus on:

1. State-level prediction errors.
2. Manufacturer-RMX supply network completeness.
3. Material-flow and production-capacity consistency.
4. Plant-level PLC introduction and OPC withdrawal evidence.
5. Calibration and validation assumptions.

The recommended workflow is to investigate one issue at
a time, verify the supporting evidence, and evaluate any
proposed change against the existing reference model.

## Scope and Limitations

This is a technical review, not an independent
reproduction of the model's reported results.

Reported validation metrics are taken from the
existing repository outputs.

The review does not establish that every identified
simplification requires modification.

Recommendations are intended to support subsequent
research decisions and targeted diagnostic work.

No changes were made to the v2 model.
