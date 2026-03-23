# Reference: Acquire Data

## Table of Contents

1. [Manifest Schema](#manifest-schema)
2. [Download Logic](#download-logic)
3. [Verification](#verification)
4. [Fallback URLs](#fallback-urls)

---

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

**Important:** All downloads go to `<output_folder>/data/<target_dir>/`. Both Stage 0 and Stage 4 write to the same location.

---

## Download Logic

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

**Key behaviors:**
- Download with timeout=30 seconds
- Retry once on failure
- Extract archives if `extract: true`
- Create target directory if needed

---

## Verification

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

---

## Fallback URLs

For common public health data sources, maintain fallback URLs:

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

This helper can be used when building the manifest in the orchestrator.

---

## Output Contract

**Files created:**

1. **Downloaded data files:** `<output_folder>/data/<target_dir>/*`
2. **README:** `<output_folder>/data/README.md` — documents each file with one-sentence descriptions
3. **Download report:** `<output_folder>/0_data_acquisition/download_report.json` (Stage 0) or `<output_folder>/2_research_question/download_report.json` (Stage 4)

**Idempotency:** Running the skill twice with the same manifest will skip already-downloaded files.

**Graceful degradation:** Download failure → report in download_report.json with status="failed", pipeline proceeds with available data.
