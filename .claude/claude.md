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
│   ├── templates/
│   │   └── template.tex       # JAMA Network Open LaTeX template
│   ├── scripts/               # Reusable Python/R scripts called by skills
│   │   ├── progress_utils.py  # Stage progress tracking, cycle state management
│   │   ├── feedback_utils.py  # Feedback signal detection, decision logging
│   │   └── ...
│   └── references/
│       └── base_references.bib  # Pre-loaded common public health references (optional)
├── exam_paper/                # ALL runtime outputs for a specific dataset run
│   ├── 1_data_profile/        # Stage 1 outputs
│   ├── 2_research_question/   # Stage 2 outputs (candidate questions)
│   ├── 2_scoring/             # Stage 3 outputs (ranked/selected question)
│   ├── 3_analysis/            # Stage 5 outputs
│   ├── 4_figures/             # Stage 6 outputs
│   ├── 5_references/          # Stage 7 outputs
│   ├── 6_paper/               # Stage 8 outputs
│   ├── cycle_state.json       # Feedback loop state
│   ├── decision_log.json      # Question selection audit trail
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
| 0 | acquire-data (Stage 0) | `Data_Description.md` | `exam_paper/0_data_acquisition/` + `data/` | Downloaded datasets exist, manifest.json created |
| 1 | load-and-profile | `<data_folder>/` | `exam_paper/1_data_profile/` | profile.json exists, >0 columns detected |
| 2 | generate-research-questions | `exam_paper/1_data_profile/` | `exam_paper/2_research_question/` | research_questions.json has candidate_questions array |
| 3 | score-and-rank | `exam_paper/2_research_question/` | `exam_paper/2_scoring/` | ranked_questions.json exists with scored candidate |
| 4 | acquire-data | `exam_paper/2_scoring/` | `exam_paper/2_research_question/downloaded/` | Downloaded files exist (or skip if none needed) |
| 5 | statistical-analysis | `exam_paper/1_data_profile/` + `exam_paper/2_scoring/` | `exam_paper/3_analysis/` | analysis_results.json exists with p-values, effect sizes |
| 5→3 | *(feedback loop)* | `exam_paper/3_analysis/` | Re-triggers stages 3-5 | Structural failure detected in analysis |
| 6 | generate-figures | `exam_paper/3_analysis/` | `exam_paper/4_figures/` | At least 2 figures and 1 table generated |
| 7 | literature-review | `exam_paper/2_scoring/` | `exam_paper/5_references/` | references.bib has ≥10 entries |
| 8 | write-paper | All upstream outputs + `workflow/templates/template.tex` | `exam_paper/6_paper/` | paper.tex compiles without fatal errors |
| 9 | compile-and-review | `exam_paper/6_paper/` | `exam_paper/paper.pdf` | paper.pdf exists, is ≤10 pages (excl. refs + supplement) |

### Feedback Loop

After Stage 5 (statistical-analysis), the orchestrator checks for structural analysis failures (non-convergence, complete separation, violated assumptions, insufficient N). If critical issues are found and the cycle limit (2) has not been reached:

1. The failed candidate is penalized (score set to 0)
2. Stages 3-5 are re-run in **fast-track mode** (no web searches, primary model + Table 1 only)
3. The decision is logged in `decision_log.json`
4. Maximum 2 total cycles (1 original + 1 retry)

## Progress Tracking Requirements

**MANDATORY**: Every stage skill MUST implement progress tracking using `workflow/scripts/progress_utils.py`.

### When Developing or Modifying a Skill

1. **Track every step** with `update_step()`:
   - Call `update_step(output_folder, stage_name, step_id, "completed")` immediately after each step finishes
   - Include the `outputs` parameter when a step produces files
   - Never leave a step without a progress checkpoint

2. **Validate outputs** before marking stage complete:
   - Call `complete_stage(output_folder, stage_name, expected_outputs=[...])` at stage end
   - List ALL required output files in `expected_outputs`
   - The stage will NOT be marked complete if any expected file is missing
   - Empty files generate a warning but still allow completion

3. **Use the standard pattern**:
   ```python
   import sys; sys.path.insert(0, "workflow/scripts")
   from progress_utils import create_stage_tracker, update_step, complete_stage

   # At stage start
   tracker = create_stage_tracker(output_folder, "stage_name", ["step_1", "step_2", ...])

   # After each step completes
   update_step(output_folder, "stage_name", "step_1", "completed",
               outputs=["path/to/output1.json"])

   # At stage end - validates outputs before marking complete
   complete_stage(output_folder, "stage_name",
                  expected_outputs=["stage_folder/output1.json",
                                    "stage_folder/output2.json"])
   ```

### Progress Files

Each stage creates a `progress.json` in its output folder:
- `1_data_profile/progress.json`
- `2_research_question/progress.json`
- `2_scoring/progress.json`
- `3_analysis/progress.json`
- `4_figures/progress.json`
- `5_references/progress.json`
- `6_paper/progress.json`

The orchestrator reads these files to determine resume points and overall pipeline status.

### Resume Protocol

If a stage is interrupted, read `progress.json` to find the last completed step and continue from the next incomplete step. Never re-run a completed step.

For the feedback loop, `cycle_state.json` tracks which cycle we're on. If `current_cycle > 1`, stages 3-5 run in fast-track mode. Use `reset_stage_progress()` to clear progress before re-running a stage.

## Trigger Prompt

When the user says anything like:
- "Write a paper using the data in the folder"
- "Run the pipeline"
- "Generate paper"

Execute the orchestrator skill which runs stages 0–9 in sequence (with potential feedback loop between 5→3).

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
| 0. Acquire Documented Data | low | haiku | Simple downloads from documented sources |
| 1. Load & Profile | medium | sonnet | Data inspection, profiling |
| 2. Research Questions | high | opus[1m] | Deep reasoning for PICO formulation |
| 3. Score & Rank | medium | sonnet | Literature search + scoring |
| 4. Acquire Data | low | haiku | Simple downloads |
| 5. Statistical Analysis | medium | sonnet | Code generation, models |
| 6. Generate Figures | medium | sonnet | Visualization code |
| 7. Literature Review | low | haiku | Search and format |
| 8. Write Paper | high | opus[1m] | Complex synthesis and writing |
| 9. Compile & Review | low | haiku | Compilation, error handling |

## Other

During execution of the pipeline, do not modify `workflow/`, direct all output to `exam_paper/`.
