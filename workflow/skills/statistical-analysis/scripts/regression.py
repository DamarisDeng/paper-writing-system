"""
regression.py — Traditional regression model fitting.

Supports OLS, logistic, Poisson, negative binomial, mixed-effects, and Cox PH.
Each returns a standardised results dict with coefficients, CIs, p-values,
and model-fit statistics.
"""

from typing import Optional

import numpy as np
import pandas as pd

from utils import safe_pval


def fit_regression(
    df: pd.DataFrame,
    outcome: str,
    exposure: str,
    covariates: list,
    method: str = "ols",
    cluster_col: Optional[str] = None,
) -> dict:
    """
    Fit a regression model and return structured results.

    method: 'ols', 'logit', 'poisson', 'negbin', 'mixed', 'cox'
    """
    if method == "cox":
        return _fit_cox(df, outcome, exposure, covariates)
    if method == "mixed":
        return _fit_mixed(df, outcome, exposure, covariates, cluster_col)

    import statsmodels.api as sm

    covars = [c for c in covariates if c in df.columns]
    X = pd.get_dummies(df[[exposure] + covars], drop_first=True, dtype=float)
    X = sm.add_constant(X)
    y = df[outcome].astype(float)

    mask = X.notna().all(axis=1) & y.notna()
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
        result = model_map[method](y, X).fit(disp=0)
    except Exception as e:
        return {"error": str(e), "method": method}

    return _extract_results(result, method, exposure, X.columns.tolist())


# ── Cox PH ──────────────────────────────────────────────────────────────────

def _fit_cox(df, outcome, exposure, covars) -> dict:
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
    try:
        cph.fit(cdf, duration_col=outcome, event_col=event_col)
    except Exception as e:
        return {"error": str(e), "method": "cox"}

    s = cph.summary
    exp_rows = [c for c in s.index if exposure in c] or [s.index[0]]
    effects = {}
    for row in exp_rows:
        effects[row] = {
            "hazard_ratio": round(s.loc[row, "exp(coef)"], 4),
            "ci_lower": round(s.loc[row, "exp(coef) lower 95%"], 4),
            "ci_upper": round(s.loc[row, "exp(coef) upper 95%"], 4),
            "p_value": safe_pval(s.loc[row, "p"]),
        }

    return {
        "method": "Cox proportional hazards",
        "n": len(cdf),
        "exposure_effect": effects,
        "concordance": round(cph.concordance_index_, 4),
        "log_likelihood": round(cph.log_likelihood_, 4),
        "aic": (round(cph.AIC_partial_AIC_, 4)
                if hasattr(cph, "AIC_partial_AIC_") else None),
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
        pv = pvals[col]

        if method == "logit":
            effects[col] = {
                "odds_ratio": round(np.exp(est), 4),
                "ci_lower": round(np.exp(ci_lo), 4),
                "ci_upper": round(np.exp(ci_hi), 4),
                "p_value": safe_pval(pv),
                "interpretation": (f"OR = {np.exp(est):.2f} "
                                   f"(95% CI, {np.exp(ci_lo):.2f}-{np.exp(ci_hi):.2f})"),
            }
        elif method == "poisson":
            effects[col] = {
                "rate_ratio": round(np.exp(est), 4),
                "ci_lower": round(np.exp(ci_lo), 4),
                "ci_upper": round(np.exp(ci_hi), 4),
                "p_value": safe_pval(pv),
                "interpretation": (f"RR = {np.exp(est):.2f} "
                                   f"(95% CI, {np.exp(ci_lo):.2f}-{np.exp(ci_hi):.2f})"),
            }
        else:
            effects[col] = {
                "estimate": round(est, 4),
                "ci_lower": round(ci_lo, 4),
                "ci_upper": round(ci_hi, 4),
                "p_value": safe_pval(pv),
                "interpretation": f"β = {est:.4f} (95% CI, {ci_lo:.4f}-{ci_hi:.4f})",
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
