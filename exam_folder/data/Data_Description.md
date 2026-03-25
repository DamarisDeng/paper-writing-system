# Data Description

Here are the datasets related to the NIH funding cuts in 2025. Also we provide datasets on the research, economic, and health outcomes which could be related for the analysis.

There are also reports on the Harvard indirect cost and funding cancellations in the folder `/harvard_reports`.

You do not have to use all the data.

## Grant Witness 

### What it is
Grant Witness is a public tracker of federal grant terminations and disruptions. It is useful as a fast-moving supplementary source for identifying 2025 grant terminations.

The file `nih_terminations.csv` is a snapshot downloaded from Grant Witness. It contains **5,419 grant records** and **57 columns** covering NIH (and some non-NIH HHS) awards that were terminated, frozen, unfrozen, or reinstated, primarily during 2025.

### Key variables
- `status` column classifies each record with an emoji-prefixed label.
- `termination_date` — date the award was formally terminated (range: 2024-11-08 to 2026-02-28)
- `frozen_date` / `unfrozen_date` — dates funding was frozen or unfrozen (freeze range: 2025-03-21 to 2025-07-29)
- `targeted_start_date` / `targeted_end_date` — projected disruption window

### Award and financial variables
- `total_award` — total obligated award amount (median ≈ \$1.6 M; sum ≈ \$17.2 B across 5,410 non-missing records)
- `total_estimated_outlays` — estimated spending already disbursed
- `total_estimated_remaining` — estimated unspent balance at time of termination/freeze
- `file_c_outlays` — monthly outlay breakdown from USAspending File C (free-text, formatted as a list of month-amount pairs)
- `spending_categories` / `categories_predicted` — topic-based spending tags

#### Cancellation and reinstatement variables
- `cancellation_source` — how the termination was identified: `HHS reported`, `Court filing`, `Self and HHS reported`, `Self reported`, or `No USAspending payments`
- `hhs_web_reported`, `hhs_pdf_reported`, `self_reported`, `court_reported`, `source_reported` — boolean flags for each reporting channel
- `reinstatement_indicator` — free-text field listing the legal or administrative basis for reinstatement (e.g., `APHA v. NIH 2025-06-18`, `MA v. RFK 2025-06-18`, `Thakur v. Trump (Sep 2025)`, `AAUP-Harvard v DOJ, Harvard v HHS`, `Columbia capitulation`, `Removed from TAGGS list`, `Termination removed from RePORTER`)
- `reinstated_est_date` / `reinstatement_case` — estimated reinstatement date and linked legal case

#### Grant and institution variables
- `activity_code` — NIH mechanism (top codes: R01 2,353; F31 409; R21 257; R35 255; R25 230; T32 214; U01 160)
- `funding_category` — broad category (`Research and Development` 3,677; `Research Training and Career Development` 1,569; `Other Transactions` 34; `Small Business` 15)
- `org_name`, `org_type`, `org_state`, `org_city`, `org_congdist` — recipient institution name, Carnegie/NIH type, and location
- `org_type` top values: Schools of Medicine (3,038), Schools of Arts and Sciences (608), Schools of Public Health (528)
- Top states: NY (1,435), MA (780), CA (776), IL (764), RI (269)
- `us_rep` / `us_rep_phone` — U.S. House representative for the institution's congressional district
- `dept_type`, `program_office`, `prog_office_code` — NIH institute/center and program office
- `org_traits` — institutional characteristics (e.g., minority-serving institution flags)
- `pct_ugrad_pellgrant`, `pct_ugrad_fedloan` — share of undergraduates receiving Pell grants or federal loans (for university-level context)

#### Scientific content variables
- `project_title` — award title
- `abstract_text`, `phr_text` — project abstract and public health relevance statement
- `terms` — MeSH / controlled vocabulary terms
- `study_section` — NIH study section that reviewed the application
- `foa` / `foa_title` — funding opportunity announcement number and title
- `flagged_words` — keywords flagged by Grant Witness as related to grant-termination risk categories

#### Cross-reference URLs
- `usaspending_url` — direct link to the award on USAspending.gov
- `taggs_url` — link to TAGGS (HHS grant tracking system)
- `reporter_url` — link to the NIH RePORTER project page
- `court_restoration_url` — link to court-ordered restoration documentation where applicable

#### Record integrity
- `record_sha1` — SHA-1 hash of the record for deduplication and version tracking

#### Practical cautions
- `status` is assigned by Grant Witness curators and may lag official databases by days to weeks.
- `file_c_outlays` is a multi-line free-text field; parse carefully before using as a numeric variable.
- Records with `status` = "Possibly Reinstated" or "Possibly Unfrozen Funding" reflect unconfirmed reversals and should be treated with caution in causal analyses.
- `termination_date` predating 2025 (earliest: 2024-11-08) likely reflects administrative groundwork preceding the main 2025 wave.
- Merge to NIH RePORTER using `appl_id` (integer) or `core_award_number` / `full_award_number` for richer project-level covariates.

---

## OpenAlex

### What it is
OpenAlex is a fully open scholarly metadata database covering works, authors, institutions, concepts/topics, sources, and funders.


### Common variables
- Work ID / DOI / PMID when available
- Publication date
- Authorships and institutions
- Citation counts
- Concepts/topics and open access metadata

### Access options
- REST API
- Full data snapshot for large-scale work

#### API example
```bash
curl "https://api.openalex.org/works?filter=institutions.display_name.search:Harvard,from_publication_date:2024-01-01,to_publication_date:2025-12-31&per-page=25"
```

#### Practical cautions
- Institution disambiguation is much better than raw PubMed affiliations, but still audit large institutions manually.
- Citation counts change over time; freeze a snapshot for reproducibility.


## NIH RePORTER / ExPORTER

### What it is
NIH RePORTER is the official project-level award database for NIH and some non-NIH federal biomedical research projects. ExPORTER is the bulk-download companion that provides CSV files for large-scale analysis.

### Common variables
- Fiscal year (`fy`)
- Organization name / DUNS / UEI where available
- Project number (`project_num`)
- Activity code (`R01`, `P01`, `T32`, etc.)
- Award amount
- Project start and end dates
- Linked PubMed IDs / patents in related files

### Data Download
- Web/API: NIH RePORTER API v2
- Bulk CSV: NIH ExPORTER
- Data dictionary: ExPORTER data dictionary

#### API example
```bash
curl -X POST "https://api.reporter.nih.gov/v2/projects/search" \
  -H "Content-Type: application/json" \
  -d '{
    "criteria": {
      "org_names": ["Harvard University"],
      "fiscal_years": [2024, 2025]
    },
    "include_fields": [
      "ProjectNum",
      "ProjectTitle",
      "Organization",
      "AwardAmount",
      "FiscalYear",
      "ProjectStartDate",
      "ProjectEndDate"
    ],
    "offset": 0,
    "limit": 100
  }'
```

#### Bulk download notes
- Use ExPORTER when you need a complete panel across many years.
- Download yearly project, publication, patent, and organization-related files.
- Merge by project number and fiscal year as needed.

---

## USAspending

### What it is
USAspending is the official U.S. federal spending database. It is especially useful for transaction timing, obligations, assistance awards, and validating actual federal outlays.


### Common variables
- Award ID / recipient / agency / subagency
- Award type and assistance listing
- Transaction date
- Obligated amount / outlay-related fields
- Place of performance / recipient location

### Access options
- REST API
- Website downloads

#### API example
```bash
curl -X POST "https://api.usaspending.gov/api/v2/search/spending_by_award/" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "time_period": [
        {"start_date": "2024-01-01", "end_date": "2025-12-31"}
      ],
      "agencies": [
        {"type": "funding", "tier": "toptier", "name": "Department of Health and Human Services"}
      ],
      "recipient_search_text": ["Harvard"]
    },
    "fields": [
      "Award ID",
      "Recipient Name",
      "Award Amount",
      "Start Date",
      "Last Modified Date",
      "Awarding Agency"
    ],
    "page": 1,
    "limit": 100,
    "sort": "Award Amount",
    "order": "desc"
  }'
```

#### Practical cautions
- USAspending and RePORTER are related but not identical reporting systems.
- Check whether you want award-level totals or transaction-level movements.
- For NIH-only analysis, USAspending is best used as a validation and timing source.




---

## PubMed + NIH iCite

### What it is
PubMed is the main biomedical literature index from NLM/NCBI. iCite is an NIH bibliometrics service with API and bulk data that provides citation-based measures for PubMed-indexed papers.

### Best use in your project
- Biomedical publication output
- Grant-linked literature discovery
- Citation-normalized impact (for example, RCR-like metrics from iCite)
- Disease-area tagging using MeSH terms

### Typical unit of observation
- PMID
- Institution × year
- Disease area × time

### Access options
- PubMed E-utilities API
- iCite API and bulk snapshots

#### PubMed API example
```bash
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=Harvard%5BAffiliation%5D+AND+2025%5Bpdat%5D&retmode=json&retmax=20"
```

#### iCite API example
```bash
curl "https://icite.od.nih.gov/api/pubs?pmids=40000000,40000001"
```

#### Practical cautions
- PubMed affiliation strings are noisy for institution matching.
- OpenAlex is often easier for institution-level panels; PubMed is stronger for biomedical specificity and MeSH.
- iCite covers PubMed-linked literature, not the entire scholarly universe.

---

## ClinicalTrials.gov API

### What it is
ClinicalTrials.gov is the main public registry of clinical studies. The modernized API provides structured access to protocol and status fields.

### Common variables
- Study status
- Start date / primary completion date
- Enrollment
- Conditions / interventions
- Sponsor and collaborators
- Locations
- Trial starts, suspensions, withdrawals, terminations
- Enrollment changes
- NIH-funded or academically sponsored trial activity
- Disease-area trial pipeline disruptions

### Access options
- ClinicalTrials.gov API v2

#### API example
```bash
curl "https://clinicaltrials.gov/api/query/studies?expr=AREA[Condition]cancer&min_rnk=1&max_rnk=20&fmt=json"
```

#### Practical cautions
- The site has modernized APIs and documentation; check current query syntax before building a large pipeline.
- Sponsor names can vary across Harvard hospitals and affiliates.
- Trial status changes do not always indicate funding cuts directly, so combine with award exposure.

---

## BLS QCEW

### What it is
The Quarterly Census of Employment and Wages (QCEW) is a near-universe count of U.S. employment and wages based on unemployment insurance records.


### Common variables
- Employment
- Establishment counts
- Total quarterly wages
- Average weekly wage
- County/state/area codes
- NAICS industry codes

### Access options
- Open CSV slices for recent years
- Downloadable data files for full history
- BLS public API for many BLS time series (QCEW users often rely on bulk/open files instead)

#### Data access example
The QCEW open-data files are distributed as CSV slices by area, industry, and size class. For large county-industry panels, bulk CSV downloads are usually easier than the BLS API.

#### API examples
```bash
curl "https://data.bls.gov/cew/data/api/{year}/{quarter}/area/{area_code}.csv"
# Direct download example:
curl -L "https://data.bls.gov/cew/data/api/2024/1/area/26000.csv" -o qcew_2024q1_michigan.csv
# BLS also documents the industry-slice pattern as:
curl "https://data.bls.gov/cew/data/api/{year}/{quarter}/industry/{industry_code}.csv"
```

---

## PatentsView

### What it contains
PatentsView is a USPTO research-grade patent database that provides cleaned and linked U.S. patent data. It covers patents, inventors, assignees, locations, citations, classifications, and government-interest information. USPTO describes PatentsView as an AI-enhanced, research-ready dataset and notes that it is in the process of being migrated to the USPTO Open Data Portal.

### Variables could be extracted
PatentsView is valuable for tracking downstream innovation after funding shocks, including:
- Patent counts
- Assignee-level patenting
- Inventor networks
- Citation-weighted patents
- Technology classes
- Government-interest-linked patents

### Access options
PatentsView offers a PatentSearch API with documented endpoints and field details in its reference and data dictionary. The platform supports endpoints for patents, inventors, assignees, locations, citations, and classifications, with query parameters for filters, returned fields, sorting, and other options.

#### API example

```bash
curl -X POST "https://search.patentsview.org/api/v1/patent/" \
  -H "Content-Type: application/json" \
  -d '{
    "q": {"_text_any":{"patent_title":"cancer"}},
    "f": ["patent_id","patent_title","patent_date","assignees.assignee_organization"]
  }'
```

For large-scale research, bulk files are often better than repeated API calls. USPTO says PatentsView provides downloadable granted-patent data, pre-grant publication data, long-text data, and annualized patent data through the Open Data Portal.
