"""
causal.py — Causal inference methods.

Propensity score matching, inverse probability weighting,
difference-in-differences, interrupted time series, and E-value.
"""

from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from utils import safe_pval


# ── Propensity Score Matching ───────────────────────────────────────────────

def propensity_score_match(
    df: pd.DataFrame,
    treatment_col: str,
    covariates: list,
    outcome_col: str,
    caliper: float = 0.2,
) -> dict:
    """1:1 nearest-neighbour propensity score matching. Returns ATT."""
    cols = [c for c in covariates if c in df.columns]
    X = pd.get_dummies(df[cols], drop_first=True, dtype=float)
    t = df[treatment_col].astype(float)
    y = df[outcome_col].astype(float)
    mask = X.notna().all(axis=1) & t.notna() & y.notna()
    X, t, y = X[mask], t[mask].values, y[mask].values

    scaler = StandardScaler()
    ps_model = LogisticRegression(max_iter=5000, random_state=42)
    ps_model.fit(scaler.fit_transform(X), t)
    ps = ps_model.predict_proba(scaler.transform(X))[:, 1]

    treated = np.where(t == 1)[0]
    control = np.where(t == 0)[0]
    caliper_abs = caliper * ps.std()

    pairs, used = [], set()
    for ti in treated:
        dists = np.abs(ps[control] - ps[ti])
        for ci_pos in np.argsort(dists):
            ci = control[ci_pos]
            if ci not in used and dists[ci_pos] < caliper_abs:
                pairs.append((ti, ci))
                used.add(ci)
                break

    if not pairs:
        return {"error": "No matches within caliper. Try increasing caliper."}

    t_out = np.array([y[p[0]] for p in pairs])
    c_out = np.array([y[p[1]] for p in pairs])
    att = float(t_out.mean() - c_out.mean())
    se = float(np.sqrt(t_out.var() / len(pairs) + c_out.var() / len(pairs)))

    return {
        "method": "Propensity score matching (1:1 nearest-neighbour)",
        "n_treated": int(len(treated)),
        "n_control": int(len(control)),
        "n_matched_pairs": len(pairs),
        "caliper": caliper,
        "att": round(att, 4),
        "att_se": round(se, 4),
        "att_ci_lower": round(att - 1.96 * se, 4),
        "att_ci_upper": round(att + 1.96 * se, 4),
        "p_value": safe_pval(2 * (1 - stats.norm.cdf(abs(att / se)))) if se > 0 else None,
    }


# ── Inverse Probability Weighting ──────────────────────────────────────────

def ipw_estimate(
    df: pd.DataFrame,
    treatment_col: str,
    covariates: list,
    outcome_col: str,
) -> dict:
    """Horvitz-Thompson IPW estimate of ATE with bootstrap SE."""
    cols = [c for c in covariates if c in df.columns]
    X = pd.get_dummies(df[cols], drop_first=True, dtype=float)
    t = df[treatment_col].astype(float)
    y = df[outcome_col].astype(float)
    mask = X.notna().all(axis=1) & t.notna() & y.notna()
    X, t, y = X[mask].values, t[mask].values, y[mask].values

    ps_model = LogisticRegression(max_iter=5000, random_state=42)
    ps_model.fit(X, t)
    ps = np.clip(ps_model.predict_proba(X)[:, 1], 0.01, 0.99)

    n = len(y)
    ate = float((np.sum(y * t / ps) - np.sum(y * (1 - t) / (1 - ps))) / n)

    # Bootstrap SE
    rng = np.random.RandomState(42)
    boot = []
    for _ in range(500):
        idx = rng.choice(n, n, replace=True)
        b = (np.sum(y[idx] * t[idx] / ps[idx])
             - np.sum(y[idx] * (1 - t[idx]) / (1 - ps[idx]))) / n
        boot.append(b)
    se = float(np.std(boot))

    return {
        "method": "Inverse probability weighting",
        "n": int(n),
        "ate": round(ate, 4),
        "se": round(se, 4),
        "ci_lower": round(ate - 1.96 * se, 4),
        "ci_upper": round(ate + 1.96 * se, 4),
        "p_value": safe_pval(2 * (1 - stats.norm.cdf(abs(ate / se)))) if se > 0 else None,
    }


# ── Difference-in-Differences ──────────────────────────────────────────────

def did_regression(
    df: pd.DataFrame,
    outcome: str,
    treatment_col: str,
    time_col: str,
    covariates: Optional[list] = None,
) -> dict:
    """OLS DiD with treatment × time interaction."""
    import statsmodels.api as sm

    covars = [c for c in (covariates or []) if c in df.columns]
    df2 = df.copy()

    ix = f"{treatment_col}_x_{time_col}"
    df2[ix] = df2[treatment_col].astype(float) * df2[time_col].astype(float)

    predictors = [treatment_col, time_col, ix] + covars
    X = pd.get_dummies(df2[predictors], drop_first=True, dtype=float)
    X = sm.add_constant(X)
    y = df2[outcome].astype(float)
    mask = X.notna().all(axis=1) & y.notna()
    X, y = X[mask], y[mask]

    result = sm.OLS(y, X).fit()
    int_cols = [c for c in X.columns if ix in c]
    did_col = int_cols[0] if int_cols else ix

    if did_col not in result.params.index:
        return {"error": f"Interaction term '{did_col}' not found in model."}

    return {
        "method": "Difference-in-differences",
        "did_estimate": round(float(result.params[did_col]), 4),
        "ci_lower": round(float(result.conf_int().loc[did_col, 0]), 4),
        "ci_upper": round(float(result.conf_int().loc[did_col, 1]), 4),
        "p_value": safe_pval(result.pvalues[did_col]),
        "n": int(result.nobs),
        "r_squared": round(float(result.rsquared), 4),
    }


# ── Interrupted Time Series ────────────────────────────────────────────────

def its_analysis(
    df: pd.DataFrame,
    outcome: str,
    time_col: str,
    intervention_point: Any,
) -> dict:
    """ITS with level and slope change terms, HC3 robust SEs."""
    import statsmodels.api as sm

    df2 = df.sort_values(time_col).copy()
    df2["_t"] = range(len(df2))
    df2["_post"] = (df2[time_col] >= intervention_point).astype(int)
    df2["_t_post"] = df2["_t"] * df2["_post"]

    X = sm.add_constant(df2[["_t", "_post", "_t_post"]])
    y = df2[outcome].astype(float)
    mask = y.notna()
    result = sm.OLS(y[mask], X[mask]).fit(cov_type="HC3")

    return {
        "method": "Interrupted time series",
        "n": int(result.nobs),
        "level_change": {
            "estimate": round(float(result.params["_post"]), 4),
            "p_value": safe_pval(result.pvalues["_post"]),
        },
        "slope_change": {
            "estimate": round(float(result.params["_t_post"]), 4),
            "p_value": safe_pval(result.pvalues["_t_post"]),
        },
        "r_squared": round(float(result.rsquared), 4),
    }


# ── E-value ─────────────────────────────────────────────────────────────────

def compute_evalue(estimate: float, ci_lower: float,
                   estimate_type: str = "OR") -> dict:
    """E-value for unmeasured confounding (VanderWeele & Ding 2017)."""
    if estimate_type in ("OR", "HR", "RR"):
        rr = estimate
        rr_lo = ci_lower
    else:
        rr = np.exp(abs(estimate))
        rr_lo = np.exp(abs(ci_lower))

    if rr < 1:
        rr, rr_lo = 1 / rr, (1 / rr_lo if rr_lo > 0 else rr_lo)

    ev = round(float(rr + np.sqrt(rr * (rr - 1))), 2)
    ev_ci = round(float(rr_lo + np.sqrt(rr_lo * (rr_lo - 1))), 2) if rr_lo > 1 else 1.0

    return {
        "e_value_point": ev,
        "e_value_ci": ev_ci,
        "interpretation": (
            f"An unmeasured confounder would need to be associated with both "
            f"the exposure and outcome by a risk ratio of at least {ev} each, "
            f"above and beyond measured confounders, to explain away the "
            f"observed association."
        ),
    }
