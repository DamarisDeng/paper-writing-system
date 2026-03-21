"""
descriptive.py — Table 1 / descriptive statistics generation.

Produces stratified summaries with normality-aware stats, appropriate
comparison tests, and standardized mean differences.
"""

import numpy as np
import pandas as pd
from scipy import stats

from utils import safe_pval


def generate_table1(
    df: pd.DataFrame,
    group_col: str,
    continuous_vars: list,
    categorical_vars: list,
) -> dict:
    """
    Generate Table 1 descriptive statistics stratified by group_col.

    Returns a dict ready for analysis_results.json["descriptive_statistics"].
    """
    groups = df[group_col].dropna().unique()
    result = {
        "variables": {},
        "group_column": group_col,
        "groups": {str(g): {"n": int((df[group_col] == g).sum())} for g in groups},
    }

    for var in continuous_vars:
        if var in df.columns:
            result["variables"][var] = _describe_continuous(df, var, group_col, groups)

    for var in categorical_vars:
        if var in df.columns:
            result["variables"][var] = _describe_categorical(df, var, group_col, groups)

    return result


# ── Continuous helpers ──────────────────────────────────────────────────────

def _describe_continuous(df, var, group_col, groups) -> dict:
    data = df[var].dropna()
    sample = data.sample(min(5000, len(data)), random_state=42)
    try:
        _, p_normal = stats.shapiro(sample[:5000])
    except Exception:
        p_normal = 0.0

    is_normal = p_normal > 0.05
    overall = _continuous_stats(data, is_normal)

    by_group = {}
    group_data = []
    for g in groups:
        gd = df.loc[df[group_col] == g, var].dropna()
        by_group[str(g)] = _continuous_stats(gd, is_normal)
        group_data.append(gd)

    # Comparison test
    if len(groups) == 2:
        if is_normal:
            _, pval = stats.ttest_ind(*group_data, equal_var=False)
            test = "Welch's t-test"
        else:
            _, pval = stats.mannwhitneyu(*group_data, alternative="two-sided")
            test = "Mann-Whitney U"
    else:
        if is_normal:
            _, pval = stats.f_oneway(*group_data)
            test = "ANOVA"
        else:
            _, pval = stats.kruskal(*group_data)
            test = "Kruskal-Wallis"

    # SMD for two-group comparisons
    smd = None
    if len(groups) == 2:
        m1, m2 = group_data[0].mean(), group_data[1].mean()
        s1, s2 = group_data[0].std(), group_data[1].std()
        pooled = np.sqrt((s1**2 + s2**2) / 2)
        smd = round(abs(m1 - m2) / pooled, 4) if pooled > 0 else 0.0

    return {
        "type": "continuous",
        "distribution": "normal" if is_normal else "non-normal",
        "overall": overall,
        "by_group": by_group,
        "p_value": safe_pval(pval),
        "test_used": test,
        "smd": smd,
    }


def _continuous_stats(series, is_normal) -> dict:
    if is_normal:
        return {"mean": round(series.mean(), 4),
                "sd": round(series.std(), 4),
                "n": int(len(series))}
    return {"median": round(series.median(), 4),
            "q1": round(series.quantile(0.25), 4),
            "q3": round(series.quantile(0.75), 4),
            "n": int(len(series))}


# ── Categorical helpers ─────────────────────────────────────────────────────

def _describe_categorical(df, var, group_col, groups) -> dict:
    overall_counts = df[var].value_counts(dropna=False)
    overall = {str(k): {"n": int(v), "pct": round(v / len(df) * 100, 2)}
               for k, v in overall_counts.items()}

    by_group = {}
    for g in groups:
        gdf = df[df[group_col] == g]
        gc = gdf[var].value_counts(dropna=False)
        by_group[str(g)] = {str(k): {"n": int(v), "pct": round(v / len(gdf) * 100, 2)}
                            for k, v in gc.items()}

    try:
        ct = pd.crosstab(df[var], df[group_col])
        if (ct < 5).any().any():
            if ct.shape == (2, 2):
                _, pval = stats.fisher_exact(ct)
                test = "Fisher's exact"
            else:
                _, pval, _, _ = stats.chi2_contingency(ct)
                test = "Chi-square (small cell warning)"
        else:
            _, pval, _, _ = stats.chi2_contingency(ct)
            test = "Chi-square"
    except Exception:
        pval, test = None, "test failed"

    return {
        "type": "categorical",
        "overall": overall,
        "by_group": by_group,
        "p_value": safe_pval(pval),
        "test_used": test,
    }
