# Methods Reference — Statistical Analysis Skill

Quick-reference for implementation details, known pitfalls, and decision guidance for each analysis method category. Read the section relevant to your chosen method before writing the primary analysis script.

---

## Table of Contents
1. Traditional Regression
2. Penalized Regression (LASSO / Ridge / Elastic Net)
3. Machine Learning Prediction
4. Causal Inference
5. Survival Analysis
6. Common Pitfalls (All Methods)
7. Output Contract Schema

---

## 1. Traditional Regression

### OLS (Linear Regression)
- Always check VIF for multicollinearity before interpreting coefficients. VIF > 10 means a problem.
- Use heteroscedasticity-robust standard errors (`model.fit(cov_type='HC3')`) when Breusch-Pagan rejects.
- For log-transformed outcomes, report exponentiated coefficients as percent changes.
- Watch for influential observations: Cook's distance > 4/N warrants investigation.

### Logistic Regression
- Report odds ratios, not raw coefficients. Use `np.exp(params)`.
- Hosmer-Lemeshow test: p > 0.05 means adequate fit. But it's sensitive to large N — prefer calibration plots.
- Check for separation: if a predictor perfectly predicts the outcome, the model won't converge. Use Firth's penalized logistic regression as fallback.
- C-statistic (AUC) > 0.7 is acceptable, > 0.8 is good discrimination.

### Poisson / Negative Binomial
- If the variance is much larger than the mean (overdispersion), use negative binomial instead of Poisson.
- Test: fit Poisson, then check `results.pearson_chi2 / results.df_resid`. If >> 1, switch to NegBin.
- For rate outcomes, include log(population) as an offset: `sm.Poisson(y, X, offset=np.log(pop))`.

### Mixed-Effects Models
- Use when data has clustering (patients within hospitals, repeated measures).
- Always specify the grouping variable in `groups=`.
- Start with random intercepts only. Add random slopes if justified and the model converges.
- Convergence failures: try `method='nm'` or `method='powell'` instead of default.

### Ordinal Logistic Regression
- Use `statsmodels.miscmodels.ordinal_model.OrderedModel` with `distr='logit'`.
- Check proportional odds assumption: the effect should be consistent across cut-points.

---

## 2. Penalized Regression

### When to Use
- More predictors than you'd like in a standard regression (p/N > 0.1).
- You suspect many covariates are noise and want automatic selection (LASSO).
- Predictors are highly correlated (Ridge or Elastic Net).

### LASSO (L1)
- Performs variable selection by shrinking some coefficients to exactly zero.
- Use `LassoCV` or `LogisticRegressionCV(penalty='l1')` for automatic alpha tuning.
- **Pitfall**: LASSO is unstable with correlated features — it picks one arbitrarily. Use Elastic Net instead.
- Report: selected features, alpha, cross-validated R² or AUC.

### Ridge (L2)
- Shrinks coefficients but never to zero — no variable selection.
- Better than LASSO when all features matter but magnitudes need controlling.
- Use `RidgeCV` for alpha tuning.

### Elastic Net
- Combines L1 and L2 penalties. Best default choice for penalized regression.
- `l1_ratio` controls the mix: 1.0 = pure LASSO, 0.0 = pure Ridge.
- Use `ElasticNetCV(l1_ratio=[0.1, 0.5, 0.7, 0.9, 0.95])`.

### Important Notes
- **Always standardize features** before fitting penalized models (use `StandardScaler`).
- The regularized coefficients are biased — don't interpret them as causal effects.
- For inference (CIs, p-values), refit an unpenalized model with only the LASSO-selected features.

---

## 3. Machine Learning Prediction

### When to Use
- The research question asks "Can we predict X from Y?" not "Does X cause Y?"
- Non-linear relationships are expected.
- The goal is risk stratification, biomarker discovery, or clinical prediction rules.

### Random Forest
- Good default. Handles non-linearity, interactions, missing values (with imputation).
- Feature importance: use `model.feature_importances_` (mean decrease in impurity) or permutation importance.
- **Pitfall**: Overfits to high-cardinality categorical features. Limit `max_depth`.

### XGBoost
- Usually best predictive performance on tabular data.
- Key hyperparameters: `max_depth` (3-10), `learning_rate` (0.01-0.3), `n_estimators` (100-1000).
- Use early stopping on a validation set to prevent overfitting.
- **Pitfall**: Very easy to overfit if not using cross-validation for tuning.

### SVM
- Works best in high-dimensional, moderate-N settings.
- **Must standardize features.**
- RBF kernel handles non-linearity; linear kernel for interpretability.
- Slow with N > 10000.

### Reporting Requirements for ML
1. **Train/test split or cross-validation** — never report training performance only.
2. **Performance gap** — if test AUC is >15% below train AUC, the model is overfitting.
3. **Feature importance** — SHAP values are preferred; tree-based importances are acceptable.
4. **Calibration** — for classifiers, report calibration (Brier score or calibration plot).
5. **Comparison baseline** — always compare against a simple model (logistic regression).

---

## 4. Causal Inference

Import:
```python
from causal import propensity_score_match, ipw_estimate, did_regression, its_analysis, compute_evalue
```

### Propensity Score Matching (PSM)
- Use `causal.propensity_score_match()`.
- Check covariate balance after matching: SMD < 0.1 for all covariates.
- Default caliper: 0.2 × SD of the logit propensity score.
- Report: N matched pairs, balance diagnostics, ATT.
- **Pitfall**: Matching discards unmatched units — report how many were lost.

### Inverse Probability Weighting (IPW)
- Use `causal.ipw_estimate()`.
- Advantages over PSM: retains full sample, can estimate ATE (not just ATT).
- **Pitfall**: Extreme weights (from PS near 0 or 1) inflate variance. Clip PS to [0.01, 0.99] or use stabilized weights.
- Always check weight distribution: if max weight > 20, results may be unreliable.

### Difference-in-Differences (DiD)
- Use `causal.did_regression()`.
- Requires: treatment group, control group, pre-period, post-period.
- **Critical assumption**: parallel trends — treatment and control groups would have had the same trend absent the intervention.
- Test parallel trends if you have multiple pre-periods.
- The DiD estimate is the coefficient on the treatment × post interaction.

### Interrupted Time Series (ITS)
- Use `causal.its_analysis()`.
- Good for single-group policy evaluations with time-series data.
- Reports both level change (immediate) and slope change (gradual).
- Needs ≥8 time points pre- and post-intervention for reliable estimates.
- Use Newey-West or HC3 standard errors for autocorrelation.

### E-Value
- Use `causal.compute_evalue()` for observational studies.
- Reports the minimum strength of association an unmeasured confounder would need to explain away the result.
- E-value > 2 is moderately robust to confounding.

---

## 5. Survival Analysis

### Cox Proportional Hazards
- Requires: time variable, event indicator (binary), predictors.
- Use `lifelines.CoxPHFitter`.
- Check proportional hazards assumption: `cph.check_assumptions(df)` runs Schoenfeld residual tests.
- If PH violated: stratify by the offending variable, or use time-varying coefficients.
- Report hazard ratios with 95% CI, concordance index.

### Kaplan-Meier
- Non-parametric survival curves. Good for visualization and log-rank tests.
- `lifelines.KaplanMeierFitter` for curves, `lifelines.statistics.logrank_test` for comparison.

---

## 6. Common Pitfalls (All Methods)

| Pitfall | Fix |
|---|---|
| p-value = 0.000 | Report as "< 0.001" |
| OR = 999 or Inf | Model didn't converge — check for separation |
| Negative R² | Model is worse than intercept-only — specification is wrong |
| VIF > 100 | Perfect collinearity — drop one of the collinear variables |
| Model won't converge | Reduce predictors, increase `max_iter`, try different optimizer |
| Wildly different train vs test performance | Overfitting — reduce complexity, add regularization |
| Zero variance in a predictor group | Drop the variable or recode |
| Memory error with large datasets | Sample down for tuning, use full data for final fit |

---

## 7. Output Contract Schema

The full JSON schema for `analysis_results.json` is defined in the SKILL.md. Key additions for different method types:

### For penalized regression, add under `primary_analysis`:
```json
"regularization": {
  "method": "lasso",
  "alpha": 0.042,
  "n_features_selected": 8,
  "selected_features": {"feature1": 0.45, "feature2": -0.23}
}
```

### For ML models, add `ml_performance` (replaces `model_fit`):
```json
"ml_performance": {
  "train": {"auc_roc": 0.89, "accuracy": 0.82},
  "test": {"auc_roc": 0.85, "accuracy": 0.79},
  "cv_mean_auc": 0.86,
  "cv_std_auc": 0.03,
  "feature_importance": [{"feature": "age", "importance": 0.25}],
  "hyperparameters": {"max_depth": 6, "n_estimators": 200},
  "calibration_brier_score": 0.15
}
```

### For causal inference, add `causal_estimate`:
```json
"causal_estimate": {
  "method": "Propensity score matching",
  "estimand": "ATT",
  "estimate": 3.2,
  "ci_lower": 1.1,
  "ci_upper": 5.3,
  "p_value": 0.003,
  "balance_achieved": true,
  "max_smd_after_matching": 0.08,
  "e_value": 2.4
}
```
