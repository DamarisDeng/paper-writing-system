# Reference: Generating Research Questions

## Table of Contents

1. [PICO Format Guidelines](#pico-format-guidelines)
2. [Feasibility Validation](#feasibility-validation)
3. [Scoring Criteria](#scoring-criteria)
4. [Variable Role Decision Rules](#variable-role-decision-rules)
5. [Output Schema](#output-schema)
6. [Worked Example](#worked-example)

---

## PICO Format Guidelines

For each promising outcome–exposure pair, write a full PICO/PECO question specifying:

- **P**opulation — Who is being studied? (be specific: "US states in 2020-2021", not "people")
- **I/E**ntervention or Exposure — The main independent variable, referencing the exact column name in backticks
- **C**omparator — The reference group (e.g., "states without mask mandates", "pre-policy period")
- **O**utcome — The dependent variable, referencing the exact column name in backticks

**Every PICO question must reference actual column names in backticks.** This is critical for downstream validation and traceability.

### What makes a BAD candidate (reject these):

- **Vague association**: "What is the relationship between X and Y?" — no direction, no comparison group.
- **Identifier as exposure**: "Do states with higher `State_FIPS` have worse outcomes?" — FIPS codes are join keys, not exposures.
- **Denominator as outcome**: "Is `Total_Population` associated with policy adoption?" — population is a covariate for rate calculation.
- **Missing data dependency**: The outcome has 60% missingness, or the exposure exists in a dataset that can't be joined to the outcome dataset.
- **Trivial descriptive**: "What is the mean `Age` in the dataset?" — not a research question.
- **Requires external data**: The question needs variables not present in or derivable from the provided datasets.

---

## Feasibility Validation

### Running the Validator

```python
import sys; sys.path.insert(0, "workflow/scripts")
from feasibility_validator import validate_all_candidates

# Run rigorous feasibility check
validated_candidates = validate_all_candidates(
    candidates,  # Your list of candidate dicts from Step 3
    variable_types,  # Loaded from variable_types.json
    profile,  # Loaded from profile.json
    data_acquisition_requirements  # From your candidates (if any)
)

# Check feasibility results
feasible_candidates = [c for c in validated_candidates if c.get("status") == "feasible"]
infeasible_candidates = [c for c in validated_candidates if c.get("status") == "infeasible"]
```

### What the Validator Checks

| Check | Requirement | Failure Mode |
|-------|-------------|---------------|
| **Control Group** | At least one exposure group AND one comparison group exists | `no_control_group` |
| **Outcome Data** | Outcome variable exists OR can be derived/downloaded | `no_outcome_data` |
| **Sample Size** | Total N ≥ 20 (cross-sectional), ≥ 50 (DiD/longitudinal) | `insufficient_sample` |
| **Study Design Match** | Required data structure exists (e.g., time series for DiD) | `design_mismatch` |
| **Variable Availability** | All critical variables exist in data | `missing_critical_variables` |

### Handling Infeasible Candidates

- Keep them in the output (for audit trail)
- Mark with `status: "infeasible"` and `infeasibility_reason` with comma-separated failure codes
- Do NOT assign `preliminary_scores` to infeasible candidates
- Only `status: "feasible"` candidates proceed to scoring

### Example Output After Validation

```json
{
  "candidate_id": "CQ2",
  "status": "infeasible",
  "infeasibility_reason": "no_control_group,no_outcome_data,insufficient_sample",
  "question": "...",
  "variable_roles": {...}
  // Note: No preliminary_scores for infeasible candidates
}
```

---

## Scoring Criteria

Only score candidates that passed the feasibility check (`status: "feasible"`). Infeasible candidates should NOT receive `preliminary_scores`.

Score each candidate (0.0–1.0) on:

1. **Data feasibility** (weight: 0.40) — Can the question be answered with the available variables, sample size, and data structure? 1.0 = all variables present, low missingness, adequate N. 0.0 = missing key variables or insufficient sample.
2. **Clinical/public health significance** (weight: 0.20) — Would JAMA Network Open reviewers find this meaningful? 1.0 = directly policy-relevant. 0.0 = trivially descriptive.
3. **Novelty** (weight: 0.25) — Does it go beyond obvious descriptive statistics? 1.0 = novel comparison or evaluation. 0.0 = restatement of known facts.
4. **Methodological rigor** (weight: 0.15) — Can appropriate statistical methods be applied given the data structure? 1.0 = clean design. 0.0 = fundamental design flaw.

Compute `composite = 0.40*feasibility + 0.20*significance + 0.25*novelty + 0.15*rigor`.

Also match each candidate to the study design the data supports:
- Cross-sectional data → prevalence comparisons, associations
- Repeated measures / time series → before-after, interrupted time series, difference-in-differences
- Ecological (state-level) data → ecological study (cannot make individual-level claims)
- Individual-level data with exposure timing → cohort-style analysis

---

## Variable Role Decision Rules

For each feasible candidate question, map every column from `variable_types.json` into exactly one of these five roles:

**Role definitions:**
- **outcome_variables** — The dependent variable(s). Must be `numeric` or `binary` type and represent actual health measures.
- **exposure_variables** — The main independent variable(s). Must be `categorical`, `binary`, `numeric`, or `datetime`. Must NOT be `identifier` or `text`.
- **covariates** — Confounders and adjustment variables.
- **stratification_variables** — Variables used for subgroup analysis (not in the main model).
- **excluded_variables** — Variables not used, with a reason for each.

Optionally:
- **derived_variables** — Variables computed from raw columns. Each needs: `name`, `derivation`, and `source_columns`.

### Decision Rules for Ambiguous Columns

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

**Every raw column must appear in exactly one of the five raw-column categories.**

---

## Output Schema

Write to `<output_folder>/2_research_question/research_questions.json`:

**Important:** This stage outputs an array of **candidate questions** — it does NOT select a primary. Selection is deferred to the score-and-rank stage.

```json
{
  "candidate_questions": [
    {
      "candidate_id": "CQ1",
      "status": "feasible",
      "question": "Full PICO question referencing column names in backticks",
      "population": "Target population",
      "exposure_or_intervention": "Main IV with `column_name`",
      "comparator": "Reference/control group",
      "outcome": "Primary DV with `column_name`",
      "study_design": "e.g., ecological difference-in-differences",
      "rationale": "Why answerable and clinically relevant (2-3 sentences)",
      "preliminary_scores": {
        "data_feasibility": 0.85,
        "significance": 0.70,
        "novelty": 0.60,
        "rigor": 0.75,
        "composite": 0.725
      },
      "secondary_questions": [
        {
          "question": "Secondary question text",
          "variables_involved": ["exact_column_name_1", "exact_column_name_2"],
          "analysis_type": "e.g., subgroup analysis, sensitivity analysis",
          "rationale": "Brief justification (1-2 sentences)"
        }
      ],
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
      },
      "feasibility_assessment": {
        "strengths": ["Strength 1", "Strength 2"],
        "limitations": ["Limitation 1 with specifics", "Limitation 2 with specifics"],
        "required_assumptions": ["Assumption 1", "Assumption 2"]
      }
    },
    {
      "candidate_id": "CQ2",
      "status": "infeasible",
      "infeasibility_reason": "no_control_group,no_outcome_data,insufficient_sample",
      "question": "Question that failed feasibility check",
      "population": "...",
      "exposure_or_intervention": "...",
      "comparator": "...",
      "outcome": "...",
      "study_design": "...",
      "rationale": "...",
      "secondary_questions": [],
      "variable_roles": {...},
      "feasibility_assessment": {...}
      // Note: No preliminary_scores for infeasible candidates
    }
  ],
  "data_acquisition_requirements": [
    {
      "variable": "Name of variable needing download",
      "source_column": "URL column pointing to data",
      "target_file": "<output_folder>/2_research_question/downloaded/<filename>.csv",
      "action": "Specific download steps"
    }
  ]
}
```

Each `candidate_questions` entry contains its own `variable_roles`, `secondary_questions`, and `feasibility_assessment`. The `data_acquisition_requirements` array at the top level is the union of all candidates' needs.

---

## Worked Example

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
