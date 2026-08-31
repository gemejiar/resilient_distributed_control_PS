---
name: ieee-elsevier-benchmark-figures
description: Use when creating or revising manuscript figures for forecasting or benchmarking papers that should match the real style of this workspace: matplotlib plus seaborn, Times New Roman serif, compact 88 mm to 178 mm layouts, PDF plus SVG export, light dashed grids, shared top legends, and evidence-first IEEE or Elsevier benchmark visuals instead of glossy Nature or Cell-style graphics.
---

# IEEE Elsevier Benchmark Figures

## Use This Skill When

- The user wants a new figure for the benchmark paper or appendix.
- The user wants to restyle an existing plot so it matches the real figures in this repo.
- The figure should align with `experiments/eda/generate_legacy_eda_figures_v1.py` or `experiments/phase_6/generate_paper_artifacts.py`.
- The output is a reproducible manuscript artifact, not an interactive dashboard.

## Default Stack

- Use `matplotlib` and `seaborn`.
- Prefer repo scripts over notebook-only snippets.
- Do not use `plotly` unless the user explicitly asks for interactive output.

## House Style

- Font family: `Times New Roman` with serif fallback.
- Math fontset: `stix`.
- Font size:
  - `8 pt` for compact EDA panels.
  - `10 pt` for benchmark and results figures.
- Figure widths:
  - `88 mm` for compact single-column figures.
  - `100 mm` for square or near-square emphasis figures.
  - `178 mm` for double-column layouts.
- Export both `PDF` and `SVG`.
- Set `pdf.fonttype = 42`, `ps.fonttype = 42`, and `svg.fonttype = "none"`.
- Use white background, light gray dashed grids, and hide top and right spines.
- Keep legends compact. Prefer one shared legend above the plot when many series are present.
- Use semantically stable colors by target, model family, or regime. Do not force a generic palette if the existing figure family already encodes meaning consistently.

## Common Layouts In This Repo

- `3x1` stacked panels for `Load`, `Solar`, and `Wind`.
- Single square or near-square panels for trade-off figures such as Pareto plots.
- Shared legend at top center with tight margins.
- Axis labels with units in brackets or parentheses.
- Log-scale on latency or cost axes when values span multiple orders of magnitude.
- Panel captions should be sober and useful, not decorative.

## Workflow

1. Identify the claim the figure must support.
2. Inspect nearby figure scripts before inventing a new style.
3. Reuse the established visual grammar first.
4. Keep decorative elements subordinate to the data.
5. Export deterministically to the correct artifact path.
6. If the figure is manuscript-facing, check that aspect ratio and width fit the target LaTeX slot.

## Default Claim Discipline

- Every figure must support a concrete claim, comparison, or limitation.
- Prefer conservative visual emphasis over dramatic styling.
- If uncertainty bands, significance markers, or error bars are not necessary for the claim, omit them.
- Never make the figure visually imply a stronger result than the underlying benchmark supports.

## Default Output Paths

- Manuscript-facing figure derivatives: `paper/figures/`
- General derived figures: `outputs/figures/`
- Phase 6 benchmark artifacts: `outputs/phase6/results/artifacts/figures/`

If the user points to an existing figure family, preserve its path convention unless there is a clear reason to relocate the output.

## Do Not

- Do not style the figure as `Nature`, `Science`, `Cell`, or infographic-first unless the user explicitly asks.
- Do not default to sans-serif fonts.
- Do not add significance stars, confidence ribbons, or error bars by habit.
- Do not use rainbow or `jet` palettes.
- Do not write benchmark claims directly into the figure that are not already supported elsewhere.
- Do not write outputs outside `outputs/` or `paper/figures/` without a concrete reason.

## Minimal Preset

```python
import matplotlib.pyplot as plt
import seaborn as sns


def mm_to_in(mm: float) -> float:
    return mm / 25.4


def apply_ieee_elsevier_benchmark_style(font_size: int = 10) -> None:
    sns.set_theme(
        style="whitegrid",
        rc={
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "font.size": font_size,
            "axes.labelsize": font_size,
            "axes.titlesize": font_size,
            "xtick.labelsize": font_size,
            "ytick.labelsize": font_size,
            "legend.fontsize": font_size,
            "figure.titlesize": font_size,
            "mathtext.fontset": "stix",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.grid": True,
            "grid.linestyle": "--",
            "grid.linewidth": 0.45,
            "grid.alpha": 0.45,
        },
    )
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "mathtext.fontset": "stix",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def clean_axes(ax) -> None:
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
```

## Trigger Phrases

- `haz una figura para el paper`
- `ajusta esta figura al estilo del benchmark`
- `genera una figura Q1 para resultados`
- `restila este plot para que se parezca a las figuras reales del repo`
