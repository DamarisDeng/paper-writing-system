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

## Instructions

You are an expert data scientist. Follow these steps exactly:

### Step 1: Read & Understand the Data Description

- Look for `Data_Description.md` or any `.md` files in `<data_folder>`.
- Read them thoroughly. Understand what each dataset represents, what the variables mean, and how the datasets relate to each other.
- If no description file exists, note that you will rely solely on inspection.

### Step 2: Inspect the Raw Files

- Peek at the first few rows of each CSV/XLSX file in `<data_folder>` using pandas (via a quick Python snippet or by reading the file).
- Verify alignment with the description.
- Note any structural issues: multi-row headers in XLSX, metadata rows, encoding issues, etc.

### Step 3: Run the Profiling Script

Run the Python profiling script:

```bash
python workflow/skills/load-and-profile/load_and_profile.py <data_folder> <output_folder>/1_data_profile
```

This produces `<output_folder>/1_data_profile/profile.json` and `<output_folder>/1_data_profile/variable_types.json` with mechanical profiling.

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

### Step 5: Save Final Outputs

Write the corrected files back to:
- `<output_folder>/1_data_profile/profile.json` (with `data_context` added and any fixes)
- `<output_folder>/1_data_profile/variable_types.json` (with any type corrections)

Confirm both files are valid JSON.

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
