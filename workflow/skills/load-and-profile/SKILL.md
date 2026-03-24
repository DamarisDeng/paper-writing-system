---
name: load-and-profile
model: medium
description: >
  Load and profile any dataset folder. Clean data, inspect structure,
  and produce profile.json and variable_types.json for downstream stages.
  Use this skill at the start of the pipeline to understand available data.
argument-hint: <data_folder>
---

# Load and Profile Data

Load any dataset folder, clean it, and produce `profile.json` + `variable_types.json` for downstream pipeline stages.

## Usage
```
/load-and-profile <data_folder>
```

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/1_data_profile/progress.json`.

**Steps tracked:**
- `step_1_read_description`: Read data description files
- `step_2_inspect_files`: Inspect raw file structure
- `step_3_run_profiling`: Execute profiling script
- `step_4_enrich_output`: Review and enrich outputs
- `step_5_save_final`: Save and validate final outputs

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

## Instructions

You are an expert data scientist. Follow these steps exactly:

### Step 1: Read & Understand the Data Description

- Look for `Data_Description.md` or any `.md` files in `<data_folder>`.
- Read them thoroughly. Understand what each dataset represents, what the variables mean, and how the datasets relate to each other.
- If no description file exists, note that you will rely solely on inspection.

**Progress checkpoint:** After completing this step, update progress:
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker, update_step

# At stage start
tracker = create_stage_tracker(output_folder, "load_and_profile",
    ["step_1_read_description", "step_2_inspect_files",
     "step_3_run_profiling", "step_4_enrich_output", "step_5_save_final"])

# After step 1
update_step(output_folder, "load_and_profile", "step_1_read_description", "completed")
```

### Step 2: Inspect the Raw Files

- Peek at the first few rows of each CSV/XLSX file in `<data_folder>` using pandas (via a quick Python snippet or by reading the file).
- Verify alignment with the description.
- Note any structural issues: multi-row headers in XLSX, metadata rows, encoding issues, etc.

**Progress checkpoint:**
```python
update_step(output_folder, "load_and_profile", "step_2_inspect_files", "completed")
```

### Step 3: Run the Profiling Script

**Note:** This script is located within the skill directory at `workflow/skills/load-and-profile/`,
not in the shared `workflow/scripts/` folder (which contains only shared utilities like `progress_utils.py`).

**Choose the appropriate profiler:**

**Option A: Standard profiler** (for small/medium datasets <100MB total):
```bash
python workflow/skills/load-and-profile/load_and_profile.py <data_folder> <output_folder>/1_data_profile
```

**Option B: Quick profiler** (for large datasets or when efficiency matters):
```bash
python workflow/scripts/quick_profile.py <data_folder> <output_folder>/1_data_profile
```

The quick profiler uses a smart sampling strategy:
1. Reads `Data_Description.md` first for context
2. Samples first 10K rows of each file for structure
3. Reads data dictionary if available for variable meanings
4. Uses dictionary info to guide interpretation
5. Produces same output format with significantly less time

**Recommendation:** Use quick_profile.py for HPS data, large surveys, or any dataset with accompanying data dictionaries. Use standard load_and_profile.py only for small, simple datasets without documentation.

This produces `<output_folder>/1_data_profile/profile.json` and `<output_folder>/1_data_profile/variable_types.json` with mechanical profiling.

**Progress checkpoint:**
```python
update_step(output_folder, "load_and_profile", "step_3_run_profiling", "completed",
             outputs=["1_data_profile/profile.json", "1_data_profile/variable_types.json"])
```

### Step 4: Review & Enrich the Output

Read the generated `<output_folder>/1_data_profile/profile.json` and `<output_folder>/1_data_profile/variable_types.json`. Use your judgment to:

1. **Fix misclassified variable types** in `variable_types.json`:
   - Zip codes, FIPS codes, phone numbers detected as `numeric` → change to `categorical` or `identifier`
   - Date strings that failed parsing → change to `datetime`
   - IDs or codes that are semantically categorical → reclassify
   - Apply domain knowledge from the data description

2. **Add a `data_context` field** to the top level of `profile.json`:
   ```json
   {
     "data_context": {
       "summary": "Brief description of what this data collection is about",
       "dataset_relationships": "How the datasets relate to each other (e.g., linkable by state, joinable on date)",
       "research_directions": ["Potential research question 1", "Potential research question 2"],
       "data_quality_notes": ["Any issues found: missing data patterns, suspicious values, etc."]
     },
     "datasets": { ... }
   }
   ```

3. **Flag data quality issues**:
   - Columns with >50% missing values
   - Unexpected value ranges
   - Datasets that may need filtering (e.g., metadata rows in what should be data)

**Progress checkpoint:**
```python
update_step(output_folder, "load_and_profile", "step_4_enrich_output", "completed")
```

### Step 5: Save Final Outputs

Write the corrected files back to:
- `<output_folder>/1_data_profile/profile.json` (with `data_context` added and any fixes)
- `<output_folder>/1_data_profile/variable_types.json` (with any type corrections)

Confirm both files are valid JSON.

**Progress checkpoint - Mark stage complete:**
```python
from progress_utils import complete_stage, complete_stage_with_context

# Option 1: Standard completion (no context tracking)
complete_stage(output_folder, "load_and_profile",
               expected_outputs=["1_data_profile/profile.json",
                                 "1_data_profile/variable_types.json"])

# Option 2: Context-aware completion (recommended for pipeline mode)
#    This automatically extracts key decisions and adds to context bundle
complete_stage_with_context(
    output_folder=output_folder,
    stage_name="load_and_profile",
    context_mode="safe",  # or "aggressive" or "off"
    expected_outputs=["1_data_profile/profile.json",
                      "1_data_profile/variable_types.json"],
    summary="Loaded and profiled dataset(s), classified variable types"
)
```

**Context Decisions Captured** (when using `complete_stage_with_context`):
- `datasets_identified`: List of datasets found
- `variable_classification_strategy`: How variables were typed
- `data_limitations_identified`: Data quality issues noted
- `data_context_summary`: Research directions and dataset relationships

## Output Contract

Downstream stages consume these two files:

**`profile.json`** — Dataset shapes, column stats, and LLM-generated context:
```json
{
  "data_context": { "summary": "...", "dataset_relationships": "...", "research_directions": [...], "data_quality_notes": [...] },
  "datasets": {
    "filename.csv": {
      "file_path": "...",
      "shape": [rows, cols],
      "columns": {
        "col_name": {
          "dtype": "float64",
          "missing_count": 5, "missing_pct": 2.3,
          "unique_count": 42,
          "sample_values": ["val1", "val2", "val3"],
          "mean": 5.2, "std": 1.3, "min": 0, "max": 10, "median": 5.0,
          "top_values": {"a": 10, "b": 8}
        }
      }
    }
  }
}
```

**`variable_types.json`** — Semantic type for every column:
```json
{
  "filename.csv": {
    "col_name": "numeric|categorical|datetime|text|binary|identifier"
  }
}
```
