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

### Step 2: Literature Search (Skip in Fast-Track Mode)

For each candidate question, construct 1-2 search queries from its PICO elements:

1. **Novelty query**: `"{population}" "{exposure}" "{outcome}" site:pubmed.ncbi.nlm.nih.gov OR site:scholar.google.com`
   - Goal: Assess how many existing studies address this exact question.
   - **High novelty** (score 0.7-1.0): Few or no direct studies found.
   - **Medium novelty** (0.4-0.6): Some related studies but not the exact question.
   - **Low novelty** (0.0-0.3): Many studies on this exact topic.

2. **Support query**: `"{exposure}" "{outcome}" association OR effect`
   - Goal: Assess whether the literature supports the plausibility of this association.
   - **Strong support** (0.7-1.0): Clear biological/epidemiological mechanism documented.
   - **Moderate support** (0.4-0.6): Some evidence but mixed or indirect.
   - **Weak support** (0.0-0.3): No evidence of plausible association.

Use web search tools (WebSearch or equivalent) for each query. Limit to 1-2 searches per candidate to stay within the 3-minute budget.

Record raw search results (titles, snippets) in `scoring_details.json` for reuse in fast-track mode.

**In fast-track mode:** Skip this step entirely. Reuse `novelty` and `support` scores from prior `scoring_details.json`.

**Progress checkpoint:**
```python
update_step(output_folder, "score_and_rank", "step_2_literature_search", "completed")
```

---

### Step 3: Compute Composite Scores

For each candidate, compute a final composite score using:

```
composite = 0.40 * data_feasibility + 0.25 * novelty + 0.20 * support + 0.15 * rigor
```

Where:
- `data_feasibility` comes from `preliminary_scores.data_feasibility` (Stage 2)
- `novelty` comes from the literature search (Step 2) or prior scoring details
- `support` comes from the literature search (Step 2) or prior scoring details
- `rigor` comes from `preliminary_scores.rigor` (Stage 2)

Note: `significance` from Stage 2 preliminary scores is subsumed by `support` (literature backing implies significance).

Rank candidates by composite score (descending).

**Progress checkpoint:**
```python
update_step(output_folder, "score_and_rank", "step_3_compute_scores", "completed")
```

---

### Step 4: Apply Feedback Penalties

If `cycle_state.json` exists and `current_cycle > 1`:

1. Read `feedback_history` from cycle state.
2. For each previously failed candidate (identified by `candidate_id`), set its composite score to **0.0**.
3. Re-rank remaining candidates.
4. If all candidates have been tried (all scores = 0.0), select the candidate with the highest original composite from Step 3 and add a warning note.

**In normal mode (cycle 1):** Skip this step (no penalties to apply).

**Progress checkpoint:**
```python
update_step(output_folder, "score_and_rank", "step_4_apply_feedback", "completed")
```

---

### Step 5: Select Top Candidate and Save

Extract the top-ranked candidate and write two output files:

#### 5a. `ranked_questions.json` (backward-compatible with downstream stages)

This file must have the **same schema** as the old `research_questions.json` so downstream stages (acquire-data, statistical-analysis, generate-figures, literature-review, write-paper) work without modification. Plus a `selection_metadata` block.

```json
{
  "primary_question": {
    "question": "<from top candidate>",
    "population": "<from top candidate>",
    "exposure_or_intervention": "<from top candidate>",
    "comparator": "<from top candidate>",
    "outcome": "<from top candidate>",
    "study_design": "<from top candidate>",
    "rationale": "<from top candidate>"
  },
  "secondary_questions": "<from top candidate's secondary_questions>",
  "variable_roles": "<from top candidate's variable_roles>",
  "feasibility_assessment": "<from top candidate's feasibility_assessment>",
  "data_acquisition_requirements": "<from top-level in research_questions.json>",
  "selection_metadata": {
    "selected_candidate_id": "CQ1",
    "cycle": 1,
    "composite_score": 0.78,
    "literature_scores": {
      "novelty": 0.7,
      "support": 0.6
    },
    "feedback_signal": null,
    "selection_rationale": "Highest composite score (0.78). Strong data feasibility, moderate novelty — no existing studies examine this exact exposure-outcome pair at the state level."
  }
}
```

#### 5b. `scoring_details.json` (internal, for fast-track reuse and audit)

```json
{
  "scored_at": "ISO-8601",
  "cycle": 1,
  "candidates": [
    {
      "candidate_id": "CQ1",
      "preliminary_scores": { "data_feasibility": 0.85, "significance": 0.70, "novelty": 0.60, "rigor": 0.75 },
      "literature_scores": { "novelty": 0.70, "support": 0.60 },
      "search_results_summary": "Found 3 related studies but none examining exact exposure-outcome pair...",
      "final_composite": 0.78,
      "rank": 1
    }
  ]
}
```

#### 5c. Update `decision_log.json`

```python
from feedback_utils import update_decision_log

update_decision_log(output_folder, {
    "cycle": cycle_state["current_cycle"],
    "candidates_scored": [
        {"candidate_id": c["candidate_id"], "composite": c["final_composite"]}
        for c in scored_candidates
    ],
    "selected": top_candidate["candidate_id"],
    "feedback_signal": feedback_signal  # None in cycle 1
})
```

**Progress checkpoint:**
```python
update_step(output_folder, "score_and_rank", "step_5_select_and_save", "completed",
            outputs=["2_scoring/ranked_questions.json", "2_scoring/scoring_details.json"])
```

---

### Step 6: Validate

Run the validation script against `ranked_questions.json` to confirm backward compatibility:

```bash
python workflow/skills/generate-research-questions/validate_research_questions.py <output_folder> --ranked
```

This verifies the file has all required fields (`primary_question`, `variable_roles`, etc.) and passes all column checks.

**Progress checkpoint - Mark stage complete:**
```python
update_step(output_folder, "score_and_rank", "step_6_validate", "completed")

complete_stage(output_folder, "score_and_rank",
               expected_outputs=["2_scoring/ranked_questions.json",
                                 "2_scoring/scoring_details.json"])
```

---

### Degraded Fallback

If literature search fails entirely (network errors, no results), fall back to using only the preliminary scores from Stage 2:
- Use `preliminary_scores.composite` as the final composite.
- Set `novelty` and `support` literature scores to 0.5 (neutral).
- Note the fallback in `selection_rationale`.

If the entire scoring stage fails, use the first candidate from `research_questions.json` as-is. Extract it into `ranked_questions.json` with `selection_metadata.selection_rationale = "Scoring failed — using first candidate as fallback"`.

## Output Contract

**`<output_folder>/2_scoring/ranked_questions.json`** — Selected question in backward-compatible format.

**`<output_folder>/2_scoring/scoring_details.json`** — Full scoring details for all candidates.

**`<output_folder>/2_scoring/progress.json`** — Stage progress tracker.
