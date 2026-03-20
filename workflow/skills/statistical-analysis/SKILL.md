---
name: statistical-analysis
description: >
  Run statistical analyses based on research_questions.json. Produces descriptive
  statistics (Table 1 data), primary regression analysis, and sensitivity analyses.
  Saves all scripts, model summaries, and analysis_results.json.
  Use after /acquire-data when research questions and data are ready.
  Triggers on: "run analysis", "statistical analysis", "fit model", "regression",
  "analyze the data", or any request to go from research questions to results.
argument-hint: <output_folder>
---

# Statistical Analysis

Run descriptive and inferential statistical analyses driven by `research_questions.json`, producing `analysis_results.json` and saved scripts for reproducibility.

## Usage

```
/statistical-analysis <output_folder>
```

Reads from `<output_folder>/1_data_profile/`, `<output_folder>/2_research_question/`, and original raw data (paths from `profile.json`). Writes to `<output_folder>/3_analysis/`.

## Instructions

You are a biostatistician conducting analyses for a JAMA Network Open paper. Every analysis must be reproducible, correctly specified, and honestly reported.

### Step 1: Load All Inputs

Read these files:

1. **`<output_folder>/2_research_question/research_questions.json`** — Primary question, variable roles, derived variables, study design.
2. **`<output_folder>/1_data_profile/profile.json`** — Dataset metadata and column statistics (includes original file paths).
3. **`<output_folder>/1_data_profile/variable_types.json`** — Semantic variable types.
4. **Raw data files** — read from original paths stored in `profile.json` file_path fields.
5. **Downloaded data** from `<output_folder>/2_research_question/downloaded/` (if any).

### Step 2: Prepare the Analytic Dataset

Write a Python script (`<output_folder>/3_analysis/scripts/prepare_data.py`) that:

1. **Loads all required datasets** using pandas.
2. **Merges/joins datasets** as needed based on `profile.json` → `data_context.dataset_relationships` and shared key columns.
3. **Creates derived variables** specified in `research_questions.json` → `variable_roles.derived_variables`. For each:
   - Follow the `derivation` field exactly.
   - Validate the derived variable has the expected distribution.
4. **Handles missing data**:
   - Document missingness rates for all analysis variables.
   - For variables with <5% missing: complete-case analysis is acceptable.
   - For variables with 5-20% missing: use multiple imputation or note as limitation.
   - For variables with >20% missing: exclude from primary analysis; include in sensitivity analysis if possible.
5. **Applies exclusion criteria** based on the research question's population definition.
6. **Saves the analytic dataset** to `<output_folder>/3_analysis/analytic_dataset.csv`.
7. **Prints a summary**: N observations, N excluded, missingness per variable.

### Step 3: Descriptive Statistics (Table 1 Data)

Write a script (`<output_folder>/3_analysis/scripts/descriptive_stats.py`) that produces baseline characteristics stratified by the exposure variable:

- **Continuous variables**: Report mean (SD) or median (IQR) depending on distribution. Use Shapiro-Wilk or visual inspection to assess normality.
- **Categorical variables**: Report N (%).
- **Comparison tests**:
  - Continuous normal → t-test or ANOVA
  - Continuous non-normal → Wilcoxon rank-sum or Kruskal-Wallis
  - Categorical → chi-square or Fisher's exact test
- **Standardized mean differences (SMD)** for key covariates if applicable.
- **Survey weights**: Apply if the data includes sampling weights.

Save output as structured JSON in `analysis_results.json` under the `descriptive_statistics` key.

### Step 4: Primary Analysis

Select the statistical method based on the outcome variable type and study design from `research_questions.json`:

| Outcome Type | Study Design | Method | Python Package |
|-------------|--------------|--------|----------------|
| Continuous | Cross-sectional | Linear regression (OLS) | `statsmodels.OLS` |
| Continuous | Longitudinal | Mixed-effects model | `statsmodels.MixedLM` |
| Binary | Cross-sectional | Logistic regression | `statsmodels.Logit` |
| Binary | Before-after | Difference-in-differences logit | `statsmodels.Logit` with interaction |
| Time-to-event | Cohort | Cox proportional hazards | `lifelines.CoxPHFitter` |
| Count | Cross-sectional | Poisson or negative binomial | `statsmodels.Poisson` / `NegativeBinomial` |

Write the primary analysis script (`<output_folder>/3_analysis/scripts/primary_analysis.py`):

1. **Specify the model** with outcome, exposure, and covariates from `variable_roles`.
2. **Fit the model** and extract:
   - Coefficient estimates (or odds ratios / hazard ratios as appropriate)
   - 95% confidence intervals
   - P-values (2-sided, α = 0.05)
   - Model fit statistics (R², AIC, BIC, C-statistic as relevant)
3. **Check assumptions**:
   - Linear regression: residual normality, homoscedasticity, multicollinearity (VIF)
   - Logistic regression: Hosmer-Lemeshow goodness-of-fit, ROC-AUC
   - Cox model: Schoenfeld residuals for proportional hazards
   - DiD: parallel trends test (if pre-period data available)
4. **Save model summary** to `<output_folder>/3_analysis/models/primary_model_summary.txt`.

### Step 5: Sensitivity Analyses

Run at least one sensitivity analysis. Common options:

1. **Alternative model specification** — Add/remove covariates, use different functional form.
2. **Subgroup analysis** — Stratify by `stratification_variables` from `research_questions.json`.
3. **Robustness check** — Different handling of missing data, outlier exclusion, alternative outcome definition.
4. **Quantitative bias analysis** — E-value for unmeasured confounding (for observational studies).

Write script(s) to `<output_folder>/3_analysis/scripts/sensitivity_*.py`.

### Step 6: Compile Results

Save all results to `<output_folder>/3_analysis/analysis_results.json`.

### Step 7: Validate

Before completing, verify:

- [ ] `analysis_results.json` exists and is valid JSON
- [ ] `descriptive_statistics` section has data for all exposure groups
- [ ] `primary_analysis` has coefficients, CIs, and p-values
- [ ] At least one sensitivity analysis is present
- [ ] All scripts in `scripts/` directory run without errors
- [ ] No p-values are exactly 0.000 (report as `<0.001` instead)
- [ ] Effect sizes are plausible (not astronomically large)

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
        "type": "continuous|categorical",
        "overall": {"mean": 45.2, "sd": 12.1},
        "by_group": {
          "group_1": {"mean": 44.8, "sd": 11.9},
          "group_2": {"mean": 45.5, "sd": 12.3}
        },
        "p_value": 0.032,
        "test_used": "t-test"
      }
    }
  },
  "primary_analysis": {
    "method": "Logistic regression",
    "outcome": "vaccination_status",
    "exposure": "mandate_status",
    "covariates": ["age", "sex", "race", "income"],
    "results": {
      "exposure_effect": {
        "estimate": 1.45,
        "ci_lower": 1.22,
        "ci_upper": 1.72,
        "p_value": 0.001,
        "interpretation": "OR = 1.45 (95% CI, 1.22-1.72)"
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
    }
  },
  "sensitivity_analyses": [
    {
      "name": "Subgroup analysis by age group",
      "description": "Stratified logistic regression by age category",
      "results": {}
    }
  ],
  "scripts_used": [
    "scripts/prepare_data.py",
    "scripts/descriptive_stats.py",
    "scripts/primary_analysis.py",
    "scripts/sensitivity_subgroup.py"
  ]
}
```

**`<output_folder>/3_analysis/analytic_dataset.csv`** — Merged, cleaned dataset used for analysis.

**`<output_folder>/3_analysis/scripts/`** — All Python scripts (must be independently runnable).

**`<output_folder>/3_analysis/models/`** — Saved model summaries as text files.
