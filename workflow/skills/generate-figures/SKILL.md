---
name: generate-figures
model: medium
description: >
  Generate publication-quality JAMA-style figures and LaTeX tables from
  analysis_results.json. Produces at least 2 figures (.png + .pdf) and
  1 table (.tex). Uses colorblind-safe palettes, golden-ratio dimensions,
  and JAMA formatting standards.
  Triggers on: "generate figures", "create tables", "make plots",
  "publication figures", "visualize analysis results".
argument-hint: <output_folder>
---

# Generate Figures and Tables

Create publication-quality JAMA Network Open-style figures and tables from statistical analysis results.

## Usage

```
/generate-figures <output_folder>
```

Reads from `<output_folder>/3_analysis/analysis_results.json` and `<output_folder>/2_scoring/ranked_questions.json`. Writes to `<output_folder>/4_figures/`.

## Progress Tracking

Uses `progress_utils.py` for stage-level progress tracking. Progress saved to `<output_folder>/4_figures/progress.json`.

**Steps tracked:**
- `step_1_load_inputs`: Load analysis results and research questions
- `step_2_setup_style`: Import jama_style.py for publication styling
- `step_3_table1`: Generate Table 1 (baseline characteristics)
- `step_4_primary_figure`: Generate primary results figure
- `step_5_additional_figures`: Generate additional figures
- `step_6_additional_tables`: Generate additional tables
- `step_7_manifest`: Create figure/table manifest
- `step_8_validate`: Validate publication quality standards

## Instructions

Initialize progress tracker at start:
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker

tracker = create_stage_tracker(output_folder, "generate_figures",
    ["step_1_load_inputs", "step_2_setup_style", "step_3_table1",
     "step_4_primary_figure", "step_5_additional_figures",
     "step_6_additional_tables", "step_7_manifest", "step_8_validate"])
```

### Step 1: Load Inputs

Read `<output_folder>/3_analysis/analysis_results.json` for statistical results, `<output_folder>/2_scoring/ranked_questions.json` for variable context, and `<output_folder>/3_analysis/analytic_dataset.csv` if raw data is needed for plots.

### Step 2: Import Style Module

Copy and import `workflow/skills/generate-figures/scripts/jama_style.py` to your output folder. This module provides:

- `get_colors(n)` — Colorblind-safe Okabe-Ito palette
- `create_figure(width_type, nrows, ncols)` — Golden-ratio dimensions
- `add_subplot_labels(axes)` — Panel labels (A, B, C...)
- `add_reference_line(ax)` — Null value reference lines
- `save_figure(fig, path)` — Multi-format export (PNG, PDF)

### Step 3: Generate Table 1 (Required)

Use `scripts/template_table1.tex` as a starting point. Key requirements:

- Continuous normal: mean (SD); Continuous skewed: median (IQR)
- Categorical: N (%) with % from column n, not total
- P-values: exact if ≥0.001, otherwise `<0.001`
- Include units in row headers, not data cells
- Define all abbreviations in footnotes

Save as `<output_folder>/4_figures/tables/table1.tex`.

### Step 4: Generate Primary Results Figure (Required)

Select appropriate visualization based on analysis type:

| Analysis Type | Recommended Figure | Template |
|--------------|-------------------|----------|
| Logistic/Cox regression | Forest plot | `template_forest.py` |
| Linear regression | Coefficient plot | `template_forest.py` |
| Survival analysis | Kaplan-Meier curve | `template_km.py` |
| Continuous outcome | Scatter + regression | `template_scatter.py` |
| Correlation matrix | Heatmap | `template_heatmap.py` |
| Multi-panel | Combined figure | `template_multipanel.py` |

Copy the relevant template to `<output_folder>/4_figures/scripts/`, modify the data section, and run it.

### Step 5: Generate Additional Figures

Create at least 1 more figure using any template. Consider:

- Subgroup forest plot (`template_forest.py`)
- Distribution plot (histogram/density)
- Sensitivity analysis comparison
- Dose-response curve

### Step 6: Generate Additional Tables

As needed: regression results table, sensitivity analysis, or full model output.

### Step 7: Create Manifest

Save `<output_folder>/4_figures/manifest.json`:

```json
{
  "figures": [{"id": "figure1", "title": "...", "files": {"png": "...", "pdf": "..."}}],
  "tables": [{"id": "table1", "title": "...", "file": "..."}]
}
```

### Step 8: Validate Checklist

**File Existence:**
- [ ] ≥2 figure files exist in `4_figures/figures/` (both .png and .pdf for each)
- [ ] ≥1 table file exists in `4_figures/tables/` (.tex)
- [ ] `manifest.json` exists and lists all generated figures and tables
- [ ] `jama_style.py` was copied/created in output folder
- [ ] At least one figure script exists in `4_figures/scripts/`

**Publication Quality — Figures:**
- [ ] Uses colorblind-safe palette (Okabe-Ito)
- [ ] Colors remain distinct when converted to grayscale
- [ ] Axis labels include units in parentheses (e.g., "Age (years)")
- [ ] Error bars or confidence intervals shown for all estimates
- [ ] Reference line at null value where applicable (OR=1, β=0)
- [ ] No title text in image (titles go in LaTeX captions)
- [ ] Legend entries are descriptive (not cryptic codes)
- [ ] Fonts ≥9pt (labels), ≥8pt (tick marks) for readability
- [ ] PNG files are 300 DPI (check with `file` command or PIL)
- [ ] Panel labels (A, B, C...) present for multi-panel figures

**Publication Quality — Tables:**
- [ ] booktabs used (`\toprule`, `\midrule`, `\bottomrule`)
- [ ] No vertical lines
- [ ] Consistent decimal places within columns
- [ ] Units in row headers, not data cells
- [ ] P-values formatted correctly (exact if ≥0.001, otherwise `<0.001`)
- [ ] Abbreviations defined in footnotes

**Progress checkpoint:**
```python
from progress_utils import complete_stage
complete_stage(output_folder, "generate_figures",
               expected_outputs=["4_figures/manifest.json",
                                 "4_figures/tables/table1.tex",
                                 "4_figures/jama_style.py",
                                 "4_figures/scripts/figure1.py"])
# Note: individual .png/.pdf figure files vary by name; check manifest.json for listing
```

## Output Contract

**`4_figures/figures/`** — PNG and PDF files
**`4_figures/tables/`** — LaTeX table files
**`4_figures/scripts/`** — Python scripts that generated figures
**`4_figures/manifest.json`** — Figure/table listing
