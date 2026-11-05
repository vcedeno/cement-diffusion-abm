# Module 05 — RMX adoption decisions (evidence collection in progress)

## Research scope
PLC-related adoption decisions and implementation experiences at the facility, company, project and industry levels. Do not infer adoption by any of the 3,761 modeled RMX facilities from company or survey evidence.

## Data
- `data/rmx_adoption_evidence.csv` — one consolidated master evidence table. Original 28 observations retained; 15 source-grounded observations appended from two additional sources.
- `../08_evidence_synthesis/data/module05_insight_register.csv` — provisional synthesis-ready interpretations and limitations; not measured causal effects.

## Newly verified sources
- California Air Resources Board, Draft SB 596 Cement Strategy (March 2025), Appendix C, pp. 117–122: survey fielded May–November 2023; 22 responses. The report is a 2025 publication reporting 2023 survey results, **not** a 2025 adoption event.
- City of Portland, *Low-Carbon Concrete Pilot Project: Type 1L + Slag Mixes for Sidewalk & Pavement Applications* (January 2022), pilot performed October–November 2021.

## Interpretation rules
- Survey selection counts are not counts of adopting plants, mutually exclusive categories, nationally representative estimates, or causal effect sizes.
- Do not compare raw frequency of qualitative observations across differently sampled sources as if they are population prevalence.
- `state` is geographic scope of evidence; `rmx_id` remains empty unless a specific facility match is documented.
- The 2025 CARB strategy is **outside** the 2005–2024 publication window, but included as a retrospective source for 2023 observations.
- Source verification in this update applies to the **15 appended observations**. The original 28 have not been re-audited row-by-row.

## Status and next steps
43 observations across 12 unique URLs; three descriptive figures generated. Recheck original 28 citations, broaden independent producer coverage, verify figure-specific question wording and denominators against primary sources, and consider a producer case-study timeline.

## Reproducible descriptive figures (November 2026)

From repository root:

```bash
python research/05_rmx_adoption_decisions/scripts/plot_rmx_adoption.py
```

Outputs in `figures/`:

- `01_carb_barriers.png`: CARB 2023 producer-survey selections concerning reasons for not using/considering PLC. Multi-select response counts; **not** representative plant-level prevalence.
- `02_nrmca_producer_experiences.png`: percentages reported in the 2023 NRMCA survey of 22 companies as summarized in ACI–ASCC (2024). These are reported percentages, **not** inferred numbers of facilities.
- `03_carb_demand_signals.png`: distinct CARB survey response selections illustrating that approval and actual demand are different concepts; selections need not be mutually exclusive.
- `figure_source_index.csv`: evidence-row provenance for every plotted quantity, reusable in Module 08.
- `04_source_coverage.csv`: source-level evidence-row coverage for audit; **not** a chart of mechanism importance.

### Important limits

The master CSV has 43 observations from 12 source URLs, but multiple observations come from the same sources. These figures do not estimate U.S. RMX adoption rates, causal effects, or facility-level parameters. The existing 28 observations from earlier passes still require full original-source re-audit; plots are provisional until source verification is complete. A missing state or RMX ID must not be interpreted as non-adoption. The two survey figures use reported metrics from different surveys and should not be combined into a single population estimate.


## Figure interpretation and limitations (for Module 08 synthesis)

These are **descriptive findings**, not causal tests or estimates of national adoption. Interpret each chart at its original unit of observation and preserve the distinction between **what respondents reported**, **our interpretation**, and **what remains unmeasured**.

### Figure 01 — Operational and market barriers reported by California concrete producers (2023)

**Evidence basis:** California Air Resources Board (CARB) survey fielded in 2023, reported in the 2025 strategy appendix. The chart displays counts of selections for reasons for not using or considering PLC, including additional storage (11) and additional testing/processes (8).

**Meaning of the categories:** "Additional storage" may involve silo capacity, segregating cement types during a transition, or handling separate inventories; the survey selection alone does **not** identify which arrangement each respondent needed. "Additional testing/processes" signals perceived qualification or procedural burdens; it does **not** mean respondents necessarily wanted more testing.

**Interpretation limits:**
- The survey had 22 company responses overall, but the eligible/responding denominator for this particular question must be checked against the original questionnaire before calculating percentages.
- Respondents could select multiple barriers; counts are not mutually exclusive and should not be summed into a total number of companies.
- Selection frequency does not establish barrier severity, cost, duration of delay, or causal effect on adoption.
- The responding companies do not constitute a representative sample of all California or U.S. RMX facilities; no facility-level prevalence should be inferred.

**Supported insight:** Storage and qualification requirements are **reported implementation barriers**. They warrant consideration alongside supply and regulatory acceptance, without implying a quantified adoption delay.

### Figure 02 — Supply conditions and technical adjustments reported by ready-mix producers (2023)

**Evidence basis:** A 2023 NRMCA survey of 22 concrete-producing companies, summarized in a 2024 ACI–ASCC publication. The chart presents reported percentages: only PLC available from suppliers (60%), 1:1 replacement (70%), lower 28-day compressive strength (50%), and increased water-reducer dosage (40%). These are survey-reported percentages; **do not convert them to plant counts**.

**Meaning of the categories:**
- **Only PLC available:** Some surveyed producers reported that their cement sources offered only PLC. This does not mean 60% of U.S. RMX plants had only PLC available, or prove that supply restrictions caused adoption.
- **1:1 replacement:** PLC was substituted for conventional cement at the same cement quantity in the reported practice; this does **not** imply all other mixture ingredients, testing, or performance remained unchanged.
- **Lower 28-day strength:** Some respondents reported lower measured compressive strength at 28 days. This does **not** establish that PLC generally fails strength specifications or performs worse under all conditions.
- **Increased water-reducer dosage:** This concerns a **chemical admixture**, not necessarily adding more mixing water. It may raise admixture expense, but the survey does not measure net concrete-production cost.

**Interpretation limits:**
- Results describe surveyed companies, not the national RMX facility population; question-specific denominators and rounding should be verified in the original publication.
- Responses may overlap. The chart does not establish which companies experienced which combination of effects.
- No causal estimate, aggregate cost premium, magnitude of strength reduction, or adoption response period can be derived from these percentages.

**Supported insight:** Supply-side transitions and technical mix adjustments can coexist; **using PLC** is not equivalent to **requiring no operational adaptation**.

### Figure 03 — Reported demand signals for PLC among California concrete producers (2023)

**Evidence basis:** The same 2023 CARB survey used in Figure 01. Plotted selections include Caltrans approval cited as a demand factor (7), project-owner low-carbon choices cited (5), and a combined response indicating no PLC inquiries or no PLC sales (8).

**Interpretation limits:**
- These are **different response categories**, not three exclusive adoption states or directly comparable adoption rates.
- "No inquiries" and "no sales" are distinct outcomes, but the combined category does not distinguish them. A producer might use PLC as its default cement without receiving PLC-specific inquiries.
- The figure does not measure realized PLC sales, market share, or the elapsed period between Caltrans approval and uptake.
- Respondents' identification of approval or owner preferences as demand factors does **not** establish that those factors caused any particular producer to adopt.
- As in Figure 01, verify question-specific denominators before displaying percentages.

**Supported insight:** Regulatory acceptance, expressed customer interest, and realized use are **different dimensions** of diffusion; regulatory permission alone should not be equated with immediate demand or adoption.

### Synthesis handoff

Preserve these **three provisional insights** in `../08_evidence_synthesis/data/module05_insight_register.csv` (or reconcile them with existing rows there):

1. **Supply-driven transition:** Manufacturer product availability may constrain downstream material choice; supported by producer reports, not a quantified causal effect.
2. **Implementation constraints:** Storage, testing, mixture performance, and admixture adjustment can complicate PLC implementation; survey responses do not quantify delays or total costs.
3. **Regulatory acceptance versus demand:** Approval and customer demand are distinct from actual use; the CARB survey documents reported signals but cannot establish causal sequencing.
