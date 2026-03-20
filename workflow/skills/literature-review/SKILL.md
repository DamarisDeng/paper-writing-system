---
name: literature-review
description: >
  Conduct a time-boxed literature search and produce a references.bib file
  with ≥10 BibTeX entries. Searches across 4 categories: similar studies,
  methodology, clinical/policy context, and data sources. Falls back to
  foundational references if search yields insufficient results.
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

Reads from `<output_folder>/2_research_question/research_questions.json`. Writes to `<output_folder>/5_references/`.

## Instructions

You are a research librarian and systematic reviewer. Your task is to build a focused, high-quality reference list that supports the paper's introduction, methods, and discussion sections. This stage is time-boxed to 10 minutes — prioritize quality over exhaustiveness.

### Step 1: Extract Search Context

Read `<output_folder>/2_research_question/research_questions.json` and identify:

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

### Step 3: Search Methods

Use these approaches in order of preference:

1. **Web search** for peer-reviewed articles using targeted queries:
   - `"[topic]" site:pubmed.ncbi.nlm.nih.gov`
   - `"[topic]" JAMA OR Lancet OR NEJM OR BMJ`
   - Search Google Scholar for highly cited papers.

2. **Known reference databases**:
   - PubMed (via web search)
   - Google Scholar
   - CDC/WHO publications for public health context

3. **Check `workflow/references/base_references.bib`** if it exists — use relevant pre-loaded references.

### Step 4: Format as BibTeX

For each reference, create a BibTeX entry. Use this format:

```bibtex
@article{AuthorYear,
  author  = {Last1, First1 and Last2, First2 and Last3, First3},
  title   = {Full title of the article},
  journal = {Journal Name},
  year    = {2023},
  volume  = {329},
  number  = {12},
  pages   = {1023--1034},
  doi     = {10.1001/jama.2023.xxxxx},
}
```

Citation key convention: `FirstAuthorLastNameYear` (e.g., `Smith2023`). If multiple papers by same author in same year, append a/b (e.g., `Smith2023a`).

For reports and websites:
```bibtex
@misc{CDCReport2023,
  author       = {{Centers for Disease Control and Prevention}},
  title        = {Report Title},
  year         = {2023},
  howpublished = {\url{https://www.cdc.gov/...}},
  note         = {Accessed January 15, 2024},
}
```

### Step 5: Quality Checks for Each Reference

Before including a reference, verify:
- The citation is for a real, published work (not hallucinated).
- Author names, journal, year, and title are accurate.
- The DOI is correctly formatted (if available).
- The reference is relevant to the paper's content.

**If you cannot verify a reference is real, do not include it.** Use a known foundational reference instead.

### Step 6: Fallback Strategy

If the search yields fewer than 10 verified references, supplement with foundational references appropriate to the domain:

- **Public health methodology**: STROBE statement, relevant Cochrane handbook chapters.
- **Statistical methods**: Original papers for the methods used (e.g., Cox 1972 for Cox regression, Rosenbaum & Rubin 1983 for propensity scores).
- **Data sources**: Official documentation for major surveys (NHANES, BRFSS, Census).
- **General epidemiology**: Textbook references from Rothman, Greenland, or Porta.

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
