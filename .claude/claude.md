# CLAUDE.md — Automated JAMA Network Open Paper Generation Workflow

## Project Overview

This project is an end-to-end automated research workflow that generates a JAMA Network Open–style paper from any public health dataset. The user triggers the entire pipeline with a single prompt. Claude Code executes all stages autonomously with zero human intervention.

## Directory Structure

```
repo/
├── CLAUDE.md                  # This file — project-level instructions for Claude Code
├── Readme.md                  # Project documentation, tutorial links
├── workflow/                  # GENERIC reusable assets (skills, templates, scripts)
│   ├── skills/                # Claude Code SKILL.md files (one per pipeline stage)
│   │   ├── orchestrator/
│   │   │   └── SKILL.md       # Master orchestrator — chains all stages
│   │   ├── load-and-profile/
│   │   │   └── SKILL.md       # Stage 1: data ingestion & profiling
│   │   ├── generate-research-questions/
│   │   │   └── SKILL.md       # Stage 2: PICO/PECO research question formulation
│   │   ├── acquire-data/
│   │   │   └── SKILL.md       # Stage 3: download external supporting data
│   │   ├── statistical-analysis/
│   │   │   └── SKILL.md       # Stage 4: statistical modeling & analysis
│   │   ├── generate-figures/
│   │   │   └── SKILL.md       # Stage 5: publication-quality figures & tables
│   │   ├── literature-review/
│   │   │   └── SKILL.md       # Stage 6: reference search & .bib generation
│   │   ├── write-paper/
│   │   │   └── SKILL.md       # Stage 7: LaTeX paper drafting
│   │   └── compile-and-review/
│   │       └── SKILL.md       # Stage 8: compile PDF, self-review, revise, recompile
│   ├── templates/
│   │   └── template.tex       # JAMA Network Open LaTeX template
│   ├── scripts/               # Reusable Python/R scripts called by skills
│   │   └── ...
│   └── references/
│       └── base_references.bib  # Pre-loaded common public health references (optional)
├── exam_paper/                # ALL runtime outputs for a specific dataset run
│   ├── 1_data_profile/        # Stage 1 outputs
│   │   ├── profile.json
│   │   └── variable_types.json
│   ├── 2_research_question/   # Stage 2-3 outputs
│   │   ├── research_questions.json
│   │   └── downloaded/        # External data from acquire-data
│   ├── 3_analysis/            # Stage 4 outputs
│   │   ├── analysis_results.json
│   │   ├── models/            # Saved model summaries
│   │   └── scripts/           # Analysis scripts used
│   ├── 4_figures/             # Stage 5 outputs
│   │   ├── figures/           # .png/.pdf figure files
│   │   └── tables/            # .tex or .csv formatted tables
│   ├── 5_references/          # Stage 6 outputs
│   │   └── references.bib
│   ├── 6_paper/               # Stage 7 outputs
│   │   ├── paper.tex
│   │   └── supplementary.tex  # Optional
│   └── paper.pdf              # FINAL deliverable
└── sample/                    # Provided sample data and reference paper
    ├── data/
    ├── output/
    │   └── paper.pdf
    └── tex/
        └── template.tex
```

## Pipeline Stages

Each stage has a corresponding skill in `workflow/skills/<stage>/SKILL.md`.
Stages run sequentially. Each stage reads from previous stage outputs and writes to its own numbered directory inside `exam_paper/`.

| Stage | Skill | Input | Output | Validates |
|-------|-------|-------|--------|-----------|
| 1 | load-and-profile | `<data_folder>/` | `exam_paper/1_data_profile/` | profile.json exists, >0 columns detected |
| 2 | generate-research-questions | `exam_paper/1_data_profile/` | `exam_paper/2_research_question/` | research_questions.json has PICO fields |
| 3 | acquire-data | `exam_paper/2_research_question/` | `exam_paper/2_research_question/downloaded/` | Downloaded files exist (or skip if none needed) |
| 4 | statistical-analysis | `exam_paper/1_data_profile/` + `exam_paper/2_research_question/` | `exam_paper/3_analysis/` | analysis_results.json exists with p-values, effect sizes |
| 5 | generate-figures | `exam_paper/3_analysis/` | `exam_paper/4_figures/` | At least 2 figures and 1 table generated |
| 6 | literature-review | `exam_paper/2_research_question/` | `exam_paper/5_references/` | references.bib has ≥10 entries |
| 7 | write-paper | All upstream outputs + `workflow/templates/template.tex` | `exam_paper/6_paper/` | paper.tex compiles without fatal errors |
| 8 | compile-and-review | `exam_paper/6_paper/` | `exam_paper/paper.pdf` | paper.pdf exists, is ≤10 pages (excl. refs + supplement) |

## Critical Rules for Claude Code

### Autonomy
- **NEVER ask the user a question.** Make reasonable decisions autonomously.
- If a stage fails, attempt to fix it up to 3 times before moving on with a degraded output.
- If data is ambiguous, pick the most reasonable interpretation and document the assumption in the paper's Limitations section.

### Data Handling
- Original data files are never modified. All skills read from original paths stored in `profile.json`.
- All intermediate outputs go into the appropriate `exam_paper/` subdirectory.
- All scripts used during analysis must be saved in `exam_paper/3_analysis/scripts/`.

### Statistical Analysis (Stage 4)
- Read `research_questions.json` to determine outcome, exposure, and covariates.
- Select methods based on variable types: continuous outcome → linear regression; binary outcome → logistic regression; time-to-event → Cox proportional hazards; count data → Poisson/negative binomial.
- Always include: descriptive statistics (Table 1), primary analysis, at least one sensitivity analysis.
- Report confidence intervals, p-values, and effect sizes. Use α = 0.05 unless stated otherwise.
- Use Python (pandas, statsmodels, scipy, scikit-learn) for analysis. Use lifelines for survival analysis if needed.

### Figures and Tables (Stage 5)
- Follow JAMA style: clean, minimal, grayscale-friendly, high-resolution (≥300 DPI).
- Save as both .png and .pdf.
- Every figure must have a descriptive title and clear axis labels.
- Table 1 should always be a baseline characteristics table.

### Paper Writing (Stage 7)
- Use the JAMA Network Open LaTeX template from `workflow/templates/template.tex`.
- Sections: Title, Key Points, Abstract (structured: Importance, Objective, Design/Setting/Participants, Main Outcomes, Results, Conclusions), Introduction, Methods, Results, Discussion, Limitations, Conclusions, References.
- Paper must be ≤10 pages excluding references and supplementary material.
- Write in third person, past tense for methods and results.
- Include at least one supplementary section (e.g., detailed statistical methods, additional tables).

### LaTeX Compilation (Stage 8)
- Compile with: `pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex`
- If compilation fails, read the `.log` file, fix the `.tex` source, and retry (up to 3 attempts).
- Copy final `paper.pdf` to `exam_paper/paper.pdf`.

### Time Awareness
- The entire pipeline should complete within 60 minutes to leave buffer for the 90-minute exam.
- If a stage takes too long, produce a simplified version and move on.
- Literature review should be time-boxed: spend at most 10 minutes searching.

## Trigger Prompt

When the user says anything like:
- "Write a paper using the data in the folder"
- "Run the pipeline"
- "Generate paper"

Execute the orchestrator skill which runs stages 1–8 in sequence.