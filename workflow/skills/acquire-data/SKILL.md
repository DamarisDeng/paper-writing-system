---
name: acquire-data
model: low
description: >
  Stateless data downloader that reads a download manifest and acquires datasets.
  Used twice in the pipeline: Stage 0 (documented datasets from Data_Description.md)
  and Stage 4 (supplementary data from research_questions.json).
  Takes a manifest path as input, downloads files to data/[target_dir]/.
argument-hint: "[output_folder] [manifest_path]"
---

# Acquire Data

Stateless downloader that reads a download manifest and acquires datasets. Used twice in the pipeline: Stage 0 (documented datasets from Data_Description.md) and Stage 4 (supplementary data from research_questions.json).

## Usage

```
/acquire-data <output_folder> <manifest_path>
```

- `<output_folder>`: Base output directory (e.g., `exam_paper`)
- `<manifest_path>`: Path to the download manifest JSON file

Downloads files to `<output_folder>/data/<target_dir>/` and creates `<output_folder>/data/README.md` and download report.

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking.

**Stage 0:** Progress saved to `<output_folder>/0_data_acquisition/progress.json`
**Stage 4:** Progress saved to `<output_folder>/2_research_question/progress.json` (shared with generate-research-questions stage)

**Steps tracked:**
- `step_1_read_manifest`: Read manifest JSON
- `step_2_check_existing`: Check what's already on disk
- `step_3_download`: Download missing files
- `step_4_verify`: Verify downloads against patterns
- `step_5_document`: Write README.md and download report

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

## Manifest Schema

The manifest is a JSON array where each entry has `name`, `description`, `target_dir`, `downloads`, `verify_patterns`, and `skip_patterns`.

See `references/REFERENCE.md: Manifest Schema` for the complete manifest structure and field definitions.

**Important:** All downloads go to `<output_folder>/data/<target_dir>/`. Both Stage 0 and Stage 4 write to the same location.

## Instructions

You are a stateless data downloader. Follow these steps:

**Initialize progress tracker at start:**
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker, update_step, complete_stage

# Determine stage name based on manifest path for progress tracking
if "0_data_acquisition" in manifest_path or manifest_path.endswith("manifest.json"):
    stage_name = "acquire_data_stage0"
    progress_dir = "0_data_acquisition"
else:
    stage_name = "acquire_data"
    progress_dir = "2_research_question"

tracker = create_stage_tracker(output_folder, stage_name,
    ["step_1_read_manifest", "step_2_check_existing", "step_3_download",
     "step_4_verify", "step_5_document"])
```

### Step 1: Read the Manifest

Read the manifest JSON from the provided path:

```python
import json
from pathlib import Path

manifest_path = Path(args[1])
with open(manifest_path) as f:
    manifest = json.load(f)
```

If the manifest is empty or not found, report the error and exit.

**Progress checkpoint:**
```python
update_step(output_folder, stage_name, "step_1_read_manifest", "completed")
```

### Step 2: Check What's Already on Disk

For each entry in the manifest, check if target files already exist in `<output_folder>/data/<target_dir>/`. This provides idempotency — re-running the skill won't re-download existing files.

```python
data_base = Path(output_folder) / "data"
missing_downloads = []

for entry in manifest:
    target_dir = data_base / entry["target_dir"]
    # Check if expected files exist
    if target_dir.exists() and list(target_dir.glob("*.csv")):
        print(f"[SKIP] {entry['name']} already present in {entry['target_dir']}/")
    else:
        missing_downloads.append(entry)
```

**Progress checkpoint:**
```python
update_step(output_folder, stage_name, "step_2_check_existing", "completed")
```

### Step 3: Download Missing Files

For each entry that needs downloading:
1. Create target directory
2. Download with timeout=30 seconds
3. Extract archives if `extract: true`
4. Retry once on failure

See `references/REFERENCE.md: Download Logic` for the complete download function implementation.

### Step 4: Verify Downloads

For each downloaded entry, verify files against `verify_patterns` if provided.

See `references/REFERENCE.md: Verification` for the verification function.

**Progress checkpoint:**
```python
update_step(output_folder, stage_name, "step_4_verify", "completed")
```

### Step 5: Write Documentation

Create two documentation files:

**5.1: `<output_folder>/data/README.md`** — Lists all files with descriptions:

```markdown
# Data Files

## HPS_PUF/
- pulse2021_puf_31.csv: Week 31 Household Pulse Survey microdata with vaccination responses
- pulse2021_puf_32.csv: Week 32 Household Pulse Survey microdata with vaccination responses

## covid_deaths/
- us-states.csv: NY Times COVID-19 case and death data by state (downloaded as supplementary outcome data)
```

**5.2: Download report JSON** — Written to the appropriate location:
- Stage 0: `<output_folder>/0_data_acquisition/download_report.json`
- Stage 4: `<output_folder>/2_research_question/download_report.json`

```json
{
  "datasets": [
    {
      "name": "HPS_PUF",
      "status": "downloaded|already_present|failed",
      "files_acquired": ["pulse2021_puf_31.csv", ...],
      "source": "https://...",
      "purpose": "Individual-level vaccination survey data for HCW vaccine uptake analysis"
    }
  ]
}
```

**Progress checkpoint - Mark stage complete:**
```python
update_step(output_folder, stage_name, "step_5_document", "completed")

# Determine expected outputs based on stage
if progress_dir == "0_data_acquisition":
    expected_outputs = ["data/README.md", "0_data_acquisition/download_report.json"]
else:
    expected_outputs = ["data/README.md", "2_research_question/download_report.json"]

complete_stage(output_folder, stage_name, expected_outputs=expected_outputs)
```

## Output Contract

See `references/REFERENCE.md: Output Contract` for files created and behavior notes.

**Files created:**

1. **Downloaded data files:** `<output_folder>/data/<target_dir>/*`
2. **README:** `<output_folder>/data/README.md` — documents each file with one-sentence descriptions
3. **Download report:** `<output_folder>/0_data_acquisition/download_report.json` (Stage 0) or `<output_folder>/2_research_question/download_report.json` (Stage 4)

**Idempotency:** Running the skill twice with the same manifest will skip already-downloaded files.

**Graceful degradation:** Download failure → report in download_report.json with status="failed", pipeline proceeds with available data.
