# Plan: Literature-Informed Research Question Scoring & Feedback Loop

## Context

The current pipeline commits to a single research question in Stage 2 (`generate-research-questions`) and never revisits that decision. If the chosen question leads to non-convergent models, violated assumptions, or insufficient power in Stage 4 (analysis), the pipeline wastes 25+ minutes producing a paper around a bad question. The proposed changes decouple question generation from selection, add a literature-informed scoring stage, and introduce a feedback loop so the pipeline can recover from structural analysis failures by trying the next-best candidate.

---

## Feasibility & Benefits Assessment

| Change | Feasibility | Benefit | Risk |
|--------|------------|---------|------|
| **1. Candidate generator** (output 2-3 candidates, no selection) | Easy -- Stage 2 already generates 2-3 internally before discarding | Medium -- eliminates premature commitment | Low -- schema change is contained |
| **2. Literature scoring stage** (new Stage 3) | Moderate -- no PubMed API, relies on web search + LLM judgment | Medium -- adds novelty/gap signal, structured decision point | Medium -- scoring quality is approximate |
| **3. Feedback loop** (analysis -> re-rank -> re-analyze) | Hard -- breaks linear execution model, requires cycle-aware progress tracking | **High -- biggest quality improvement**; catches structural failures before wasting downstream stages | High -- resume logic, time budget, orchestrator complexity |
| **4. Cycle counting (hard limit 2)** | Easy -- single state variable | Necessary safeguard | Low |
| **5. decision_log.json** | Easy -- append-only JSON | Medium -- methods section transparency, debugging | Low |
| **6. Time budget reallocation** | Easy -- bookkeeping | Low -- honest accounting | Low |

**Overall verdict:** Feasible. The feedback loop (Change 3) is the hardest part but also the highest-value. The two-file schema strategy (below) keeps downstream blast radius low.

---

## Key Design Decisions

### 1. Two-file schema strategy (avoids breaking 5 downstream skills)

- **`research_questions.json`** (Stage 2 output): `candidate_questions` array, no `primary_question`
- **`ranked_questions.json`** (new Stage 3 output): Identical schema to current `research_questions.json` (has `primary_question`, `secondary_questions`, `variable_roles`, etc.) + `selection_metadata`

Downstream stages 4-9 swap one file path and get an identical schema. Zero structural changes needed.

### 2. Folder naming: no renumbering

New scoring stage writes to `exam_paper/2_scoring/`. All existing folders (`1_data_profile`, `2_research_question`, `3_analysis`, etc.) keep their names. Only `progress_utils.py` stage mapping constants change.

### 3. Feedback cycle limit: 2 total cycles (1 original + 1 retry), time-constrained

To fit within a **70-minute total pipeline budget**, the feedback re-run uses a **fast-track analysis** mode:
- Re-score: 2 min (skip web searches, reuse literature scores, only apply penalty + re-rank)
- Re-acquire: 2 min (likely same data, mostly skipped)
- Re-analyze: 10 min (run primary model + Table 1 only, skip sensitivity analyses)
- Feedback cycle total: **14 min**

### 4. Compressed time budget (70 min hard ceiling)

| Stage | Happy path | With feedback |
|-------|-----------|---------------|
| 1. Load & Profile | 5 min | 5 min |
| 2. Research Questions | 5 min | 5 min |
| 3. Score & Rank | 3 min | 3 min |
| 4. Acquire Data | 3 min | 3 min |
| 5. Statistical Analysis | 13 min | 13 min |
| *Feedback re-run (3-5)* | -- | *14 min* |
| 6. Generate Figures | 8 min | 8 min |
| 7. Literature Review | 8 min | 8 min |
| 8. Write Paper | 8 min | 8 min |
| 9. Compile & Review | 3 min | 3 min |
| **Total** | **56 min** | **70 min** |

The 2x-budget degradation rule still applies: if any stage hits 2x its allocation, produce a simplified version and move on.

---

## Implementation Phases

### Phase 1: Infrastructure (`progress_utils.py` + new `feedback_utils.py`)

**File: `workflow/scripts/progress_utils.py`**
- Add `score_and_rank` to `STAGE_MAPPING` and `STAGE_TO_FOLDER` (`2_scoring`)
- Renumber internal stage keys (3->4, 4->5, ..., 8->9) -- affects metadata only, not folder paths
- Add `reset_stage_progress(output_folder, stage_name)` -- deletes `progress.json` for re-entrant stages
- Add `get_cycle_state(output_folder)` / `save_cycle_state(output_folder, state)` -- reads/writes `cycle_state.json`

**New file: `workflow/scripts/feedback_utils.py`**
- `build_feedback_signal(output_folder) -> dict | None` -- reads `3_analysis/analysis_results.json`, checks for non-convergence, violated assumptions, insufficient N, complete separation
- `update_decision_log(output_folder, entry)` -- appends to `decision_log.json`
- `read_decision_log(output_folder) -> list`

### Phase 2: Modify `generate-research-questions` skill

**File: `workflow/skills/generate-research-questions/SKILL.md`**
- Step 4: Stop selecting a primary. Output all 2-3 candidates with preliminary scores (`data_feasibility`, `significance`, `novelty`, `rigor`, `composite`)
- Step 5: Assign variable roles per-candidate (each candidate carries its own `variable_roles`)
- Step 7: New output schema -- `candidate_questions` array replaces `primary_question`
- Keep `data_acquisition_requirements` at top level (union of all candidates' needs)

**File: `workflow/skills/generate-research-questions/validate_research_questions.py`**
- Update `check_schema()` for `candidate_questions` array
- Run column coverage, analyzability, specificity checks per-candidate

### Phase 3: Create `score-and-rank` skill

**New dir: `workflow/skills/score-and-rank/`**

**New file: `workflow/skills/score-and-rank/SKILL.md`** (model: medium, budget: 3 min)
- Step 1: Load `research_questions.json` candidates + optional `cycle_state.json`/`feedback_signal`
- Step 2: For each candidate, run 1-2 web searches (PubMed/Google Scholar keywords from PICO elements), assess novelty and literature support. **Fast-track mode** (cycle > 1): skip web searches, reuse prior `scoring_details.json`, apply penalty to failed candidate only.
- Step 3: Compute composite scores: `0.4*feasibility + 0.25*novelty + 0.2*support + 0.15*rigor`
- Step 4: If feedback_signal exists, penalize previously-tried candidate (set its composite to 0)
- Step 5: Extract top candidate into `ranked_questions.json` (backward-compatible schema)
- Step 6: Write `scoring_details.json` + update `decision_log.json`
- Degraded fallback: if scoring fails, use first candidate as-is

**Output folder:** `exam_paper/2_scoring/`
**Output files:** `ranked_questions.json`, `scoring_details.json`, `progress.json`

### Phase 4: Update downstream consumers (5 skills)

Each skill: swap `2_research_question/research_questions.json` -> `2_scoring/ranked_questions.json` in Step 1 input loading. Schema is identical so no other changes needed.

| Skill | File |
|-------|------|
| acquire-data | `workflow/skills/acquire-data/SKILL.md` |
| statistical-analysis | `workflow/skills/statistical-analysis/SKILL.md` |
| generate-figures | `workflow/skills/generate-figures/SKILL.md` |
| literature-review | `workflow/skills/literature-review/SKILL.md` |
| write-paper | `workflow/skills/write-paper/SKILL.md` |

**Additional write-paper changes:**
- Add `decision_log.json` as input
- Add methods section paragraph describing question selection process (candidates considered, scoring approach, any feedback cycles)

### Phase 5: Update orchestrator

**File: `workflow/skills/orchestrator/SKILL.md`**
- Insert Stage 3 (score-and-rank) in execution table with validation: `ranked_questions.json` exists with scored candidate
- Renumber stages 3-8 -> 4-9 in the table
- Add `mkdir -p <output_folder>/2_scoring` to initialization
- Add feedback loop logic after Stage 5 (analysis):
  ```
  After Stage 5 completes:
  1. Call build_feedback_signal()
  2. If null OR cycle >= 2: proceed to Stage 6
  3. If structural issues: increment cycle, reset stages 3-5 progress,
     return to Stage 3 with feedback_signal and fast_track=true
  ```
- Fast-track mode for feedback re-runs: Stage 3 skips web searches (reuses scores, applies penalty only), Stage 5 runs primary model + Table 1 only (no sensitivity analyses). Total re-run: 14 min.
- Update time budget table (9 stages, 56 min happy path, 70 min worst case)
- Update inter-stage data flow diagram with backward arrow

### Phase 6: Update project docs

**File: `.claude/CLAUDE.md`**
- Update pipeline stages table (9 stages)
- Add `2_scoring/` to directory structure
- Update progress files list
- Add score-and-rank to model mapping (medium/sonnet)

---

## New Schemas

### `research_questions.json` (Stage 2 output -- changed)

```json
{
  "candidate_questions": [
    {
      "candidate_id": "CQ1",
      "question": "...", "population": "...", "exposure_or_intervention": "...",
      "comparator": "...", "outcome": "...", "study_design": "...", "rationale": "...",
      "preliminary_scores": {
        "data_feasibility": 0.85, "significance": 0.70,
        "novelty": 0.60, "rigor": 0.75, "composite": 0.725
      },
      "secondary_questions": [...],
      "variable_roles": {...},
      "feasibility_assessment": {...}
    }
  ],
  "data_acquisition_requirements": [...]
}
```

### `ranked_questions.json` (Stage 3 output -- new, backward-compatible)

Same core schema as current `research_questions.json` plus:
```json
{
  "primary_question": { ... },
  "secondary_questions": [...],
  "variable_roles": {...},
  "feasibility_assessment": {...},
  "data_acquisition_requirements": [...],
  "selection_metadata": {
    "selected_candidate_id": "CQ1",
    "cycle": 1,
    "composite_score": 0.78,
    "literature_scores": { "novelty": 0.7, "support": 0.6 },
    "feedback_signal": null,
    "selection_rationale": "..."
  }
}
```

### `decision_log.json` (pipeline artifact -- new)

```json
[
  {
    "cycle": 1, "timestamp": "ISO-8601",
    "candidates_scored": [
      { "candidate_id": "CQ1", "composite": 0.78 },
      { "candidate_id": "CQ2", "composite": 0.65 }
    ],
    "selected": "CQ1",
    "feedback_signal": null
  }
]
```

### `cycle_state.json` (orchestrator state -- new)

```json
{
  "current_cycle": 1,
  "max_cycles": 2,
  "feedback_history": []
}
```

---

## Verification Plan

1. **Schema validation**: Run existing `validate_research_questions.py` against `ranked_questions.json` to confirm backward compatibility
2. **Unit test `feedback_utils.py`**: Test with well-formed analysis results (no feedback), non-convergent model (feedback triggered), insufficient N (feedback triggered)
3. **Integration test**: Run full pipeline on `sample/data/`, verify all 9 stages complete, `decision_log.json` exists, `paper.pdf` produced
4. **Feedback loop test**: Manually create an `analysis_results.json` that triggers feedback, verify orchestrator re-runs stages 3-5, `decision_log.json` has 2 entries, cycle does not exceed limit
5. **Regression**: Compare paper output quality on same dataset before/after changes

---

## Critical Files

| File | Action | Complexity |
|------|--------|-----------|
| `workflow/scripts/progress_utils.py` | Edit | Low |
| `workflow/scripts/feedback_utils.py` | **Create** | Medium |
| `workflow/skills/generate-research-questions/SKILL.md` | Edit | Medium |
| `workflow/skills/generate-research-questions/validate_research_questions.py` | Edit | Medium |
| `workflow/skills/score-and-rank/SKILL.md` | **Create** | High |
| `workflow/skills/orchestrator/SKILL.md` | Edit | **High** |
| `workflow/skills/acquire-data/SKILL.md` | Edit (path swap) | Low |
| `workflow/skills/statistical-analysis/SKILL.md` | Edit (path swap) | Low |
| `workflow/skills/generate-figures/SKILL.md` | Edit (path swap) | Low |
| `workflow/skills/literature-review/SKILL.md` | Edit (path swap) | Low |
| `workflow/skills/write-paper/SKILL.md` | Edit | Low-Medium |
| `.claude/CLAUDE.md` | Edit | Low |
