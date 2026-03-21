---
name: statistical-analysis
model: medium
description: >
  Run statistical analyses based on research_questions.json. Supports a wide
  range of methods: regression (OLS, logistic, Cox, Poisson, mixed-effects),
  penalized regression (LASSO, Ridge, Elastic Net), machine learning prediction
  (Random Forest, XGBoost, SVM), causal inference (DiD, propensity score matching,
  inverse probability weighting), and survival analysis. Produces descriptive
  statistics (Table 1 data), primary analysis, sensitivity analyses, and
  analysis_results.json. Ships with pre-built helper functions for robust execution.
  Use after /acquire-data when research questions and data are ready.
  Triggers on: "run analysis", "statistical analysis", "fit model", "regression",
  "LASSO", "machine learning", "prediction model", "analyze the data",
  "causal inference", "propensity score", "survival analysis", or any request
  to go from research questions to results.
argument-hint: <output_folder>
---

# Statistical Analysis

Run descriptive and inferential statistical analyses driven by `research_questions.json`, producing `analysis_results.json` and saved scripts for reproducibility. Ships with a helper library (`helpers.py`) and method-specific templates to reduce fragility.

## Usage

```
/statistical-analysis <output_folder>
```

Reads from `<output_folder>/1_data_profile/`, `<output_folder>/2_research_question/`, and original raw data. Writes to `<output_folder>/3_analysis/`.

## Resume Protocol

If you are resuming after context compaction or picking up mid-stage:

1. Read `<output_folder>/3_analysis/progress.json` (if it exists).
2. Find the last completed step.
3. Read `analysis_plan.json` (if it exists) to restore the analysis strategy.
4. Continue from the next incomplete step. **Never re-run a completed step.**

| If `progress.json` says last completed is... | Resume at |
|----------------------------------------------|-----------|
| `step_2_prepare_data` | Step 3: Descriptive stats |
| `step_3_descriptive_stats` | Step 3b: Write analysis plan |
| `step_3b_analysis_plan` | Step 4: Primary analysis (read plan first) |
| `step_4_primary_analysis` | Step 5: Sensitivity analyses |
| `step_5_sensitivity` | Step 6: Compile and validate |

If `progress.json` does not exist, start from Step 1.

## Before You Start

1. **Copy the always-required helper modules** from this skill's `scripts/` directory into `<output_folder>/3_analysis/scripts/`:

   ```
   utils.py        — p-value formatting, JSON I/O (imported by all others)
   data_utils.py   — loading, merging, derived vars, missingness, exclusions
   descriptive.py  — Table 1 generation
   validation.py   — assumption checks, result validation, compilation
   ```

   Copy the method-specific module **after Step 3b**, once `analysis_plan.json` has been written and the method is known:

   | Module | Copy when `model_selection.selected_method` is... |
   |---|---|
   | `regression.py` | OLS, logistic, Poisson, NegBin, mixed-effects, Cox |
   | `penalized.py` | LASSO, Ridge, Elastic Net |
   | `ml.py` | Random Forest, XGBoost, SVM, KNN |
   | `causal.py` | PSM, IPW, DiD, ITS |

2. **Read the method reference**: If the analysis method is non-trivial (anything beyond OLS), read `references/methods.md` from this skill's directory for implementation guidance and known pitfalls.

3. **Install dependencies** up front:
   ```bash
   pip install --break-system-packages pandas numpy scipy statsmodels scikit-learn lifelines xgboost tableone
   ```

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

1. **`<output_folder>/2_research_question/research_questions.json`** — Primary question, variable roles, derived variables, study design.
2. **`<output_folder>/1_data_profile/profile.json`** — Dataset metadata and column statistics (includes original file paths).
3. **`<output_folder>/1_data_profile/variable_types.json`** — Semantic variable types.
4. **Raw data files** — from original paths in `profile.json`.
5. **Downloaded data** from `<output_folder>/2_research_question/downloaded/` (if any).

Parse the `study_design` and `analysis_type` fields from `research_questions.json` — these drive method selection in Step 4.

---

### Step 2: Prepare the Analytic Dataset

Write `<output_folder>/3_analysis/scripts/prepare_data.py`. This script imports from the helper modules:

```python
# Template — adapt to your data
import sys; sys.path.insert(0, ".")
from data_utils import load_and_merge, create_derived_variables, document_missingness, apply_exclusions, save_analytic_dataset
```

The script should:

1. **Load all required datasets** using `load_and_merge()`, which handles CSV/Excel detection, encoding issues, and merge validation.
2. **Create derived variables** from `research_questions.json → variable_roles.derived_variables`. Use `create_derived_variables()` which logs each derivation and validates output.
3. **Document missingness** with `document_missingness()`:
   - <5% missing → complete-case is fine
   - 5–20% missing → flag for sensitivity analysis with imputation
   - \>20% missing → exclude from primary analysis
4. **Apply exclusion criteria** based on population definition.
5. **Save** to `<output_folder>/3_analysis/analytic_dataset.csv`.
6. **Print summary**: N total, N excluded (with reasons), missingness per variable.

**Checkpoint:** Update `<output_folder>/3_analysis/progress.json`:
```json
{
  "current_step": "step_2_prepare_data",
  "completed_steps": ["step_2_prepare_data"],
  "last_updated": "ISO-8601",
  "notes": ""
}
```

---

### Step 3: Descriptive Statistics (Table 1 Data)

Write `<output_folder>/3_analysis/scripts/descriptive_stats.py`. Use the helper:

```python
from descriptive import generate_table1
from utils import update_json_section
```

Derive variable lists from `variable_types.json` and call `generate_table1` with all required arguments:

```python
# Derive variable lists from variable_types.json
continuous_vars = [col for col, info in variable_types.items()
                   if info.get("type") in ("continuous", "numeric")]
categorical_vars = [col for col, info in variable_types.items()
                    if info.get("type") in ("categorical", "binary", "ordinal")]
group_col = research_questions["variable_roles"]["exposure"]

table1 = generate_table1(df, group_col=group_col,
                         continuous_vars=continuous_vars,
                         categorical_vars=categorical_vars)
```

`generate_table1()` handles:
- Continuous variables: mean (SD) or median (IQR) based on Shapiro-Wilk normality test
- Categorical variables: N (%)
- Appropriate comparison tests (t-test / Wilcoxon for continuous, chi-square / Fisher's for categorical)
- Standardized mean differences for key covariates
- Graceful handling of small cell sizes (switches to Fisher's exact when expected count <5)

Save output to `analysis_results.json` under `descriptive_statistics`.

Include a pre-formatted Table 1 array in `analysis_results.json` under `descriptive_statistics.table1_formatted` that Stage 5 can render directly:

```json
{
  "table1_formatted": [
    {
      "variable": "Age, mean (SD)",
      "overall": "45.0 (12.0)",
      "group_1": "45.2 (12.1)",
      "group_2": "44.8 (11.9)",
      "p_value": ".03",
      "test": "t-test"
    },
    {
      "variable": "Female sex, No. (%)",
      "overall": "15336 (49.3)",
      "group_1": "6234 (50.2)",
      "group_2": "9102 (48.6)",
      "p_value": ".01",
      "test": "χ²"
    }
  ]
}
```

This follows JAMA Table 1 conventions and can be consumed by Stage 5 (generate-figures) without recomputation.

**Checkpoint:** Update `<output_folder>/3_analysis/progress.json`:
```json
{
  "current_step": "step_3_descriptive_stats",
  "completed_steps": ["step_2_prepare_data", "step_3_descriptive_stats"],
  "last_updated": "ISO-8601",
  "notes": ""
}
```

---

### Step 3b: Write the Analysis Plan

Before fitting any models, save the complete analysis strategy to
`<output_folder>/3_analysis/analysis_plan.json`. This file captures
the reasoning that is expensive to reproduce — model selection,
covariate rationale, sensitivity strategy — so that if context
compacts, the model can re-read this file and proceed directly to
computation without re-deriving the plan.

Walk through the model selection decision tree (Step 4's table) and
record the result. Also specify the sensitivity analyses you intend
to run.

Save to `<output_folder>/3_analysis/analysis_plan.json`:

```json
{
  "created_at": "ISO-8601",

  "analytic_sample_summary": {
    "total_n": 44312,
    "exposure_groups": {
      "vaccinated": 28100,
      "unvaccinated": 16212
    }
  },

  "model_selection": {
    "outcome_variable": "hospitalization",
    "outcome_type": "binary",
    "exposure_variable": "vaccination_status",
    "covariates": ["age", "sex", "race", "comorbidity_index"],
    "clustering_detected": false,
    "clustering_variable": null,
    "study_design": "cross-sectional",
    "selected_method": "Logistic regression",
    "python_class": "statsmodels.Logit",
    "cov_type": null,
    "rationale": "Binary outcome, cross-sectional design, no clustering detected. Covariates selected based on variable_roles from research_questions.json."
  },

  "sensitivity_analyses_planned": [
    {
      "name": "Subgroup by age group",
      "description": "Stratified logistic regression for age <65 vs ≥65",
      "why": "Effect may differ by age due to differential vaccine efficacy"
    },
    {
      "name": "Alternative covariate set",
      "description": "Add income and education as additional covariates",
      "why": "Assess sensitivity to potential socioeconomic confounding"
    }
  ],

  "table1_grouping_variable": "vaccination_status",
  "table1_comparison_test_strategy": "t-test for normal continuous, Wilcoxon for skewed, chi-square for categorical"
}
```

The remaining steps (4, 5, 6) execute this plan. If context compacts
at any point after this step, re-read `analysis_plan.json` and
continue from the next incomplete step per `progress.json`.

**Copy the method-specific module now.** Look up `model_selection.selected_method` in `analysis_plan.json` and copy the corresponding script from this skill's `scripts/` directory into `<output_folder>/3_analysis/scripts/` (see the table in "Before You Start").

**Checkpoint:** Update `<output_folder>/3_analysis/progress.json`:
```json
{
  "current_step": "step_3b_analysis_plan",
  "completed_steps": ["step_2_prepare_data", "step_3_descriptive_stats", "step_3b_analysis_plan"],
  "last_updated": "ISO-8601",
  "notes": "Logistic regression selected; binary outcome, no clustering"
}
```

---

### Step 4: Primary Analysis — Model Selection Decision Tree

Read `<output_folder>/3_analysis/analysis_plan.json` → `model_selection` to determine the method, covariates, and clustering strategy. Do NOT re-derive the model choice — use what the plan specifies.

Walk through these checks **in order**. Stop at the first matching terminal node.

1. **What is the outcome type?**
   - Read from `variable_types.json` for the outcome column.
   - If `numeric`: go to 2.
   - If `binary`: go to 3.
   - If `numeric` but unique values ≤ 10: treat as **ordinal** → use ordinal logistic
     (`statsmodels.OrderedModel`). Go to 5.

2. **Continuous outcome — is there clustering?**
   - Check: are observations nested within groups (e.g., states, hospitals, schools)?
     Look for identifier columns in `variable_roles.covariates` that are categorical
     with 5–200 levels.
   - If YES + study_design is `longitudinal`: **Mixed-effects model**
     (`statsmodels.MixedLM`). → Go to 5.
   - If YES + study_design is `cross-sectional`: **OLS with clustered standard errors**
     (`statsmodels.OLS` + `cov_type='cluster'`). → Go to 5.
   - If NO clustering: **OLS** (`statsmodels.OLS`). → Go to 5.

3. **Binary outcome — is there clustering?**
   - If YES: **GEE with logit link** (`statsmodels.GEE`) or logistic with
     clustered SEs. → Go to 5.
   - If NO + study_design is `ecological-did`:
     **Logistic regression with exposure × time interaction**. → Go to 5.
   - If NO: **Logistic regression** (`statsmodels.Logit`). → Go to 5.

4. **Count outcome — check dispersion.**
   - Fit Poisson first. Compute dispersion = deviance / df_resid.
   - If dispersion > 1.5: use **Negative Binomial**
     (`statsmodels.NegativeBinomial`).
   - If many zeros (>30% of outcome values are 0): use **Zero-Inflated Poisson**
     (`statsmodels.ZeroInflatedPoisson`).
   - Otherwise: **Poisson** (`statsmodels.Poisson`).
   - → Go to 5.

**After resolving the method from `analysis_plan.json`, call the corresponding helper:**

| Method | Import + Call |
|--------|--------------|
| OLS / logit / Poisson / NegBin / mixed / Cox | `from regression import fit_regression`<br>`results = fit_regression(df, outcome, exposure, covariates, method=..., cluster_col=...)` |
| LASSO / Ridge / Elastic Net | `from penalized import fit_penalized`<br>`results = fit_penalized(df, outcome, predictors, method=..., task="auto")` |
| Random Forest / XGBoost / SVM / KNN | `from ml import fit_ml_model`<br>`results = fit_ml_model(df, outcome, predictors, method=..., task="auto")` |
| PSM | `from causal import propensity_score_match`<br>`results = propensity_score_match(df, treatment_col, covariates, outcome_col)` |
| IPW | `from causal import ipw_estimate`<br>`results = ipw_estimate(df, treatment_col, covariates, outcome_col)` |
| DiD | `from causal import did_regression`<br>`results = did_regression(df, outcome, treatment_col, time_col, covariates)` |
| ITS | `from causal import its_analysis`<br>`results = its_analysis(df, outcome, time_col, intervention_point)` |

Do NOT re-implement these from scratch — the helpers handle clustering, SE correction,
output formatting, and JSON-ready results.

5. **Record the decision.**
   Save to `<output_folder>/3_analysis/model_selection.json`:
```json
   {
     "outcome_variable": "col_name",
     "outcome_type_raw": "numeric",
     "outcome_type_resolved": "continuous",
     "clustering_detected": true,
     "clustering_variable": "state_id",
     "study_design": "cross-sectional",
     "selected_method": "OLS with clustered standard errors",
     "python_class": "statsmodels.OLS",
     "cov_type": "cluster",
     "rationale": "Continuous outcome, cross-sectional design, 50 state clusters detected"
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

**Checkpoint:** Update `<output_folder>/3_analysis/progress.json`:
```json
{
  "current_step": "step_4_primary_analysis",
  "completed_steps": ["step_2_prepare_data", "step_3_descriptive_stats", "step_3b_analysis_plan", "step_4_primary_analysis"],
  "last_updated": "ISO-8601",
  "notes": ""
}
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

Returns `{check_name: {"passed": bool, "details": str}}`. If a check fails, document it
and add a sensitivity analysis (Step 5). Save to `assumption_checks.json`.

Supported methods: `"ols"`, `"logit"`, `"cox"`. For penalized/ML/causal, skip
`check_assumptions` and run method-specific diagnostics per `references/methods.md`.
---

### Step 5: Sensitivity Analyses

Run **at least two** of the following (more is better). Write each as a separate script in `scripts/sensitivity_*.py`.

1. **Alternative model specification** — Add/remove covariates, different functional form.
2. **Subgroup analysis** — Stratify by `stratification_variables`.
3. **Robustness to missing data** — Compare complete-case vs. imputed results.
4. **E-value for unmeasured confounding** — For observational studies, compute the E-value.
5. **Alternative ML model** — If primary was XGBoost, run Random Forest as comparison.
6. **Bootstrap confidence intervals** — Non-parametric CI estimation.
7. **Outlier sensitivity** — Refit excluding influential observations (Cook's distance > 4/N).
8. **Alternative outcome definition** — If outcome can be operationalized differently.

**Checkpoint:** Update `<output_folder>/3_analysis/progress.json`:
```json
{
  "current_step": "step_5_sensitivity",
  "completed_steps": ["step_2_prepare_data", "step_3_descriptive_stats", "step_3b_analysis_plan", "step_4_primary_analysis", "step_5_sensitivity"],
  "last_updated": "ISO-8601",
  "notes": ""
}
```

---

### Step 6: Compile Results

Save all results to `<output_folder>/3_analysis/analysis_results.json` using `validation.compile_analysis_results()`. This function sanitizes p-values and validates the JSON schema before writing.

The output schema is documented in `references/methods.md` under "Output Contract."

**Checkpoint:** Update `<output_folder>/3_analysis/progress.json`:
```json
{
  "current_step": "step_6_compile",
  "completed_steps": ["step_2_prepare_data", "step_3_descriptive_stats", "step_3b_analysis_plan", "step_4_primary_analysis", "step_5_sensitivity", "step_6_compile"],
  "last_updated": "ISO-8601",
  "notes": ""
}
```

After writing `analysis_results.json`, also write `<output_folder>/3_analysis/results_summary.md`. This is prose Stage 7 can copy directly into the paper. Structure:

```markdown
## Study Sample
- Total analytic sample: N = {total_n} ({group_1_name}: n = {n1}; {group_2_name}: n = {n2})
- {key demographic line from table1_formatted, e.g. "Mean age 45.2 (SD 12.1) years"}
- {one line per additional demographic worth flagging}

## Primary Result
{primary_analysis.results.exposure_effect.formatted.jama_sentence}

## Sensitivity Analyses
- {sensitivity_name}: {jama-formatted sentence from sensitivity results}
- (repeat for each sensitivity analysis)

## Figure Captions
**Figure 1.** {What is shown}. {Method used}. {Covariates adjusted for, if any}. {Sample, N=...}.
(repeat for each figure)

## Statistical Methods Note
All analyses were conducted in Python (version X.X) using statsmodels (version X.X), scipy (version X.X), and pandas (version X.X). Statistical significance was defined as a 2-sided P < .05. {Model-specific sentence, e.g. "Logistic regression was used to estimate odds ratios with 95% confidence intervals."} {Sensitivity analysis description sentence.}
```

---

### Step 7: Validate

Run the validation checks (built into `validation.validate_analysis()`):

- `analysis_results.json` exists and parses as valid JSON
- `descriptive_statistics` has data for all exposure groups
- `primary_analysis` has coefficients, CIs, and p-values (or performance metrics for ML)
- At least one sensitivity analysis is present
- All scripts in `scripts/` directory execute without errors
- No p-values reported as exactly 0.000 (use `< 0.001`)
- Effect sizes are plausible (ORs between 0.01 and 100; coefficients not infinite)
- If ML: train/test performance gap < 15% (checks for overfitting)

---

## Output Contract

**`<output_folder>/3_analysis/analysis_results.json`**:

```json
{
  "analytic_sample": {
    "total_n": 31142,
    "excluded_n": 500,
    "exclusion_reasons": ["Missing outcome: 300", "Missing exposure: 200"],
    "exposure_groups": {
      "group_1_name": {"n": 12431},
      "group_2_name": {"n": 18711}
    }
  },
  "descriptive_statistics": {
    "variables": {
      "variable_name": {
        "type": "continuous",
        "overall": {"mean": 45.2, "sd": 12.1},
        "by_group": {
          "group_1": {"mean": 44.8, "sd": 11.9},
          "group_2": {"mean": 45.5, "sd": 12.3}
        },
        "p_value": 0.032,
        "test_used": "t-test",
        "smd": 0.058
      }
    },
    "table1_formatted": [
      {
        "variable": "Age, mean (SD)",
        "overall": "45.0 (12.0)",
        "group_1": "45.2 (12.1)",
        "group_2": "44.8 (11.9)",
        "p_value": ".03",
        "test": "t-test"
      },
      {
        "variable": "Female sex, No. (%)",
        "overall": "15336 (49.3)",
        "group_1": "6234 (50.2)",
        "group_2": "9102 (48.6)",
        "p_value": ".01",
        "test": "χ²"
      }
    ]
  },
  "primary_analysis": {
    "method": "Logistic regression",
    "method_category": "regression|penalized|ml_prediction|causal_inference",
    "rationale": "Why this method was selected",
    "outcome": "vaccination_status",
    "exposure": "mandate_status",
    "covariates": ["age", "sex", "race", "income"],
    "results": {
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
    },
    "model_fit": {
      "aic": 12345.6,
      "bic": 12400.1,
      "pseudo_r_squared": 0.087,
      "c_statistic": 0.72
    },
    "assumption_checks": {
      "check_name": {"passed": true, "details": "..."}
    },
    "ml_performance": null
  },
  "sensitivity_analyses": [
    {
      "name": "Subgroup analysis by age group",
      "description": "Stratified logistic regression by age category",
      "results": {}
    }
  ],
  "scripts_used": [
    "scripts/utils.py",
    "scripts/data_utils.py",
    "scripts/descriptive.py",
    "scripts/regression.py",
    "scripts/validation.py",
    "scripts/prepare_data.py",
    "scripts/descriptive_stats.py",
    "scripts/primary_analysis.py",
    "scripts/sensitivity_subgroup.py"
  ]
}
```

If the primary analysis uses ML prediction, `ml_performance` replaces `model_fit`:

```json
"ml_performance": {
  "train": {"auc_roc": 0.89, "accuracy": 0.82},
  "test": {"auc_roc": 0.85, "accuracy": 0.79},
  "cv_mean_auc": 0.86,
  "cv_std_auc": 0.03,
  "feature_importance": [
    {"feature": "age", "importance": 0.25},
    {"feature": "income", "importance": 0.18}
  ],
  "hyperparameters": {"max_depth": 6, "n_estimators": 200}
}
```

**`<output_folder>/3_analysis/analytic_dataset.csv`** — Merged, cleaned dataset.

**`<output_folder>/3_analysis/scripts/`** — All Python scripts (independently runnable). Must include `helpers.py`.

**`<output_folder>/3_analysis/models/`** — Saved model summaries as text files.

**`<output_folder>/3_analysis/analysis_plan.json`** — Written at Step 3b. Contains model selection reasoning (method, covariates, clustering strategy) and planned sensitivity analyses. Used to resume mid-stage after context compaction without re-deriving the analysis strategy.

**`<output_folder>/3_analysis/progress.json`** — Updated after each sub-step (Steps 2, 3, 3b, 4, 5, 6). Tracks `current_step`, `completed_steps`, `last_updated`, and `notes`. Read at the start of a resumed session to find the next incomplete step.

**`<output_folder>/3_analysis/results_summary.md`** — Written at Step 6. Prose summary (study sample, primary result sentence, sensitivity sentences, figure captions, statistical methods note) ready for Stage 7 to paste into the paper without recomputation.
