"""
validation.py — Model assumption checks and result validation.

Provides assumption checks for linear, logistic, and Cox models,
plus schema validation for analysis_results.json and final compilation.
"""

import json
import os
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from utils import safe_pval, sanitize_pvalues, save_json


# ============================================================================
# ASSUMPTION CHECKS
# ============================================================================

def check_assumptions(
    model_result,
    method: str,
    df: Optional[pd.DataFrame] = None,
    outcome: Optional[str] = None,
    predictors: Optional[list] = None,
) -> dict:
    """
    Run appropriate assumption checks for the given model type.

    Returns {check_name: {passed: bool, details: str}}.
    """
    if method in ("ols", "linear"):
        return _linear_checks(model_result, df, predictors)
    if method == "logit":
        return _logistic_checks(model_result)
    if method == "cox":
        return _cox_checks(model_result, df, outcome, predictors)
    if method in ("fine_gray", "fine-gray"):
        return _fine_gray_checks(model_result, df, outcome)
    return {}


def _linear_checks(result, df, predictors) -> dict:
    checks = {}

    # Residual normality
    try:
        resid = result.resid
        _, p = stats.shapiro(resid[:5000])
        checks["residual_normality"] = {
            "passed": p > 0.05,
            "details": f"Shapiro-Wilk p={safe_pval(p)}",
        }
    except Exception as e:
        checks["residual_normality"] = {"passed": None, "details": str(e)}

    # VIF
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        import statsmodels.api as sm

        if df is not None and predictors:
            cols = [p for p in predictors if p in df.columns]
            X = pd.get_dummies(df[cols], drop_first=True, dtype=float)
            X = sm.add_constant(X).dropna()
            vifs = {}
            for i, col in enumerate(X.columns):
                if col == "const":
                    continue
                vifs[col] = round(variance_inflation_factor(X.values, i), 2)
            mx = max(vifs.values()) if vifs else 0
            checks["multicollinearity_vif"] = {
                "passed": mx < 10,
                "details": f"Max VIF = {mx:.2f}" + (
                    f" (high: {[k for k, v in vifs.items() if v > 10]})"
                    if mx >= 10 else ""),
            }
    except Exception as e:
        checks["multicollinearity_vif"] = {"passed": None, "details": str(e)}

    # Breusch-Pagan
    try:
        from statsmodels.stats.diagnostic import het_breuschpagan
        _, bp_p, _, _ = het_breuschpagan(result.resid, result.model.exog)
        checks["homoscedasticity"] = {
            "passed": bp_p > 0.05,
            "details": f"Breusch-Pagan p={safe_pval(bp_p)}",
        }
    except Exception as e:
        checks["homoscedasticity"] = {"passed": None, "details": str(e)}

    return checks


def _logistic_checks(result) -> dict:
    checks = {}

    # AUC
    try:
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(result.model.endog, result.predict())
        checks["discrimination_auc"] = {
            "passed": auc > 0.5,
            "details": f"C-statistic (AUC) = {auc:.4f}",
        }
    except Exception as e:
        checks["discrimination_auc"] = {"passed": None, "details": str(e)}

    # Hosmer-Lemeshow (simplified)
    try:
        y_true = result.model.endog
        y_prob = result.predict()
        groups = np.array_split(np.argsort(y_prob), 10)
        hl = 0
        for g in groups:
            obs, exp, n_g = y_true[g].sum(), y_prob[g].sum(), len(g)
            if exp > 0 and (n_g - exp) > 0:
                hl += ((obs - exp) ** 2 / exp
                       + ((n_g - obs) - (n_g - exp)) ** 2 / (n_g - exp))
        p = 1 - stats.chi2.cdf(hl, 8)
        checks["hosmer_lemeshow"] = {
            "passed": p > 0.05,
            "details": f"H-L stat={hl:.2f}, p={safe_pval(p)}",
        }
    except Exception as e:
        checks["hosmer_lemeshow"] = {"passed": None, "details": str(e)}

    return checks


def _cox_checks(result, df, outcome, predictors) -> dict:
    """Proportional hazards assumption checks for Cox models."""
    checks = {}

    # Basic checks from result dict
    if "concordance" in result:
        conc = result["concordance"]
        checks["discrimination_concordance"] = {
            "passed": conc > 0.5,
            "details": f"C-index = {conc:.4f}"
        }

    # Note: Full Schoenfeld test requires refitting the model
    # Document that user should run manually if needed
    checks["proportional_hazards"] = {
        "passed": None,
        "details": "Schoenfeld test requires running cph.check_assumptions() manually "
                   "on the fitted CoxPHFitter object with original data."
    }

    return checks


def _fine_gray_checks(result, df, outcome, event_col=None) -> dict:
    """Assumption checks for competing risks models."""
    checks = {}

    # Detect event column if not provided
    if event_col is None:
        for name in ("event", "status", "cause", "event_type", f"{outcome}_event"):
            if name in df.columns:
                event_col = name
                break

    # Check sufficient number of competing events
    if event_col and event_col in df.columns:
        n_competing = (df[event_col] == 2).sum()
        n_eoi = (df[event_col] == 1).sum()
        n_censored = (df[event_col] == 0).sum()

        checks["sufficient_events"] = {
            "passed": n_competing >= 10 and n_eoi >= 10,
            "details": f"n_comp={n_competing}, n_eoi={n_eoi}, n_censored={n_censored}"
        }

    return checks


# ============================================================================
# RESULT VALIDATION
# ============================================================================

def validate_analysis(results: dict) -> list:
    """Validate analysis_results.json. Returns a list of error strings."""
    errors = []

    if "analytic_sample" not in results:
        errors.append("Missing 'analytic_sample' section")
    elif results["analytic_sample"].get("total_n", 0) == 0:
        errors.append("analytic_sample.total_n is 0")

    if "descriptive_statistics" not in results:
        errors.append("Missing 'descriptive_statistics' section")

    if "primary_analysis" not in results:
        errors.append("Missing 'primary_analysis' section")
    else:
        pa = results["primary_analysis"]
        if "error" in pa:
            errors.append(f"Primary analysis error: {pa['error']}")
        if "exposure_effect" in pa:
            for key, val in pa["exposure_effect"].items():
                if isinstance(val, dict):
                    for m in ("odds_ratio", "hazard_ratio", "rate_ratio"):
                        v = val.get(m)
                        if v is not None and (v > 100 or v < 0.01):
                            errors.append(f"Implausible {m}={v} for {key}")

    if not results.get("sensitivity_analyses"):
        errors.append("No sensitivity analyses present")

    return errors


# ============================================================================
# COMPILATION
# ============================================================================

def compile_analysis_results(
    analytic_sample: dict,
    descriptive_stats: dict,
    primary_analysis: dict,
    sensitivity_analyses: list,
    scripts_used: list,
    output_path: str,
) -> dict:
    """Compile, sanitize p-values, validate, and save analysis_results.json."""
    results = {
        "analytic_sample": analytic_sample,
        "descriptive_statistics": descriptive_stats,
        "primary_analysis": primary_analysis,
        "sensitivity_analyses": sensitivity_analyses,
        "scripts_used": scripts_used,
    }
    results = sanitize_pvalues(results)

    errors = validate_analysis(results)
    if errors:
        print("  Validation warnings:")
        for e in errors:
            print(f"    - {e}")

    save_json(results, output_path)
    return results
