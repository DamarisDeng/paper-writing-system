# Context Management System

## Overview

The context management system prevents token overflow during pipeline execution by:
1. **Capturing semantic decisions** (why) rather than just raw outputs (what)
2. **Enabling pruning of verbose intermediate files** after checkpoint stages
3. **Providing compressed context views** for downstream stages

## Components

### 1. Context Bundle (`context_bundle.json`)

A layered semantic decision store that propagates high-value reasoning forward. Each stage adds exactly one layer capturing *why* decisions were made.

**Location:** `<output_folder>/context_bundle.json`

**Schema:**
```json
{
  "meta": {
    "version": "1.0",
    "created_at": "ISO-8601",
    "last_updated": "ISO-8601",
    "pipeline_stage": "current_stage",
    "cycle": 1,
    "max_cycles": 2,
    "completed_stages": ["load_and_profile", "score_and_rank"]
  },
  "layers": {
    "layer_1_load_and_profile": {
      "stage_name": "load_and_profile",
      "cycle": 1,
      "timestamp": "ISO-8601",
      "key_decisions": {
        "datasets_identified": {"value": ["data.csv"], "rationale": "Found in data folder"},
        "variable_classification_strategy": {"value": "automatic", "rationale": "..."}
      },
      "forward_references": {
        "for_generate_research_questions": ["datasets_identified"]
      },
      "outputs_produced": ["1_data_profile/profile.json"],
      "stage_summary": "Profiled 1 dataset"
    }
  }
}
```

### 2. Forget Mechanism

Selective context pruning with safety modes.

**Location:** `<output_folder>/context_config.json`

**Pruning Modes:**
- `safe` - Only prune after checkpoint stages (statistical_analysis, generate_figures, literature_review)
- `aggressive` - Prune after every eligible stage
- `off` - Disable all pruning

**Pruning Rules:**

| After Stage | Can Prune | Must Preserve |
|-------------|-----------|---------------|
| load_and_profile | profile.json (44KB) | variable_types.json, progress.json |
| score_and_rank | scoring_details.json | ranked_questions.json, decision_log |
| statistical_analysis | *.py scripts, *.txt models | analysis_results.json, analysis_plan.json |
| generate_figures | *.png source files | manifest.json, *.tex tables |
| literature-review | search_log.json | references.bib |

**Feedback Loop Protection:** Stages 3-5 cannot be pruned if `current_cycle < max_cycles`.

## API Reference

### `initialize_context_bundle(output_folder, cycle=1, max_cycles=2)`

Initialize a new context bundle for the pipeline run.

```python
from progress_utils import initialize_context_bundle

initialize_context_bundle(output_folder, cycle=1, max_cycles=2)
```

### `complete_stage_with_context(...)`

Mark stage complete and optionally add context layer + prune outputs.

```python
from progress_utils import complete_stage_with_context

result = complete_stage_with_context(
    output_folder=output_folder,
    stage_name="load_and_profile",
    context_mode="safe",  # or "aggressive" or "off"
    expected_outputs=["1_data_profile/profile.json"],
    summary="Profiled dataset(s)"
)
```

**Returns:** Dict with `progress`, `context_added`, `pruning_report`, `errors`

### `get_context_for_stage(output_folder, stage_name, include_raw=False)`

Query relevant context layers for a given stage.

```python
from context_manager import get_context_for_stage

context = get_context_for_stage(output_folder, "statistical_analysis")
# Returns summaries of all previous layers
```

### `can_prune_stage(output_folder, stage_name, mode="safe")`

Check if it's safe to prune outputs for a given stage.

```python
from context_manager import can_prune_stage

if can_prune_stage(output_folder, "statistical_analysis", mode="aggressive"):
    # Safe to prune
    pass
```

### `prune_stage_outputs(output_folder, stage_name, mode="safe", dry_run=False)`

Execute pruning rules for a completed stage.

```python
from context_manager import prune_stage_outputs

report = prune_stage_outputs(
    output_folder=output_folder,
    stage_name="statistical_analysis",
    mode="aggressive",
    dry_run=False
)
# Returns: {"deleted": [...], "preserved": [...], "space_freed_kb": ...}
```

## Usage Examples

### In the Orchestrator

```python
from progress_utils import (
    initialize_context_bundle,
    complete_stage_with_context
)

# At pipeline start
context_mode = kwargs.get("context_mode", "safe")
if context_mode != "off":
    initialize_context_bundle(output_folder)

# After each stage
result = complete_stage_with_context(
    output_folder=output_folder,
    stage_name=stage_name,
    context_mode=context_mode,
    expected_outputs=expected_outputs,
    summary=f"Completed {stage_name}"
)
```

### In Stage Skills

```python
# At stage end
from progress_utils import complete_stage_with_context

complete_stage_with_context(
    output_folder=output_folder,
    stage_name="statistical_analysis",
    context_mode="safe",
    expected_outputs=["3_analysis/analysis_results.json"],
    summary=f"Completed {method} analysis with N={n}, effect: {estimate}"
)
```

### Querying Context in Downstream Stages

```python
from context_manager import get_context_for_stage

# Get relevant context for current stage
context = get_context_for_stage(output_folder, "write_paper")

# Access previous layer summaries
for layer_key, summary in context["summaries"].items():
    print(f"{layer_key}: {summary['summary']}")

# Get specific decision
from context_manager import get_decision
selected = get_decision(output_folder, "selected_candidate_id")
```

## Testing

Run the test suite to verify the system works:

```bash
python workflow/scripts/test_context_manager.py
```

All 7 tests should pass:
1. Create Context Bundle
2. Add Layer
3. Get Context for Stage
4. Pruning Safety (Feedback Loop Protection)
5. Pruning Dry Run
6. Integration with progress_utils
7. Context Bundle Summary

## Benefits

1. **Reduced Token Usage:** Large JSON files (profile.json ~44KB, analysis_results.json ~16KB) are summarized rather than re-read in full
2. **Preserved Semantics:** Key decisions and rationale are captured, enabling downstream stages to understand *why* choices were made
3. **Graceful Degradation:** System works even if context_manager.py is unavailable (falls back to standard completion)
4. **Feedback Loop Safe:** Automatic protection prevents pruning of stages that may re-run
5. **Resume Compatible:** Pruning preserves all files needed for resume functionality

## Migration Path

The system is **backward compatible**. Existing stages work unchanged:
- Context functions are opt-in via `complete_stage_with_context()`
- Standard `complete_stage()` continues to work
- No breaking changes to existing files

To adopt incrementally:
1. Start with stages 1, 3, 5 (highest value)
2. Add `complete_stage_with_context()` calls
3. Test with `context_mode=off` first
4. Enable `context_mode=safe` for normal operation
5. Use `context_mode=aggressive` only for long-running pipelines
