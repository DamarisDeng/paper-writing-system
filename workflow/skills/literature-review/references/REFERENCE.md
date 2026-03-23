# Reference: Literature Review

## Table of Contents

1. [Search Strategy](#search-strategy)
2. [API Usage](#api-usage)
3. [BibTeX Format](#bibtex-format)
4. [Fallback Strategy](#fallback-strategy)

---

## Search Strategy

Search for references across 4 categories. Target at least 2-3 per category:

### Category 1: Similar Studies (3-4 references)

Studies that examined similar exposure-outcome relationships in similar populations.
- Search terms: `[exposure] AND [outcome] AND [population/setting]`
- Prefer recent (2019-2025) peer-reviewed articles in high-impact journals.

### Category 2: Methodology References (2-3 references)

Papers that describe or validate the statistical methods used.
- The specific regression technique or study design.
- Guidelines for the analysis approach (e.g., STROBE for observational studies, difference-in-differences methodology).

### Category 3: Clinical/Policy Context (2-3 references)

Background references that establish why this research question matters.
- Burden of disease / prevalence statistics.
- Current clinical guidelines or policy documents.
- Systematic reviews or meta-analyses in the field.

### Category 4: Data Source References (1-2 references)

Citations for the datasets used.
- Original data source documentation or codebook citations.
- Methodological papers describing the survey/dataset design.

---

## API Usage

### Semantic Scholar API (most reliable)

```bash
# Get API key from https://www.semanticscholar.org/product/api#api-key
export S2_API_KEY=your_key_here

# Search and convert to BibTeX
python workflow/skills/literature-review/fetch_references.py \
    "COVID-19 vaccine mandates healthcare workers" 10 references.bib
```

Or use Python code:
```python
import sys; sys.path.insert(0, "workflow/skills/literature-review")
from fetch_references import search_semantic_scholar, semantic_scholar_to_bibtex

papers = search_semantic_scholar("COVID-19 vaccine mandates", limit=5)
for paper in papers:
    bibtex = semantic_scholar_to_bibtex(paper)
    print(bibtex)
```

**Important:** Set `S2_API_KEY` environment variable for higher rate limits.

### PubMed API (via NCBI E-utilities)

```python
import requests

def search_pubmed(query, limit=5):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": limit}
    response = requests.get(base_url, params=params)
    # Fetch summaries using esummary.fcgi
    return response
```

### Web Search

- `"[topic]" site:pubmed.ncbi.nlm.nih.gov`
- `"[topic]" JAMA OR Lancet OR NEJM OR BMJ`
- Search Google Scholar for highly cited papers.

---

## BibTeX Format

### Article Entry

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

### Report/Website Entry

```bibtex
@misc{CDCReport2023,
  author       = {{Centers for Disease Control and Prevention}},
  title        = {Report Title},
  year         = {2023},
  howpublished = {\url{https://www.cdc.gov/...}},
  note         = {Accessed January 15, 2024},
}
```

---

## Fallback Strategy

If the search yields fewer than 10 verified references, supplement with foundational references appropriate to the domain:

- **Public health methodology**: STROBE statement, relevant Cochrane handbook chapters.
- **Statistical methods**: Original papers for the methods used (e.g., Cox 1972 for Cox regression, Rosenbaum & Rubin 1983 for propensity scores).
- **Data sources**: Official documentation for major surveys (NHANES, BRFSS, Census).
- **General epidemiology**: Textbook references from Rothman, Greenland, or Porta.

### Quality Checks

Before including a reference, verify:
- The citation is for a real, published work (not hallucinated).
- Author names, journal, year, and title are accurate.
- The DOI is correctly formatted (if available).
- The reference is relevant to the paper's content.

**If you cannot verify a reference is real, do not include it.** Use a known foundational reference instead.
