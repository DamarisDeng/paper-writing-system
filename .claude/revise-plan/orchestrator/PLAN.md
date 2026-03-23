# Revision Plan: orchestrator

## Current State

- **Lines**: 498
- **Structure**: SKILL.md only
- **Naming**: "orchestrator" — noun form, clear and descriptive ✓

---

## Core Problems

1. **At 500-line limit** (risky for future additions)
2. **Stage execution table inline** (lines 226-240, 15 rows)
3. **Feedback loop logic inline** (lines 241-320, 79 lines)
4. **Time budgets table inline** (lines 371-389, 19 rows)
5. **Data flow diagram inline** (lines 392-431, 40 lines)
6. **JSON schemas inline** (lines 449-498, 50 lines)

---

## Target State

- **SKILL.md target**: ~280 lines (44% reduction)
- **New structure**:
  ```
  orchestrator/
  ├── SKILL.md (~280 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 0-4)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (keep "orchestrator")

---

## Orchestrator Compatibility

This skill INVOKES all other skills. After revision:
- All skill invocations remain unchanged (`/skill-name`)
- Stage execution table keeps current skill names
- No changes to how skills are called

---

## Detailed Content Extraction Plan

### 1. Stage Execution Table (lines 226-240)

**Extract to:** `REFERENCE.md` > "Stage Execution Table"

**Keep in SKILL.md:** Brief reference with link
> See REFERENCE.md: Stage Execution Table for validation checks and degraded fallbacks.

### 2. Feedback Loop Logic (lines 241-320)

**Extract to:** `REFERENCE.md` > "Feedback Loop Logic"

**Keep in SKILL.md:**
- Summary sentence about feedback loop purpose
- Link to REFERENCE.md for detailed implementation
- Fast-track mode summary (3 lines max)

### 3. Time Budgets (lines 371-389)

**Extract to:** `REFERENCE.md` > "Time Budgets"

**Keep in SKILL.md:**
- Single summary paragraph: "Target completion is 61 min happy path, up to 75 min with feedback loop."
- Link to REFERENCE.md for detailed per-stage breakdown

### 4. Data Flow Diagram (lines 392-431)

**Extract to:** `REFERENCE.md` > "Data Flow Diagram"

**Keep in SKILL.md:**
- Brief note: "Both Stage 0 and Stage 4 write to the same `<output_folder>/data/` directory."
- Link to REFERENCE.md for full diagram

### 5. JSON Schemas (lines 449-498)

**Extract to:** `REFERENCE.md` > "Output Contracts"

**Keep in SKILL.md:**
- Output file locations only (what files, not schemas)
- Link to REFERENCE.md for schema details

---

## New REFERENCE.md Structure

```markdown
# Reference: Orchestrator

## Table of Contents

1. [Stage Execution Table](#stage-execution-table)
2. [Feedback Loop Logic](#feedback-loop-logic)
3. [Time Budgets](#time-budgets)
4. [Data Flow Diagram](#data-flow-diagram)
5. [Output Contracts](#output-contracts)

---

## Stage Execution Table

| Stage | Skill | Validation Check | Degraded Fallback |
|-------|-------|-----------------|-------------------|
| 0 | acquire-data (Stage 0) | `data/README.md` exists, documented datasets downloaded | Skip — proceed with available data only |
| 1 | load-and-profile | `profile.json` and `variable_types.json` exist with >0 datasets | Generate minimal profile from file headers only |
| 2 | generate-research-questions | `research_questions.json` has `candidate_questions` array with ≥2 candidates | Use first numeric column as outcome, first categorical as exposure |
| 3 | score-and-rank | `ranked_questions.json` exists with `primary_question` and `selection_metadata` | Use first candidate from `research_questions.json` as-is |
| 4 | acquire-data (Stage 4) | Downloaded files exist (or `data_acquisition_requirements` is empty) | Skip — proceed with available data only |
| 5 | statistical-analysis | `analysis_results.json` exists with `descriptive_statistics` and `primary_analysis` | Run descriptive stats only, skip regression |
| 6 | generate-figures | At least 2 `.png` files in `figures/` and 1 `.tex` file in `tables/` | Generate Table 1 only as a LaTeX table |
| 7 | literature-review | `references.bib` has ≥10 `@article` entries | Use 10 foundational public health references |
| 8 | write-paper | `paper.tex` exists and is >5KB | Generate a minimal paper with abstract + methods + results |
| 9 | compile-and-review | `paper.pdf` exists in `<output_folder>/` and `<output_folder>/6_paper/` | Return the `.tex` file as final output |

---

## Feedback Loop Logic

### When It Triggers

After Stage 5 (statistical-analysis) completes, check for structural analysis failures.

### Detection Code

```python
from feedback_utils import build_feedback_signal
from progress_utils import get_cycle_state, save_cycle_state, reset_stage_progress

cycle_state = get_cycle_state(output_folder)
feedback_signal = build_feedback_signal(output_folder)

if feedback_signal is not None and feedback_signal["recommendation"] == "retry_next_candidate":
    # Execute feedback loop...
```

### Feedback Loop Flow

1. Record failure in cycle state
2. Reset progress for stages 3-5
3. Update context bundle with feedback cycle
4. Re-run Stage 3 (score-and-rank) in FAST-TRACK mode
5. Re-run Stage 4 (acquire-data)
6. Re-run Stage 5 (statistical-analysis) in FAST-TRACK mode
7. Clear feedback loop flag

### Fast-Track Mode Details

- **Stage 3 re-run**: Skips web searches, reuses prior `scoring_details.json`, applies score penalty (0.0) to failed candidate, re-ranks remaining candidates.
- **Stage 4 re-run**: Mostly skipped if data acquisition requirements are the same.
- **Stage 5 re-run**: Run primary model + Table 1 only, skip sensitivity analyses. Target: 10 min.
- **Total feedback re-run budget**: 14 min.

### Context Management Note

During feedback loop cycles, pruning of stages 3-5 is automatically disabled regardless of `context_mode` setting. This preserves files needed for re-ranking and re-analysis.

---

## Time Budgets

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

---

## Data Flow Diagram

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

---

## Output Contracts

### pipeline_log.json

**Location:** `<output_folder>/pipeline_log.json`

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

### cycle_state.json

**Location:** `<output_folder>/cycle_state.json`

```json
{
  "current_cycle": 1,
  "max_cycles": 2,
  "feedback_history": []
}
```

### decision_log.json

**Location:** `<output_folder>/decision_log.json`

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

### paper.pdf

**Location:** `<output_folder>/paper.pdf`

The final deliverable at output root. Must exist unless stage 9 failed after 3 retries.
```

---

## Files to Create

- `workflow/skills/orchestrator/references/REFERENCE.md`

---

## Files to Modify

- **`workflow/skills/orchestrator/SKILL.md`**:
  - Lines 226-240 → replace with link to REFERENCE.md: Stage Execution Table
  - Lines 241-320 → replace with summary + link to REFERENCE.md: Feedback Loop
  - Lines 371-389 → replace with summary + link to REFERENCE.md: Time Budgets
  - Lines 392-431 → replace with note + link to REFERENCE.md: Data Flow
  - Lines 449-498 → replace with file locations + link to REFERENCE.md: Output Contracts
  - Keep all skill invocations unchanged (`/acquire-data`, `/load-and-profile`, etc.)

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 15 | 15 | No change |
| Usage/Progress | 65 | 65 | No change |
| Instructions | 180 | 180 | Core steps |
| Stage table | 15 | 3 | Keep 3 lines + link |
| Feedback loop | 79 | 5 | Keep summary + link |
| Time budgets | 19 | 3 | Keep summary + link |
| Data flow | 40 | 3 | Keep note + link |
| JSON schemas | 50 | 9 | Keep locations + link |
| Other cleanup | -50 | 0 | Remove redundant content |
| **Total** | **498** | **~280** | 44% reduction |

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~280)
- [ ] REFERENCE.md has TOC
- [ ] Stage execution table moved to REFERENCE.md
- [ ] Feedback loop logic moved to REFERENCE.md
- [ ] Time budgets moved to REFERENCE.md
- [ ] Data flow diagram moved to REFERENCE.md
- [ ] JSON schemas moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] All skill invocations remain unchanged
- [ ] No information lost in extraction
- [ ] Orchestrator can still invoke all skills correctly
- [ ] Pipeline flow documented in REFERENCE.md
