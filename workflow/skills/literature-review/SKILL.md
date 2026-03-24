---
name: literature-review
model: medium
description: >
  Conduct a time-boxed literature search and produce a references.bib file
  with ≥10 BibTeX entries. Uses Semantic Scholar API for accurate citation
  retrieval, supplemented by web searches. Falls back to foundational references
  if search yields insufficient results.
  Triggers on: "literature review", "find references", "search literature",
  "build bibliography", or any request to gather citations for the paper.
argument-hint: <output_folder>
---

# Literature Review

Conduct a focused literature search and produce a BibTeX bibliography (`references.bib`) with at least 10 entries for the JAMA Network Open paper.

## Usage

```
/literature-review <output_folder>
```

Reads from `<output_folder>/2_scoring/ranked_questions.json`. Writes to `<output_folder>/5_references/`.

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/5_references/progress.json`.

**Steps tracked:**
- `step_1_extract_context`: Extract search context from research questions
- `step_2_search_strategy`: Define search strategy across categories
- `step_3_conduct_searches`: Execute web searches and database queries
- `step_4_format_bibtex`: Format results as BibTeX entries
- `step_5_validate_quality`: Quality check each reference
- `step_6_fallback_supplement`: Add foundational references if needed
- `step_7_save_output`: Write references.bib and search_log.json

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

## Instructions

You are a research librarian and systematic reviewer. Your task is to build a focused, high-quality reference list that supports the paper's introduction, methods, and discussion sections. This stage is time-boxed to 10 minutes — prioritize quality over exhaustiveness.

**Initialize progress tracker at start:**
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker

tracker = create_stage_tracker(output_folder, "literature_review",
    ["step_1_extract_context", "step_2_search_strategy", "step_3_conduct_searches",
     "step_4_format_bibtex", "step_5_validate_quality", "step_6_fallback_supplement",
     "step_7_save_output"])
```

### Step 1: Extract Search Context

Read `<output_folder>/2_scoring/ranked_questions.json` and identify:

1. **Topic keywords**: From the primary question's population, exposure, and outcome.
2. **Methodological terms**: From the study design and analysis type.
3. **Clinical/policy domain**: The broader public health context.
4. **Data source name**: If the study uses a named survey or dataset (e.g., Household Pulse Survey, BRFSS, NHANES).

### Step 2: Search Strategy

Search for references across 4 categories. Target at least 2-3 per category:

#### Category 1: Similar Studies (3-4 references)
Studies that examined similar exposure-outcome relationships in similar populations.
- Search terms: `[exposure] AND [outcome] AND [population/setting]`
- Prefer recent (2019-2025) peer-reviewed articles in high-impact journals.

#### Category 2: Methodology References (2-3 references)
Papers that describe or validate the statistical methods used.
- The specific regression technique or study design.
- Guidelines for the analysis approach (e.g., STROBE for observational studies, difference-in-differences methodology).

#### Category 3: Clinical/Policy Context (2-3 references)
Background references that establish why this research question matters.
- Burden of disease / prevalence statistics.
- Current clinical guidelines or policy documents.
- Systematic reviews or meta-analyses in the field.

#### Category 4: Data Source References (1-2 references)
Citations for the datasets used.
- Original data source documentation or codebook citations.
- Methodological papers describing the survey/dataset design.

### Step 3: Search and Fetch via API

**CRITICAL RULE: You must NEVER write BibTeX entries by hand. All BibTeX must be produced by `fetch_references.py` from API-returned metadata. LLM-authored BibTeX is forbidden — it introduces hallucinated author names, fake DOIs, and wrong volume/page numbers.**

Your only job here is to supply search query strings. The script does the rest.

Run one call per category using `search_and_collect`:

```python
import sys
sys.path.insert(0, "workflow/skills/literature-review/scripts")
from fetch_references import search_and_collect

# Build queries from your Step 1 keywords — strings only, no BibTeX
queries = [
    "COVID-19 vaccine mandates healthcare workers compliance",   # similar studies
    "logistic regression observational study methodology",       # methodology
    "COVID-19 vaccination coverage United States burden",        # clinical context
    "Household Pulse Survey methodology design CDC",             # data source
]

# Fetches from Semantic Scholar first, then PubMed as fallback
# Returns verified BibTeX strings with all fields from the API
entries = search_and_collect(queries, per_query=5)
print(f"Fetched {len(entries)} verified entries")
```

Optional: set `S2_API_KEY` (Semantic Scholar) or `NCBI_API_KEY` (PubMed) env vars for higher rate limits.

If the API call itself fails (network error, 5xx), fall back to web search to find the paper's DOI or PMID, then fetch by ID:

```python
import sys; sys.path.insert(0, "workflow/skills/literature-review/scripts")
from fetch_references import search_semantic_scholar, semantic_scholar_to_bibtex
# Search by exact title to get accurate metadata
papers = search_semantic_scholar("Exact paper title here", limit=1)
bib = semantic_scholar_to_bibtex(papers[0]) if papers else ""
```

For reports or institutional documents with no API record, use `@misc` manually **only** when the URL/author/date are directly copy-pasted from the source page — never recalled from memory.

### Step 4: Deduplicate and Collect

`search_and_collect` already calls `deduplicate_bibtex` internally. If you ran multiple separate calls, merge and deduplicate manually:

```python
import sys; sys.path.insert(0, "workflow/skills/literature-review/scripts")
from fetch_references import deduplicate_bibtex
all_entries = deduplicate_bibtex(entries_batch_1 + entries_batch_2)
```

### Step 5: Quality Checks for Each Reference

Run this check script on `entries` before writing the file:

```python
import re

def validate_entries(entries: list[str]) -> list[str]:
    """Drop entries that lack minimum required fields."""
    good = []
    for bib in entries:
        has_author  = re.search(r"author\s*=", bib)
        has_title   = re.search(r"title\s*=", bib)
        has_year    = re.search(r"year\s*=\s*\{(\d{4})\}", bib)
        # Reject entries whose author field contains obvious LLM artifacts
        garbled = re.search(r"legality|undefined|unknown|et al\.", bib, re.I)
        if has_author and has_title and has_year and not garbled:
            good.append(bib)
        else:
            print(f"  [SKIP] dropped suspect entry", file=sys.stderr)
    return good

entries = validate_entries(entries)
```

**If you cannot confirm a reference came from an API call, do not include it.** Use a foundational reference from Step 6 instead.

### Step 6: Fallback Strategy

If the search yields fewer than 10 verified references, search for well-known foundational papers by name via the API (do not write them from memory):

```python
fallback_queries = [
    "STROBE statement strengthening reporting observational studies epidemiology",
    "Rosenbaum Rubin central role propensity score observational studies",
    "Cox regression survival analysis methodology",
]
import sys; sys.path.insert(0, "workflow/skills/literature-review/scripts")
from fetch_references import search_and_collect, deduplicate_bibtex
fallback_entries = search_and_collect(fallback_queries, per_query=2)
all_entries = deduplicate_bibtex(entries + fallback_entries)
```

For official reports/websites with no indexed record, write one `@misc` entry per document, copying author/title/year/URL verbatim from the source page — not from memory.

### Step 7: Save Output

Write the complete bibliography to `<output_folder>/5_references/references.bib`.

Also create `<output_folder>/5_references/search_log.json`:

```json
{
  "search_queries": [
    {"query": "search terms used", "source": "PubMed/Scholar", "results_found": 5}
  ],
  "references_by_category": {
    "similar_studies": ["Smith2023", "Jones2022"],
    "methodology": ["STROBE2007"],
    "clinical_context": ["WHO2023"],
    "data_sources": ["Census2020"]
  },
  "total_references": 12,
  "verified": true,
  "fallbacks_used": 2
}
```

### Step 8: Validate

- [ ] `references.bib` exists and has ≥10 `@article` or `@misc` entries
- [ ] All entries have: author, title, year (minimum required fields)
- [ ] No duplicate citation keys
- [ ] Citation keys follow `AuthorYear` convention
- [ ] BibTeX syntax is valid (balanced braces, proper field separators)
- [ ] `search_log.json` exists

**Progress checkpoint - Mark stage complete:**
```python
from progress_utils import complete_stage

complete_stage(output_folder, "literature_review",
               expected_outputs=["5_references/references.bib",
                                 "5_references/search_log.json"])
```

## Output Contract

**`<output_folder>/5_references/references.bib`** — BibTeX bibliography with ≥10 entries:
```bibtex
@article{Smith2023,
  author  = {Smith, John A. and Doe, Jane B.},
  title   = {Title of the Article},
  journal = {JAMA Network Open},
  year    = {2023},
  volume  = {6},
  number  = {3},
  pages   = {e231234},
  doi     = {10.1001/jamanetworkopen.2023.1234},
}
% ... at least 9 more entries
```

**`<output_folder>/5_references/search_log.json`** — Search process documentation.
