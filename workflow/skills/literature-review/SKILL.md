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

Search for references across 4 categories. Target at least 2-3 per category.

See `references/REFERENCE.md: Search Strategy` for the complete category definitions and target counts.

### Step 3: Search Methods

Use Semantic Scholar API, PubMed API, or web search.

See `references/REFERENCE.md: API Usage` for detailed API usage examples and helper functions.

### Step 4: Format as BibTeX

For each reference, create a BibTeX entry. Use `AuthorYear` citation key convention.

See `references/REFERENCE.md: BibTeX Format` for BibTeX templates and formatting rules.

### Step 5: Quality Checks for Each Reference

Before including a reference, verify it's a real published work with accurate author, title, journal, year. Do not include unverified references.

See `references/REFERENCE.md: Fallback Strategy` for quality check guidelines.

### Step 6: Fallback Strategy

If fewer than 10 verified references, supplement with foundational references.

See `references/REFERENCE.md: Fallback Strategy` for foundational reference categories.

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
