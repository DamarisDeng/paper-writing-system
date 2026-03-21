"""
ml.py — Machine learning prediction models.

Supports Random Forest, XGBoost, SVM, and KNN with cross-validated
hyperparameter tuning, train/test evaluation, and feature importance.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV,
)
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, recall_score,
    f1_score, mean_squared_error, mean_absolute_error, r2_score,
    confusion_matrix,
)


def fit_ml_model(
    df: pd.DataFrame,
    outcome: str,
    predictors: list,
    method: str = "random_forest",
    task: str = "auto",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """
    Fit an ML model with train/test split, CV tuning, and feature importance.

    method : 'random_forest' | 'xgboost' | 'svm' | 'knn'
    task   : 'auto' | 'classification' | 'regression'
    """
    cols = [c for c in predictors if c in df.columns]
    X = pd.get_dummies(df[cols], drop_first=True, dtype=float)
    y = df[outcome]
    mask = X.notna().all(axis=1) & y.notna()
    X, y = X[mask], y[mask]
    feature_names = X.columns.tolist()

    if task == "auto":
        task = "classification" if len(y.unique()) <= 2 else "regression"

    stratify = y if (task == "classification" and len(y.unique()) <= 10) else None
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify,
    )

    # Scale for distance-based methods
    scaler = StandardScaler()
    if method in ("svm", "knn"):
        X_tr_s = pd.DataFrame(scaler.fit_transform(X_tr), columns=feature_names)
        X_te_s = pd.DataFrame(scaler.transform(X_te), columns=feature_names)
    else:
        X_tr_s, X_te_s = X_tr, X_te

    model, param_grid = _model_and_params(method, task)

    # Hyperparameter search
    scoring = "roc_auc" if task == "classification" else "r2"
    try:
        gs = GridSearchCV(model, param_grid, cv=5, scoring=scoring, n_jobs=-1)
        gs.fit(X_tr_s, y_tr)
        best = gs.best_estimator_
        best_params = gs.best_params_
    except Exception:
        best = model
        best.fit(X_tr_s, y_tr)
        best_params = {}

    # Evaluate
    pred_tr = best.predict(X_tr_s)
    pred_te = best.predict(X_te_s)

    if task == "classification":
        metrics = _classification_metrics(best, X_tr_s, X_te_s, y_tr, y_te, pred_tr, pred_te)
        cv = cross_val_score(best, X_tr_s, y_tr, cv=5, scoring="roc_auc")
    else:
        metrics = _regression_metrics(y_tr, y_te, pred_tr, pred_te)
        cv = cross_val_score(best, X_tr_s, y_tr, cv=5, scoring="r2")

    importances = _feature_importance(best, feature_names, X_te_s, y_te)

    return {
        "method": method,
        "task": task,
        "n_train": len(X_tr),
        "n_test": len(X_te),
        "hyperparameters": best_params,
        **metrics,
        "cv_mean": round(float(cv.mean()), 4),
        "cv_std": round(float(cv.std()), 4),
        "feature_importance": importances,
    }


# ── Model / param constructors ──────────────────────────────────────────────

def _model_and_params(method, task):
    if method == "random_forest":
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        cls = RandomForestClassifier if task == "classification" else RandomForestRegressor
        return cls(random_state=42, n_jobs=-1), {
            "n_estimators": [100, 200],
            "max_depth": [5, 10, None],
            "min_samples_leaf": [5, 10],
        }
    if method == "xgboost":
        import xgboost as xgb
        cls = xgb.XGBClassifier if task == "classification" else xgb.XGBRegressor
        return cls(random_state=42, use_label_encoder=False,
                   eval_metric="logloss" if task == "classification" else "rmse"), {
            "n_estimators": [100, 200],
            "max_depth": [3, 6],
            "learning_rate": [0.05, 0.1],
        }
    if method == "svm":
        from sklearn.svm import SVC, SVR
        if task == "classification":
            return SVC(probability=True, random_state=42), {
                "C": [0.1, 1, 10], "kernel": ["rbf", "linear"],
            }
        return SVR(), {"C": [0.1, 1, 10], "kernel": ["rbf", "linear"]}
    if method == "knn":
        from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
        cls = KNeighborsClassifier if task == "classification" else KNeighborsRegressor
        return cls(), {"n_neighbors": [3, 5, 10, 15], "weights": ["uniform", "distance"]}
    raise ValueError(f"Unknown ML method: {method}")


# ── Metrics ─────────────────────────────────────────────────────────────────

def _classification_metrics(model, X_tr, X_te, y_tr, y_te, pred_tr, pred_te):
    try:
        prob_tr = model.predict_proba(X_tr)[:, 1]
        prob_te = model.predict_proba(X_te)[:, 1]
        auc_tr = round(roc_auc_score(y_tr, prob_tr), 4)
        auc_te = round(roc_auc_score(y_te, prob_te), 4)
    except Exception:
        auc_tr = auc_te = None

    return {
        "train": {"auc_roc": auc_tr,
                   "accuracy": round(accuracy_score(y_tr, pred_tr), 4)},
        "test":  {"auc_roc": auc_te,
                   "accuracy": round(accuracy_score(y_te, pred_te), 4),
                   "precision": round(precision_score(y_te, pred_te, zero_division=0), 4),
                   "recall": round(recall_score(y_te, pred_te, zero_division=0), 4),
                   "f1": round(f1_score(y_te, pred_te, zero_division=0), 4),
                   "confusion_matrix": confusion_matrix(y_te, pred_te).tolist()},
    }


def _regression_metrics(y_tr, y_te, pred_tr, pred_te):
    return {
        "train": {"rmse": round(np.sqrt(mean_squared_error(y_tr, pred_tr)), 4),
                   "r2": round(r2_score(y_tr, pred_tr), 4)},
        "test":  {"rmse": round(np.sqrt(mean_squared_error(y_te, pred_te)), 4),
                   "mae": round(mean_absolute_error(y_te, pred_te), 4),
                   "r2": round(r2_score(y_te, pred_te), 4)},
    }


# ── Feature importance ──────────────────────────────────────────────────────

def _feature_importance(model, feature_names, X_test, y_test) -> list:
    if hasattr(model, "feature_importances_"):
        imps = model.feature_importances_
    elif hasattr(model, "coef_"):
        imps = np.abs(model.coef_).flatten()
    else:
        try:
            from sklearn.inspection import permutation_importance
            r = permutation_importance(model, X_test, y_test,
                                        n_repeats=10, random_state=42, n_jobs=-1)
            imps = r.importances_mean
        except Exception:
            return []

    ranked = sorted(zip(feature_names, imps), key=lambda x: -x[1])
    return [{"feature": f, "importance": round(float(v), 6)} for f, v in ranked[:20]]
