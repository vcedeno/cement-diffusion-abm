# Module 07 — External signals (research inventory)

## Scope and limitations
This is a **documented event inventory**, not an exhaustive search or a causal model. It includes **32 events** (29 carried over, 3 new source-verified additions). Events labeled `previously_recorded_not_reverified_this_pass` were inherited from the prior collection and **have not been independently reverified in this update**. Dates may be publication dates rather than underlying event dates. The five category files are subsets of `external_signals_master.csv`.

## Publication analysis
Existing OpenAlex files are preserved without alteration. Raw hits are not counts of verified PLC/LC3 research, and title triage is not abstract screening. Do not infer that LC3 has more published research from raw search hits.

## Figure
`figures/03_external_signals_timeline.png` displays dated evidence events with IDs matching the master CSV. The 2020–2022 shading is contextual and does not establish causality. The other two publication figures remain preliminary.

Reproduce from repository root:
```bash
python research/07_external_signals/scripts/plot_external_signals_timeline.py --input research/07_external_signals/data/external_signals_master.csv --output research/07_external_signals/figures/03_external_signals_timeline.png
```

## Newly source-verified records
- ES030 (2011): FHWA TechBrief on blended/performance cements including PLC.
- ES031 (2021): PCA released PLC-specific industry-wide EPD.
- ES032 (2023 revision): PCA PLC EPD describes an inventory sample from 15 plants; **not** national production.

## Still not established
An exhaustive national historical external-signal search; a full cross-module deduplication against Modules 01–06; abstract-level bibliometric screening; a PLC-only national production series; causal effects of individual policies. These cannot be represented as completed.
