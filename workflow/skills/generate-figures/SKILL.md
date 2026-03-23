---
name: generate-figures
model: medium
description: >
  Generate publication-quality JAMA-style figures and LaTeX tables from
  analysis_results.json. Produces at least 2 figures (.png) and
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
- `save_figure(fig, path)` — PNG export (300 DPI)

### Step 3: Generate Table 1 (Required)

Use `scripts/template_table1.tex` as a starting point.

See `references/REFERENCE.md: JAMA Style Guide` and `Figure Types` for complete Table 1 requirements and visualization templates.

### Step 4-6: Generate Additional Figures and Tables

Select appropriate visualization based on analysis type.

See `references/REFERENCE.md: Figure Types` for the complete template mapping table.

### Step 7: Create Manifest

Save `<output_folder>/4_figures/manifest.json` with figures and tables listings.

### Step 8: Validate Checklist

See `references/REFERENCE.md: Publication Quality Checklist` for the complete validation checklist.

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

**`4_figures/figures/`** — PNG files
**`4_figures/tables/`** — LaTeX table files
**`4_figures/scripts/`** — Python scripts that generated figures
**`4_figures/manifest.json`** — Figure/table listing
