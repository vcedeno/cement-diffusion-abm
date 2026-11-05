# Module 06 — DOT decision factors (evidence collection in progress)

## Scope
Document what state transportation agencies evaluated, permitted, and required when considering Type IL portland-limestone cement (PLC). Module 03 separately records acceptance dates. Research funding or publication is not itself evidence of an approval decision.

## Data
`data/dot_decision_evidence.csv` is the single master evidence table. It currently contains **15 evidence observations from 12 distinct source URLs**. Multiple observations from one document are not independent sources.

## Findings from newly added primary sources
- **California (2020):** A Caltrans–industry scoping document stated that Type IL was not then permitted and proposed work on concrete performance and implementation.
- **California (2021):** Caltrans CPD 21-19 explicitly allowed Type IL under revised specifications, citing sustainability and performance. It also provided a no-cost change-order pathway for older projects.
- **Wisconsin (2021):** WisDOT documented Type IL material acceptance, approved suppliers, and differing trial-batch requirements by concrete class and contract status.
- **Georgia (2017):** GDOT-sponsored tests of Type IL cements from five producers found evaluated concretes met the tested GDOT class specifications, with important material-source variability.
- **Texas (2015):** TxDOT funded investigation of cements with **more than 15% limestone**; this must not be conflated with standard Type IL qualification.

## Interpretation limits
- A technical study documents an evaluation, not necessarily the cause of approval.
- A policy directive establishes permitted use under stated conditions, not actual adoption or quantities purchased.
- Requirements vary by state, project, concrete class, and date.
- No evidence frequencies should be interpreted as the prevalence or importance of mechanisms across all 50 DOTs.

## Status
Evidence collection is ongoing. The California 2020→2021 sequence is a useful directly documented example of technical review followed by specification permission, but does not by itself establish causation. Further work should seek original approval rationale and early state cases before figures are finalized.


## Earlier historical evidence (2008–2018)

The earliest DOT examples located in this search concern **ASTM C1157 performance-specified portland-limestone cement**, not necessarily the later ASTM C595 Type IL classification. Colorado's U.S. Highway 287 project began in 2008, and a contemporary report describes Utah's ASTM C1157 use and 2008 fly-ash blending permission. Indiana's 2013 DOT-sponsored study recommended that INDOT could consider ASTM C595/AASHTO M240 PLC suitable for applications. These records describe field use and technical evaluation, **not independently verified first-acceptance dates**.

The 2018 Colorado brief reports an average 28-day flexural strength of 695 psi versus a 650 psi requirement on the U.S. 287 project, and describes climate objectives as a motivation. The two Colorado rows share the same source/project and are **not independent corroboration**.

Sources:
- CP Road Map Brief (2018): https://www.intrans.iastate.edu/wp-content/uploads/2019/10/MAPbriefOctober2018.pdf
- Roads & Bridges (2010): https://www.roadsbridges.com/concrete/article/10586682/performance-enhancing
- INDOT/Purdue JTRP report (2013): https://docs.lib.purdue.edu/jtrp/1548/

**Research limitation:** Original Colorado/Utah 2008 DOT approval records have not been retrieved; distinguish retrospective field evidence from original approval documentation. Avoid counting different cement standards as equivalent acceptance events in Module 03.


## Historical source follow-up — 2018 CP Road MAP brief

The October 2018 technical brief documents Oklahoma I-40 Crosstown PLC paving, a Utah SR 201 comparison in 2009, and Denver municipal demonstration work in 2007. It also distinguishes pre-2012 ASTM C1157 projects from ASTM C595/AASHTO M240 Type IL specification acceptance in 2012. All observations are retrospective descriptions from **one source**, not independent confirmation from seven documents. The original ODOT special provision and the original 2009 UDOT trial report remain unverified. The Oklahoma section of the brief inconsistently uses Type IL and Type II terminology; preserve that ambiguity rather than silently correcting it. Source: https://www.cptechcenter.org/wp-content/uploads/2019/10/MAPbriefOctober2018.pdf


## Targeted historical document search (November 2026)

- **Utah, agency-authored evidence (2023):** UDOT reported that cement shortages created project budget/schedule problems and that expedited PLC testing and approval helped suppliers respond. This is a documented **later** rationale, not proof of why UDOT permitted its 2009 trial.
- **Utah, 2009 field comparison (TRB technical presentation):** SR 201 used conventional cement in August eastbound work and 10%-limestone ASTM C1157 cement in October westbound work, with 25% Class F fly ash in both. The presentation is not the original trial authorization.
- **Oklahoma:** An official ODOT archive of 2009 special provisions is available at https://www.odot.org/c_manuals/specprov2009/ ; the original PLC-specific I-40 provision was **not located or verified** in this search. Do not assign a formal acceptance date from this archive.
- **Colorado:** 2008–2009 US 287 project details are supported by contemporary technical accounts, but an original CDOT project authorization has **not** been verified.

**Status:** 28 observations in the working evidence CSV, including two new source records. The early original approval documents remain outstanding. A single source can support multiple observations, so row counts are not counts of independent studies.


## Descriptive evidence figures (November 2026)

From the repository root:

```bash
python research/06_dot_decision_factors/scripts/plot_dot_decisions.py
```

- `figures/01_dot_historical_evidence_timeline.png`: dated state-level evidence observations, with specification/procedure records distinguished from research and field reports. **Observation years are not automatically DOT acceptance dates.**
- `figures/02_dot_evidence_themes.png`: number of distinct source URLs supporting each broad documented theme. These are **coverage counts**, not the number of DOTs adopting PLC or evidence of relative causal importance.
- `figures/03_dot_case_pathways.png`: California's documented 2020–2021 evaluation/acceptance sequence and Utah's separate 2009 field experience and 2023 supply-related decision account. The Utah events are not assumed to form a single causal sequence.
- `figures/figure_source_index.csv`: complete original evidence rows with plot theme classifications and source URLs for later synthesis.

### Interpretation limits

This is a purposively collected set of 28 observations from 19 URLs, not a systematic sample of all state DOTs. Multiple observations can originate from one document. Early ASTM C1157 field use is not equivalent to statewide ASTM C595 Type IL acceptance. Research findings and retrospective reports do not by themselves establish the causes or dates of agency approval. Figure 02 reflects what the current collection documents, not national prevalence. Source-specific limitations remain in `data/dot_decision_evidence.csv`.
