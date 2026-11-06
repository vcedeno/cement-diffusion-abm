# PLC → LC3 | Evidence and next-model discussion

**Goal for the meeting:** Show what we learned from PLC, what we have documented for LC3, and what a simpler, more explanatory model could test.

## 1 · PLC: what we already have

| Show | What it establishes | What remains to test |
|---|---|---|
| **Historical PLC adoption vs model** (V1 figure) | We can compare simulated and observed national diffusion. | A good curve fit does **not** identify the mechanism that caused adoption. |
| **State-level PLC results** | We can inspect whether the model captures geographic variation. | Which states and periods are poorly reproduced? |
| **Mechanism and sensitivity experiments** | Regulatory acceptance, manufacturer availability, RMX demand and peers can be examined separately. | Which mechanisms are necessary, rather than merely capable of improving fit? |
| **PLC historical evidence** | DOT records and manufacturer histories can inform how the model is built. | Which model rules are directly supported by sources, and which remain assumptions? |

**V1 → V2:** Majid reports revised historical evidence and mechanisms, with promising preliminary PLC reproduction. 

## 2 · LC3 data search

Seven reproducible modules under `lc3/`, with source-backed CSVs and figures where useful:

| Modules | Show / takeaway |
|---|---|
| `01_manufacturer_projects/` + `02_market_demand/` | Announced projects and potential demand are **not** operating supply or observed purchasing. |
| `03_regulations_standards/` | Documented testing and research are **not** DOT approval. |
| `04_manufacturer_economics/` | Modeled production costs and payback depend on assumptions and local conditions. |
| `05_rmx_adoption_decisions/` | Demonstrations establish technical possibilities, **not** commercial adoption probabilities. |
| `06_external_signals/` | Procurement incentives can create demand, but are not LC3-specific adoption. |
| `07_evidence_synthesis/` | Evidence → possible mechanism → uncertainty / data gap. |

**What is missing:** Reliable national LC3 adoption histories, individual RMX decisions, and confirmed future DOT acceptance dates. **Missing evidence stays missing—not an invented model input.**

## 3 · The three original research questions

1. **Reproduce PLC:** Can the model match historical national **and regional** diffusion?
2. **Explain PLC:** Which mechanisms are actually needed to account for that diffusion?
3. **Explore LC3:** Under what conditions could LC3 adoption accelerate, and what coordination helps?

**Progression:** Reproduce → explain → test prospective interventions.

## 4 · Possible direction: simpler, evidence-informed model

**Keep:** Existing geographic manufacturer–RMX network; manufacturer, RMX, and DOT decisions.

**Explore, not prescribe:**
- **Manufacturer:** Invest when expected demand makes production viable, instead of assuming a deployment date.
- **RMX:** Adopt when accessible supply, eligibility for the intended market, and commercial viability align.
- **DOT:** Evaluate technical evidence; do not treat research completion as an acceptance date.

Separate **when an actor decides** from **how long physical implementation takes**. Begin with a few explicit rules; add peer effects, learning, or AI agents only if they provide demonstrable explanatory value. These rules are hypotheses, **not yet validated behavioral laws**.

## 5 · What could the model reveal?

| Hypothesis | Simple experiment |
|---|---|
| **Coordination bottleneck** | Independent manufacturer/RMX decisions vs credible demand commitments. |
| **Supply–regulation complementarity** | Regulatory change alone vs supply expansion alone vs both. |
| **Regional lock-in** | Different locations of initial viable manufacturer investments. |

## 6 · Questions

1. **What changed in V2**, and which historical PLC evidence motivated each change?
2. What is the **smallest set of mechanisms** that still reproduces **and explains** PLC?
3. Which **LC3 coordination experiment** should we run first using the evidence repository?

**Methodology opportunity:** Preserve a traceable chain: **source → finding → model-design decision → experiment**. 
