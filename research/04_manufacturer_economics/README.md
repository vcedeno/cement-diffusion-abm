# 04 — Manufacturer economics and investment

This module contains source-linked observations about PLC manufacturer motivations and related cement investments. The current CSV has 12 observations; **it is not a completed 100-plant systematic search**. No source-verbatim quotes have been verified in the CSV (`exact_quote` is empty), so the timeline uses clearly labeled paraphrased evidence summaries rather than fabricated quotations.

## Reproduce (from repository root)

```bash
python research/04_manufacturer_economics/scripts/plot_manufacturer_economics.py \
  --csv research/04_manufacturer_economics/data/manufacturer_economics_evidence.csv \
  --outdir research/04_manufacturer_economics/figures
```

## Figures

- `plc_manufacturer_motivations_timeline.png`: PLC-specific manufacturer source statements by publication year, with paraphrased summaries; excludes industry-wide retrospective evidence.
- `plc_manufacturer_economic_mechanisms.png`: frequency of primary coded themes across PLC-specific manufacturer observations. Not a measure of prevalence among 100 plants, nor of causation.

Source titles and original URLs are in the CSV. `plc_specific=no` entries are related cement-industry investments and are excluded from PLC-specific figures. Source publication dates must not be confused with investment or PLC availability dates. A separate Module 01 audit contains PLC availability evidence.
