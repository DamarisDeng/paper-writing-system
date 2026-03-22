---
name: orchestrator
model: medium
description: >
  Master orchestrator that runs the full paper-generation pipeline (stages 1-9)
  sequentially. Handles initialization, stage execution with validation,
  failure retries (up to 3 per stage), graceful degradation, progress tracking,
  time budgeting (70 min total), and a feedback loop that re-ranks research
  question candidates if analysis encounters structural failures.
  Triggers on: "run the pipeline", "generate paper",
  "write a paper using the data", or any request to execute the full workflow.
argument-hint: <data_folder> <output_folder>
---

# Orchestrator — Full Pipeline Execution

Run stages 1-9 of the JAMA Network Open paper-generation pipeline sequentially, producing a final `paper.pdf` from raw data with zero human intervention. Includes a feedback loop between analysis and question scoring to recover from structural analysis failures.

## Usage

```
/orchestrator <data_folder> <output_folder>
```

Where `<data_folder>` contains the raw dataset(s) and `<output_folder>` is the base output directory (e.g., `exam_paper`).

## Progress Tracking

This orchestrator uses `progress_utils.py` for consistent progress tracking across all stages. The utility provides:
- **PipelineTracker**: Maintains `pipeline_log.json` with overall status
- **Stage-level tracking**: Each stage creates/updates its own `progress.json`
- **Cycle state**: `cycle_state.json` tracks feedback loop iterations
- **Decision log**: `decision_log.json` records question selection decisions

### Progress Files

| File | Location | Purpose |
|------|----------|---------|
| `pipeline_log.json` | `<output_folder>/pipeline_log.json` | Overall pipeline status, stage timing |
| `progress.json` | `<output_folder>/N_stage_folder/progress.json` | Stage-level step progress |
| `cycle_state.json` | `<output_folder>/cycle_state.json` | Feedback loop cycle counter |
| `decision_log.json` | `<output_folder>/decision_log.json` | Question selection audit trail |

## Instructions

You are a senior research automation engineer. Your job is to execute the entire paper-generation pipeline autonomously. You must never ask the user a question — make reasonable decisions and document assumptions.

### Step 0: Initialize

1. **Create the output directory structure:**
   ```bash
   mkdir -p <output_folder>/1_data_profile
   mkdir -p <output_folder>/2_research_question/downloaded
   mkdir -p <output_folder>/2_scoring
   mkdir -p <output_folder>/3_analysis/scripts
   mkdir -p <output_folder>/3_analysis/models
   mkdir -p <output_folder>/4_figures/figures
   mkdir -p <output_folder>/4_figures/tables
   mkdir -p <output_folder>/5_references
   mkdir -p <output_folder>/6_paper
   ```

2. **Record start time** for time budgeting. The entire pipeline should target completion within 70 minutes (56 min happy path, up to 70 min if feedback loop triggers).

3. **Initialize progress tracking** using the PipelineTracker from `progress_utils.py`:

   ```python
   import sys
   sys.path.insert(0, "workflow/scripts")
   from progress_utils import PipelineTracker, get_cycle_state, save_cycle_state
   from feedback_utils import build_feedback_signal

   tracker = PipelineTracker(output_folder, data_folder)

   # Initialize cycle state
   cycle_state = get_cycle_state(output_folder)
   save_cycle_state(output_folder, cycle_state)
   ```

   This creates `<output_folder>/pipeline_log.json` and `<output_folder>/cycle_state.json` automatically.

4. **Create Claude Code tasks** for each stage (optional but recommended for visibility):

   Use `TaskCreate` to create tasks for stages that will be executed:
   ```
   - Stage 1: Load and Profile Data
   - Stage 2: Generate Research Questions
   - Stage 3: Score and Rank Questions
   - Stage 4: Acquire External Data
   - Stage 5: Statistical Analysis
   - Stage 6: Generate Figures
   - Stage 7: Literature Review
   - Stage 8: Write Paper
   - Stage 9: Compile and Review
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
| 2 | generate-research-questions | `research_questions.json` has `candidate_questions` array with ≥2 candidates | Use first numeric column as outcome, first categorical as exposure |
| 3 | score-and-rank | `ranked_questions.json` exists with `primary_question` and `selection_metadata` | Use first candidate from `research_questions.json` as-is |
| 4 | acquire-data | Downloaded files exist (or `data_acquisition_requirements` is empty) | Skip — proceed with available data only |
| 5 | statistical-analysis | `analysis_results.json` exists with `descriptive_statistics` and `primary_analysis` | Run descriptive stats only, skip regression |
| 6 | generate-figures | At least 2 `.png` files in `figures/` and 1 `.tex` file in `tables/` | Generate Table 1 only as a LaTeX table |
| 7 | literature-review | `references.bib` has ≥10 `@article` entries | Use 10 foundational public health references |
| 8 | write-paper | `paper.tex` exists and is >5KB | Generate a minimal paper with abstract + methods + results |
| 9 | compile-and-review | `paper.pdf` exists in `<output_folder>/` | Return the `.tex` file as final output |

### Step 1b: Feedback Loop After Stage 5

**After Stage 5 (statistical-analysis) completes**, check for structural analysis failures:

```python
from feedback_utils import build_feedback_signal
from progress_utils import get_cycle_state, save_cycle_state, reset_stage_progress

cycle_state = get_cycle_state(output_folder)
feedback_signal = build_feedback_signal(output_folder)

if feedback_signal is not None and feedback_signal["recommendation"] == "retry_next_candidate":
    if cycle_state["current_cycle"] < cycle_state["max_cycles"]:
        # --- FEEDBACK LOOP: Re-rank and retry ---
        print(f"[FEEDBACK] Structural issues detected: {[i['check'] for i in feedback_signal['issues']]}")
        print(f"[FEEDBACK] Initiating cycle {cycle_state['current_cycle'] + 1}")

        # 1. Record the failure in cycle state
        cycle_state["current_cycle"] += 1
        cycle_state["feedback_history"].append({
            "cycle": cycle_state["current_cycle"] - 1,
            "failed_candidate_id": feedback_signal["failed_candidate_id"],
            "issues": feedback_signal["issues"]
        })
        save_cycle_state(output_folder, cycle_state)

        # 2. Reset progress for stages 3-5
        reset_stage_progress(output_folder, "score_and_rank")
        reset_stage_progress(output_folder, "acquire_data")
        reset_stage_progress(output_folder, "statistical_analysis")

        # 3. Re-run Stage 3 (score-and-rank) in FAST-TRACK mode
        #    The skill reads cycle_state.json and skips web searches,
        #    applies penalty to failed candidate, re-ranks.
        #    → Execute /score-and-rank <output_folder>

        # 4. Re-run Stage 4 (acquire-data) — mostly skipped if data unchanged
        #    → Execute /acquire-data <output_folder>

        # 5. Re-run Stage 5 (statistical-analysis) in FAST-TRACK mode
        #    Run primary model + Table 1 only, skip sensitivity analyses.
        #    → Execute /statistical-analysis <output_folder>

        # 6. After re-run, do NOT loop again — proceed to Stage 6
    else:
        print(f"[FEEDBACK] Issues detected but max cycles ({cycle_state['max_cycles']}) reached — proceeding with current results")
else:
    # No structural issues or only minor issues — proceed normally
    pass
```

**Fast-track mode details:**
- **Stage 3 re-run**: Skips web searches, reuses prior `scoring_details.json`, applies score penalty (0.0) to failed candidate, re-ranks remaining candidates.
- **Stage 4 re-run**: Mostly skipped if data acquisition requirements are the same.
- **Stage 5 re-run**: Run primary model + Table 1 only, skip sensitivity analyses. Target: 10 min.
- **Total feedback re-run budget**: 14 min.

### Step 2: Time Budget Management

Allocate time across stages approximately:

| Stage | Happy Path | With Feedback |
|-------|-----------|---------------|
| 1. Load & Profile | 5 min | 5 min |
| 2. Research Questions | 5 min | 5 min |
| 3. Score & Rank | 3 min | 3 min |
| 4. Acquire Data | 3 min | 3 min |
| 5. Statistical Analysis | 13 min | 13 min |
| *Feedback re-run (3-5)* | — | *14 min* |
| 6. Generate Figures | 8 min | 8 min |
| 7. Literature Review | 8 min | 8 min |
| 8. Write Paper | 8 min | 8 min |
| 9. Compile & Review | 3 min | 3 min |
| **Total** | **56 min** | **70 min** |

If a stage exceeds its budget by 2x, produce a simplified version and move on. The goal is a complete (even if imperfect) paper, not a perfect partial paper.

### Step 3: Inter-Stage Data Flow

Ensure correct data flow between stages:

```
Stage 1 → profile.json, variable_types.json
  ↓
Stage 2 → research_questions.json (candidate_questions array)
  ↓
Stage 3 → ranked_questions.json (selected primary + scoring details)
  ↓
Stage 4 → downloaded/ files (reads 2_scoring/ranked_questions.json)
  ↓
Stage 5 → analysis_results.json (reads profile + variable_types + 2_scoring/ranked_questions + downloaded data)
  ↓                                    ↑
  ↓  ← ← ← FEEDBACK LOOP ← ← ← ← ← ↑  (if structural failure: re-score → re-acquire → re-analyze)
  ↓
Stage 6 → figures/*.png, tables/*.tex (reads 3_analysis/analysis_results)
  ↓
Stage 7 → references.bib (reads 2_scoring/ranked_questions for topic context)
  ↓
Stage 8 → paper.tex (reads ALL upstream outputs + template + decision_log.json)
  ↓
Stage 9 → paper.pdf (compiles paper.tex)
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

**`<output_folder>/cycle_state.json`** — Feedback loop state:
```json
{
  "current_cycle": 1,
  "max_cycles": 2,
  "feedback_history": []
}
```

**`<output_folder>/decision_log.json`** — Question selection audit trail:
```json
[
  {
    "cycle": 1,
    "timestamp": "ISO-8601",
    "candidates_scored": [
      { "candidate_id": "CQ1", "composite": 0.78 },
      { "candidate_id": "CQ2", "composite": 0.65 }
    ],
    "selected": "CQ1",
    "feedback_signal": null
  }
]
```

**`<output_folder>/paper.pdf`** — The final deliverable. Must exist unless stage 9 failed after 3 retries.
