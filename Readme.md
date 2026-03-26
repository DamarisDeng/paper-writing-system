# Automated JAMA Network Open Paper Generation Pipeline

An end-to-end automated research workflow that generates a publication-ready JAMA Network Open-style paper from any public health dataset. Triggered by a single prompt, Claude Code executes all stages autonomously with zero human intervention.

Tutorial of building a research automation pipeline can be found [here](https://damarisdeng.github.io/blog/2026-03-24-research-workflow-tutorial/). A video version of the tutorial can be found [here](https://youtu.be/4lOvvX4AVuE).

## Prerequisites

Before running this pipeline, ensure you have the following installed:

| Requirement | Installation |
|-------------|--------------|
| **Node.js / npm** | [Download from nodejs.org](https://nodejs.org/) or use `brew install node` (macOS) |
| **Claude Code** | [Install via npm](https://claude.ai/claude-code): `npm install -g @anthropic-ai/claude-code` |
| **Python 3.12** | [Download from python.org](https://www.python.org/downloads/) or use `brew install python3` (macOS) |
| **Python packages** | `pip install pandas statsmodels scipy scikit-learn matplotlib openpyxl` |
| **LaTeX** | [Download MiKTeX](https://miktex.org/download) or [MacTeX](https://www.tug.org/mactex/) (macOS) |
| **ppt-creator skill** | Installed automatically by Claude Code; or install manually: `/skill-creator:skill-clone ppt-creator` |
| **Marp CLI** *(optional)* | For exporting slides to PDF/PPTX: `npm install -g @marp-team/marp-cli` |

## Quick Start

Place your data in a folder (e.g., `exam_folder_sample/data/`), then enter this prompt in claude code:

```
write a paper using data in exam_folder_sample/data/, all output (intermediate and final) should be placed inside exam_paper/
```

That's it. The pipeline will autonomously execute all stages (including an initial Stage 0 for data acquisition) and produce a final `exam_paper/paper.pdf`.

> **Note**: Model level mappings are automatically configured by Claude Code. See `.claude/CLAUDE.md` for details.

---

## Tutorial

For a deep technical dive into research workflow design, including implementation details on progress tracking, token management, validation patterns, and real bug fixes, see [tutorial.md](tutorial.md).

---

## Feasibility-First Approach

This pipeline uses a **feasibility-first** approach to avoid wasting time on infeasible research questions:

1. **Stage 2** generates candidate questions and runs a **rigorous feasibility check**:
   - Control groups: At least 2 exposure groups with adequate N
   - Outcome data: Outcome exists or can be downloaded
   - Sample size: Meets minimum for study design (≥20 cross-sectional, ≥50 DiD)
   - Design match: Required data structure exists
   - Variable availability: All critical variables present

2. Candidates are marked as `feasible` or `infeasible` with specific reasons

3. **Stage 3** only performs expensive literature searches on **feasible candidates**

4. If NO feasible candidates exist, the pipeline fails early with clear error

This prevents wasting computational resources on literature searches and analysis for questions that cannot be answered with the available data.

---

## Pipeline Steps

Each stage can be run independently via Claude Code slash command (e.g., `/load-and-profile <args>`) or as part of the full orchestrator pipeline. All stages have full progress tracking with resume capability.

### Stage 0: Acquire Documented Data (Pre-Processing)

**Run**: Automatically by orchestrator (before Stage 1)

**Purpose**: Download datasets documented in `Data_Description.md` before profiling

**Logic**:
1. Orchestrator reads `Data_Description.md` from data folder
2. Builds download manifest from documented datasets with URLs
3. Calls acquire-data skill with manifest
4. Downloads to `<output_folder>/data/<target_dir>/`

**Outputs**:
- `0_data_acquisition/manifest.json` — Download manifest
- `0_data_acquisition/download_report.json` — Download results
- `data/<target_dir>/*` — Downloaded datasets
- `data/README.md` — File documentation

**Note**: This step ensures all documented datasets are available before profiling, so the question generator sees the full data landscape.

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
4. **RIGOROUS FEASIBILITY VALIDATION** (Step 3b):
   - Checks control groups (at least 2 exposure groups with adequate N)
   - Checks outcome data availability (exists or can be downloaded)
   - Checks sample size (≥20 cross-sectional, ≥50 DiD/longitudinal)
   - Checks study design match (required data structure exists)
   - Checks variable availability (all critical variables in data)
5. Mark candidates as `feasible` or `infeasible` with reasons
6. Score only **feasible** candidates on feasibility (0.40), significance (0.20), novelty (0.25), rigor (0.15)
7. For each candidate, assign variable roles (outcome, exposure, covariates, excluded)
8. Assess feasibility (strengths, limitations, required assumptions, data acquisition needs)
9. Save and validate output (runs validation script)

**Progress Tracking**: 7 checkpoints (`step_1_load_inputs` → `step_7_save_validate`)

**Outputs**:
- `2_research_question/research_questions.json` — Candidate questions with **status** field (`feasible`/`infeasible`), PICO fields, variable roles, feasibility
- `2_research_question/progress.json` — Progress state for resume

**Key Feature**: Infeasible candidates are rejected BEFORE expensive literature searches in Stage 3, saving time and computational resources.

---

### Stage 3: Score and Rank Research Questions (medium)

**Run**: `/score-and-rank <output_folder>`

**Input**: `research_questions.json` (Stage 2 output), `cycle_state.json` (if in feedback loop)

**Logic**:
1. Load candidates and filter to **only `status: "feasible"`** candidates
2. **Literature Search** (skip in fast-track mode):
   - For each feasible candidate, search for novelty (few existing studies) and support (plausible mechanism)
   - Record results for fast-track reuse
3. Compute composite scores: `0.40 * data_feasibility + 0.25 * novelty + 0.20 * support + 0.15 * rigor`
4. **Apply feedback penalties** (if in feedback loop): set failed candidates to score 0.0
5. Select top candidate and save `ranked_questions.json` (backward-compatible format)
6. Validate output

**Progress Tracking**: 6 checkpoints (`step_1_load_inputs` → `step_6_validate`)

**Early Termination**: If NO feasible candidates exist, stage fails immediately with clear error rather than wasting time on literature searches.

**Outputs**:
- `2_scoring/ranked_questions.json` — Selected question with `selection_metadata`
- `2_scoring/scoring_details.json` — Full scoring details for audit trail
- `2_scoring/progress.json` — Progress state for resume

---

### Stage 4: Acquire Supplementary Data (low)

**Run**: `/acquire-data <output_folder> <manifest_path>`

**Input**: Orchestrator builds manifest from `data_acquisition_requirements` in `ranked_questions.json`

**Logic** (manifest-driven, stateless downloader):
1. Read manifest JSON (array of download entries with name, target_dir, downloads[])
2. Check what's already on disk (idempotent)
3. Download missing files, extract archives, retry on failure
4. Verify against verify_patterns, skip skip_patterns
5. Write data/README.md documenting each file
6. Write download report JSON

**Progress Tracking**: 5 checkpoints (`step_1_read_manifest` → `step_5_document`)

**Outputs**:
- `data/<target_dir>/*.csv` — Downloaded data files (same location as Stage 0)
- `data/README.md` — Documentation of all acquired files
- `2_research_question/download_report.json` — Download summary

**Note**: acquire-data is used twice in the pipeline:
- **Stage 0**: Orchestrator builds manifest from Data_Description.md → downloads base datasets
- **Stage 4**: Orchestrator builds manifest from data_acquisition_requirements → downloads supplementary data

---

### Stage 5: Statistical Analysis (medium)

**Run**: `/statistical-analysis <output_folder>`

**Input**: Profile, ranked_questions.json, raw data, downloaded data

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

**Feedback Loop**: If critical failures detected (non-convergence, separation, violated assumptions), triggers re-ranking from Stage 3.

---

### Stage 6: Generate Figures and Tables (medium)

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

### Stage 7: Literature Review (low)

**Input**: `ranked_questions.json` (selected question)

**What it does**:
- Searches for references across 4 categories: similar studies, methodology, clinical/policy context, data sources
- Formats entries as BibTeX
- Falls back to foundational references if needed

**Outputs**:
- `5_references/references.bib` — Bibliography with ≥10 entries
- `5_references/search_log.json` — Search process documentation

---

### Stage 8: Write Paper (high)

**Run**: `/write-paper <output_folder>`

**Input**: `ranked_questions.json`, `analysis_results.json`, `manifest.json`, `references.bib`, `profile.json`, `template.tex`, `decision_log.json` (optional)

**Logic**:
1. Load all upstream outputs (research questions, analysis results, figure manifest, references, data profile, decision log)
2. Copy assets to `6_paper/` — figures (`.png`, `.pdf`), tables (`.tex`), and `references.bib`
3. Generate LaTeX paper skeleton from template with boilerplate pre-filled (preamble, colors, styles, metadata, section structure)
4. Draft complete paper content — structured abstract (7 subsections), Key Points box, Introduction (3–5 paragraphs), Methods (Data, Outcomes, Exposure, Covariates, Statistical Analysis), Results (sample description, primary analysis, sensitivity analyses), Discussion (4–6 paragraphs with Limitations subsection), Conclusions
5. Integrate figures (`\includegraphics`), tables (`\input`), and citations (`\cite`) with paths validated against copied assets
6. Add Supplement (eAppendix, eTables, eFigures) with detailed model specifications
7. Validate completeness — balanced LaTeX braces, all 7 abstract subsections present, Key Points filled, no placeholder text, citation keys match `references.bib`, figure/table paths resolve, statistical values match `analysis_results.json`

**Progress Tracking**: 4 checkpoints (`step_1_load_inputs` → `step_2_copy_assets` → `step_3_draft_paper` → `step_4_validate`)

**Helper Script**: `workflow/skills/write-paper/write_paper.py` provides `load_all_inputs()`, `copy_assets()`, `generate_paper_skeleton()`, `validate_paper_tex()`, and `format_stat()` utilities

**Outputs**:
- `6_paper/paper.tex` — Complete LaTeX source
- `6_paper/references.bib` — Bibliography copy
- `6_paper/figures/` — Figure copies (`.png` and `.pdf`)
- `6_paper/tables/` — Table copies (`.tex`)
- `6_paper/progress.json` — Progress state for resume

---

### Stage 9: Compile and Review (low)

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
│   ├── skills/                         # Pipeline stage definitions
│   │   ├── orchestrator/SKILL.md       # Master coordinator
│   │   ├── load-and-profile/            # Stage 1
│   │   ├── generate-research-questions/ # Stage 2
│   │   ├── score-and-rank/              # Stage 3 (NEW - literature-informed scoring)
│   │   ├── acquire-data/                # Stage 4 (also used in Stage 0)
│   │   ├── statistical-analysis/        # Stage 5
│   │   ├── generate-figures/            # Stage 6
│   │   ├── literature-review/           # Stage 7
│   │   ├── write-paper/                 # Stage 8
│   │   └── compile-and-review/          # Stage 9
│   ├── scripts/                         # Shared utility scripts
│   │   ├── feasibility_validator.py     # Rigorous feasibility checking (NEW)
│   │   ├── progress_utils.py            # Progress tracking across stages
│   │   └── feedback_utils.py            # Feedback loop management
│   └── templates/
│       └── template.tex                 # JAMA Network Open LaTeX template
├── exam_paper/                          # Runtime outputs
│   ├── 0_data_acquisition/              # Stage 0 (pre-profiling data acquisition)
│   │   ├── manifest.json                # Download manifest built from Data_Description.md
│   │   └── download_report.json         # Download results
│   ├── data/                            # All acquired datasets (from Stage 0 and Stage 4)
│   │   ├── HPS_PUF/                     # Example: Household Pulse Survey data
│   │   ├── covid_deaths/                # Example: Supplementary outcome data
│   │   └── README.md                    # File documentation
│   ├── 1_data_profile/
│   ├── 2_research_question/
│   │   └── downloaded/                  # Legacy: acquired external data
│   ├── 2_scoring/                      # Stage 3 outputs (NEW)
│   ├── 3_analysis/
│   ├── 4_figures/
│   ├── 5_references/
│   ├── 6_paper/
│   ├── cycle_state.json                 # Feedback loop state
│   ├── decision_log.json                # Selection audit trail
│   ├── pipeline_log.json
│   └── paper.pdf                        # FINAL DELIVERABLE
└── README.md
```

---

## Output Deliverables

| File | Description |
|------|-------------|
| `exam_paper/paper.pdf` | Final compiled paper (main deliverable) |
| `exam_paper/pipeline_log.json` | Execution log with timestamps, status, notes |
| `exam_paper/data/README.md` | All acquired datasets documentation |
| `exam_paper/6_paper/paper.tex` | LaTeX source (editable) |
| `exam_paper/3_analysis/analysis_results.json` | All statistical results |
| `exam_paper/4_figures/figures/*.png` | Publication-ready figures |
| `exam_paper/5_references/references.bib` | Bibliography |
| `exam_paper/0_data_acquisition/download_report.json` | Stage 0 download results |

---

## Requirements

- Python 3.12 with pandas, statsmodels, scipy, scikit-learn, matplotlib, openpyxl
- LaTeX distribution (pdflatex, bibtex)
- Claude Code with Opus 4.6 model access
- ppt-creator skill (for generating presentation slides after paper completion)
- Marp CLI (optional, for exporting slides to PDF/PPTX)
