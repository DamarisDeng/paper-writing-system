---
name: orchestrator
model: medium
description: >
  Master orchestrator that runs the full paper-generation pipeline (stages 1-8)
  sequentially. Handles initialization, stage execution with validation,
  failure retries (up to 3 per stage), graceful degradation, progress tracking,
  and time budgeting (60 min total). Triggers on: "run the pipeline", "generate paper",
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

## Progress Tracking

This orchestrator uses `progress_utils.py` for consistent progress tracking across all stages. The utility provides:
- **PipelineTracker**: Maintains `pipeline_log.json` with overall status
- **Stage-level tracking**: Each stage creates/updates its own `progress.json`
- **Task integration**: Tracks Claude Code task statuses for better visibility

### Progress Files

| File | Location | Purpose |
|------|----------|---------|
| `pipeline_log.json` | `<output_folder>/pipeline_log.json` | Overall pipeline status, stage timing |
| `progress.json` | `<output_folder>/N_stage_folder/progress.json` | Stage-level step progress |

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

3. **Initialize progress tracking** using the PipelineTracker from `progress_utils.py`:

   ```python
   import sys
   sys.path.insert(0, "workflow/scripts")
   from progress_utils import PipelineTracker

   tracker = PipelineTracker(output_folder, data_folder)
   ```

   This creates `<output_folder>/pipeline_log.json` automatically.

4. **Create Claude Code tasks** for each stage (optional but recommended for visibility):

   Use `TaskCreate` to create tasks for stages that will be executed:
   ```
   - Stage 1: Load and Profile Data
   - Stage 2: Generate Research Questions
   - Stage 3: Acquire External Data
   - Stage 4: Statistical Analysis
   - Stage 5: Generate Figures
   - Stage 6: Literature Review
   - Stage 7: Write Paper
   - Stage 8: Compile and Review
   ```

   Store task IDs in a dict for status updates: `task_ids = {}`

### Step 1: Execute Stages Sequentially

Run each stage in order. For each stage:

1. **Log stage start** using the PipelineTracker:
   ```python
   tracker.start_stage(stage_number, stage_name)
   ```

2. **Update Claude Code task** to in_progress (if task was created):
   ```
   TaskUpdate(task_id, status="in_progress")
   ```

3. **Execute the stage** by following the corresponding skill instructions.
   Each skill will manage its own `progress.json` using `progress_utils.py`.

4. **Read stage progress** after execution:
   ```python
   from progress_utils import get_progress, is_stage_complete
   stage_complete = is_stage_complete(output_folder, stage_name)
   progress = get_progress(output_folder, stage_name)
   ```

5. **Validate outputs** against the stage's output contract.

6. **Log stage completion**:
   ```python
   status = "success" if stage_complete else "degraded"
   tracker.complete_stage(stage_number, stage_name, status,
                         outputs=progress.get("outputs", []),
                         notes=progress.get("notes", ""))
   ```

7. **Update Claude Code task** to completed (or failed):
   ```
   TaskUpdate(task_id, status="completed")
   ```

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

2. **Mark pipeline complete**:
   ```python
   tracker.complete_pipeline(overall_status="success")  # or "degraded" or "failed"
   ```

3. **Print summary** using the built-in method:
   ```python
   tracker.print_summary()
   ```

   This lists each stage's status, output files, and any degraded/failed stages.

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
