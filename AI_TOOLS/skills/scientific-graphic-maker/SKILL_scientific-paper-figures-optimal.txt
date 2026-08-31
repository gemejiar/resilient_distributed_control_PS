---
name: scientific-paper-figures-optimal
description: >
  End-to-end skill for designing, generating, auditing and repairing publication-ready scientific paper figures.
  Use for Q1 journal figures, review-paper graphics, control/system plots, forecasting figures, corpus visualizations,
  taxonomy diagrams, validation ladders, Sankey/alluvial plots, timelines, heatmaps and multi-panel figures.
metadata:
  version: "1.1.0"
  intended_agents: ["Codex", "Claude Code"]
  owner_profile: "scientific research, power systems, power electronics, microgrids, control, RL, HIL"
  compatibility: "portable SKILL.md"
---

# Scientific Paper Figures — Optimal Skill

## Mission

Create figures that are scientifically meaningful, visually rigorous, reproducible, journal-compatible and directly aligned with the manuscript contribution.

This skill does not merely make attractive plots. It forces a complete figure workflow:

1. Specify the claim.
2. Validate the data.
3. Select the proper visual grammar.
4. Generate reproducible code.
5. Export publication files.
6. Audit editorial quality.
7. Produce repair instructions when needed.

## Use when

Use this skill for any task involving:

- figures for journal papers, books, theses or conference papers;
- Q1/Q2 manuscript figures;
- corpus-based review figures;
- control, power electronics, microgrid, EMS, DERMS, IBR, BESS, HIL, EMT or RL visualizations;
- forecast benchmarks, error metrics, ablation studies or sensitivity plots;
- taxonomy figures, Sankey/alluvial diagrams, validation ladders, maturity timelines or evidence maps;
- audit of existing figures;
- instructions for another AI agent to repair plotting scripts.

## Non-negotiable principles

1. The figure must answer a scientific question.
2. Every visual encoding must correspond to a defined variable.
3. Counts, percentages and scores must be traceable to data or declared manual coding.
4. Captions must state the measured construct, data scope and main insight.
5. Export must include a vector file unless the figure is intrinsically raster.
6. The script must regenerate the figure without manual editing.
7. The figure must remain readable at final publication width.
8. Do not invent data, labels, references, corpus counts, DOIs or numerical results.

## Figure specification contract

Before implementation, create or infer this contract:

```yaml
figure_id:
manuscript_section:
scientific_claim:
figure_type:
target_journal_or_template:
final_width_mm:
final_height_mm:
data_source:
required_columns:
units:
statistical_summary:
visual_encodings:
caption_message:
output_formats:
acceptance_tests:
```

If missing information is non-critical, assume defaults and record them under `assumptions`. If missing information changes the conclusion, ask only for the minimum missing data.

## Default journal presets

Use these unless the user specifies otherwise:

| Use case | Width | Font | Export |
|---|---:|---|---|
| IEEE single column | 88 mm | Times New Roman or DejaVu Serif, 8–9 pt | PDF, SVG, PNG 600 dpi |
| Elsevier single column | 90 mm | Times New Roman or DejaVu Serif, 8–10 pt | PDF, SVG, PNG 600 dpi |
| Compact review figure | 100 mm | Times New Roman or DejaVu Serif, 9–10 pt | PDF, SVG, PNG 600 dpi |
| Double column | 178 mm | Times New Roman or DejaVu Serif, 9–10 pt | PDF, SVG, PNG 600 dpi |
| Slide-derived figure for paper | 120–170 mm | Times New Roman or DejaVu Serif, 10 pt | PDF, SVG, PNG 600 dpi |

## Visual grammar selection

Choose the plot by the scientific message:

| Message | Preferred figure | Avoid |
|---|---|---|
| Temporal dynamics | time-series line, event markers, limits | 3D plots |
| Multi-method comparison | dot plot, grouped bars for few methods, critical difference plot | crowded bars |
| Corpus distribution | stacked bars, heatmap, matrix, alluvial/Sankey | pie charts |
| Taxonomy crosswalk | matrix, bipartite Sankey, alluvial | disconnected boxes |
| Validation maturity | ladder, timeline, score heatmap | decorative roadmap |
| Stability/control response | traces with operating bounds, settling/rise/overshoot markers | unscaled qualitative sketches |
| Forecast horizon behavior | horizon-wise error curve, heatmap, calibration plot | aggregate-only bars |
| Uncertainty | ribbons, confidence intervals, box/violin if sample size is clear | unlabeled error bars |
| Sensitivity | heatmap, contour, tornado plot | arbitrary color patches |

## Corpus-review figure requirements

For review papers, require:

1. Data file with one row per paper or per paper-method unit.
2. Explicit coding dictionary.
3. Scope statement:
   - full reference corpus;
   - research-paper subset;
   - anchor subset;
   - scored subset.
4. Denominator in every percentage.
5. Handling of multi-label papers.
6. Reproducible aggregation script.
7. Captions that distinguish evidence from interpretation.

Never mix `N=178`, `N=150` and `N=66` without declaring which subset each statistic uses.

## Engineering/control figure requirements

For power systems, power electronics and control figures, require:

1. Units and base values.
2. Sign convention.
3. Sampling time or simulation step.
4. Operating point and disturbance definition.
5. Controller parameters if relevant.
6. Bounds, standards or thresholds when claims depend on compliance.
7. Metrics:
   - frequency nadir, RoCoF, settling time;
   - voltage deviation and recovery;
   - THD, current ripple, overshoot;
   - SoC drift, power sharing error;
   - computational time for real-time claims.

## Code architecture

Every generated figure script must follow this structure:

```python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

FIGURE_ID = "fig_x"
OUTDIR = Path("figures")
WIDTH_MM = 100
DPI = 600

def mm_to_in(mm):
    return mm / 25.4

def load_data(path):
    ...

def validate_data(df):
    ...

def preprocess(df):
    ...

def make_figure(df):
    ...

def save_outputs(fig, outdir=OUTDIR):
    ...

def main():
    ...
    
if __name__ == "__main__":
    main()
```

## Required outputs

The agent must produce:

1. Source script.
2. Figure files:
   - `.pdf`
   - `.svg`
   - `.png`
3. `figure_spec.yaml`
4. `figure_qc_report.md`
5. Optional: `processed_data.csv` if aggregation is non-trivial.

## Style defaults

Use:

- object-oriented Matplotlib API;
- deterministic ordering of categories;
- explicit figure size in mm;
- vector text where possible;
- readable labels after downscaling;
- colorblind-safe palette;
- restrained annotations;
- legends outside dense data regions;
- SI units in labels;
- consistent notation with manuscript.

Do not use:

- arbitrary gradients;
- decorative shadows;
- 3D plots without a technical reason;
- low-resolution screenshots;
- hand-edited labels not generated by code;
- colors as the only encoding for critical categories.

## Accessibility and grayscale test

The agent must check:

1. Does the figure remain interpretable in grayscale?
2. Are categories distinguishable by markers, line styles or direct labels?
3. Is contrast sufficient?
4. Are font sizes legible at final width?
5. Is any important information encoded only by color?

## Caption template

Use this structure:

`Figure X. [What is measured] for [data/system/corpus scope]. [How visual encodings map to variables]. [Main quantitative or structural insight]. [Important limitation or denominator if relevant].`

Example:

`Figure X. Validation maturity distribution across the scored anchor corpus. Bar height reports the number of papers per validation rung, and color encodes the presence of formal stability or safety guarantees. The distribution shows that most methods remain at offline-simulation level, while HIL/PHIL and field evidence remain exceptional within the scored subset.`

## Quality-control rubric

Score 0–3:

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Scientific message | absent | vague | clear | central to argument |
| Data traceability | none | partial | reproducible | fully versioned |
| Visual encoding | arbitrary | partially mapped | mostly correct | fully defined |
| Statistical validity | absent | weak | acceptable | rigorous |
| Technical notation | wrong/missing | incomplete | acceptable | manuscript-consistent |
| Readability | poor | marginal | acceptable | excellent |
| Accessibility | poor | partial | acceptable | colorblind/grayscale robust |
| Export quality | screenshot | raster only | vector+raster | journal-ready |
| Caption | descriptive only | partial | clear | self-contained and insightful |
| Manuscript alignment | weak | indirect | useful | necessary |

Decision:

- 27–30: publication-ready.
- 22–26: minor revision.
- 16–21: major revision.
- <16: redesign or remove.

## Acceptance tests

Before final delivery, verify:

1. Script runs without errors.
2. All output files are generated.
3. Required columns exist.
4. No NaN or infinite values reach plotting unexpectedly.
5. Axis labels include units where applicable.
6. Figure has no clipped labels.
7. Caption matches plotted data.
8. Percentages use correct denominators.
9. Output dimensions match target width.
10. QC score and remaining risks are reported.

## Agent response format

When completing a figure task, return:

1. `Verdict` or `Generated outputs`.
2. `Scientific message`.
3. `Files created or modified`.
4. `Key assumptions`.
5. `QC score`.
6. `Remaining risks`.
7. `Exact next actions`.

## Repair mode

When repairing an existing figure/script:

1. Locate the generating script.
2. Identify the current data source.
3. Rebuild the figure specification contract.
4. List contradictions or missing evidence.
5. Modify the script, not the exported image.
6. Regenerate outputs.
7. Compare before/after using the QC rubric.
8. Report exactly what changed.

## Prohibited behavior

Do not:

- invent data to make the figure look complete;
- change denominators silently;
- use manually typed numbers when data can be computed;
- generate a figure disconnected from manuscript claims;
- hide preprocessing decisions;
- overstate causal, statistical or deployment claims;
- present subjective maturity indices as objective physical measurements.
