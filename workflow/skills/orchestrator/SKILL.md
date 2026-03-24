---
name: orchestrator
model: medium
description: >
  Master orchestrator that runs the full paper-generation pipeline (stages 0-9)
  sequentially. Handles initialization, stage execution with validation,
  failure retries (up to 3 per stage), graceful degradation, progress tracking,
  time budgeting (61 min total), and a feedback loop that re-ranks research
  question candidates if analysis encounters structural failures.
  Stage 0 performs initial data acquisition from documented datasets.
  Supports context management modes to prevent token overflow during execution.
  Triggers on: "run the pipeline", "generate paper",
  "write a paper using the data", or any request to execute the full workflow.
argument-hint: <data_folder> <output_folder> [--context-mode: safe|aggressive|off]
---

# Orchestrator — Full Pipeline Execution

Run stages 0-9 of the JAMA Network Open paper-generation pipeline sequentially, producing a final `paper.pdf` from data documentation with zero human intervention. Stage 0 acquires documented datasets, Stages 1-9 process data and generate the paper. Includes a feedback loop between analysis and question scoring to recover from structural analysis failures.

## Usage

```
/orchestrator <data_folder> <output_folder> [--context-mode: safe|aggressive|off]
```

Where:
- `<data_folder>` contains the raw dataset(s)
- `<output_folder>` is the base output directory (e.g., `exam_paper`)
- `--context-mode` controls context pruning behavior:
  - `safe` (default): Prune only after checkpoint stages, preserves more files
  - `aggressive`: Prune after every eligible stage, minimizes token usage
  - `off`: Disable all pruning, useful for debugging

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
   mkdir -p <output_folder>/0_data_acquisition
   mkdir -p <output_folder>/1_data_profile
   mkdir -p <output_folder>/2_scoring
   mkdir -p <output_folder>/3_analysis/scripts
   mkdir -p <output_folder>/4_figures/figures
   mkdir -p <output_folder>/4_figures/tables
   mkdir -p <output_folder>/5_references
   mkdir -p <output_folder>/6_paper
   mkdir -p <output_folder>/data
   ```

2. **Record start time** for time budgeting. The entire pipeline should target completion within 75 minutes (61 min happy path, up to 75 min if feedback loop triggers). 

3. **Initialize progress tracking** using the PipelineTracker from `progress_utils.py`:

   ```python
   import sys
   sys.path.insert(0, "workflow/scripts")
   from progress_utils import (
       PipelineTracker, get_cycle_state, save_cycle_state,
       initialize_context_bundle, complete_stage_with_context
   )
   from feedback_utils import build_feedback_signal

   tracker = PipelineTracker(output_folder, data_folder)

   # Initialize cycle state
   cycle_state = get_cycle_state(output_folder)
   save_cycle_state(output_folder, cycle_state)

   # Initialize context bundle (if context mode enabled)
   context_mode = kwargs.get("context_mode", "safe")  # Default to safe mode
   if context_mode != "off":
       initialize_context_bundle(output_folder,
                                 cycle=cycle_state["current_cycle"],
                                 max_cycles=cycle_state["max_cycles"])
   ```

   This creates `<output_folder>/pipeline_log.json`, `<output_folder>/cycle_state.json`, and `<output_folder>/context_bundle.json` (if context mode enabled).

4. **Create Claude Code tasks** for each stage (optional but recommended for visibility):

   Use `TaskCreate` to create tasks for stages that will be executed:
   ```
   - Stage 0: Acquire Documented Data
   - Stage 1: Load and Profile Data
   - Stage 2: Generate Research Questions
   - Stage 3: Score and Rank Questions
   - Stage 4: Acquire Supplementary Data
   - Stage 5: Statistical Analysis
   - Stage 6: Generate Figures
   - Stage 7: Literature Review
   - Stage 8: Write Paper
   - Stage 9: Compile and Review
   ```

   Store task IDs in a dict for status updates: `task_ids = {}`

### Step 0.5: Execute Stage 0 — Acquire Documented Data

**Before profiling**, acquire datasets documented in `Data_Description.md`:

**IMPORTANT: Use the automated parser script** to properly check for missing datasets. Do NOT manually check for files — the parser handles this correctly.

1. **Run the data description parser:**
   ```bash
   python workflow/scripts/parse_data_description.py <data_folder> <output_folder>
   ```

   This script:
   - Reads `Data_Description.md` from `<data_folder>`
   - Extracts all documented datasets with download URLs
   - Checks which datasets are actually present in `<data_folder>/data/`
   - Generates `<output_folder>/0_data_acquisition/manifest.json` for missing datasets
   - Exits with code 1 if downloads are needed, 0 if all present

2. **Check the availability report:**
   ```bash
   cat <output_folder>/0_data_acquisition/availability_report.json
   ```

3. **If the parser indicated missing datasets**, call acquire-data:
   ```
   /acquire-data <output_folder> <output_folder>/0_data_acquisition/manifest.json
   ```

4. **Verify outputs**:
   - `<output_folder>/data/<target_dir>/` contains downloaded files
   - `<output_folder>/data/README.md` exists
   - `<output_folder>/0_data_acquisition/download_report.json` exists

**If `Data_Description.md` doesn't exist**, skip this stage and proceed to profiling with whatever data is on disk.

**Why this matters:** The previous approach of checking "what files exist" was too simplistic. The parser correctly identifies ALL documented datasets and verifies they're complete, not just "some files are present." This prevents missing critical data like HPS_PUF which contains HCW vaccination variables.


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

6. **Log stage completion** with context management:
   ```python
   status = "success" if stage_complete else "degraded"

   # Use context-aware completion if enabled
   if context_mode != "off":
       context_result = complete_stage_with_context(
           output_folder=output_folder,
           stage_name=stage_name,
           context_mode=context_mode,
           validate_outputs=False,  # Already validated above
           expected_outputs=progress.get("outputs", []),
           summary=f"Completed {stage_name} with status {status}"
       )
   else:
       # Fallback to standard completion
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
| 0 | acquire-data (Stage 0) | `data/README.md` exists, documented datasets downloaded | Skip — proceed with available data only |
| 1 | load-and-profile | `profile.json` and `variable_types.json` exist with >0 datasets | Generate minimal profile from file headers only |
| 2 | generate-research-questions | `research_questions.json` has `candidate_questions` array with ≥2 candidates | Use first numeric column as outcome, first categorical as exposure |
| 3 | score-and-rank | `ranked_questions.json` exists with `primary_question` and `selection_metadata` | Use first candidate from `research_questions.json` as-is |
| 4 | acquire-data (Stage 4) | Downloaded files exist in `data/` (or `data_acquisition_requirements` is empty) | Skip — proceed with available data only |
| 5 | statistical-analysis | `analysis_results.json` exists with `descriptive_statistics` and `primary_analysis` | Run descriptive stats only, skip regression |
| 6 | generate-figures | At least 2 `.png` files in `figures/` and 1 `.tex` file in `tables/` | Generate Table 1 only as a LaTeX table |
| 7 | literature-review | `references.bib` has ≥10 `@article` entries | Use 10 foundational public health references |
| 8 | write-paper | `paper.tex` exists and is >5KB; supplement section present (`\section*{Supplement`); no placeholder tokens (`[INSERT`, `TODO`, `PLACEHOLDER`, `TBD`) in supplement | Generate a minimal paper with abstract + methods + results; add stub eAppendix 1 with model equations extracted from `analysis_results.json` |
| 9 | compile-and-review | `paper.pdf` exists in `<output_folder>/` and `<output_folder>/6_paper/` | Return the `.tex` file as final output |

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

        # 3. Update context bundle with feedback cycle
        #    (pruning is automatically disabled for feedback stages)
        if context_mode != "off":
            import context_manager
            bundle = context_manager.get_context_bundle(output_folder)
            if bundle:
                bundle["meta"]["cycle"] = cycle_state["current_cycle"]
                bundle["meta"]["in_feedback_loop"] = True
                context_manager._save_bundle(
                    os.path.join(output_folder, "context_bundle.json"),
                    bundle
                )

        # 4. Re-run Stage 3 (score-and-rank) in FAST-TRACK mode
        #    The skill reads cycle_state.json and skips web searches,
        #    applies penalty to failed candidate, re-ranks.
        #    → Execute /score-and-rank <output_folder>

        # 5. Re-run Stage 4 (acquire-data) — mostly skipped if data unchanged
        #    → Execute /acquire-data <output_folder>

        # 6. Re-run Stage 5 (statistical-analysis) in FAST-TRACK mode
        #    Run primary model + Table 1 only, skip sensitivity analyses.
        #    → Execute /statistical-analysis <output_folder>

        # 7. Clear feedback loop flag after re-run completes
        if context_mode != "off":
            import context_manager
            bundle = context_manager.get_context_bundle(output_folder)
            if bundle:
                bundle["meta"]["in_feedback_loop"] = False
                context_manager._save_bundle(
                    os.path.join(output_folder, "context_bundle.json"),
                    bundle
                )
    else:
        print(f"[FEEDBACK] Issues detected but max cycles ({cycle_state['max_cycles']}) reached — proceeding with current results")
else:
    # No structural issues or only minor issues — proceed normally
    pass
```

**Context Management Note**: During feedback loop cycles, pruning of stages 3-5 is automatically disabled regardless of `context_mode` setting. This preserves files needed for re-ranking and re-analysis.

**Fast-track mode details:**
- **Stage 3 re-run**: Skips web searches, reuses prior `scoring_details.json`, applies score penalty (0.0) to failed candidate, re-ranks remaining candidates.
- **Stage 4 re-run**: Mostly skipped if data acquisition requirements are the same.
- **Stage 5 re-run**: Run primary model + Table 1 only, skip sensitivity analyses. Target: 10 min.
- **Total feedback re-run budget**: 14 min.

### Step 1c: Execute Stage 4 — Acquire Supplementary Data

**After Stage 3 (score-and-rank) completes**, check if supplementary data is needed:

1. **Run the manifest builder script:**
   ```bash
   python workflow/skills/orchestrator/scripts/build_stage4_manifest.py <output_folder>
   ```
   - Prints `NO_DOWNLOADS_NEEDED` → skip to Stage 5
   - Prints `MANIFEST_WRITTEN <path>` → proceed to step 2

2. **Call acquire-data** with the manifest:
   ```
   /acquire-data <output_folder> <output_folder>/2_research_question/download_manifest.json
   ```

3. **Verify outputs**:
   - `<output_folder>/data/<target_dir>/` contains downloaded files (same location as Stage 0)
   - `<output_folder>/data/README.md` is updated with new file descriptions
   - `<output_folder>/2_research_question/download_report.json` exists

### Step 1d: Validate Stage 8 — Supplement Check

**After Stage 8 (write-paper) completes**, run this validation before proceeding to Stage 9:

```bash
python workflow/skills/orchestrator/scripts/validate_supplement.py <output_folder>
```

- Exit 0 → proceed to Stage 9
- Exit 1 → re-run Stage 8 once, passing the printed failure reason in the prompt so the model knows what to fix. If the second run also fails, proceed to Stage 9 and log a warning in `pipeline_log.json` — a paper with an incomplete supplement is better than no paper.

### Step 2: Time Budget Management

Allocate time across stages approximately:

| Stage | Happy Path | With Feedback |
|-------|-----------|---------------|
| 0. Acquire Documented Data | 5 min | 5 min |
| 1. Load & Profile | 5 min | 5 min |
| 2. Research Questions | 5 min | 5 min |
| 3. Score & Rank | 3 min | 3 min |
| 4. Acquire Supplementary Data | 3 min | 3 min |
| 5. Statistical Analysis | 13 min | 13 min |
| *Feedback re-run (3-5)* | — | *14 min* |
| 6. Generate Figures | 8 min | 8 min |
| 7. Literature Review | 8 min | 8 min |
| 8. Write Paper | 8 min | 8 min |
| 9. Compile & Review | 3 min | 3 min |
| **Total** | **61 min** | **75 min** |

If a stage exceeds its budget by 2x, produce a simplified version and move on. The goal is a complete (even if imperfect) paper, not a perfect partial paper.

### Step 3: Inter-Stage Data Flow

Ensure correct data flow between stages:

```
Data_Description.md (in <data_folder>)
  ↓ (orchestrator parses, builds manifest)
0_data_acquisition/manifest.json
  ↓ (acquire-data downloads to <output_folder>/data/)
<output_folder>/data/HPS_PUF/*.csv
<output_folder>/data/README.md
0_data_acquisition/download_report.json
  ↓
Stage 1: load-and-profile → profiles <output_folder>/data/ (all CSV/XLSX)
  → profile.json, variable_types.json
  ↓
Stage 2: generate-research-questions → research_questions.json
  ↓
Stage 3: score-and-rank → ranked_questions.json
  ↓ (orchestrator extracts data_acquisition_requirements, builds manifest)
2_research_question/download_manifest.json
  ↓ (acquire-data downloads to SAME <output_folder>/data/)
<output_folder>/data/covid_deaths/*.csv (supplementary)
<output_folder>/data/README.md (updated)
2_research_question/download_report.json
  ↓
Stage 5: statistical-analysis → analysis_results.json
  ↓                                    ↑
  ↓  ← ← ← FEEDBACK LOOP ← ← ← ← ← ← ← ↑  (if structural failure: re-score → re-acquire → re-analyze)
  ↓
Stage 6 → figures/*.png, tables/*.tex (reads 3_analysis/analysis_results)
  ↓
Stage 7 → references.bib (reads 2_scoring/ranked_questions for topic context)
  ↓
Stage 8 → paper.tex (reads ALL upstream outputs + template + decision_log.json)
  ↓
Stage 9 → paper.pdf (compiles paper.tex)
```

**Key point:** Both Stage 0 and Stage 4 write to the same `<output_folder>/data/` directory. The profiler (Stage 1) reads everything in that directory, including data from both acquisition passes.

### Step 4: Finalize

1. **Copy final PDF** to `<output_folder>/paper.pdf` (keeping `<output_folder>/6_paper/paper.pdf` as reference).

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

**`<output_folder>/paper.pdf`** — The final deliverable at output root. Must exist unless stage 9 failed after 3 retries.

**`<output_folder>/6_paper/paper.pdf`** — The same PDF remains in the stage folder for reference.
