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

The manifest is a JSON array where each entry has:

```json
[
  {
    "name": "HPS_PUF",
    "description": "Household Pulse Survey microdata weeks 31-39",
    "target_dir": "HPS_PUF",
    "downloads": [
      {
        "url": "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2021/wk31/HPS_Week31_PUF_CSV.zip",
        "extract": true
      }
    ],
    "verify_patterns": ["*.csv"],
    "skip_patterns": ["*repwgt*", "*dictionary*"]
  }
]
```

**Fields:**
- `name`: Dataset identifier (used in reporting)
- `description`: What this data is for (included in README)
- `target_dir`: Subdirectory name inside `<output_folder>/data/`
- `downloads`: Array of download objects with:
  - `url`: Download URL
  - `extract`: Boolean, whether to extract archives
- `verify_patterns`: Optional glob patterns to verify expected files
- `skip_patterns`: Optional glob patterns to exclude certain files

**Important:** All downloads go to `<output_folder>/data/<target_dir>/`. Both Stage 0 and Stage 4 write to the same location. Example: `target_dir: "HPS_PUF"` → files downloaded to `<output_folder>/data/HPS_PUF/`.

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

1. Create target directory: `<output_folder>/data/<target_dir>/`
2. For each download URL:
   - Download with timeout=30 seconds
   - If `extract: true`, extract the archive
   - Retry once on failure

```python
import requests
import zipfile
from io import BytesIO

def download_entry(entry, output_folder):
    """Download a single manifest entry."""
    target_dir = Path(output_folder) / "data" / entry["target_dir"]
    target_dir.mkdir(parents=True, exist_ok=True)

    downloaded_files = []

    for dl in entry.get("downloads", []):
        url = dl["url"]
        should_extract = dl.get("extract", False)

        try:
            print(f"Downloading {url}...")
            r = requests.get(url, timeout=30)
            r.raise_for_status()

            filename = url.split("/")[-1]
            temp_path = target_dir / filename

            with open(temp_path, "wb") as f:
                f.write(r.content)

            if should_extract:
                print(f"  Extracting {filename}...")
                with zipfile.ZipFile(temp_path, 'r') as zf:
                    zf.extractall(target_dir)
                temp_path.unlink()  # Remove archive after extraction

            downloaded_files.append(filename)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    return downloaded_files
```

**Progress checkpoint:**
```python
downloaded_files = []
for entry in missing_downloads:
    files = download_entry(entry, output_folder)
    downloaded_files.extend(files)

update_step(output_folder, stage_name, "step_3_download", "completed",
             outputs=[f"data/{entry['target_dir']}" for entry in missing_downloads])
```

### Step 4: Verify Downloads

For each downloaded entry, verify files against `verify_patterns` if provided:

```python
def verify_entry(entry, output_folder):
    """Verify downloaded files match expected patterns."""
    target_dir = Path(output_folder) / "data" / entry["target_dir"]

    verify_patterns = entry.get("verify_patterns", [])
    if not verify_patterns:
        return True  # No verification required

    # Check that at least one file matches each pattern
    for pattern in verify_patterns:
        matching = list(target_dir.glob(pattern))
        if not matching:
            print(f"  WARNING: No files matching pattern '{pattern}'")
            return False

    return True
```

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

## Fallback Logic for Common Sources

While the manifest-driven design removes the need for source-specific logic from the main flow, you can maintain a helper function for known COVID data sources. This is optional but useful for Stage 4 when supplementary data is needed:

```python
COVID_FALLBACKS = {
    "nytimes": "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv",
    "jhu": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us.csv",
}

def get_fallback_url(variable_name: str) -> str | None:
    """Return a fallback URL for common public health data."""
    if "covid" in variable_name.lower() or "mortality" in variable_name.lower():
        return COVID_FALLBACKS["nytimes"]
    return None
```

This helper can be used when building the manifest in the orchestrator, not here.

## Output Contract

**Files created:**

1. **Downloaded data files:** `<output_folder>/data/<target_dir>/*`
2. **README:** `<output_folder>/data/README.md` — documents each file with one-sentence descriptions
3. **Download report:** `<output_folder>/0_data_acquisition/download_report.json` (Stage 0) or `<output_folder>/2_research_question/download_report.json` (Stage 4)

**Idempotency:** Running the skill twice with the same manifest will skip already-downloaded files.

**Graceful degradation:** Download failure → report in download_report.json with status="failed", pipeline proceeds with available data.
