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

Reads from `<output_folder>/1_data_profile/`, `<output_folder>/2_research_question/`, and original raw data. Writes to `<output_folder>/3_analysis/`.

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

1. **Copy the always-required helper modules** from this skill's `scripts/` directory into `<output_folder>/3_analysis/scripts/`:

   ```
   utils.py        — p-value formatting, JSON I/O (imported by all others)
   data_utils.py   — loading, merging, derived vars, missingness, exclusions
   descriptive.py  — Table 1 generation
   validation.py   — assumption checks, result validation, compilation
   ```

   Copy the method-specific module **after Step 3b**, once `analysis_plan.json` has been written and the method is known:

   | Module | Copy when `model_selection.task_track` and `selected_method` is... |
   |---|---|
   | `regression.py` | Track A: OLS, logistic, Poisson, NegBin, ordinal, mixed-effects, GEE<br>Track D: Cox, AFT, Fine-Gray |
   | `penalized.py` | Track A (high-dim) or Track B: LASSO, Ridge, Elastic Net |
   | `ml.py` | Track B: Random Forest, XGBoost, SVM, KNN |
   | `causal.py` | Track C: PSM, IPW, AIPW, DiD, ITS |

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

**Progress checkpoint:**
```python
update_step(output_folder, "statistical_analysis", "step_2_prepare_data", "completed",
             outputs=["3_analysis/analytic_dataset.csv"])
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
                         categorical_vars=categorical_vars,
                         weights_col=weights_col)  # Optional: survey weights
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

**Progress checkpoint:**
```python
update_step(output_folder, "statistical_analysis", "step_3_descriptive_stats", "completed",
             outputs=["3_analysis/analysis_results.json"])  # Partial results with descriptive stats
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
    "task_track": "A",
    "task_track_label": "Explanatory inference",
    "candidate_methods": ["Logistic regression"],
    "selected_method": "Logistic regression",
    "python_class": "statsmodels.Logit",
    "cov_type": null,
    "tie_breaking_rule_applied": null,
    "flexibility_override": false,
    "rationale": "Binary outcome, cross-sectional design, no clustering. Track A inference: logistic regression is the sole qualifying candidate. Covariates from variable_roles."
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

**Progress checkpoint:**
```python
update_step(output_folder, "statistical_analysis", "step_3b_analysis_plan", "completed",
             outputs=["3_analysis/analysis_plan.json"],
             notes="Logistic regression selected; binary outcome, no clustering")
```

---

### Step 4: Primary Analysis — Model Selection Decision Tree

Read `<output_folder>/3_analysis/analysis_plan.json` → `model_selection` to determine the method, covariates, and clustering strategy. Do NOT re-derive the model choice — use what the plan specifies.

The tree has **three levels**: task → outcome + design → candidate methods. Work through them in order. At the terminal node you will find 1–3 candidate methods; apply the tie-breaking rules to pick one and document why.

---

#### Level 1 — What is the primary task?

Read `research_questions.json → analysis_type`. Map it to one of four tracks:

| `analysis_type` value | Track |
|---|---|
| `"association"`, `"risk_factor"`, `"inference"` | **Track A — Explanatory inference** |
| `"prediction"`, `"classification"`, `"risk_score"` | **Track B — Prediction** |
| `"causal_effect"`, `"treatment_effect"`, `"policy_evaluation"` | **Track C — Causal inference** |
| `"survival"`, `"time_to_event"` | **Track D — Survival / time-to-event** |

If `analysis_type` is ambiguous or absent, default to **Track A** and note it in `rationale`.

---

#### Track A — Explanatory Inference

Goal: estimate an interpretable association (coefficient, OR, RR) with valid uncertainty. Prioritize interpretability and assumption transparency over predictive performance.

**A1. What is the outcome type?**

- **Continuous** → go to A2
- **Binary** → go to A3
- **Count** → go to A4
- **Ordinal** (numeric, ≤ 10 unique values) → **Ordinal logistic** (`statsmodels.OrderedModel`). Candidates: `[OrderedModel]`. Go to A5.
- **Multinomial** (categorical, > 2 classes) → **Multinomial logistic** (`statsmodels.MNLogit`). Candidates: `[MNLogit]`. Go to A5.

**A2. Continuous outcome — is there clustering or repeated measures?**

- Clustering present AND `study_design = "longitudinal"` → Candidates: **`[MixedLM, GEE-identity]`**. Prefer `MixedLM` if random effects are of scientific interest; prefer `GEE` if only population-average estimate is needed.
- Clustering present AND `study_design = "cross-sectional"` → Candidates: **`[OLS + clustered SE, GEE-identity]`**. Prefer `OLS + clustered SE` for simplicity; prefer `GEE` if correlation structure is complex.
- No clustering → Candidates: **`[OLS]`**. Go to A5.

**A3. Binary outcome — is there clustering?**

- Clustering present → Candidates: **`[GEE-logit, Mixed logistic (MixedLM with binomial)]`**. Prefer `GEE` for population-average OR; prefer mixed logistic if subject-specific OR is needed.
- `study_design = "ecological-did"` → Candidates: **`[Logistic with exposure × time interaction]`**. Go to A5.
- No clustering → Candidates: **`[Logistic regression]`**. Go to A5.

**A4. Count outcome — check dispersion.**

Fit Poisson first; compute dispersion = deviance / df_resid.

- dispersion > 1.5 → Candidates: **`[NegativeBinomial, Quasi-Poisson]`**. Prefer NegBin for count data with clear overdispersion; prefer Quasi-Poisson when overdispersion is moderate and you want simpler inference.
- Zero-inflated (> 30% zeros) → Candidates: **`[ZeroInflatedPoisson, ZeroInflatedNegBin]`**. Prefer ZINB if overdispersion is also present.
- Otherwise → Candidates: **`[Poisson]`**.

**A5. Penalized regression as an alternative for Track A.** If p > N/5 (many predictors relative to sample size) OR collinearity (VIF > 10 for ≥ 2 predictors), add **Elastic Net** to the candidates list and note it in `rationale`. Elastic Net preserves interpretable coefficients while handling high dimensionality; prefer it over LASSO when predictors are correlated.

---

#### Track B — Prediction

Goal: maximize generalization performance. Interpretability is secondary unless the research question requires a risk score that clinicians will use directly.

**B1. How many predictors are there relative to N?**

- High-dimensional (p > N/10) → Candidates: **`[LASSO, Elastic Net, Ridge]`** for linear/logistic tasks. Add a tree method if non-linearity is suspected.
- Low-to-moderate dimensionality → go to B2.

**B2. Is the outcome continuous or categorical?**

- Continuous → Candidates: **`[XGBoost-regressor, Random Forest-regressor, Ridge]`**.
  - Use `Ridge` if a linear baseline or interpretable coefficients are needed.
  - Use `XGBoost` or `Random Forest` when non-linearity or interactions are likely.
  - Use `XGBoost` over `Random Forest` if N > 5000 and computational budget allows.
- Binary classification → Candidates: **`[XGBoost-classifier, Random Forest-classifier, Logistic + penalization]`**.
  - Use penalized logistic as the interpretable baseline.
  - Add XGBoost or RF when AUC of the baseline falls below 0.70.
- Multi-class → Candidates: **`[XGBoost-multiclass, Random Forest-multiclass]`**.

**B3. Evaluation protocol for all prediction models.**

Regardless of method chosen:
- Split: stratified 70/15/15 (train/val/test) or 5-fold CV if N < 500.
- Report train and test AUC/RMSE; flag if gap > 15% (overfitting).
- Report feature importances (SHAP values preferred for XGBoost/RF).
- If a penalized model is chosen, perform cross-validated hyperparameter search (alpha/lambda).

---

#### Track C — Causal Inference

Goal: estimate an average treatment effect (ATE or ATT) under explicit assumptions. Causal methods are only valid when the study design supports causal claims (observational with a well-defined treatment; natural experiment; panel data with a policy change). Document the causal assumption being invoked.

**C1. What is the study design?**

- `"observational"` with a binary treatment AND no natural experiment → go to C2.
- `"observational"` with a binary treatment AND rich confounder data (≥ 10 measured confounders) → go to C3.
- `"panel"` or `"ecological-did"` with a policy change at a known time → **Difference-in-Differences (DiD)**. Candidates: **`[DiD OLS with treatment × post interaction, Callaway-Sant'Anna staggered DiD]`**. Prefer staggered DiD if treatment timing varies across units.
- `"ecological-panel"` with a single treated unit and no control group → **Interrupted Time Series (ITS)**. Candidates: **`[ITS segmented regression]`**. Go to C4.

**C2. Standard observational — balance first.**

- Run propensity score model (logistic or LASSO-logistic if many confounders).
- Assess overlap (check propensity score distributions; flag if < 10% of treated or control have no counterparts).
- Candidates: **`[PSM (1:1 nearest-neighbor), IPW (stabilized weights), AIPW (doubly robust)]`**.
  - Use `PSM` when you want matched-pair intuition and balanced Table 1. Call `propensity_score_match()` from `causal.py`.
  - Use `IPW` when matching would discard too many observations. Call `ipw_estimate()` from `causal.py`.
  - Use `AIPW` (doubly robust) when you want protection against misspecification of either the propensity score or the outcome model — **preferred default when N > 1000**. Call `aipw_estimate()` from `causal.py`.
- Go to C4.

**C3. High-dimensional confounding (≥ 10 confounders or p > N/5).**

- Candidates: **`[LASSO-based propensity score + IPW, AIPW (doubly robust), high-dimensional PSM (hdPS)]`**.
- Prefer AIPW (doubly robust) for robustness against misspecification of either the propensity score or outcome model. Call `aipw_estimate()` from `causal.py`.
- Go to C4.

**C4. All causal analyses must report:**
- Balance table (SMD before and after weighting/matching; target SMD < 0.1 for all covariates).
- Positivity/overlap check.
- Sensitivity analysis: E-value for unmeasured confounding (mandatory for observational designs).
- For DiD: pre-trend test (parallel trends assumption).
- For ITS: test for autocorrelation (Durbin-Watson).

---

#### Track D — Survival / Time-to-Event

**D0. Data requirements for survival analysis:**
- `time_col`: Time-to-event or age-at-event column
- `event_col`: Event indicator (0=censored, 1=event, 2=competing for Fine-Gray)
- For age-as-time-scale: include entry age column (`age_entry`, `entry_age`, etc.)

**D1. Is the hazard assumption plausible?**

- Standard survival with time-varying or fixed covariates → Candidates: **`[Cox PH, Parametric AFT (Weibull or log-normal)]`**.
  - Use Cox PH as default (semi-parametric, no distributional assumption).
  - Use `time_scale="age"` for age-as-time-scale analysis (left-truncation).
  - Use parametric AFT if Schoenfeld residuals show PH violation AND the event-time distribution is well-characterized.
- Competing risks present → Candidates: **`[Cause-specific Cox, Fine-Gray subdistribution hazard]`**.
  - Use cause-specific Cox when the mechanism for the event of interest is the focus.
  - Use Fine-Gray (`method="fine_gray"`) when the research question is about cumulative incidence in the presence of competing events.
  - Event coding: 0=censored, 1=event_of_interest, 2=competing_event.

**D2. All survival analyses must report:**
- Median survival with 95% CI per group (Kaplan-Meier).
- Schoenfeld residuals test for proportional hazards (if Cox used).
- Censoring summary (% censored, reason if known).
- For competing risks: cumulative incidence functions.

**Example: Age-as-time-scale Cox model**
```python
from regression import fit_regression
results = fit_regression(
    df,
    outcome="age_at_death",      # Age at event/censoring
    exposure="treatment",
    covariates=["sex", "comorbidity"],
    method="cox",
    time_scale="age",            # Use age as time scale
    # Requires: age_entry column in df
)
```

---

#### Tie-breaking rules (apply when candidates list has > 1 method)

When multiple candidates qualify, use these rules in order:

1. **Simplest valid model first.** If a parametric model (OLS, logistic, Cox) fits the data adequately (assumptions pass), prefer it over ML or penalized alternatives. Simpler models are easier to audit and reproduce.
2. **Sample size guard.** Tree-based ML methods (RF, XGBoost) require N ≥ 200 in the training set and at least 10 events per predictor for reliable performance. Below these thresholds, fall back to penalized linear/logistic.
3. **Interpretability requirement.** If `research_questions.json → primary_question` uses language like "association between," "effect of," or "risk factor for," the primary model should produce a coefficient, OR, HR, or RR — not just an AUC. ML models may be added as sensitivity analyses.
4. **Reproducibility anchor.** When you choose a non-default method (anything other than OLS/logistic/Cox), document the specific justification in `rationale`. A future analyst should be able to re-derive your choice from the documented data properties alone.
5. **Flexibility override.** These rules establish a recommended default — they are not a hard constraint. If a method not listed in the candidates would produce materially better or more valid results given the specific data (e.g., a GAM for a non-linear dose-response, a quantile regression for a highly skewed outcome), you may use it. Document the override in `rationale` and add the default method as a sensitivity analysis.

---

**After resolving the method from `analysis_plan.json`, call the corresponding helper:**

| Method | Import + Call |
|--------|--------------|
| OLS / logit / Poisson / NegBin / ordinal / mixed / GEE | `from regression import fit_regression`<br>`results = fit_regression(df, outcome, exposure, covariates, method=..., cluster_col=..., weights_col=...)` |
| LASSO / Ridge / Elastic Net | `from penalized import fit_penalized`<br>`results = fit_penalized(df, outcome, predictors, method=..., task="auto")` |
| Random Forest / XGBoost / SVM / KNN | `from ml import fit_ml_model`<br>`results = fit_ml_model(df, outcome, predictors, method=..., task="auto")` |
| PSM | `from causal import propensity_score_match`<br>`results = propensity_score_match(df, treatment_col, covariates, outcome_col)` |
| IPW | `from causal import ipw_estimate`<br>`results = ipw_estimate(df, treatment_col, covariates, outcome_col)` |
| AIPW | `from causal import aipw_estimate`<br>`results = aipw_estimate(df, treatment_col, covariates, outcome_col)` |
| DiD | `from causal import did_regression`<br>`results = did_regression(df, outcome, treatment_col, time_col, covariates)` |
| ITS | `from causal import its_analysis`<br>`results = its_analysis(df, outcome, time_col, intervention_point)` |
| Cox / Fine-Gray | `from regression import fit_regression`<br>`results = fit_regression(df, outcome, exposure, covariates, method="cox"|"fine_gray", time_scale="time"|"age", weights_col=...)` |

Do NOT re-implement these from scratch — the helpers handle clustering, SE correction,
output formatting, and JSON-ready results.

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

Returns `{check_name: {"passed": bool, "details": str}}`. If a check fails, document it
and add a sensitivity analysis (Step 5). Save to `assumption_checks.json`.

Supported methods and their key checks:

| Track | Method | Key assumption checks |
|---|---|---|
| A | `"ols"` | Linearity, homoscedasticity, normality of residuals, no influential outliers |
| A | `"logit"` | No complete separation, linearity of log-odds for continuous predictors |
| A | `"poisson"` / `"negbin"` | Dispersion check, no excess zeros |
| A | `"mixed"` / `"gee"` | Residual correlation structure, convergence |
| B | penalized / ML | No structural assumption checks; run calibration + overfitting diagnostics instead |
| C | PSM / IPW / AIPW | Overlap/positivity check, covariate balance (SMD < 0.1 post-weighting), SUTVA plausibility |
| C | DiD | Pre-trend parallel test, no anticipation effects |
| C | ITS | Autocorrelation (Durbin-Watson), no concurrent interventions |
| D | `"cox"` | Schoenfeld residuals (PH test), no influential observations |
| D | `"cox"` | Schoenfeld residuals (PH test), concordance (C-index), no influential observations |
| D | `"fine_gray"` | Sufficient competing events (n ≥ 10 for each event type), concordance for event of interest |
| D | `"aft"` | Distribution fit (AIC comparison across Weibull/log-normal/log-logistic) |

For causal and survival tracks, run the track-specific checks documented in `references/methods.md` in addition to calling `check_assumptions()`.
---

### Step 5: Sensitivity Analyses

Run **at least two** of the following. Write each as a separate script in `scripts/sensitivity_*.py`. Choose sensitivities appropriate to the method track identified in Step 4.

**Universal (all tracks):**
1. **Alternative covariate set** — Add/remove covariates, different functional form.
2. **Subgroup analysis** — Stratify by `stratification_variables`.
3. **Robustness to missing data** — Compare complete-case vs. imputed results.
4. **Outlier sensitivity** — Refit excluding influential observations (Cook's distance > 4/N for regression; top-1% leverage for ML).

**Track A (Explanatory inference):**
5. **Alternative model specification** — E.g., add interaction terms, splines for continuous predictors.
6. **Penalized regression comparison** — If OLS/logistic was primary, run Elastic Net and compare coefficient direction and magnitude.

**Track B (Prediction):**
7. **Alternative ML model** — If primary was XGBoost, run Random Forest (or vice versa). Compare AUC/RMSE on the same test split.
8. **Bootstrap confidence intervals** — Non-parametric CI estimation for AUC/RMSE.
9. **Calibration check** — Calibration curve and Brier score for classifiers; residual plot for regressors.

**Track C (Causal inference):**
10. **E-value for unmeasured confounding** — Mandatory for all observational designs. Compute and report.
11. **Alternative propensity model** — If PSM/IPW was primary, re-estimate propensity scores using a different model (e.g., LASSO vs. logistic) and compare ATEs.
12. **Pre-trend test** — For DiD: formal test of parallel pre-treatment trends.
13. **Trimming sensitivity** — For IPW: compare results under different propensity score trimming thresholds (e.g., [0.05, 0.95] vs. [0.10, 0.90]).
14. **Doubly robust check** — If PSM or IPW was primary, run AIPW as a sensitivity.

**Track D (Survival):**
15. **Proportional hazards test** — Schoenfeld residuals. If PH violated, re-run with time-varying coefficient or parametric AFT.
16. **Competing risks sensitivity** — If competing risks are present but not modeled in primary, run Fine-Gray as sensitivity.
17. **Landmark analysis** — Re-run survival analysis starting from a landmark time to address immortal-time bias if applicable.

**Progress checkpoint:**
```python
update_step(output_folder, "statistical_analysis", "step_5_sensitivity", "completed")
```

---

### Step 6: Compile Results

Save all results to `<output_folder>/3_analysis/analysis_results.json` using `validation.compile_analysis_results()`. This function sanitizes p-values and validates the JSON schema before writing.

The output schema is documented in `references/methods.md` under "Output Contract."

**Progress checkpoint - Mark stage complete:**
```python
update_step(output_folder, "statistical_analysis", "step_6_compile", "completed")

# Mark stage complete with validation
complete_stage(output_folder, "statistical_analysis",
               expected_outputs=["3_analysis/analysis_results.json",
                                 "3_analysis/analytic_dataset.csv",
                                 "3_analysis/analysis_plan.json",
                                 "3_analysis/results_summary.md"])
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

## Figures Planned
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