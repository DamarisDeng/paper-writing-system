---
name: generate-research-questions
model: high
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

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/2_research_question/progress.json`.

**Steps tracked:**
- `step_1_load_inputs`: Load profile and variable_types
- `step_2_understand_data`: Build mental model of data landscape
- `step_3_identify_pairings`: Find outcome-exposure pairs
- `step_4_rank_select`: Select primary and secondary questions
- `step_5_assign_variables`: Map variables to roles
- `step_6_assess_feasibility`: Document strengths and limitations
- `step_7_save_validate`: Write and validate research_questions.json

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

## Instructions

You are an epidemiologist and biostatistician formulating research questions from available data. Your goal is to identify the single best primary research question the data can answer, along with supporting secondary questions. Every question must be grounded in variables that actually exist in the data — no aspirational questions about data you wish you have.

---

### Step 0: Initialize Progress Tracker

```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker

tracker = create_stage_tracker(output_folder, "generate_research_questions",
    ["step_1_load_inputs", "step_2_understand_data", "step_3_identify_pairings",
     "step_4_rank_select", "step_5_assign_variables", "step_6_assess_feasibility",
     "step_7_save_validate"])
```

### Step 1: Load Inputs

Read both files from `<output_folder>/1_data_profile/`:

1. **`profile.json`** — Contains `data_context` (summary, dataset_relationships, research_directions, data_quality_notes) and per-dataset column-level statistics (dtype, missing_count, missing_pct, unique_count, sample_values, descriptive stats, top_values).

2. **`variable_types.json`** — Semantic type classification for every column: `numeric`, `categorical`, `datetime`, `text`, `binary`, `identifier`.

Also check whether the original data folder (referenced in `profile.json` file paths) has a `Data_Description.md` or any `.md` files. If so, read them for additional domain context.

---

### Step 2: Understand the Data Landscape

Before generating any questions, build a structured mental model:

- **Datasets available**: List each dataset, its size (rows × cols), and what it represents.
- **How they relate**: Can they be joined? By what key? At what level of analysis (individual, state, facility)? If datasets cannot be joined, note this constraint — questions requiring cross-dataset variables from unjoinable tables are infeasible.
- **Candidate outcome variables**: Scan for `numeric` or `binary` columns with clinical/health significance — mortality rates, case counts, disease incidence, health scores, readmission flags, etc. Population counts and denominators are NOT outcomes.
- **Candidate exposure/intervention variables**: Policy indicators, treatment flags, demographic groups, time periods, facility characteristics. Must be `categorical`, `binary`, `numeric`, or `datetime`. Never `identifier` or `text`.
- **Available covariates**: Demographics, geographic identifiers, time variables, facility-level factors.
- **Data limitations to flag early**:
  - Datasets with very few rows (N < 30) limit statistical power
  - Columns with >30% missingness are risky as primary variables
  - Metadata-only files (e.g., archive indexes) that don't contain analyzable data
  - Ecological (aggregate) vs. individual-level data — this constrains causal claims
  - Temporal misalignment between datasets

---

### Step 3: Identify the Strongest Outcome–Exposure Pairings

This is the core generative step. Rather than brainstorming many vague ideas, work systematically:

#### 3a. Start from outcomes, not topics

List the 2-4 strongest candidate outcome variables from your Step 2 scan. A "strong" outcome has:
- Clinical/public health meaning (not just any numeric column)
- Low missingness (<30%)
- Sufficient variation (check `std`, `unique_count`, or `top_values` — a binary outcome that is 99% one value won't work)
- Enough sample size (check row count of the dataset it belongs to)

#### 3b. For each outcome, find the best exposure

For each candidate outcome, ask: *What comparison or contrast can the data support?* Look for:
- A categorical/binary variable that splits the population into meaningful groups (e.g., policy vs. no-policy states, treatment vs. control)
- A numeric exposure with enough range to detect a dose-response
- A temporal exposure (before/after an event) if the data has time structure

Check that exposure groups have adequate N. A comparison of 2 vs. 48 is not feasible. Look at `top_values` for group sizes.

#### 3c. Form 2-3 candidate PICO questions

For each promising outcome–exposure pair, write a full PICO/PECO question specifying:
- **P**opulation — Who is being studied? (be specific: "US states in 2020-2021", not "people")
- **I/E**ntervention or Exposure — The main independent variable, referencing the exact column name in backticks
- **C**omparator — The reference group (e.g., "states without mask mandates", "pre-policy period")
- **O**utcome — The dependent variable, referencing the exact column name in backticks

**Every PICO question must reference actual column names in backticks.** This is critical for downstream validation and traceability.

#### What makes a BAD candidate (reject these):

- **Vague association**: "What is the relationship between X and Y?" — no direction, no comparison group.
- **Identifier as exposure**: "Do states with higher `State_FIPS` have worse outcomes?" — FIPS codes are join keys, not exposures.
- **Denominator as outcome**: "Is `Total_Population` associated with policy adoption?" — population is a covariate for rate calculation.
- **Missing data dependency**: The outcome has 60% missingness, or the exposure exists in a dataset that can't be joined to the outcome dataset.
- **Trivial descriptive**: "What is the mean `Age` in the dataset?" — not a research question.
- **Requires external data**: The question needs variables not present in or derivable from the provided datasets.

---

### Step 4: Rank and Select

From your 2-3 candidates, select 1 primary and 1-2 secondary questions using these criteria (in priority order):

1. **Data feasibility** — Can the question be answered with the available variables, sample size, and data structure? Disqualify anything that requires data you don't have.
2. **Clinical/public health significance** — Would JAMA Network Open reviewers find this meaningful for clinicians, policymakers, or public health practitioners?
3. **Novelty** — Does it go beyond obvious descriptive statistics? Look for comparisons, associations, or policy evaluations.
4. **Methodological rigor** — Can appropriate statistical methods be applied given the data structure?

Select:
- **1 primary question** — the strongest across all criteria
- **1-2 secondary questions** — subgroup analyses, sensitivity analyses, or complementary questions that strengthen the paper

Also match each question to the study design the data supports:
- Cross-sectional data → prevalence comparisons, associations
- Repeated measures / time series → before-after, interrupted time series, difference-in-differences
- Ecological (state-level) data → ecological study (cannot make individual-level claims)
- Individual-level data with exposure timing → cohort-style analysis

---

### Step 5: Assign Variable Roles

Map every column from `variable_types.json` into exactly one of these five roles. Use the decision rules below for ambiguous cases.

**Role definitions:**
- **outcome_variables** — The dependent variable(s). Must be `numeric` or `binary` type and represent actual health measures.
- **exposure_variables** — The main independent variable(s). Must be `categorical`, `binary`, `numeric`, or `datetime`. Must NOT be `identifier` or `text`.
- **covariates** — Confounders and adjustment variables.
- **stratification_variables** — Variables used for subgroup analysis (not in the main model).
- **excluded_variables** — Variables not used, with a reason for each.

Optionally:
- **derived_variables** — Variables computed from raw columns. Each needs: `name`, `derivation`, and `source_columns`.

**Decision rules for ambiguous columns:**

| Ambiguity | Rule |
|---|---|
| Column is central to the research question's comparison | → **exposure** |
| Column could confound the exposure–outcome relationship | → **covariate** |
| `datetime` column | If it defines a before/after contrast → **exposure**; if it's for trend adjustment → **covariate**; if unused → **excluded** |
| `identifier` column (state names, patient IDs, facility codes) | → **covariate** (as a join key or fixed effect) or **excluded**. NEVER exposure or outcome. |
| Population count / denominator column | → **covariate** (for rate calculation). NEVER outcome. |
| Column with >50% missing | → **excluded** (cite missingness as reason) |
| Metadata column (file paths, URLs, archive links) | → **excluded** ("metadata only") |
| Column relevant only to a secondary/subgroup question | → **stratification** |

**Every raw column must appear in exactly one of the five raw-column categories.** This mapping drives downstream study design and analysis.

---

### Step 6: Assess Feasibility

Write an honest assessment:

**Strengths**: What makes these questions answerable? (e.g., clear exposure-outcome pairing, adequate sample size, natural experiment design, multiple years of data)

**Limitations** (minimum 2, with specifics):
- Missing confounders (name them)
- Sample size constraints (cite the N)
- Ecological fallacy risk if using aggregate data
- Temporal limitations (cross-sectional vs. longitudinal)
- Selection bias, measurement issues
- Data acquisition requirements (if outcomes must be downloaded from URLs)

**Required assumptions**: What must hold for the analysis to be valid? (e.g., parallel trends for diff-in-diff, no unmeasured confounding, missing at random)

**Data acquisition requirements** (if applicable): If the primary outcome or exposure is accessible through URL columns in the data (e.g., Archive Link), document what needs downloading. Specify the target file path as `<output_folder>/2_research_question/downloaded/<filename>`. Include fallback sources if primary URLs may be deprecated.

---

### Step 7: Save and Validate Output

Write to `<output_folder>/2_research_question/research_questions.json` with this exact structure:

```json
{
  "primary_question": {
    "question": "Full PICO question referencing column names in backticks",
    "population": "Target population",
    "exposure_or_intervention": "Main IV with `column_name`",
    "comparator": "Reference/control group",
    "outcome": "Primary DV with `column_name`",
    "study_design": "e.g., ecological difference-in-differences",
    "rationale": "Why answerable and clinically relevant (2-3 sentences)"
  },
  "secondary_questions": [
    {
      "question": "Secondary question text",
      "variables_involved": ["exact_column_name_1", "exact_column_name_2"],
      "analysis_type": "e.g., subgroup analysis, sensitivity analysis",
      "rationale": "Brief justification (1-2 sentences)"
    }
  ],
  "data_acquisition_requirements": [
    {
      "variable": "Name of variable needing download",
      "source_column": "URL column pointing to data",
      "target_file": "<output_folder>/2_research_question/downloaded/<filename>.csv",
      "action": "Specific download steps"
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
        "derivation": "How to compute",
        "source_columns": ["raw_col_1", "raw_col_2"]
      }
    ]
  }
}
```

---

### Worked Example (condensed)

Suppose `variable_types.json` contains one dataset with these columns:

| Column | Type |
|---|---|
| `State` | identifier |
| `Year` | datetime |
| `Mask_Mandate` | binary |
| `COVID_Deaths` | numeric |
| `Total_Population` | numeric |
| `Median_Income` | numeric |
| `Archive_Link` | text |

And `profile.json` shows: 51 rows, `COVID_Deaths` has 0% missing and std=4200, `Mask_Mandate` splits 32/19, `Total_Population` has 0% missing.

**Step 3a — Strongest outcomes:** `COVID_Deaths` is numeric, 0% missing, high variance, clinically meaningful. `Total_Population` is numeric but is a denominator, not an outcome → reject.

**Step 3b — Best exposure for `COVID_Deaths`:** `Mask_Mandate` is binary with a 32/19 split — adequate group sizes. `Median_Income` is numeric but less specific as an exposure. `State` is identifier → cannot be exposure.

**Step 3c — PICO question:**
> Among US states in 2020-2021 (**P**), is the presence of a statewide `Mask_Mandate` (**E**), compared to no mandate (**C**), associated with lower `COVID_Deaths` (**O**)?

**Variable roles:**
- outcome: `COVID_Deaths`
- exposure: `Mask_Mandate`
- covariates: `Total_Population` (for per-capita rate), `Median_Income`, `Year`
- excluded: `State` ("identifier — used as join key only"), `Archive_Link` ("metadata URL, not analyzable")
- derived: `Death_Rate` = `COVID_Deaths` / `Total_Population` × 100,000

**Bad alternative rejected:** "Is `Total_Population` higher in mandate states?" — denominator as outcome, trivially descriptive, no clinical significance.

---

### Validation

After saving, **run the validation script**:

```bash
python workflow/skills/generate-research-questions/validate_research_questions.py <output_folder>
```

The script checks: schema completeness, column coverage (every column assigned to exactly one role), column reference validity, identifier role violations, outcome analyzability (type + missingness), exposure analyzability, denominator-as-outcome heuristic, question specificity (column names referenced), and derived variable structure.

If the script reports **errors (exit code 1)**, fix `research_questions.json` and re-run until all checks pass. Do not proceed to study design with validation errors.

**Progress checkpoint - Mark stage complete:**
```python
from progress_utils import update_step, complete_stage

# After validation passes
update_step(output_folder, "generate_research_questions", "step_7_save_validate", "completed")

# Mark stage complete with validation
complete_stage(output_folder, "generate_research_questions",
               expected_outputs=["2_research_question/research_questions.json"])
```