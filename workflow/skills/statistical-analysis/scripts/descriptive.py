"""
descriptive.py — Table 1 / descriptive statistics generation.

Produces stratified summaries with normality-aware stats, appropriate
comparison tests, and standardized mean differences.
"""

import numpy as np
import pandas as pd
from scipy import stats

from utils import safe_pval, jama_p


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

    result["table1_formatted"] = format_table1_for_display(result, df)
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


# ── Table 1 formatting for display ────────────────────────────────────────────

def format_table1_for_display(table1_result: dict, df: pd.DataFrame) -> list:
    """Convert nested table1 result to flat array for Stage 5 rendering.

    Returns a list of dicts ready for table1_formatted in analysis_results.json.
    Each dict has: variable, overall, group_0, group_1, p_value, test
    """
    formatted = []
    group_labels = sorted(table1_result["groups"].keys())

    # Process continuous variables
    for var, info in table1_result["variables"].items():
        if info.get("type") != "continuous":
            continue

        if info.get("distribution") == "normal":
            overall = f"{info['overall']['mean']:.1f} ({info['overall']['sd']:.1f})"
            group_strs = [
                f"{info['by_group'][g]['mean']:.1f} ({info['by_group'][g]['sd']:.1f})"
                for g in group_labels
            ]
        else:  # non-normal
            overall = f"{info['overall']['median']:.1f} ({info['overall']['q1']:.1f}-{info['overall']['q3']:.1f})"
            group_strs = [
                f"{info['by_group'][g]['median']:.1f} ({info['by_group'][g]['q1']:.1f}-{info['by_group'][g]['q3']:.1f})"
                for g in group_labels
            ]

        row = {
            "variable": var.replace("_", " ").title(),
            "overall": overall,
            **{f"group_{i}": s for i, s in enumerate(group_strs)},
            "p_value": jama_p(info["p_value"]) if info.get("p_value") is not None else None,
            "test": info["test_used"]
        }
        formatted.append(row)

    # Process categorical variables (for binary categories)
    for var, info in table1_result["variables"].items():
        if info.get("type") != "categorical":
            continue

        for cat_val in info["overall"].keys():
            cat_n = info["overall"][cat_val]["n"]
            cat_pct = info["overall"][cat_val]["pct"]
            overall = f"{cat_n} ({cat_pct})"

            group_strs = []
            for g in group_labels:
                if cat_val in info["by_group"][g]:
                    gn = info["by_group"][g][cat_val]["n"]
                    gpct = info["by_group"][g][cat_val]["pct"]
                    group_strs.append(f"{gn} ({gpct})")
                else:
                    group_strs.append("0 (0)")

            row = {
                "variable": f"{var.replace('_', ' ').title()} = {cat_val}",
                "overall": overall,
                **{f"group_{i}": s for i, s in enumerate(group_strs)},
                "p_value": jama_p(info["p_value"]) if info.get("p_value") is not None else None,
                "test": info["test_used"]
            }
            formatted.append(row)

    return formatted
