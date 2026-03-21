---
name: orchestrator
model: medium
description: >
  Master orchestrator that runs the full paper-generation pipeline (stages 1-8)
  sequentially. Handles initialization, stage execution with validation,
  failure retries (up to 3 per stage), graceful degradation, and time budgeting
  (60 min total). Triggers on: "run the pipeline", "generate paper",
  "write a paper using the data", or any request to execute the full workflow.
argument-hint: <data_folder> <output_folder>
---

# Orchestrator — Full Pipeline Execution

Run stages 1-8 of the JAMA Network Open paper-generation pipeline sequentially, producing a final `paper.pdf` from raw data with zero human intervention.

## Usage

```
/orchestrator <data_folder> <output_folder>
```

Where `<data_folder>` contains the raw dataset(s) and `<output_folder>` is the base output directory (e.g., `exam_paper`).

## Instructions

You are a senior research automation engineer. Your job is to execute the entire paper-generation pipeline autonomously. You must never ask the user a question — make reasonable decisions and document assumptions.

### Step 0: Initialize

1. **Create the output directory structure:**
   ```bash
   mkdir -p <output_folder>/1_data_profile
   mkdir -p <output_folder>/2_research_question/downloaded
   mkdir -p <output_folder>/3_analysis/scripts
   mkdir -p <output_folder>/3_analysis/models
   mkdir -p <output_folder>/4_figures/figures
   mkdir -p <output_folder>/4_figures/tables
   mkdir -p <output_folder>/5_references
   mkdir -p <output_folder>/6_paper
   ```

2. **Record start time** for time budgeting. The entire pipeline should target completion within 60 minutes.

3. **Create a pipeline log** at `<output_folder>/pipeline_log.json`:
   ```json
   {
     "started_at": "ISO-8601 timestamp",
     "data_folder": "<data_folder>",
     "output_folder": "<output_folder>",
     "stages": {}
   }
   ```

### Step 1: Execute Stages Sequentially

Run each stage in order. For each stage:

1. **Log stage start** in `pipeline_log.json`.
2. **Execute the stage** by following the corresponding skill instructions.
3. **Validate outputs** against the stage's output contract.
4. **On failure**: retry up to 3 times. On each retry, read error logs/messages and attempt a fix. If all 3 retries fail, produce a degraded output (documented below) and continue.
5. **Log stage completion** with status (`success`, `degraded`, `failed`), duration, and any notes.

#### Stage Execution Table

| Stage | Skill | Validation Check | Degraded Fallback |
|-------|-------|-----------------|-------------------|
| 1 | load-and-profile | `profile.json` and `variable_types.json` exist with >0 datasets | Generate minimal profile from file headers only |
| 2 | generate-research-questions | `research_questions.json` has `primary_question` with all PICO fields | Use first numeric column as outcome, first categorical as exposure |
| 3 | acquire-data | Downloaded files exist (or `data_acquisition_requirements` is empty) | Skip — proceed with available data only |
| 4 | statistical-analysis | `analysis_results.json` exists with `descriptive_statistics` and `primary_analysis` | Run descriptive stats only, skip regression |
| 5 | generate-figures | At least 2 `.png` files in `figures/` and 1 `.tex` file in `tables/` | Generate Table 1 only as a LaTeX table |
| 6 | literature-review | `references.bib` has ≥10 `@article` entries | Use 10 foundational public health references |
| 7 | write-paper | `paper.tex` exists and is >5KB | Generate a minimal paper with abstract + methods + results |
| 8 | compile-and-review | `paper.pdf` exists in `<output_folder>/` | Return the `.tex` file as final output |

### Step 2: Time Budget Management

Allocate time across stages approximately:

| Stage | Budget |
|-------|--------|
| 1. Load & Profile | 5 min |
| 2. Research Questions | 5 min |
| 3. Acquire Data | 5 min |
| 4. Statistical Analysis | 15 min |
| 5. Generate Figures | 10 min |
| 6. Literature Review | 10 min |
| 7. Write Paper | 10 min |
| 8. Compile & Review | 5 min |

If a stage exceeds its budget by 2x, produce a simplified version and move on. The goal is a complete (even if imperfect) paper, not a perfect partial paper.

### Step 3: Inter-Stage Data Flow

Ensure correct data flow between stages:

```
Stage 1 → profile.json, variable_types.json
  ↓
Stage 2 → research_questions.json (reads profile + variable_types)
  ↓
Stage 3 → downloaded/ files (reads 2_research_question/research_questions)
  ↓
Stage 4 → analysis_results.json (reads profile + variable_types + 2_research_question/research_questions + downloaded data)
  ↓
Stage 5 → figures/*.png, tables/*.tex (reads 3_analysis/analysis_results)
  ↓
Stage 6 → references.bib (reads 2_research_question/research_questions for topic context)
  ↓
Stage 7 → paper.tex (reads ALL upstream outputs + template)
  ↓
Stage 8 → paper.pdf (compiles paper.tex)
```

### Step 4: Finalize

1. **Copy final PDF** to `<output_folder>/paper.pdf` (if not already there).
2. **Update pipeline log** with `completed_at` timestamp and overall status.
3. **Print summary** listing each stage's status, output files, and any degraded/failed stages.

## Output Contract

**`<output_folder>/pipeline_log.json`** — Execution log:
```json
{
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:45:00Z",
  "data_folder": "sample/data",
  "output_folder": "exam_paper",
  "overall_status": "success|degraded|failed",
  "stages": {
    "1_load_and_profile": {
      "status": "success",
      "started_at": "...",
      "completed_at": "...",
      "outputs": ["1_data_profile/profile.json", "1_data_profile/variable_types.json"],
      "notes": ""
    }
  }
}
```

**`<output_folder>/paper.pdf`** — The final deliverable. Must exist unless stage 8 failed after 3 retries.
