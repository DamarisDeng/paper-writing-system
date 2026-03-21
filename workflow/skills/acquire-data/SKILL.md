---
name: acquire-data
model: low
description: >
  Download external data files specified in research_questions.json data_acquisition_requirements.
  Reads the output from /generate-research-questions and downloads required datasets
  with automatic fallback to alternative sources if primary URLs fail.
  Use this skill after /generate-research-questions when data needs to be acquired from external sources.
argument-hint: <output_folder>
---

# Acquire Data

Download external data files specified in `data_acquisition_requirements` to support the research analysis.

## Usage

```
/acquire-data <output_folder>
```

Reads from `<output_folder>/2_research_question/research_questions.json` and writes downloaded files to `<output_folder>/2_research_question/downloaded/`.

## Instructions

You are responsible for acquiring the data needed for the research analysis. Follow these steps:

### Step 1: Load Research Questions

Read `<output_folder>/2_research_question/research_questions.json` and extract the `data_acquisition_requirements` array.

If `data_acquisition_requirements` is empty or missing, report that no data acquisition is needed and exit successfully.

### Step 2: Create Download Directory

Create the directory `<output_folder>/2_research_question/downloaded/` if it doesn't exist.

### Step 3: For Each Requirement — Use Fallback Strategy

For each entry in `data_acquisition_requirements`, use a **fallback strategy**:

**Primary approach:** Try the URLs from the source dataset
**Fallback approach:** Use known alternative sources for common public health data

#### 3.1 Parse the Requirement

- `variable`: Name of the variable to acquire (e.g., "covid_mortality_rate")
- `source_column`: Which column contains the download URLs
- `target_file`: Where to save the downloaded data
- `action`: Description of what to download

#### 3.2 Try Primary URLs, Then Fallbacks

**Attempt 1: Direct URLs from profile**
- Read `<output_folder>/1_data_profile/profile.json`
- Extract URLs from the `source_column` sample values
- Try each URL with timeout=30 seconds

**Attempt 2: Parse Archive Link format**
- If URLs point to S3/archive index files with comma-separated endpoints
- Extract the CSV endpoint (typically first one)
- Try the extracted endpoint

**Attempt 3: Known fallback sources for common data**

If the variable mentions COVID-19, mortality, cases, or deaths, use these fallbacks:

| Variable Type | Primary Fallback | URL | Notes |
|---------------|------------------|-----|-------|
| State COVID deaths/cases | NY Times GitHub | `https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv` | Daily data, all 50 states + territories |
| State COVID deaths/cases | JHU CSSE GitHub | `https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us.csv` | Daily reports format |
| State COVID deaths | CDC Wonder API | (requires web query) | Mortality data, not real-time |

#### 3.3 Download and Process

For each successful download:
1. Parse the data (CSV, JSON, or delimited text)
2. Subset to the study period if specified in the `action`
3. Validate the data has expected columns (date, state, deaths/cases)
4. Save to the exact `target_file` path
5. Record the actual source used (primary vs fallback) in a README

### Step 4: Handle Common Failure Modes

**404 errors:** Dataset deprecated → immediately try fallback source
**Timeout errors:** Retry once with longer timeout (60s)
**Parse errors:** Try different delimiters (comma, tab, pipe)
**Empty files:** URL returned redirect page → try fallback

### Step 5: Verify and Document

For each downloaded file:
1. Check file exists and is >1000 bytes
2. For CSV: verify row count and column names
3. Create `downloaded/README.md` documenting:
   - Original source URL (if available)
   - Actual source used (if fallback was used)
   - Date range covered
   - Number of rows/states
   - Any data quality notes

### Step 6: Report Summary

Output:
- Files downloaded and their sizes
- Whether primary or fallback source was used
- Row counts and date ranges
- Any warnings or issues

## Known Working Data Sources

Always try these sources for COVID-19/state-level health data:

```python
COVID_FALLBACKS = {
    "nytimes": "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv",
    "jhu": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us.csv",
    "jhu_timeseries": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
}
```

## Download Script Pattern

Use this robust download pattern:

```python
import requests
import pandas as pd
from pathlib import Path
from io import StringIO

COVID_FALLBACKS = {
    "nytimes": "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv",
    "jhu": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us.csv"
}

def download_with_fallback(variable_name: str, target_file: Path, study_start: str = None, study_end: str = None):
    """Download data with fallback to known sources."""

    # Try fallbacks first for COVID data (more reliable)
    if "covid" in variable_name.lower() or "mortality" in variable_name.lower():
        for name, url in COVID_FALLBACKS.items():
            try:
                print(f"Trying {name}: {url}")
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                df = pd.read_csv(StringIO(r.text))

                # Subset to study period if specified
                if study_start and 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df[(df['date'] >= study_start) & (df['date'] <= study_end)]

                df.to_csv(target_file, index=False)
                print(f"SUCCESS: Downloaded {len(df)} rows from {name}")
                return True

            except Exception as e:
                print(f"  {name} failed: {e}")
                continue

    return False  # All attempts failed
```

## Output Contract

Creates files in `<output_folder>/2_research_question/downloaded/`:

- The data files specified in `data_acquisition_requirements`
- `README.md` documenting sources used and data characteristics
