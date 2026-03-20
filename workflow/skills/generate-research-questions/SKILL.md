---
name: generate-research-questions
description: >
  Generate tentative research questions from profiled dataset outputs.
  Takes profile.json and variable_types.json (produced by /load-and-profile)
  and produces research_questions.json with a primary PICO/PECO question,
  secondary questions, feasibility assessment, and variable role assignments.
  Use this skill whenever the user wants to formulate research questions,
  generate hypotheses, or move from data profiling to study design.
  Triggers on: "generate research questions", "formulate hypotheses",
  "what questions can we answer", "research question", "PICO", "study question",
  or any request to go from profile.json to research_questions.json.
argument-hint: <output_folder>
---

# Generate Research Questions

Given profiled dataset outputs (`profile.json` + `variable_types.json`), generate a ranked set of research questions suitable for a JAMA Network Open-style paper, and save the result as `research_questions.json`.

## Usage

```
/generate-research-questions <output_folder>
```

Where `<output_folder>` is the base directory (e.g., `exam_paper`). The skill reads from `<output_folder>/1_data_profile/` and writes to `<output_folder>/2_research_question/`.

## Instructions

You are an epidemiologist and biostatistician formulating research questions from available data. Your goal is to identify the single best primary research question the data can answer, along with supporting secondary questions. Every question must be grounded in variables that actually exist in the data — no aspirational questions about data you wish you had.

### Step 1: Load Inputs

Read both files from `<output_folder>/1_data_profile/`:

1. **`profile.json`** — Contains `data_context` (summary, dataset_relationships, research_directions, data_quality_notes) and per-dataset column-level statistics (dtype, missing_count, missing_pct, unique_count, sample_values, descriptive stats, top_values).

2. **`variable_types.json`** — Semantic type classification for every column: `numeric`, `categorical`, `datetime`, `text`, `binary`, `identifier`.

Also check whether the original data folder (referenced in `profile.json` file paths) has a `Data_Description.md` or any `.md` files. If so, read them for additional domain context.

### Step 2: Understand the Data Landscape

Before generating any questions, build a mental model of the data:

- **Datasets available**: List each dataset, its size (rows x cols), and what it represents.
- **How they relate**: Can they be joined? By what key? At what level of analysis (individual, state, facility)?
- **Candidate outcome variables**: Look for numeric or binary columns with clinical/health significance — mortality rates, case counts, disease incidence, health scores, readmission flags, etc.
- **Candidate exposure/intervention variables**: Policy indicators, treatment flags, demographic groups, time periods, facility characteristics.
- **Available covariates**: Demographics, geographic identifiers, time variables, facility-level factors.
- **Data limitations to flag**:
  - Datasets with very few rows (N < 30) limit statistical power
  - Columns with >30% missingness are risky as primary variables
  - Metadata-only files (e.g., archive indexes) that don't contain analyzable data
  - Ecological (aggregate) vs. individual-level data — this constrains causal claims
  - Temporal misalignment between datasets

### Step 3: Generate Candidate Research Questions

Brainstorm 5-8 candidate research questions. For each candidate, verify:

1. **PICO/PECO structure**: Every question must specify Population, Intervention/Exposure, Comparator, and Outcome. Vague questions like "What is the relationship between X and Y?" are insufficient — specify direction and comparison.

2. **Variable existence — outcome data accessibility**: Both the outcome and exposure must be accessible through the provided datasets:
   - **Directly available**: The variable exists as an analyzable column in a profiled dataset
   - **Downloadable from provided URLs**: The dataset contains URL columns (e.g., Archive Link) that point to the actual outcome data. This is acceptable — note the download requirement in `data_acquisition_requirements`.
   - **Derivable from existing columns**: E.g., a rate = column A / column B, or a binary indicator from group membership

   If a question requires data that is completely external to the provided datasets (not referenced in any profile.json column or URL), that question is **infeasible**.

3. **Outcome must be a real health measure**: The outcome variable must be `numeric` or `binary` in `variable_types.json` and represent an actual health/clinical measure (e.g., mortality count, disease incidence, readmission flag). Population counts and denominators are **not** outcomes — they are covariates used for rate calculations. Columns typed as `identifier` or `text` cannot be outcomes.

4. **Exposure must not be an identifier**: Columns typed as `identifier` in `variable_types.json` (e.g., state names, patient IDs, facility codes) are join keys. They cannot be the exposure variable. If the exposure contrast is derived from an identifier (e.g., "states that appear in a policy table vs. those that don't"), the exposure is a derived binary variable — list the identifier as a covariate or excluded variable and describe the derivation in `derived_variables`.

5. **Outcome variation**: Check that the outcome variable has sufficient variation. If a binary outcome is 99% one category, it won't support analysis. Look at `unique_count`, `top_values`, and `std` in the profile.

6. **Exposure group sizes**: For categorical exposures, check `top_values` to ensure each group has adequate N. A comparison between 15 states with mandates vs. 35 without is feasible; a comparison with 2 vs. 48 is not.

7. **Study design feasibility**: Match the question to what the data structure supports:
   - Cross-sectional data → prevalence comparisons, associations
   - Repeated measures / time series → before-after, interrupted time series, difference-in-differences
   - Ecological (state-level) data → ecological study (cannot make individual-level claims)
   - Individual-level data with exposure timing → cohort-style analysis

8. **Confounding**: Consider what confounders are available in the data vs. what's missing. Questions that require adjustment for unmeasured confounders are weaker.

### Step 4: Rank and Select

Rank candidates using these criteria (in order of importance):

1. **Data feasibility** — Can this question actually be answered with the available variables, sample size, and data structure? Disqualify questions that require data you don't have.

2. **Clinical/public health significance** — Is this question meaningful to clinicians, policymakers, or public health practitioners? Would JAMA Network Open reviewers find it relevant?

3. **Novelty** — Does it go beyond obvious descriptive statistics? A question about "what is the mean age" is not a research question. Look for comparisons, associations, or policy evaluations.

4. **Methodological rigor** — Can appropriate statistical methods (regression, survival analysis, difference-in-differences, etc.) be applied given the data structure?

Select:
- **1 primary question** — the strongest candidate across all criteria
- **2-3 secondary questions** — these can be subgroup analyses, sensitivity analyses, or complementary questions that strengthen the paper

### Step 5: Assign Variable Roles

Map every column from `variable_types.json` into exactly one role:

- **outcome_variables** — The dependent variable(s). Must be `numeric` or `binary` type and represent actual health measures (not population denominators, not identifiers).
- **exposure_variables** — The main independent variable(s). Must be `categorical`, `binary`, `numeric`, or `datetime` type. Must NOT be `identifier` type — identifiers are join keys, not exposures.
- **covariates** — Confounders and adjustment variables: demographics, geographic identifiers, population denominators (for rate calculation), time variables, facility-level factors.
- **stratification_variables** — Variables used for subgroup analysis (not in the main model).
- **excluded_variables** — Variables not used in analysis, with a reason for each (e.g., "metadata column", "identifier only", ">50% missing", "not relevant to research question").

Optionally include:
- **derived_variables** — Variables that must be computed for the analysis but don't exist as raw columns. Each entry needs: `name`, `derivation` (how to compute), and `source_columns` (which raw columns feed in). Examples: mortality rate = deaths / population, mandate indicator = 1 if state in policy table else 0.

Every raw column must appear in exactly one of the five raw-column categories. This mapping drives downstream study design and analysis steps.

### Step 6: Assess Feasibility

Write an honest assessment covering:

**Strengths**: What makes these questions answerable? (e.g., clear exposure-outcome pairing, adequate sample size, natural experiment design, multiple years of data)

**Limitations**: What are the gaps? Be specific:
- Missing confounders (name them)
- Sample size constraints (cite the N)
- Ecological fallacy risk if using aggregate data
- Temporal limitations (e.g., cross-sectional snapshot vs. longitudinal)
- Selection bias (e.g., only states that adopted a policy)
- Measurement issues (e.g., self-reported data, proxy outcomes)
- Data acquisition requirements (if outcomes must be downloaded from URLs, note this)

**Required assumptions**: What must be true for the analysis to be valid?
- Parallel trends assumption (for diff-in-diff)
- No unmeasured confounding (for observational studies)
- Missing at random (for missing data handling)
- Stable unit treatment value assumption (for causal inference)

**Data acquisition requirements** (if applicable): If the primary outcome or exposure is not directly present as an analyzable column but is accessible through URL columns in the data (e.g., Archive Link columns), document what needs to be downloaded. Specify the target file path as `<output_folder>/2_research_question/downloaded/<filename>`. Include fallback sources in case primary URLs are deprecated. Example:
```json
"data_acquisition_requirements": [
  {
    "variable": "State-level COVID-19 deaths",
    "source_column": "Archive Link",
    "target_file": "exam_paper/2_research_question/downloaded/covid_deaths_timeseries.csv",
    "fallback_urls": [
      "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv",
      "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us.csv"
    ],
    "action": "Download state-level COVID-19 death time series for July-Oct 2021. Primary Archive Link URLs may be deprecated; use NY Times GitHub as fallback."
  }
]
```

### Step 7: Save and Validate Output

Write the final output to `<output_folder>/2_research_question/research_questions.json` with this exact structure:

```json
{
  "primary_question": {
    "question": "Full research question in PICO/PECO format",
    "population": "Target population description",
    "exposure_or_intervention": "Main independent variable with column name(s)",
    "comparator": "Reference/control group description",
    "outcome": "Primary outcome variable with column name(s)",
    "study_design": "Recommended design (e.g., ecological difference-in-differences)",
    "rationale": "Why this question is answerable and clinically relevant (2-3 sentences)"
  },
  "secondary_questions": [
    {
      "question": "Secondary research question text",
      "variables_involved": ["exact_column_name_1", "exact_column_name_2"],
      "analysis_type": "e.g., subgroup analysis, sensitivity analysis, effect modification",
      "rationale": "Brief justification (1-2 sentences)"
    }
  ],
  "data_acquisition_requirements": [
    {
      "variable": "Name of outcome/exposure that needs downloading",
      "source_column": "URL column or reference that points to data",
      "target_file": "<output_folder>/downloaded/<filename>.csv",
      "action": "Specific steps (e.g., 'Download time series from Archive Link URLs')"
    }
  ],
  "feasibility_assessment": {
    "strengths": ["Strength 1", "Strength 2"],
    "limitations": ["Limitation 1 with specifics", "Limitation 2 with specifics"],
    "required_assumptions": ["Assumption 1", "Assumption 2"]
  },
  "variable_roles": {
    "outcome_variables": ["col_name"],
    "exposure_variables": ["col_name"],
    "covariates": ["col_name_1", "col_name_2"],
    "stratification_variables": ["col_name"],
    "excluded_variables": {
      "col_name": "reason for exclusion"
    },
    "derived_variables": [
      {
        "name": "variable_name",
        "derivation": "How to compute this variable",
        "source_columns": ["raw_col_1", "raw_col_2"]
      }
    ]
  }
}
```

After saving the file, **run the validation script**:

```bash
python workflow/skills/generate-research-questions/validate_research_questions.py <output_folder>
```

This script checks for schema completeness, column coverage, semantic validity, and that downloaded data paths use the `<output_folder>/2_research_question/downloaded/` convention.

This script checks:
- Schema completeness (all required fields present)
- Column coverage (every column in `variable_types.json` assigned to exactly one role)
- Column references (all `variables_involved` entries exist in the data)
- Identifier role check (identifiers not used as outcome or exposure)
- Outcome analyzability (outcomes must be numeric or binary, not high-missingness)
- Exposure analyzability (exposures must be categorical/binary/numeric/datetime, not identifier/text)
- Outcome not denominator (catches population counts misclassified as outcomes)
- Question specificity (primary question references actual column names)
- Derived variables structure (if present, validates name/derivation/source_columns)

If the script reports **errors (exit code 1)**, fix the `research_questions.json` and re-run until all checks pass (exit code 0). Do not proceed to study design with validation errors.
