# Reference: Orchestrator

## Table of Contents

1. [Stage Execution Table](#stage-execution-table)
2. [Feedback Loop Logic](#feedback-loop-logic)
3. [Time Budgets](#time-budgets)
4. [Data Flow Diagram](#data-flow-diagram)
5. [Data Acquisition Manifest](#data-acquisition-manifest)
6. [Output Contracts](#output-contracts)

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

## Data Acquisition Manifest

### Stage 0 Manifest (Initial Data Acquisition)

Build manifest from `Data_Description.md`:

```python
import json
from pathlib import Path

manifest = []

# Example: If Data_Description.md documents HPS_PUF with URLs
manifest.append({
    "name": "HPS_PUF",
    "description": "Household Pulse Survey microdata weeks 31-39",
    "target_dir": "HPS_PUF",
    "downloads": [
        {
            "url": "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2021/wk31/HPS_Week31_PUF_CSV.zip",
            "extract": True
        }
    ],
    "verify_patterns": ["*.csv"],
    "skip_patterns": ["*repwgt*", "*dictionary*"]
})

# Write manifest to file
manifest_path = Path(output_folder) / "0_data_acquisition" / "manifest.json"
manifest_path.parent.mkdir(parents=True, exist_ok=True)
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)
```

### Stage 4 Manifest (Supplementary Data)

Build manifest from `data_acquisition_requirements` in `ranked_questions.json`:

```python
import json
from pathlib import Path

# Read requirements
with open(f"{output_folder}/2_scoring/ranked_questions.json") as f:
    ranked = json.load(f)
data_reqs = ranked.get("data_acquisition_requirements", [])

# Build manifest
manifest = []
for req in data_reqs:
    manifest.append({
        "name": req.get("variable", "unknown"),
        "description": req.get("action", "Supplementary data for analysis"),
        "target_dir": req.get("target_dir", req.get("variable", "unknown")),
        "downloads": [
            {
                "url": req.get("url", ""),
                "extract": req.get("extract", False)
            }
        ]
    })

# Write manifest
manifest_path = Path(output_folder) / "2_research_question" / "download_manifest.json"
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)
```

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
