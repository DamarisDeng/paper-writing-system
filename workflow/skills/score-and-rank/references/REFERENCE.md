# Reference: Score and Rank Research Questions

## Table of Contents

1. [Fast-Track Mode](#fast-track-mode)
2. [Scoring Formula](#scoring-formula)
3. [Feedback Penalties](#feedback-penalties)
4. [Output Contracts](#output-contracts)

---

## Fast-Track Mode

**Triggered when:** `cycle_state.json` exists and `current_cycle > 1`

**Behavior changes:**
- Skip web searches (Step 2)
- Reuse prior `scoring_details.json` for novelty and support scores
- Apply score penalty (0.0) to failed candidate from feedback history
- Re-rank remaining candidates

**Why:** Fast-track mode enables the feedback loop to recover from structural analysis failures without re-running expensive literature searches.

**How to detect fast-track mode:**
```python
cycle_state = get_cycle_state(output_folder)
if cycle_state["current_cycle"] > 1:
    # Fast-track: skip web searches, reuse prior scores
    prior_scoring = json.load(f"{output_folder}/2_scoring/scoring_details.json")
    # Apply penalty to failed candidate
    for failed in cycle_state["feedback_history"]:
        for candidate in candidates:
            if candidate["candidate_id"] == failed["candidate_id"]:
                candidate["composite"] = 0.0
```

---

## Scoring Formula

For each feasible candidate, compute a final composite score:

```
composite = 0.40 * data_feasibility + 0.25 * novelty + 0.20 * support + 0.15 * rigor
```

Where:
- `data_feasibility` comes from `preliminary_scores.data_feasibility` (Stage 2)
- `novelty` comes from the literature search (0.7-1.0: high novelty, 0.4-0.6: medium, 0.0-0.3: low)
- `support` comes from the literature search (0.7-1.0: strong support, 0.4-0.6: moderate, 0.0-0.3: weak)
- `rigor` comes from `preliminary_scores.rigor` (Stage 2)

Note: `significance` from Stage 2 preliminary scores is subsumed by `support` (literature backing implies significance).

Rank candidates by composite score (descending).

---

## Feedback Penalties

With the new feasibility filtering in Stage 2, `data_not_feasible` failures in Stage 5 should be rare. Candidates without control groups, missing outcomes, or insufficient sample are rejected before literature search.

However, runtime failures (model non-convergence, separation, violated assumptions) can still occur and trigger feedback.

**Penalty application:**
1. Read `feedback_history` from cycle state
2. For each previously failed candidate (by `candidate_id`), set its composite score to **0.0**
3. Re-rank remaining candidates
4. If all candidates have been tried (all scores = 0.0), select the candidate with the highest original composite from Step 3 and add a warning note

**In normal mode (cycle 1):** Skip this step (no penalties to apply).

---

## Output Contracts

### ranked_questions.json

This file must have the **same schema** as the old `research_questions.json` so downstream stages work without modification:

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
    "selection_rationale": "Highest composite score (0.78). Strong data feasibility, moderate novelty."
  }
}
```

### scoring_details.json

Internal file for fast-track reuse and audit:

```json
{
  "scored_at": "ISO-8601",
  "cycle": 1,
  "candidates": [
    {
      "candidate_id": "CQ1",
      "preliminary_scores": { "data_feasibility": 0.85, "significance": 0.70, "novelty": 0.60, "rigor": 0.75 },
      "literature_scores": { "novelty": 0.70, "support": 0.60 },
      "search_results_summary": "Found 3 related studies...",
      "final_composite": 0.78,
      "rank": 1
    }
  ]
}
```

---

## Degraded Fallback

If literature search fails entirely (network errors, no results), fall back to using only the preliminary scores from Stage 2:
- Use `preliminary_scores.composite` as the final composite
- Set `novelty` and `support` literature scores to 0.5 (neutral)
- Note the fallback in `selection_rationale`

If the entire scoring stage fails, use the first candidate from `research_questions.json` as-is. Extract it into `ranked_questions.json` with `selection_metadata.selection_rationale = "Scoring failed — using first candidate as fallback"`.
