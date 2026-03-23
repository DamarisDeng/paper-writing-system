# Reference: Generate Figures

## Table of Contents

1. [JAMA Style Guide](#jama-style-guide)
2. [Figure Types](#figure-types)
3. [Publication Quality Checklist](#publication-quality-checklist)

---

## JAMA Style Guide

The `jama_style.py` module provides:

- `get_colors(n)` — Colorblind-safe Okabe-Ito palette
- `create_figure(width_type, nrows, ncols)` — Golden-ratio dimensions
- `add_subplot_labels(axes)` — Panel labels (A, B, C...)
- `add_reference_line(ax)` — Null value reference lines
- `save_figure(fig, path)` — PNG export (300 DPI)

### Colorblind-Safe Palette

Always use `get_colors(n)` for color selection. Do not use default matplotlib colors (blue, orange, red) which are not colorblind-safe.

### Golden-Ratio Dimensions

Figures use golden-ratio (φ = 1.618) for aesthetically pleasing proportions. Single-panel figures default to 7" width × 4.33" height.

### Reference Lines

Add null reference lines at:
- OR = 1 for odds ratios
- β = 0 for regression coefficients
- HR = 1 for hazard ratios

---

## Figure Types

| Analysis Type | Recommended Figure | Template |
|--------------|-------------------|----------|
| Logistic/Cox regression | Forest plot | `template_forest.py` |
| Linear regression | Coefficient plot | `template_forest.py` |
| Survival analysis | Kaplan-Meier curve | `template_km.py` |
| Continuous outcome | Scatter + regression | `template_scatter.py` |
| Correlation matrix | Heatmap | `template_heatmap.py` |
| Multi-panel | Combined figure | `template_multipanel.py` |

### Table 1 Requirements

- Continuous normal: mean (SD); Continuous skewed: median (IQR)
- Categorical: N (%) with % from column n, not total
- P-values: exact if ≥0.001, otherwise `<0.001`
- Include units in row headers, not data cells
- Define all abbreviations in footnotes

---

## Publication Quality Checklist

### Figures

- [ ] Uses colorblind-safe palette (Okabe-Ito)
- [ ] Colors remain distinct when converted to grayscale
- [ ] Axis labels include units in parentheses (e.g., "Age (years)")
- [ ] Error bars or confidence intervals shown for all estimates
- [ ] Reference line at null value where applicable (OR=1, β=0)
- [ ] No title text in image (titles go in LaTeX captions)
- [ ] Legend entries are descriptive (not cryptic codes)
- [ ] Fonts ≥9pt (labels), ≥8pt (tick marks)
- [ ] PNG files are 300 DPI
- [ ] Panel labels (A, B, C...) present for multi-panel figures

### Tables

- [ ] booktabs used (`\toprule`, `\midrule`, `\bottomrule`)
- [ ] No vertical lines
- [ ] Consistent decimal places within columns
- [ ] Units in row headers, not data cells
- [ ] P-values formatted correctly (exact if ≥0.001, otherwise `<0.001`)
- [ ] Abbreviations defined in footnotes
