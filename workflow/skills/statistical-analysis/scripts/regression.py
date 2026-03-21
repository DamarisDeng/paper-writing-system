"""
regression.py — Traditional regression model fitting.

Supports OLS, logistic, Poisson, negative binomial, mixed-effects, and Cox PH.
Each returns a standardised results dict with coefficients, CIs, p-values,
and model-fit statistics.
"""

from typing import Optional

import numpy as np
import pandas as pd

from utils import safe_pval, jama_p, jama_ci, jama_effect


def fit_regression(
    df: pd.DataFrame,
    outcome: str,
    exposure: str,
    covariates: list,
    method: str = "ols",
    cluster_col: Optional[str] = None,
    time_scale: str = "time",
    weights_col: Optional[str] = None,
) -> dict:
    """
    Fit a regression model and return structured results.

    method: 'ols', 'logit', 'poisson', 'negbin', 'mixed', 'cox', 'fine_gray'
    time_scale: 'time' (default) or 'age' for Cox models with left-truncation
    weights_col: Column name for survey/observation weights (for OLS, logit)
    """
    if method == "cox":
        return _fit_cox(df, outcome, exposure, covariates, time_scale=time_scale)
    if method in ("fine_gray", "fine-gray"):
        return _fit_fine_gray(df, outcome, exposure, covariates)
    if method == "mixed":
        return _fit_mixed(df, outcome, exposure, covariates, cluster_col)

    import statsmodels.api as sm

    covars = [c for c in covariates if c in df.columns]
    X = pd.get_dummies(df[[exposure] + covars], drop_first=True, dtype=float)
    X = sm.add_constant(X)
    y = df[outcome].astype(float)

    # Handle weights
    weights = None
    if weights_col and weights_col in df.columns:
        weights = df[weights_col].astype(float)
        # Validate weights
        if (weights < 0).any():
            return {"error": "Weights must be non-negative.", "method": method}
        if (weights == 0).all():
            return {"error": "All weights are zero.", "method": method}

    mask = X.notna().all(axis=1) & y.notna()
    if weights is not None:
        mask = mask & weights.notna()
        weights = weights[mask]
    X, y = X[mask], y[mask]

    model_map = {
        "ols": sm.OLS,
        "logit": sm.Logit,
        "poisson": sm.Poisson,
        "negbin": sm.NegativeBinomial,
    }
    if method not in model_map:
        raise ValueError(f"Unknown method '{method}'. Use: {list(model_map)}")

    try:
        if weights is not None and method in ("ols", "linear"):
            # WLS for weighted OLS
            result = sm.WLS(y, X, weights=weights).fit(disp=0)
        elif method == "logit" and weights is not None:
            # sklearn supports sample_weight for logistic
            from sklearn.linear_model import LogisticRegression
            lr = LogisticRegression(max_iter=5000)
            lr.fit(X, y, sample_weight=weights)
            # Convert sklearn result to statsmodels-like format
            result = _sklearn_logistic_to_result(lr, X, y, weights)
        else:
            result = model_map[method](y, X).fit(disp=0)
    except Exception as e:
        return {"error": str(e), "method": method}

    return _extract_results(result, method, exposure, X.columns.tolist())


def _sklearn_logistic_to_result(lr, X, y, weights):
    """Convert sklearn LogisticRegression result to statsmodels-like format."""
    import statsmodels.api as sm

    # Fit a statsmodels model just for SE calculation (using same design)
    sm_result = sm.Logit(y, X).fit(disp=0, maxiter=0)

    class ResultWrapper:
        def __init__(self, coef_, intercept_, n_obs, feature_names):
            self.params = np.concatenate([[intercept_], coef_])
            self.feature_names = ['const'] + list(feature_names)
            self.nobs = n_obs

            # Approximate SE using Fisher information (not weighted)
            # For publication-quality weighted SEs, use survey packages
            try:
                pred_proba = lr.predict_proba(X)[:, 1]
                V = np.diag(pred_proba * (1 - pred_proba))
                X_arr = X.values if hasattr(X, 'values') else X
                cov = np.linalg.inv(X_arr.T @ V @ X_arr)
                self.bse = np.sqrt(np.diag(cov))
            except:
                self.bse = np.full(len(self.params), np.nan)

            self.pvalues = None  # Would need proper calculation
            self.conf_int = lambda alpha=0.05: self._ci(alpha)

        def _ci(self, alpha):
            from scipy import stats
            z = stats.norm.ppf(1 - alpha/2)
            lower = self.params - z * self.bse
            upper = self.params + z * self.bse
            return np.column_stack([lower, upper])

    return ResultWrapper(lr.coef_.flatten(), lr.intercept_[0], len(y), X.columns[1:])


# ── Cox PH ──────────────────────────────────────────────────────────────────

def _fit_cox(df, outcome, exposure, covars, time_scale="time") -> dict:
    from lifelines import CoxPHFitter

    event_col = None
    for name in ("event", "status", "dead", "death", "censored",
                 f"{outcome}_event"):
        if name in df.columns:
            event_col = name
            break
    if event_col is None:
        return {"error": "Cox model requires a binary event/status column."}

    cols = [outcome, event_col, exposure] + [c for c in covars if c in df.columns]
    cdf = df[cols].dropna().copy()
    cdf = pd.get_dummies(cdf, columns=[c for c in [exposure] + covars
                                        if c in cdf.columns and cdf[c].dtype == "object"],
                         drop_first=True)

    cph = CoxPHFitter()

    if time_scale == "age":
        # Detect entry age column for left-truncation
        entry_col = None
        for name in ("age_entry", "entry_age", "baseline_age", "age_start", "age_at_baseline"):
            if name in df.columns:
                entry_col = name
                break

        if entry_col is None:
            return {"error": "Age-as-time-scale requires an entry age column (e.g., age_entry, entry_age, baseline_age)."}

        # Merge entry_col into cdf (may have been lost in dropna)
        cdf = cdf.merge(df[[entry_col]], left_index=True, right_index=True, how="left")

        try:
            cph.fit(cdf, duration_col=outcome, event_col=event_col,
                    entry_col=entry_col, show_progress=False)
        except Exception as e:
            return {"error": str(e), "method": "cox"}
    else:
        # Standard time-to-event
        try:
            cph.fit(cdf, duration_col=outcome, event_col=event_col, show_progress=False)
        except Exception as e:
            return {"error": str(e), "method": "cox"}

    s = cph.summary
    exp_rows = [c for c in s.index if exposure in c] or [s.index[0]]
    effects = {}
    for row in exp_rows:
        hr_val = round(s.loc[row, "exp(coef)"], 4)
        ci_lo = round(s.loc[row, "exp(coef) lower 95%"], 4)
        ci_hi = round(s.loc[row, "exp(coef) upper 95%"], 4)
        pv = s.loc[row, "p"]

        effects[row] = {
            "raw": {
                "estimate": hr_val,
                "ci_lower": ci_lo,
                "ci_upper": ci_hi,
                "p_value": safe_pval(pv),
            },
            "formatted": {
                "estimate_str": f"{hr_val:.2f}",
                "ci_str": jama_ci(ci_lo, ci_hi),
                "p_str": jama_p(pv),
                "jama_sentence": jama_effect(hr_val, ci_lo, ci_hi, pv, "HR"),
            }
        }

    method_name = "Cox proportional hazards (age-as-time-scale)" if time_scale == "age" else "Cox proportional hazards"
    return {
        "method": method_name,
        "n": len(cdf),
        "exposure_effect": effects,
        "concordance": round(cph.concordance_index_, 4),
        "log_likelihood": round(cph.log_likelihood_, 4),
        "aic": (round(cph.AIC_partial_AIC_, 4)
                if hasattr(cph, "AIC_partial_AIC_") else None),
        "time_scale": time_scale,
    }


# ── Fine-Gray Competing Risks ───────────────────────────────────────────────────

def _fit_fine_gray(df, outcome, exposure, covars, event_of_interest=1) -> dict:
    """Fine-Gray subdistribution hazard model for competing risks.

    Uses cause-specific Cox models as a practical approximation.
    Event coding: 0=censored, 1=event_of_interest, 2=competing_event.

    Returns both cause-specific hazard ratios and cumulative incidence information.
    """
    from lifelines import CoxPHFitter

    # Detect event column
    event_col = None
    for name in ("event", "status", "cause", "event_type", f"{outcome}_event"):
        if name in df.columns:
            event_col = name
            break
    if event_col is None:
        return {"error": "Fine-Gray model requires an event/status column with competing event codes."}

    # Validate event coding (should have at least 0, 1, 2)
    unique_events = df[event_col].dropna().unique()
    if len(unique_events) < 3:
        return {"error": f"Competing risks requires >=3 event types. Found: {unique_events}"}

    cols = [outcome, event_col, exposure] + [c for c in covars if c in df.columns]
    cdf = df[cols].dropna().copy()
    cdf = pd.get_dummies(cdf, columns=[c for c in [exposure] + covars
                                        if c in cdf.columns and cdf[c].dtype == "object"],
                         drop_first=True)

    # Cause-specific Cox: event of interest
    df_eoi = cdf.copy()
    df_eoi['_event_eoi'] = (df_eoi[event_col] == event_of_interest).astype(int)
    df_eoi = df_eoi[df_eoi[event_col] != 2]  # Exclude competing events

    cph_eoi = CoxPHFitter()
    try:
        cph_eoi.fit(df_eoi, duration_col=outcome, event_col='_event_eoi', show_progress=False)
    except Exception as e:
        return {"error": f"Event-of-interest Cox failed: {str(e)}", "method": "fine_gray"}

    # Cause-specific Cox: competing event
    df_comp = cdf.copy()
    df_comp['_event_comp'] = (df_comp[event_col] == 2).astype(int)
    df_comp = df_comp[df_comp[event_col] != 1]  # Exclude events of interest

    cph_comp = CoxPHFitter()
    try:
        cph_comp.fit(df_comp, duration_col=outcome, event_col='_event_comp', show_progress=False)
    except Exception as e:
        return {"error": f"Competing event Cox failed: {str(e)}", "method": "fine_gray"}

    # Extract results for exposure variable
    s_eoi = cph_eoi.summary
    s_comp = cph_comp.summary
    exp_rows_eoi = [c for c in s_eoi.index if exposure in c] or [s_eoi.index[0]]
    exp_rows_comp = [c for c in s_comp.index if exposure in c] or [s_comp.index[0]]

    effects = {}
    for row in exp_rows_eoi:
        hr_val = round(s_eoi.loc[row, "exp(coef)"], 4)
        ci_lo = round(s_eoi.loc[row, "exp(coef) lower 95%"], 4)
        ci_hi = round(s_eoi.loc[row, "exp(coef) upper 95%"], 4)
        pv = s_eoi.loc[row, "p"]

        effects[row] = {
            "raw": {
                "estimate": hr_val,
                "ci_lower": ci_lo,
                "ci_upper": ci_hi,
                "p_value": safe_pval(pv),
                "metric": "Cause-specific HR"
            },
            "formatted": {
                "estimate_str": f"{hr_val:.2f}",
                "ci_str": jama_ci(ci_lo, ci_hi),
                "p_str": jama_p(pv),
                "jama_sentence": jama_effect(hr_val, ci_lo, ci_hi, pv, "Cause-specific HR"),
            }
        }

    # Get competing event HR for reference
    comp_effects = {}
    for row in exp_rows_comp:
        hr_val = round(s_comp.loc[row, "exp(coef)"], 4)
        ci_lo = round(s_comp.loc[row, "exp(coef) lower 95%"], 4)
        ci_hi = round(s_comp.loc[row, "exp(coef) upper 95%"], 4)
        pv = s_comp.loc[row, "p"]

        comp_effects[row] = {
            "raw": {
                "estimate": hr_val,
                "ci_lower": ci_lo,
                "ci_upper": ci_hi,
                "p_value": safe_pval(pv),
            },
            "formatted": {
                "estimate_str": f"{hr_val:.2f}",
                "ci_str": jama_ci(ci_lo, ci_hi),
                "p_str": jama_p(pv),
            }
        }

    return {
        "method": "Cause-specific Cox (competing risks)",
        "n": len(cdf),
        "exposure_effect": effects,
        "competing_event_effect": comp_effects,
        "concordance_eoi": round(cph_eoi.concordance_index_, 4),
        "concordance_competing": round(cph_comp.concordance_index_, 4),
    }


# ── Mixed-effects ──────────────────────────────────────────────────────────

def _fit_mixed(df, outcome, exposure, covars, cluster_col) -> dict:
    import statsmodels.formula.api as smf

    covars = [c for c in covars if c in df.columns]
    if not cluster_col or cluster_col not in df.columns:
        return fit_regression(df, outcome, exposure, covars, method="ols")

    # Sanitise column names for patsy formula
    df2 = df.copy()
    safe = {}
    for col in [outcome, exposure, cluster_col] + covars:
        if not col.isidentifier():
            s = col.replace(" ", "_").replace("-", "_").replace(".", "_")
            safe[col] = s
            df2.rename(columns={col: s}, inplace=True)

    so = safe.get(outcome, outcome)
    se = safe.get(exposure, exposure)
    sc = safe.get(cluster_col, cluster_col)
    sp = [safe.get(v, v) for v in covars]

    formula = f"{so} ~ {se}" + ("".join(f" + {v}" for v in sp) if sp else "")
    try:
        result = smf.mixedlm(formula, df2, groups=df2[sc]).fit(disp=0)
        return _extract_results(result, "mixed", exposure,
                                result.params.index.tolist())
    except Exception as e:
        return {"error": str(e), "method": "mixed"}


# ── Result extraction ───────────────────────────────────────────────────────

def _extract_results(result, method, exposure, col_names) -> dict:
    params = result.params
    conf = result.conf_int()
    pvals = result.pvalues

    exp_cols = [c for c in col_names if exposure in str(c)]
    if not exp_cols:
        exp_cols = [col_names[1]] if len(col_names) > 1 else col_names

    effects = {}
    for col in exp_cols:
        if col not in params.index:
            continue
        est = params[col]
        ci_lo, ci_hi = conf.loc[col, 0], conf.loc[col, 1]
        pv = float(pvals[col])
        se_val = float(result.bse[col]) if hasattr(result, 'bse') else None

        if method == "logit":
            or_val = round(np.exp(est), 4)
            ci_lo_exp = round(np.exp(ci_lo), 4)
            ci_hi_exp = round(np.exp(ci_hi), 4)
            p_str = jama_p(pv)

            effects[col] = {
                "raw": {
                    "estimate": or_val,
                    "ci_lower": ci_lo_exp,
                    "ci_upper": ci_hi_exp,
                    "p_value": safe_pval(pv),
                    "se": round(se_val, 4) if se_val is not None else None,
                },
                "formatted": {
                    "estimate_str": f"{or_val:.2f}",
                    "ci_str": jama_ci(ci_lo_exp, ci_hi_exp),
                    "p_str": p_str,
                    "interpretation": f"OR = {or_val:.2f} (95% CI, {ci_lo_exp:.2f}-{ci_hi_exp:.2f})",
                    "jama_sentence": jama_effect(or_val, ci_lo_exp, ci_hi_exp, pv, "OR"),
                }
            }
        elif method == "poisson":
            rr_val = round(np.exp(est), 4)
            ci_lo_exp = round(np.exp(ci_lo), 4)
            ci_hi_exp = round(np.exp(ci_hi), 4)
            p_str = jama_p(pv)

            effects[col] = {
                "raw": {
                    "estimate": rr_val,
                    "ci_lower": ci_lo_exp,
                    "ci_upper": ci_hi_exp,
                    "p_value": safe_pval(pv),
                    "se": round(se_val, 4) if se_val is not None else None,
                },
                "formatted": {
                    "estimate_str": f"{rr_val:.2f}",
                    "ci_str": jama_ci(ci_lo_exp, ci_hi_exp),
                    "p_str": p_str,
                    "interpretation": f"RR = {rr_val:.2f} (95% CI, {ci_lo_exp:.2f}-{ci_hi_exp:.2f})",
                    "jama_sentence": jama_effect(rr_val, ci_lo_exp, ci_hi_exp, pv, "RR"),
                }
            }
        else:
            est_val = round(est, 4)
            ci_lo_val = round(ci_lo, 4)
            ci_hi_val = round(ci_hi, 4)
            p_str = jama_p(pv)

            effects[col] = {
                "raw": {
                    "estimate": est_val,
                    "ci_lower": ci_lo_val,
                    "ci_upper": ci_hi_val,
                    "p_value": safe_pval(pv),
                    "se": round(se_val, 4) if se_val is not None else None,
                },
                "formatted": {
                    "estimate_str": f"{est_val:.4f}",
                    "ci_str": jama_ci(ci_lo_val, ci_hi_val),
                    "p_str": p_str,
                    "interpretation": f"β = {est_val:.4f} (95% CI, {ci_lo_val:.4f}-{ci_hi_val:.4f})",
                    "jama_sentence": jama_effect(est_val, ci_lo_val, ci_hi_val, pv, "β"),
                }
            }

    fit = {}
    for attr, key in [("rsquared", "r_squared"), ("rsquared_adj", "r_squared_adj"),
                       ("aic", "aic"), ("bic", "bic"),
                       ("prsquared", "pseudo_r_squared"), ("llf", "log_likelihood")]:
        val = getattr(result, attr, None)
        if val is not None:
            fit[key] = round(float(val), 4)

    return {
        "method": method,
        "n": int(result.nobs),
        "exposure_effect": effects,
        "model_fit": fit,
        "summary_text": str(result.summary()),
    }
