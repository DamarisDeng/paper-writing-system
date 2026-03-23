---
name: statistical-analysis
model: medium
description: >
  Run statistical analyses based on research_questions.json. Supports a wide
  range of methods: regression (OLS, logistic, Cox, Fine-Gray competing risks,
  Poisson, mixed-effects), penalized regression (LASSO, Ridge, Elastic Net),
  machine learning prediction (Random Forest, XGBoost, SVM), causal inference
  (DiD, propensity score matching, inverse probability weighting), and survival
  analysis (age-as-time-scale, left-truncation). Produces descriptive statistics
  (Table 1 data), primary analysis, sensitivity analyses, and analysis_results.json.
  Ships with pre-built helper functions for robust execution. Use after /acquire-data
  when research questions and data are ready. Triggers on: "run analysis",
  "statistical analysis", "fit model", "regression", "LASSO", "machine learning",
  "prediction model", "analyze the data", "causal inference", "propensity score",
  "survival analysis", or any request to go from research questions to results.
argument-hint: <output_folder>
---

# Statistical Analysis

Run descriptive and inferential statistical analyses driven by `research_questions.json`, producing `analysis_results.json` and saved scripts for reproducibility. Ships with a helper library (`helpers.py`) and method-specific templates to reduce fragility.

## Usage

```
/statistical-analysis <output_folder>
```

Reads from `<output_folder>/1_data_profile/`, `<output_folder>/2_scoring/`, and original raw data. Writes to `<output_folder>/3_analysis/`.

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/3_analysis/progress.json`.

**Steps tracked:**
- `step_1_load_inputs`: Load all input files
- `step_2_prepare_data`: Prepare analytic dataset
- `step_3_descriptive_stats`: Generate Table 1
- `step_3b_analysis_plan`: Write analysis plan
- `step_4_primary_analysis`: Run primary analysis
- `step_5_sensitivity`: Run sensitivity analyses
- `step_6_compile`: Compile and validate results

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

**Initialize progress tracker at start:**
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker, update_step, complete_stage, get_resume_point

# Check for resume point
resume_point = get_resume_point(output_folder, "statistical_analysis")
if resume_point == "start":
    tracker = create_stage_tracker(output_folder, "statistical_analysis",
        ["step_1_load_inputs", "step_2_prepare_data", "step_3_descriptive_stats",
         "step_3b_analysis_plan", "step_4_primary_analysis", "step_5_sensitivity",
         "step_6_compile"])
else:
    print(f"Resuming from: {resume_point}")
```

| If `progress.json` says last completed is... | Resume at |
|----------------------------------------------|-----------|
| `step_1_load_inputs` | Step 2: Prepare data |
| `step_2_prepare_data` | Step 3: Descriptive stats |
| `step_3_descriptive_stats` | Step 3b: Write analysis plan |
| `step_3b_analysis_plan` | Step 4: Primary analysis (read plan first) |
| `step_4_primary_analysis` | Step 5: Sensitivity analyses |
| `step_5_sensitivity` | Step 6: Compile and validate |

If `progress.json` does not exist, start from Step 1.

## Before You Start

1. **Copy helper modules** from this skill's `scripts/` directory into `<output_folder>/3_analysis/scripts/`:
   - Always: `utils.py`, `data_utils.py`, `descriptive.py`, `validation.py`
   - After Step 3b (when method is known): `regression.py`, `penalized.py`, `ml.py`, or `causal.py`

   See `references/REFERENCE.md: Helper Modules` for the complete module selection table.

2. **Read the method reference**: For non-trivial methods (anything beyond OLS), read `references/methods.md` for implementation guidance.

3. **Install dependencies**: `pip install --break-system-packages pandas numpy scipy statsmodels scikit-learn lifelines xgboost tableone`

## JAMA Formatting Helpers

`utils.py` provides `jama_p(p)`, `jama_ci(lo, hi)`, `jama_effect(estimate, ci_lo, ci_hi, p, metric="OR")`,
and `jama_fig(nrows, ncols)` for JAMA-style display strings and figures.

```python
from utils import jama_p, jama_ci, jama_effect, jama_fig, JAMA_BLUE, JAMA_ORANGE
```

## Instructions

You are a biostatistician conducting analyses for a JAMA Network Open paper. Every analysis must be reproducible, correctly specified, and honestly reported. When in doubt, choose the simpler model and document the decision.

---

### Step 1: Load All Inputs

Read these files:

1. **`<output_folder>/2_scoring/ranked_questions.json`** — Primary question, variable roles, derived variables, study design.
2. **`<output_folder>/1_data_profile/profile.json`** — Dataset metadata and column statistics (includes original file paths).
3. **`<output_folder>/1_data_profile/variable_types.json`** — Semantic variable types.
4. **Raw data files** — from original paths in `profile.json`.
5. **Downloaded data** from `<output_folder>/2_research_question/downloaded/` (if any).

Parse the `study_design` and `analysis_type` fields from `research_questions.json` — these drive method selection in Step 4.

---

### Step 2: Prepare the Analytic Dataset

Write `<output_folder>/3_analysis/scripts/prepare_data.py` using helpers from `data_utils.py`:

```python
from data_utils import load_and_merge, create_derived_variables, document_missingness, apply_exclusions, save_analytic_dataset
```

The script should: load datasets, create derived variables, document missingness (<5% fine, 5-20% flag, >20% exclude), apply exclusion criteria, save to `<output_folder>/3_analysis/analytic_dataset.csv`.

---

### Step 3: Descriptive Statistics (Table 1 Data)

Write `<output_folder>/3_analysis/scripts/descriptive_stats.py` using `generate_table1()` from `descriptive.py`:

```python
from descriptive import generate_table1
# Derive variable lists from variable_types.json
# Call generate_table1 with df, group_col, continuous_vars, categorical_vars
```

`generate_table1()` handles:
- Continuous variables: mean (SD) or median (IQR) based on Shapiro-Wilk test
- Categorical variables: N (%)
- Appropriate comparison tests (t-test, Wilcoxon, chi-square, Fisher's)
- Standardized mean differences
- Small cell size handling

Save output to `analysis_results.json` under `descriptive_statistics`. Include `table1_formatted` array for Stage 5 to consume directly (JAMA Table 1 conventions).

**Progress checkpoint:**
```python
update_step(output_folder, "statistical_analysis", "step_3_descriptive_stats", "completed",
             outputs=["3_analysis/analysis_results.json"])  # Partial results with descriptive stats
```

---

### Step 3b: Write the Analysis Plan

Before fitting models, save the analysis strategy to `<output_folder>/3_analysis/analysis_plan.json`. This captures model selection, covariates, clustering, and planned sensitivities for context compaction recovery.

Walk through the model selection decision tree and record the result. Copy the method-specific module based on `model_selection.selected_method`.

See `references/REFERENCE.md: Output Contract Schema` for the analysis plan JSON schema.

---

### Step 4: Primary Analysis — Model Selection

Read `<output_folder>/3_analysis/analysis_plan.json` → `model_selection` to determine the method, covariates, and clustering strategy. Do NOT re-derive the model choice — use what the plan specifies.

See `references/REFERENCE.md: Model Selection Decision Tree` for the complete decision tree with four tracks (Explanatory inference, Prediction, Causal inference, Survival analysis) and tie-breaking rules.

**Summary**: The decision tree has three levels (task → outcome + design → candidate methods). At the terminal node, apply tie-breaking rules to select one method. Track A for explanatory inference, Track B for prediction, Track C for causal inference, Track D for survival analysis.

See `references/REFERENCE.md: Helper Functions Reference` for the complete table of helper functions to call after method selection.

5. **Record the decision.**
   Save to `<output_folder>/3_analysis/model_selection.json`:
```json
   {
     "outcome_variable": "col_name",
     "outcome_type_raw": "numeric",
     "outcome_type_resolved": "continuous",
     "task_track": "A",
     "task_track_label": "Explanatory inference",
     "clustering_detected": true,
     "clustering_variable": "state_id",
     "study_design": "cross-sectional",
     "candidate_methods": ["OLS with clustered SE", "GEE-identity"],
     "selected_method": "OLS with clustered standard errors",
     "python_class": "statsmodels.OLS",
     "cov_type": "cluster",
     "tie_breaking_rule_applied": "Rule 1 (simplest valid model)",
     "flexibility_override": false,
     "rationale": "Continuous outcome, cross-sectional design, 50 state clusters detected. Both OLS+clustered SE and GEE qualify; OLS selected per tie-breaking rule 1 (simpler, easier to audit)."
   }
```

In the primary analysis output, include both raw and formatted values in `exposure_effect`:

```json
{
  "exposure_effect": {
    "raw": {
      "estimate": 1.45,
      "ci_lower": 1.22,
      "ci_upper": 1.72,
      "p_value": 0.00032,
      "se": 0.11
    },
    "formatted": {
      "estimate_str": "1.45",
      "ci_str": "1.22-1.72",
      "p_str": "< .001",
      "interpretation": "OR = 1.45 (95% CI, 1.22-1.72; P < .001)",
      "jama_sentence": "Vaccination was associated with significantly higher odds of hospitalization (OR, 1.45; 95% CI, 1.22-1.72; P < .001)."
    }
  }
}
```

**JAMA p-value formatting rules:**
- p < .001 → report as "< .001"
- .001 ≤ p < .01 → 3 decimal places (e.g., ".003")
- .01 ≤ p ≤ 1 → 2 decimal places (e.g., ".03")
- No leading zero (`.03` not `0.03`)

**Progress checkpoint:**
```python
update_step(output_folder, "statistical_analysis", "step_4_primary_analysis", "completed",
             outputs=["3_analysis/analysis_results.json"])  # Updated with primary analysis results
```

### Step 4b: Assumption Checks (method-specific)

Call `check_assumptions()` from `validation.py`:

```python
from validation import check_assumptions
assumption_results = check_assumptions(
    model_result=result,   # the dict returned by fit_regression / fit_ml_model / etc.
    method="ols",          # same method string passed to fit_regression
    df=df,
    outcome=outcome_col,
    predictors=covariates
)
```

Returns `{check_name: {"passed": bool, "details": str}}`. If a check fails, document it and add a sensitivity analysis. Save to `assumption_checks.json`.

See `references/REFERENCE.md: JAMA Formatting Guide` for the complete assumption checks table by method.
---

### Step 5: Sensitivity Analyses

Run **at least two** sensitivity analyses. Write each as a separate script in `scripts/sensitivity_*.py`. Choose sensitivities appropriate to the method track.

See `references/REFERENCE.md: Sensitivity Analyses` for the complete list of 17 sensitivity analyses organized by track:
- Universal: Alternative covariates, subgroup analysis, missing data robustness, outlier sensitivity
- Track A: Alternative model specification, penalized regression comparison
- Track B: Alternative ML model, bootstrap CI, calibration check
- Track C: E-value (mandatory), alternative propensity model, pre-trend test, trimming sensitivity
- Track D: Proportional hazards test, competing risks sensitivity, landmark analysis

**Progress checkpoint:**
```python
update_step(output_folder, "statistical_analysis", "step_5_sensitivity", "completed")
```

---

### Step 6: Compile Results

Save all results to `<output_folder>/3_analysis/analysis_results.json` using `validation.compile_analysis_results()`.

**Progress checkpoint - Mark stage complete:**
```python
update_step(output_folder, "statistical_analysis", "step_6_compile", "completed")
from progress_utils import complete_stage_with_context
complete_stage_with_context(
    output_folder=output_folder,
    stage_name="statistical_analysis",
    context_mode="safe",
    expected_outputs=["3_analysis/analysis_results.json",
                      "3_analysis/analytic_dataset.csv",
                      "3_analysis/analysis_plan.json",
                      "3_analysis/results_summary.md"],
    summary=f"Completed {method} analysis with N={total_n}, primary effect: {estimate} ({ci})"
)
```

After writing `analysis_results.json`, also write `<output_folder>/3_analysis/results_summary.md`. This is prose Stage 7 can copy directly into the paper.

See `references/REFERENCE.md: Output Contract Schema` for the results summary template.

---

### Step 7: Validate

Run validation checks via `validation.validate_analysis()`. Checks include:
- `analysis_results.json` exists and is valid JSON
- Descriptive and primary analysis sections complete
- At least one sensitivity analysis present
- No p-values as exactly 0.000 (use `< 0.001`)
- Plausible effect sizes (ORs between 0.01 and 100)
- If ML: train/test performance gap < 15%

---

## Output Contract

**Output files:**
- `<output_folder>/3_analysis/analysis_results.json` — Complete analysis results
- `<output_folder>/3_analysis/analytic_dataset.csv` — Merged, cleaned dataset
- `<output_folder>/3_analysis/scripts/` — All Python scripts (independently runnable)
- `<output_folder>/3_analysis/models/` — Saved model summaries as text files
- `<output_folder>/3_analysis/analysis_plan.json` — Model selection reasoning and planned sensitivities
- `<output_folder>/3_analysis/progress.json` — Step tracking for resume capability
- `<output_folder>/3_analysis/results_summary.md` — Prose summary for Stage 7

See `references/REFERENCE.md: Output Contract Schema` for complete JSON schemas.