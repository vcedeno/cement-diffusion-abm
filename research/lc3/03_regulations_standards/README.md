# Module 03 — LC3 regulations, standards, and state evidence

**Research snapshot: 2026-11-05.** This module covers **all 50 U.S. states**, not just eight scenario states. Every row has a source URL and a plain-language finding. `not_identified_in_reviewed_sources` means **no state-specific evidence found in the reviewed sources**, not proof that activity does not exist. `not_verified` does not mean rejected or prohibited.

## Data
- `data/lc3_dot_50_states.csv`: 50 states; observed activity, nonfindings, exact source URLs, dates, older secondary cement-type compilation. No arbitrary A/B/C/D categories.
- `data/lc3_documented_developments.csv`: one row per supported development; manufacturing selections distinguished from DOT testing and research.
- `data/lc3_national_standards.csv`: national standards; **a standard is not a state DOT product approval**.
- `data/lc3_eight_states.csv`: convenient *derived* subset, not the scope of research.

## Evidence and limitations
1. NCC Spring 2025 survey (33 responses), Q8 map and Q9 state comments, identifies **LC3 tested in WA, GA, and MN**. MN map says all categories tested at MnROAD. Other states reported testing calcined clay, which is **not identical to LC3**. A blank/unmarked survey map state is **not** evidence of no activity.
2. Virginia VTRC 26-R52 (2026) and VTRC 130459 (target May 2029) are LC3-specific DOT research, **not approval**.
3. DOE's industrial demonstration project selections identify proposed calcined-clay facilities in MD, GA, and TX; selection is **not an operating facility nor DOT acceptance**.
4. ACEEE October 2026 published an eight-condition, 50-state interactive map. **State-by-state interactive scores and their underlying sources were not retrievable here and are not fabricated.** Its public methodology page is cited as contextual evidence, not as a claim about any particular state.
5. CP Tech Center cement-type table is a **secondary compilation** and is kept separate from LC3-specific evidence. Its `Type IT` entries are **not LC3 approvals**.

## Figures
From repository root run:

```bash
python -m pip install matplotlib
python research/lc3/03_regulations_standards/scripts/plot_regulatory_evidence.py
```

Produces (1) named states with LC3-specific DOT testing/research (WA, GA, MN, VA), and (2) the 2025 survey's **33-response** tested-material counts (3 LC3 and 7 calcined clay, categories may overlap). No misleading approval timeline. The figures explicitly describe evidence coverage, not approval.

## Provenance
- NCC survey: https://www.intrans.iastate.edu/wp-content/uploads/2025/04/04-Spring-2025-NCC-State-Reports-on-Use-of-SCMs-and-Admixtures.pdf
- Virginia research: https://vtrc.virginia.gov/reports/all-reports/26-r52/
- Virginia project: https://vtrc.virginia.gov/projects/all-projects/130459/
- DOE selections: https://www.energy.gov/cmei/oced/industrial-demonstrations-program-selected-and-awarded-projects-cement-and-concrete
- ACEEE 50-state map: https://www.aceee.org/accelerating-adoption-limestone-calcined-clay-cement/
- CP Tech table: https://www.cptechcenter.org/state-dot-cementitious-materials-content-spec-table/
