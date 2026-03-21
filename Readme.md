# Automated JAMA Network Open Paper Generation Pipeline

An end-to-end automated research workflow that generates a publication-ready JAMA Network Open-style paper from any public health dataset. Triggered by a single prompt, Claude Code executes all stages autonomously with zero human intervention.

## Prerequisites

Before running this pipeline, ensure you have the following installed:

| Requirement | Installation |
|-------------|--------------|
| **Node.js / npm** | [Download from nodejs.org](https://nodejs.org/) or use `brew install node` (macOS) |
| **Claude Code** | [Install via npm](https://claude.ai/claude-code): `npm install -g @anthropic-ai/claude-code` |
| **Python 3.x** | [Download from python.org](https://www.python.org/downloads/) or use `brew install python3` (macOS) |
| **Python packages** | `pip install pandas statsmodels scipy scikit-learn matplotlib openpyxl` |
| **LaTeX** | [Download MiKTeX](https://miktex.org/download) or [MacTeX](https://www.tug.org/mactex/) (macOS) |

## Quick Start

Place your data in a folder (e.g., `exam_folder_sample/data/`), then enter this prompt in claude code:

```
write a paper using data in exam_folder_sample/data/, all output (intermediate and final) should be placed inside exam_paper/
```

That's it. The pipeline will autonomously execute all 8 stages and produce a final `exam_paper/paper.pdf`.

> **Note**: Model level mappings are automatically configured by Claude Code. See `.claude/CLAUDE.md` for details.

---

## Pipeline Steps

### Stage 1: Load and Profile Data (medium)

**Input**: Raw data folder (CSV, XLSX, etc.)

**What it does**:
- Reads and inspects all data files
- Generates column-level statistics (mean, SD, missingness, unique values)
- Classifies variable types (numeric, categorical, datetime, binary, identifier)
- Creates data context summary

**Outputs**:
- `1_data_profile/profile.json` — Dataset shapes, column statistics
- `1_data_profile/variable_types.json` — Semantic type for every column

---

### Stage 2: Generate Research Questions (high)

**Input**: `profile.json`, `variable_types.json`

**What it does**:
- Analyzes available variables and their relationships
- Formulates a primary PICO/PECO research question
- Identifies secondary questions
- Assigns variable roles (outcome, exposure, covariates)
- Assesses feasibility and limitations

**Outputs**:
- `2_research_question/research_questions.json` — Primary question with PICO fields, secondary questions, variable roles, feasibility assessment

---

### Stage 3: Acquire Data (low)

**Input**: `research_questions.json`

**What it does**:
- Downloads external data specified in `data_acquisition_requirements`
- Uses fallback sources if primary URLs fail
- Validates downloaded files

**Outputs**:
- `2_research_question/downloaded/` — Downloaded data files
- `2_research_question/downloaded/README.md` — Source documentation

---

### Stage 4: Statistical Analysis (medium)

**Input**: Profile, research questions, raw data, downloaded data

**What it does**:
- Prepares analytic dataset (merges, creates derived variables, handles missing data)
- Generates descriptive statistics (Table 1 data)
- Runs primary analysis (regression model based on outcome type)
- Runs sensitivity analyses
- Saves all scripts for reproducibility

**Outputs**:
- `3_analysis/analytic_dataset.csv` — Cleaned, merged dataset
- `3_analysis/analysis_results.json` — All statistical results
- `3_analysis/scripts/` — Python scripts used
- `3_analysis/models/` — Model summaries

---

### Stage 5: Generate Figures and Tables (medium)

**Input**: `analysis_results.json`, `research_questions.json`

**What it does**:
- Creates Table 1 (baseline characteristics)
- Creates primary results figure (forest plot, coefficient plot, etc.)
- Creates at least one additional figure
- Generates LaTeX tables
- All figures follow JAMA style (grayscale-friendly, ≥300 DPI)

**Outputs**:
- `4_figures/figures/*.png` and `*.pdf` — Publication-ready figures
- `4_figures/tables/*.tex` — LaTeX table files
- `4_figures/scripts/` — Python scripts that generated figures
- `4_figures/manifest.json` — Figure/table metadata

---

### Stage 6: Literature Review (low)

**Input**: `research_questions.json`

**What it does**:
- Searches for references across 4 categories: similar studies, methodology, clinical/policy context, data sources
- Formats entries as BibTeX
- Falls back to foundational references if needed

**Outputs**:
- `5_references/references.bib` — Bibliography with ≥10 entries
- `5_references/search_log.json` — Search process documentation

---

### Stage 7: Write Paper (high)

**Input**: All upstream outputs + LaTeX template

**What it does**:
- Drafts complete JAMA Network Open paper in LaTeX
- Structured abstract (7 subsections)
- Key Points box
- Introduction, Methods, Results, Discussion, Limitations, Conclusions
- Supplement with additional tables/figures
- Integrates all citations, figures, and tables

**Outputs**:
- `6_paper/paper.tex` — Complete LaTeX source
- `6_paper/references.bib` — Bibliography copy
- `6_paper/figures/` — Figure copies
- `6_paper/tables/` — Table copies

---

### Stage 8: Compile and Review (low)

**Input**: `paper.tex` and all assets

**What it does**:
- Compiles LaTeX to PDF (pdflatex + bibtex sequence)
- Fixes compilation errors (up to 3 retries)
- Runs self-review checklist
- Applies revisions if needed
- Copies final PDF to output root

**Outputs**:
- `exam_paper/paper.pdf` — **FINAL DELIVERABLE**
- `6_paper/compilation_report.json` — Compilation and review summary

---

## Directory Structure

```
repo/
├── workflow/
│   ├── skills/                    # Pipeline stage definitions
│   │   ├── orchestrator/SKILL.md  # Master coordinator
│   │   ├── load-and-profile/      # Stage 1
│   │   ├── generate-research-questions/  # Stage 2
│   │   ├── acquire-data/          # Stage 3
│   │   ├── statistical-analysis/  # Stage 4
│   │   ├── generate-figures/      # Stage 5
│   │   ├── literature-review/     # Stage 6
│   │   ├── write-paper/           # Stage 7
│   │   └── compile-and-review/    # Stage 8
│   └── templates/
│       └── template.tex           # JAMA Network Open LaTeX template
├── exam_paper/                    # Runtime outputs
│   ├── 1_data_profile/
│   ├── 2_research_question/
│   ├── 3_analysis/
│   ├── 4_figures/
│   ├── 5_references/
│   ├── 6_paper/
│   ├── pipeline_log.json
│   └── paper.pdf                  # FINAL DELIVERABLE
└── README.md
```

---

## Output Deliverables

| File | Description |
|------|-------------|
| `exam_paper/paper.pdf` | Final compiled paper (main deliverable) |
| `exam_paper/pipeline_log.json` | Execution log with timestamps, status, notes |
| `exam_paper/6_paper/paper.tex` | LaTeX source (editable) |
| `exam_paper/3_analysis/analysis_results.json` | All statistical results |
| `exam_paper/4_figures/figures/*.png` | Publication-ready figures |
| `exam_paper/5_references/references.bib` | Bibliography |

---

## Requirements

- Python 3.x with pandas, statsmodels, scipy, scikit-learn
- LaTeX distribution (pdflatex, bibtex)
- Claude Code with Opus 4.6 model access
