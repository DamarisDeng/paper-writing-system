# Plan: Two-Pass Data Acquisition (v3)

## Current Pipeline

```
Stage 1: load-and-profile              → profile what's on disk
Stage 2: generate-research-questions    → pick question from profiled variables
Stage 3: score-and-rank
Stage 4: acquire-data                   → download from research_questions.json
Stage 5: statistical-analysis
Stage 6–9: figures, lit review, paper, compile
```

## Problem

`Data_Description.md` documents datasets with download instructions, but nothing executes them before profiling. The question generator only sees what's on disk, picks the wrong question, and acquire-data only fetches what the question generator asked for. Circular dependency.

## Proposed Pipeline

```
Stage 0: orchestrator builds manifest from Data_Description.md
         → acquire-data downloads it
Stage 1: load-and-profile              → profile everything (now complete)
Stage 2: generate-research-questions    → find best question
Stage 3: score-and-rank
Stage 4: orchestrator passes data_acquisition_requirements
         → acquire-data downloads it
Stage 5: statistical-analysis
Stage 6–9: ...
```

**acquire-data does the same thing both times:** receive a manifest, download it. The orchestrator decides what goes in the manifest.

---

## Design Principle

acquire-data is a **stateless downloader**. It takes a download manifest as input and produces files + a report as output. It doesn't know or care whether the manifest came from `Data_Description.md` or `research_questions.json`. The orchestrator constructs the manifest from whatever source is relevant at that pipeline stage.

---

## What Changes

### 1. acquire-data/SKILL.md — Simplify to manifest-driven

**Remove** the current coupling to `ranked_questions.json`. The skill's input contract becomes:

**Input:** A download manifest at a specified path — a JSON array where each entry has:

```json
[
  {
    "name": "HPS_PUF",
    "description": "Household Pulse Survey microdata weeks 31-39",
    "target_dir": "data/HPS_PUF",
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

**Important:** All downloads go to `<output_folder>/data/<target_dir>/`. Both Stage 0 and Stage 4 write to the same location. Example: `target_dir: "HPS_PUF"` → files downloaded to `<output_folder>/data/HPS_PUF/`.

**Output:** Downloaded files on disk + `download_report.json` + `README.md` in `<output_folder>/data/`:

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

**Also creates `<output_folder>/data/README.md`** documenting each file with one sentence:
```markdown
# Data Files

## HPS_PUF/
- pulse2021_puf_31.csv: Week 31 Household Pulse Survey microdata with vaccination responses
- pulse2021_puf_32.csv: Week 32 Household Pulse Survey microdata with vaccination responses
- ...

## covid_deaths/
- us-states.csv: NY Times COVID-19 case and death data by state (downloaded as supplementary outcome data)
```

**The skill's steps become:**

1. Read the manifest JSON from the path it's given
2. For each entry, check if target files already exist (idempotency)
3. Download missing files, extract archives, retry on failure
4. Verify against `verify_patterns`
5. Write/update `<output_folder>/data/README.md` with file descriptions
6. Write `download_report.json`

That's it. The fallback logic for common COVID data sources can stay as a helper, but the skill no longer reads `ranked_questions.json` directly — it receives a manifest.

### 2. orchestrator/SKILL.md — Two manifest-building steps

The orchestrator gains responsibility for constructing the manifest at each pass.

**Stage 0 (before profiling):**

The orchestrator (which is LLM-driven and can read markdown) does:

1. Read `Data_Description.md` from `<data_folder>`
2. For each documented dataset that includes download instructions, build a manifest entry
3. Check what's already on disk in `<output_folder>/data/`, include only what's missing
4. Write manifest to `<output_folder>/0_data_acquisition/manifest.json`
5. Call acquire-data with that manifest path
6. acquire-data writes `<output_folder>/0_data_acquisition/download_report.json`
7. acquire-data creates `<output_folder>/0_data_acquisition/progress.json` for resume capability

**Stage 4 (after question generation):**

The orchestrator does:

1. Read `data_acquisition_requirements` from `ranked_questions.json`
2. Translate to the same manifest schema
3. Write manifest to `<output_folder>/2_research_question/download_manifest.json`
4. Call acquire-data with that manifest path
5. acquire-data writes files to `<output_folder>/data/` (same location as Stage 0)
6. acquire-data updates `<output_folder>/data/README.md` with new file descriptions
7. acquire-data writes `<output_folder>/2_research_question/download_report.json`

This is natural work for the orchestrator — it already reads upstream outputs and sets up downstream inputs at every stage boundary.

### 3. load-and-profile/load_and_profile.py — Recurse into subdirectories

`scan_data_files()` uses `rglob` with a skip list:

```python
def scan_data_files(data_folder: str) -> list[Path]:
    """Find all CSV and XLSX files in the data folder and subdirectories."""
    folder = Path(data_folder)
    files = []
    skip_names = {"__MACOSX", ".git", "downloaded"}

    for f in sorted(folder.rglob("*")):
        if any(part.startswith(".") for part in f.parts):
            continue
        if any(skip in f.parts for skip in skip_names):
            continue
        lower_name = f.name.lower()
        if any(kw in lower_name for kw in ("dictionary", "readme", "repwgt", "replicate")):
            continue
        if f.suffix.lower() in (".csv", ".xlsx"):
            files.append(f)
    return files
```

**Critical fix:** Change `main()` to use relative paths as dictionary keys to avoid filename collisions:

```python
def main():
    # ... existing setup ...

    for path in files:
        # Use relative path as key to avoid collisions when subdirectories
        # have files with the same name (e.g., data/HPS_PUF/file.csv and other/file.csv)
        rel_path = path.relative_to(data_folder)
        # ...
        all_profiles[str(rel_path)] = profile
        all_types[str(rel_path)] = types
```

### 4. load-and-profile/SKILL.md — Minor addition

Step 1: if `0_data_acquisition/download_report.json` exists, read it for context on newly acquired datasets.

### 5. generate-research-questions/SKILL.md — No changes

Existing logic handles arbitrary outcome variables correctly once they appear in the profile.

---

## Files to Modify

| File | Action | Summary |
|------|--------|---------|
| `workflow/skills/acquire-data/SKILL.md` | **Rewrite** | Manifest-driven input instead of reading `ranked_questions.json` directly |
| `workflow/skills/load-and-profile/load_and_profile.py` | **Modify** | `scan_data_files()` → recursive with skip list |
| `workflow/skills/load-and-profile/SKILL.md` | **Modify** | Step 1: note download_report.json as optional context |
| `workflow/skills/orchestrator/SKILL.md` | **Modify** | Add Stage 0 (build manifest from docs + call acquire-data), update Stage 4 (build manifest from research_questions + call acquire-data), update time budget and data flow |

**Not modified:** `generate-research-questions/SKILL.md`, `statistical-analysis/SKILL.md`.

---

## Data Flow

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
  ↓
Stage 6–9 → paper.pdf
```

---

## Time Budget

| Stage | Time |
|-------|------|
| 0. Acquire documented data | 5 min |
| 1. Load & Profile | 5 min |
| 2. Research Questions | 5 min |
| 3. Score & Rank | 3 min |
| 4. Acquire supplementary data | 3 min |
| 5. Statistical Analysis | 13 min |
| 6–9 | 27 min |
| **Total** | **61 min** |

---

## Verification

1. **Stage 0:** Orchestrator parses `Data_Description.md`, builds manifest with HPS_PUF entries. acquire-data downloads and extracts them.
2. **Stage 1:** Profiler finds HPS CSVs in subdirectory. `variable_types.json` includes vaccination columns.
3. **Stage 2:** Question generator picks mandates → vaccine uptake as primary question.
4. **Stage 4:** If question generator identifies supplementary needs, orchestrator builds a second manifest, acquire-data downloads it.
5. **Idempotency:** Running Stage 0 twice downloads nothing the second time.
6. **Graceful degradation:** Download failure → pipeline proceeds with available data, same as current behavior.

---

## Why This Design

- **acquire-data has no modes.** It reads a manifest, downloads, reports. Same logic every time.
- **Orchestrator owns the intelligence.** Parsing markdown, deciding what to download, translating between formats — that's orchestrator work. It's already LLM-driven and designed for exactly this.
- **Manifest schema is the contract.** Both passes produce the same JSON shape. acquire-data doesn't know or care about the source.
- **Minimal changes.** One skill rewrite (simpler than before), one function change in Python, orchestrator additions.