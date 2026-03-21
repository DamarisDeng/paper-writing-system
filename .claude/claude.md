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

## Trigger Prompt

When the user says anything like:
- "Write a paper using the data in the folder"
- "Run the pipeline"
- "Generate paper"

Execute the orchestrator skill which runs stages 1–8 in sequence.

## Setup: Model Mapping Configuration

**IMPORTANT**: Before running the pipeline, ensure `~/.claude/settings.json` has the model level mappings. If not present, add them:

```json
{
  "modelLevels": {
    "high": "opus[1m]",
    "medium": "sonnet",
    "low": "haiku"
  }
}
```

Each skill specifies its required model level in its SKILL.md frontmatter (`model: high|medium|low`). The orchestrator uses this mapping to select the appropriate model for each stage:

| Stage | Model Level | Model | Rationale |
|-------|-------------|-------|-----------|
| 1. Load & Profile | medium | sonnet | Data inspection, profiling |
| 2. Research Questions | high | opus[1m] | Deep reasoning for PICO formulation |
| 3. Acquire Data | low | haiku | Simple downloads |
| 4. Statistical Analysis | medium | sonnet | Code generation, models |
| 5. Generate Figures | medium | sonnet | Visualization code |
| 6. Literature Review | low | haiku | Search and format |
| 7. Write Paper | high | opus[1m] | Complex synthesis and writing |
| 8. Compile & Review | low | haiku | Compilation, error handling |

## Other

During execution of the pipeline, do not modify `workflow/`, direct all output to `exam_paper/`.
