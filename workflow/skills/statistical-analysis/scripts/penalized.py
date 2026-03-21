"""
penalized.py — Penalized / regularised regression (LASSO, Ridge, Elastic Net).

Handles both continuous and binary outcomes with cross-validated alpha/C tuning.
Always standardises features before fitting.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler


def fit_penalized(
    df: pd.DataFrame,
    outcome: str,
    predictors: list,
    method: str = "lasso",
    task: str = "auto",
) -> dict:
    """
    Fit penalized regression with cross-validation.

    method : 'lasso' | 'ridge' | 'elasticnet'
    task   : 'auto' (inferred from outcome) | 'regression' | 'classification'
    """
    cols = [c for c in predictors if c in df.columns]
    X = pd.get_dummies(df[cols], drop_first=True, dtype=float)
    y = df[outcome]
    mask = X.notna().all(axis=1) & y.notna()
    X, y = X[mask], y[mask]
    feature_names = X.columns.tolist()

    if task == "auto":
        task = "classification" if len(np.unique(y)) <= 2 else "regression"

    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)

    if task == "classification":
        return _classification(X_s, y.values, method, X.shape, feature_names)
    return _regression(X_s, y.values, method, X.shape, feature_names)


# ── Continuous outcome ──────────────────────────────────────────────────────

def _regression(X, y, method, shape, feature_names) -> dict:
    from sklearn.linear_model import LassoCV, RidgeCV, ElasticNetCV

    cls_map = {"lasso": LassoCV, "ridge": RidgeCV, "elasticnet": ElasticNetCV}
    kwargs = {"cv": 5}
    if method == "elasticnet":
        kwargs["l1_ratio"] = [0.1, 0.5, 0.7, 0.9, 0.95]

    model = cls_map.get(method, LassoCV)(**kwargs)
    model.fit(X, y)

    cv = cross_val_score(model, X, y, cv=5, scoring="r2")
    coefs = dict(zip(feature_names, [round(float(c), 6) for c in model.coef_]))
    selected = {k: v for k, v in coefs.items() if abs(v) > 1e-6}

    return {
        "method": f"{method} regression",
        "task": "regression",
        "n": shape[0],
        "n_features": shape[1],
        "alpha": round(float(model.alpha_), 6),
        "cv_r2_mean": round(float(cv.mean()), 4),
        "cv_r2_std": round(float(cv.std()), 4),
        "n_selected_features": len(selected),
        "selected_features": selected,
        "all_coefficients": coefs,
    }


# ── Binary outcome ──────────────────────────────────────────────────────────

def _classification(X, y, method, shape, feature_names) -> dict:
    from sklearn.linear_model import LogisticRegressionCV

    penalty_map = {"lasso": "l1", "ridge": "l2", "elasticnet": "elasticnet"}
    kwargs = {
        "cv": 5,
        "penalty": penalty_map.get(method, "l1"),
        "solver": "saga",
        "max_iter": 5000,
    }
    if method == "elasticnet":
        kwargs["l1_ratios"] = [0.1, 0.5, 0.7, 0.9, 0.95]

    model = LogisticRegressionCV(**kwargs)
    model.fit(X, y)

    cv = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
    coefs = dict(zip(feature_names, [round(float(c), 6) for c in model.coef_[0]]))
    selected = {k: v for k, v in coefs.items() if abs(v) > 1e-6}

    return {
        "method": f"{method} logistic regression",
        "task": "classification",
        "n": shape[0],
        "n_features": shape[1],
        "C": round(float(model.C_[0]), 6),
        "cv_auc_mean": round(float(cv.mean()), 4),
        "cv_auc_std": round(float(cv.std()), 4),
        "n_selected_features": len(selected),
        "selected_features": selected,
        "all_coefficients": coefs,
    }
