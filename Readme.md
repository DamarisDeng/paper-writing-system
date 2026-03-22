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

Each stage can be run independently via Claude Code slash command (e.g., `/load-and-profile <args>`) or as part of the full orchestrator pipeline. Stages 1-4 have full progress tracking with resume capability.

---

### Stage 1: Load and Profile Data (medium)

**Run**: `/load-and-profile <data_folder>`

**Input**: Raw data folder (CSV, XLSX, etc.)

**Logic**:
1. Read any `Data_Description.md` files for domain context
2. Inspect raw file headers to detect encoding issues, multi-row headers
3. Run profiling script to generate mechanical statistics
4. Enrich output with domain knowledge (fix misclassified types, add `data_context`)
5. Validate outputs before marking complete

**Progress Tracking**: 5 checkpoints (`step_1_read_description` → `step_5_save_final`)

**Outputs**:
- `1_data_profile/profile.json` — Dataset shapes, column statistics, data_context
- `1_data_profile/variable_types.json` — Semantic type for every column
- `1_data_profile/progress.json` — Progress state for resume

---

### Stage 2: Generate Research Questions (high)

**Run**: `/generate-research-questions <output_folder>`

**Input**: `profile.json`, `variable_types.json`

**Logic**:
1. Load inputs and extract search context (topic keywords, methodological terms)
2. Build mental model of data landscape (datasets, joins, candidates for outcome/exposure/covariates)
3. Identify strongest outcome–exposure pairings (start from outcomes, not topics)
4. Score candidates on feasibility (0.40), significance (0.20), novelty (0.25), rigor (0.15)
5. For each candidate, assign variable roles (outcome, exposure, covariates, excluded)
6. Assess feasibility (strengths, limitations, required assumptions, data acquisition needs)
7. Save and validate output (runs validation script)

**Progress Tracking**: 7 checkpoints (`step_1_load_inputs` → `step_7_save_validate`)

**Outputs**:
- `2_research_question/research_questions.json` — Candidate questions with PICO fields, variable roles, feasibility
- `2_research_question/progress.json` — Progress state for resume

---

### Stage 3: Acquire Data (low)

**Run**: `/acquire-data <output_folder>`

**Input**: `research_questions.json` → `data_acquisition_requirements`

**Logic**:
1. Load research questions and extract data acquisition requirements
2. Create download directory
3. For each requirement: try primary URLs, then parse archive links, then fallback to known sources (NYTimes COVID, JHU CSSE)
4. Download and process (parse data, subset to study period, validate columns)
5. Handle failures gracefully (404→fallback, timeout→retry, parse errors→try delimiters)
6. Verify and document each download (file size, row count, date range, source used)
7. Report summary with warnings

**Progress Tracking**: 5 checkpoints (`step_1_load_requirements` → `step_5_report_summary`)

**Outputs**:
- `2_research_question/downloaded/*.csv` — Downloaded data files
- `2_research_question/downloaded/README.md` — Source documentation
- `2_research_question/progress.json` — Progress state (shared with Stage 2)

---

### Stage 4: Statistical Analysis (medium)

**Run**: `/statistical-analysis <output_folder>`

**Input**: Profile, research questions, raw data, downloaded data

**Logic**:
1. Load all inputs and copy helper modules (utils.py, data_utils.py, descriptive.py, validation.py)
2. Prepare analytic dataset (load/merge, create derived variables, document missingness, apply exclusions)
3. Generate descriptive statistics (Table 1 with means/SDs or medians/IQRs, p-values, SMDs)
4. Write analysis plan (model selection decision tree → primary method, covariates, sensitivity strategy)
5. Run primary analysis (call method-specific helper: regression.py, penalized.py, ml.py, or causal.py)
6. Run assumption checks (linearity, homoscedasticity, PH test, overlap/positivity)
7. Run sensitivity analyses (subgroup, alternative covariates, robustness to missing data)
8. Compile and validate results (sanitize p-values, validate schema)

**Progress Tracking**: 7 checkpoints (`step_1_load_inputs` → `step_6_compile`)

**Resume Protocol**: Read `progress.json` → continue from next incomplete step

**Outputs**:
- `3_analysis/analytic_dataset.csv` — Cleaned, merged dataset
- `3_analysis/analysis_results.json` — All statistical results
- `3_analysis/analysis_plan.json` — Model selection reasoning
- `3_analysis/results_summary.md` — Prose summary for paper
- `3_analysis/scripts/` — Python scripts used
- `3_analysis/progress.json` — Progress state for resume

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
