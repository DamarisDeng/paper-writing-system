---
name: generate-figures
model: medium
description: >
  Generate publication-quality JAMA-style figures and LaTeX tables from
  analysis_results.json. Produces at least 2 figures (.png + .pdf) and
  1 table (.tex). Follows JAMA visual style: grayscale-friendly, ≥300 DPI,
  clean minimal design with booktabs tables.
  Triggers on: "generate figures", "create tables", "make plots",
  "publication figures", or any request to visualize analysis results.
argument-hint: <output_folder>
---

# Generate Figures and Tables

Create publication-quality JAMA Network Open-style figures and tables from statistical analysis results.

## Usage

```
/generate-figures <output_folder>
```

Reads from `<output_folder>/3_analysis/analysis_results.json` and `<output_folder>/2_research_question/research_questions.json`. Writes to `<output_folder>/4_figures/`.

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/4_figures/progress.json`.

**Steps tracked:**
- `step_1_load_inputs`: Load analysis results and research questions
- `step_2_setup_style`: Create JAMA matplotlib style configuration
- `step_3_table1`: Generate Table 1 (baseline characteristics)
- `step_4_primary_figure`: Generate primary results figure
- `step_5_additional_figures`: Generate additional figures
- `step_6_additional_tables`: Generate additional tables
- `step_7_manifest`: Create figure/table manifest

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

## Instructions

You are a data visualization specialist producing figures for a JAMA Network Open paper. Every visual must be clean, informative, and publication-ready.

**Initialize progress tracker at start:**
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker

tracker = create_stage_tracker(output_folder, "generate_figures",
    ["step_1_load_inputs", "step_2_setup_style", "step_3_table1",
     "step_4_primary_figure", "step_5_additional_figures",
     "step_6_additional_tables", "step_7_manifest"])
```

### Step 1: Load Inputs

1. Read `<output_folder>/3_analysis/analysis_results.json` for all statistical results.
2. Read `<output_folder>/2_research_question/research_questions.json` for variable context and study design.
3. Read `<output_folder>/3_analysis/analytic_dataset.csv` if raw data is needed for plots.

### Step 2: Set Up JAMA Matplotlib Style

Create a style setup script (`<output_folder>/4_figures/jama_style.py`) that all figure scripts import:

```python
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# JAMA Network Open color palette
JAMA_COLORS = {
    'crimson': '#AF1E37',
    'dark_gray': '#323232',
    'medium_gray': '#5A5A5A',
    'light_gray': '#C8C8C8',
    'gold': '#C39B32',
    'blue_accent': '#2E5A88',
    'green_accent': '#2E7D32',
}

# Ordered palette for multi-group plots (grayscale-friendly)
JAMA_PALETTE = ['#AF1E37', '#2E5A88', '#5A5A5A', '#C39B32', '#2E7D32', '#C8C8C8']

def set_jama_style():
    """Apply JAMA Network Open visual style to matplotlib."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
        'font.size': 9,
        'axes.titlesize': 11,
        'axes.titleweight': 'bold',
        'axes.labelsize': 9,
        'axes.labelweight': 'bold',
        'axes.linewidth': 0.8,
        'axes.edgecolor': '#323232',
        'axes.labelcolor': '#323232',
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'xtick.color': '#5A5A5A',
        'ytick.color': '#5A5A5A',
        'legend.fontsize': 8,
        'legend.frameon': False,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5,
    })
    mpl.rcParams['pdf.fonttype'] = 42  # Editable text in PDF
    mpl.rcParams['ps.fonttype'] = 42

def save_figure(fig, filepath_stem):
    """Save figure as both PNG (300 DPI) and PDF."""
    fig.savefig(f"{filepath_stem}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{filepath_stem}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {filepath_stem}.png and {filepath_stem}.pdf")
```

### Step 3: Generate Table 1 (Required)

Create `<output_folder>/4_figures/tables/table1.tex` — baseline characteristics table.

Use the JAMA table style from the template (booktabs, no vertical rules, `tabularx`):

```latex
\begin{table}[H]
\centering
\sffamily\fontsize{8.5}{11}\selectfont
\captionsetup{font={small,sf,bf}, textfont={normalfont,sf,color=jamadarkgray}}
\caption{Baseline Characteristics of Study Participants}
\label{tab:baseline}

\begin{tabularx}{\textwidth}{@{} >{\raggedright\arraybackslash}p{4cm}
  >{\centering\arraybackslash}X
  >{\centering\arraybackslash}X
  >{\centering\arraybackslash}X @{}}

\arrayrulecolor{jamadarkgray}
\toprule[0.8pt]
\textbf{Characteristic} & \textbf{Overall (N=...)} & \textbf{Group 1 (n=...)} & \textbf{Group 2 (n=...)} \\
\midrule[0.5pt]
% Rows here...
\bottomrule[0.8pt]
\end{tabularx}
\end{table}
```

Rules for Table 1:
- Continuous variables: report as mean (SD) or median (IQR)
- Categorical variables: report as N (%)
- Include p-values in last column if comparing groups
- Use `\,` for thousands separators (e.g., `31\,142`)
- Footnotes for abbreviations and data notes

### Step 4: Generate Primary Results Figure (Required)

Choose the most appropriate visualization for the primary analysis:

| Analysis Type | Recommended Figure |
|--------------|-------------------|
| Logistic/Cox regression | Forest plot of ORs/HRs with 95% CIs |
| Linear regression | Coefficient plot or adjusted means bar chart |
| Difference-in-differences | Parallel trends plot (pre/post by group) |
| Time series | Line plot with confidence bands |
| Subgroup analysis | Forest plot with subgroup estimates |

Write a script (`<output_folder>/4_figures/scripts/figure1.py`) to generate the figure.

Figure requirements:
- **Title**: Descriptive, placed below figure via LaTeX `\caption{}` (not in the image)
- **Axes**: Clear labels with units. No unnecessary gridlines.
- **Legend**: Outside plot area or in least-cluttered corner. No box.
- **Error bars/CIs**: Always show uncertainty.
- **Reference line**: Include null value line (OR=1, β=0) where applicable.
- **Size**: Width 6-7 inches (single column) or 3.2-3.4 inches (half column). Height proportional.
- **Format**: Save as both `.png` (300 DPI) and `.pdf`.

### Step 5: Generate Additional Figures (At Least 1 More)

Create at least one additional figure from:

1. **Figure 2**: Subgroup forest plot, sensitivity analysis comparison, or dose-response curve.
2. **Figure 3**: Distribution plots (histogram, density), correlation heatmap, or geographic map.
3. **eFigure 1** (supplement): Model diagnostic plots, DAG, or study flow diagram.

Each figure gets its own script in `<output_folder>/4_figures/scripts/`.

### Step 6: Generate Additional Tables (As Needed)

Beyond Table 1, generate as applicable:

- **Table 2**: Primary regression results (estimates, CIs, p-values per covariate).
- **eTable 1** (supplement): Sensitivity analysis results, full model output, or missingness summary.

Save all tables as `.tex` files in `<output_folder>/4_figures/tables/`.

### Step 7: Create Figure/Table Manifest

Save `<output_folder>/4_figures/manifest.json`:

```json
{
  "figures": [
    {
      "id": "figure1",
      "title": "Forest Plot of Adjusted Odds Ratios for Primary Outcome",
      "files": {
        "png": "figures/figure1.png",
        "pdf": "figures/figure1.pdf"
      },
      "script": "scripts/figure1.py",
      "placement": "main_text",
      "width": "single_column"
    }
  ],
  "tables": [
    {
      "id": "table1",
      "title": "Baseline Characteristics of Study Participants",
      "file": "tables/table1.tex",
      "placement": "main_text"
    }
  ]
}
```

### Step 8: Validate

- [ ] At least 2 figure files exist in `<output_folder>/4_figures/figures/` (both `.png` and `.pdf`)
- [ ] At least 1 table file exists in `<output_folder>/4_figures/tables/` (`.tex`)
- [ ] All `.png` files are ≥300 DPI
- [ ] All `.tex` table files compile without errors (test with a minimal LaTeX document)
- [ ] `manifest.json` exists and lists all figures and tables
- [ ] Figures are legible in grayscale (check by converting to grayscale mentally)
- [ ] No figures contain a title in the image (titles go in LaTeX captions)

**Progress checkpoint - Mark stage complete:**
```python
from progress_utils import complete_stage

complete_stage(output_folder, "generate_figures",
               expected_outputs=["4_figures/manifest.json",
                                 "4_figures/tables/table1.tex"])
# Note: individual figure files are too numerous to list all; just check manifest and key files
```

## Output Contract

**`<output_folder>/4_figures/figures/`** — Figure image files:
- `figure1.png`, `figure1.pdf` (primary results)
- `figure2.png`, `figure2.pdf` (secondary/supplementary)
- Additional as needed

**`<output_folder>/4_figures/tables/`** — LaTeX table files:
- `table1.tex` (baseline characteristics — always required)
- `table2.tex` (regression results — if applicable)
- Additional as needed

**`<output_folder>/4_figures/scripts/`** — Python scripts that generated each figure.

**`<output_folder>/4_figures/jama_style.py`** — Reusable JAMA style configuration.

**`<output_folder>/4_figures/manifest.json`** — Manifest listing all generated figures and tables with metadata.
