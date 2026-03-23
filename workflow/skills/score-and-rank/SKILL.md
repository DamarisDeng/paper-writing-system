---
name: score-and-rank
model: medium
description: >
  Score and rank candidate research questions using literature-informed signals
  and data feasibility scores. Reads candidate_questions from
  research_questions.json (Stage 2 output), runs web searches for novelty and
  literature support, computes composite scores, and selects the top candidate.
  Outputs ranked_questions.json in backward-compatible format for downstream
  stages. Supports fast-track mode for feedback loop re-ranking.
  Triggers on: "score questions", "rank candidates", "select research question",
  or automatically after generate-research-questions in the pipeline.
argument-hint: <output_folder>
---

# Score and Rank Research Questions

Score candidate research questions using literature-informed signals and select the best one for analysis.

## Usage

```
/score-and-rank <output_folder>
```

Reads from `<output_folder>/2_research_question/research_questions.json` and optionally `<output_folder>/cycle_state.json`. Writes to `<output_folder>/2_scoring/`.

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/2_scoring/progress.json`.

**Steps tracked:**
- `step_1_load_inputs`: Load candidates and cycle state
- `step_2_literature_search`: Search for novelty and support signals
- `step_3_compute_scores`: Compute composite scores
- `step_4_apply_feedback`: Apply feedback penalties (if in feedback cycle)
- `step_5_select_and_save`: Extract top candidate and save outputs
- `step_6_validate`: Validate ranked_questions.json

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

## Instructions

You are a research strategist evaluating candidate research questions for a JAMA Network Open paper. Your job is to add literature-informed scoring signals to the data-driven preliminary scores from Stage 2, then select the single best candidate for analysis.

**Initialize progress tracker at start:**
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker, update_step, complete_stage, get_cycle_state
from feedback_utils import update_decision_log

tracker = create_stage_tracker(output_folder, "score_and_rank",
    ["step_1_load_inputs", "step_2_literature_search", "step_3_compute_scores",
     "step_4_apply_feedback", "step_5_select_and_save", "step_6_validate"])
```

---

### Step 1: Load Inputs

Read:
1. **`<output_folder>/2_research_question/research_questions.json`** — Contains `candidate_questions` array with preliminary scores and variable roles.
2. **`<output_folder>/cycle_state.json`** (if exists) — Feedback cycle state. If `current_cycle > 1`, this is a re-ranking after analysis failure.

Determine the mode:
- **Normal mode** (`cycle_state` absent or `current_cycle == 1`): Full scoring with literature search.
- **Fast-track mode** (`current_cycle > 1`): Skip web searches, reuse prior `scoring_details.json`, apply penalty to failed candidate.

If fast-track mode:
- Read `<output_folder>/2_scoring/scoring_details.json` from the previous cycle.
- Read `cycle_state.json` → `feedback_history` to identify the failed candidate.

**Progress checkpoint:**
```python
update_step(output_folder, "score_and_rank", "step_1_load_inputs", "completed")
```

---

### Step 1b: Filter to Feasible Candidates

**CRITICAL:** Before performing expensive literature searches, filter to only candidates that passed feasibility validation in Stage 2.

```python
# Filter candidates to only feasible ones
feasible_candidates = [
    c for c in research_questions.get("candidate_questions", [])
    if c.get("status") != "infeasible"
]

infeasible_count = len(research_questions.get("candidate_questions", [])) - len(feasible_candidates)

if infeasible_count > 0:
    print(f"[score_and_rank] Filtered out {infeasible_count} infeasible candidate(s)")

if len(feasible_candidates) == 0:
    # Early termination - no viable research questions
    print("[score_and_rank] ERROR: No feasible candidates found!")
    print("All candidates were rejected during Stage 2 feasibility validation.")
    print("The data is insufficient for any viable research question.")
    raise SystemExit(
        "No feasible candidates - data insufficient for research. "
        "Check Stage 2 output for infeasibility reasons."
    )

print(f"[score_and_rank] Proceeding with {len(feasible_candidates)} feasible candidate(s)")
```

**Why this matters:** Literature searches are expensive. If all candidates are infeasible, we fail fast rather than wasting time on web searches.

**Progress checkpoint:**
```python
update_step(output_folder, "score_and_rank", "step_1_load_inputs", "completed",
            notes=f"Filtered to {len(feasible_candidates)} feasible candidates")
```

---

### Step 5: Select Top Candidate and Save

Extract the top-ranked candidate and write `ranked_questions.json` and `scoring_details.json`.

See `references/REFERENCE.md: Output Contracts` for the complete output schemas.

### Step 6: Validate

Run the validation script against `ranked_questions.json` to confirm backward compatibility:
```bash
python workflow/skills/generate-research-questions/validate_research_questions.py <output_folder> --ranked
```

See `references/REFERENCE.md: Degraded Fallback` for fallback behavior when search/scoring fails.

**`<output_folder>/2_scoring/ranked_questions.json`** — Selected question in backward-compatible format.

**`<output_folder>/2_scoring/scoring_details.json`** — Full scoring details for all candidates.

**`<output_folder>/2_scoring/progress.json`** — Stage progress tracker.
