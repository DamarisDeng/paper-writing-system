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
   mkdir -p <output_folder>/2_research_question/downloaded
   mkdir -p <output_folder>/2_scoring
   mkdir -p <output_folder>/3_analysis/scripts
   mkdir -p <output_folder>/3_analysis/models
   mkdir -p <output_folder>/4_figures/figures
   mkdir -p <output_folder>/4_figures/tables
   mkdir -p <output_folder>/5_references
   mkdir -p <output_folder>/6_paper
   mkdir -p <output_folder>/data
   ```

2. **Record start time** for time budgeting. The entire pipeline should target completion within 70 minutes (56 min happy path, up to 70 min if feedback loop triggers).

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

**Before profiling**, acquire datasets documented in `<data_folder>/Data_Description.md`:

1. Read `Data_Description.md` and parse for datasets with URLs or download instructions
2. Build a manifest JSON with dataset names, URLs, and extraction settings
3. Check what's already on disk in `<output_folder>/data/` and include only missing datasets
4. Call `/acquire-data <output_folder> <output_folder>/0_data_acquisition/manifest.json`
5. Verify: downloaded files exist, `data/README.md` updated, `download_report.json` created

See `references/REFERENCE.md: Data Acquisition Manifest` for manifest schema example.

**If `Data_Description.md` doesn't exist or has no download instructions**, skip this stage.

### Step 1: Execute Stages Sequentially

Run each stage in order. For each stage:

1. Log stage start: `tracker.start_stage(stage_number, stage_name)`
2. Update Claude Code task to `in_progress` (if created)
3. Execute the stage by following its skill instructions
4. Read stage progress with `get_progress()` and `is_stage_complete()`
5. Validate outputs against the stage's output contract
6. Log completion with `complete_stage_with_context()` or `tracker.complete_stage()`
7. Update Claude Code task to `completed`

#### Stage Execution Table

See `references/REFERENCE.md` for the complete stage execution table with validation checks and degraded fallbacks.

**Summary**: Each stage validates its outputs and provides a fallback for degraded execution.

### Step 1b: Feedback Loop After Stage 5

**After Stage 5 (statistical-analysis) completes**, check for structural analysis failures and trigger a feedback loop if needed.

See `references/REFERENCE.md: Feedback Loop Logic` for complete implementation details.

**Summary**: If structural failures are detected and cycle limit not reached:
1. Increment cycle counter and record failure
2. Reset progress for stages 3-5
3. Re-run Stage 3 (score-and-rank) in fast-track mode (skip web searches, apply penalty)
4. Re-run Stage 4 (acquire-data) if needed
5. Re-run Stage 5 (statistical-analysis) in fast-track mode (primary model + Table 1 only)

**Fast-track budget**: 14 min total.

### Step 1c: Execute Stage 4 — Acquire Supplementary Data

**After Stage 3 (score-and-rank) completes**, check `data_acquisition_requirements` in `ranked_questions.json`:

1. If non-empty, build manifest from the requirements
2. Call `/acquire-data <output_folder> <output_folder>/2_research_question/download_manifest.json`
3. Verify: files downloaded to `<output_folder>/data/`, `README.md` updated, `download_report.json` created

**If `data_acquisition_requirements` is empty**, skip this stage.

### Step 2: Time Budget Management

Target completion is 61 min happy path, up to 75 min with feedback loop.

See `references/REFERENCE.md: Time Budgets` for detailed per-stage breakdown.

### Step 3: Inter-Stage Data Flow

Both Stage 0 and Stage 4 write to the same `<output_folder>/data/` directory. The profiler (Stage 1) reads everything in that directory, including data from both acquisition passes.

See `references/REFERENCE.md: Data Flow Diagram` for the complete data flow diagram.

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

**Output files:**
- `<output_folder>/pipeline_log.json` — Overall pipeline status, stage timing
- `<output_folder>/cycle_state.json` — Feedback loop cycle counter
- `<output_folder>/decision_log.json` — Question selection audit trail
- `<output_folder>/paper.pdf` — The final deliverable

See `references/REFERENCE.md: Output Contracts` for complete JSON schemas.
