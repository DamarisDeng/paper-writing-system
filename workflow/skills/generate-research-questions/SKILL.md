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
- `step_3b_validate_feasibility`: Rigorous feasibility check for each candidate
- `step_4_rank_select`: Score candidates (feasible only)
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
     "step_3b_validate_feasibility", "step_4_rank_select", "step_5_assign_variables",
     "step_6_assess_feasibility", "step_7_save_validate"])
```

### Step 1: Load Inputs

Read both files from `<output_folder>/1_data_profile/`:

1. **`profile.json`** — Contains `data_context` (summary, dataset_relationships, research_directions, data_quality_notes) and per-dataset column-level statistics (dtype, missing_count, missing_pct, unique_count, sample_values, descriptive stats, top_values).

2. **`variable_types.json`** — Semantic type classification for every column: `numeric`, `categorical`, `datetime`, `text`, `binary`, `identifier`.

Also check whether the original data folder (referenced in `profile.json` file paths) has a `Data_Description.md` or any `.md` files. If so, read them for additional domain context.

**Progress checkpoint:**
```python
from progress_utils import update_step
update_step(output_folder, "generate_research_questions", "step_1_load_inputs", "completed")
```

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

**Progress checkpoint:**
```python
update_step(output_folder, "generate_research_questions", "step_2_understand_data", "completed")
```

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

For each promising outcome–exposure pair, write a full PICO/PECO question specifying Population, Intervention/Exposure, Comparator, and Outcome.

**Every PICO question must reference actual column names in backticks.**

See `references/REFERENCE.md: PICO Format Guidelines` for detailed PICO format rules and examples of bad candidates to reject.

**Progress checkpoint:**
```python
update_step(output_folder, "generate_research_questions", "step_3_identify_pairings", "completed")
```

---

### Step 3b: Validate Feasibility (RIGOROUS)

**CRITICAL:** Before proceeding to scoring, validate each candidate's feasibility using `validate_all_candidates()`.

```python
from feasibility_validator import validate_all_candidates
validated_candidates = validate_all_candidates(candidates, variable_types, profile, data_acquisition_requirements)
```

See `references/REFERENCE.md: Feasibility Validation` for what the validator checks and how to handle infeasible candidates.

**Progress checkpoint:**
```python
update_step(output_folder, "generate_research_questions", "step_3b_validate_feasibility", "completed")
```

---

### Step 4: Score Candidates (Preliminary)

**IMPORTANT:** Only score candidates that passed the feasibility check (`status: "feasible"`). Infeasible candidates should NOT receive `preliminary_scores`.

For each feasible candidate, compute preliminary scores (0.0–1.0) on data feasibility (0.40), significance (0.20), novelty (0.25), and rigor (0.15). Compute composite weighted score.

See `references/REFERENCE.md: Scoring Criteria` for detailed scoring rubric and study design matching.

**Progress checkpoint:**
```python
update_step(output_folder, "generate_research_questions", "step_4_rank_select", "completed")
```

---

### Step 5: Assign Variable Roles (Per Candidate)

For **each feasible candidate question**, map every column from `variable_types.json` into exactly one of these five roles. Different candidates may assign different roles to the same column (e.g., a column is an outcome for one candidate but a covariate for another).

**Note:** Infeasible candidates should still include `variable_roles` for documentation purposes, but they will not be used in analysis.

**Role definitions:**
- **outcome_variables** — The dependent variable(s). Must be `numeric` or `binary` type and represent actual health measures.
- **exposure_variables** — The main independent variable(s). Must be `categorical`, `binary`, `numeric`, or `datetime`. Must NOT be `identifier` or `text`.
- **covariates** — Confounders and adjustment variables.
- **stratification_variables** — Variables used for subgroup analysis (not in the main model).
- **excluded_variables** — Variables not used, with a reason for each.

Optionally:
- **derived_variables** — Variables computed from raw columns. Each needs: `name`, `derivation`, and `source_columns`.

**Decision rules for ambiguous columns:**

See `references/REFERENCE.md: Variable Role Decision Rules` for the complete decision table on how to assign ambiguous columns (identifiers, denominators, datetime, metadata, etc.) to roles.

**Every raw column must appear in exactly one of the five raw-column categories.**

**Progress checkpoint:**
```python
update_step(output_folder, "generate_research_questions", "step_5_assign_variables", "completed")
```

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

**Progress checkpoint:**
```python
update_step(output_folder, "generate_research_questions", "step_6_assess_feasibility", "completed")
```

---

### Step 7: Save and Validate Output

Write to `<output_folder>/2_research_question/research_questions.json`.

**Important:** This stage outputs an array of **candidate questions** — it does NOT select a primary. Selection is deferred to the score-and-rank stage.

See `references/REFERENCE.md: Output Schema` for the complete JSON structure.

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