"""
data_utils.py — Data loading, merging, cleaning, and preparation.

Handles CSV/Excel/TSV with encoding fallback, auto-merging multiple datasets,
derived variable creation, missingness documentation, and exclusion logic.
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ── Loading ─────────────────────────────────────────────────────────────────

def load_dataset(file_path: str) -> pd.DataFrame:
    """Safely load a dataset from CSV, TSV, or Excel with encoding fallback."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    elif suffix == ".tsv":
        return _read_csv_safe(file_path, sep="\t")
    else:
        return _read_csv_safe(file_path, sep=",")


def _read_csv_safe(path: str, sep: str) -> pd.DataFrame:
    """Try multiple encodings and separator sniffing."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path, sep=sep, encoding=encoding, low_memory=False)
            if df.shape[1] == 1 and sep == ",":
                df2 = pd.read_csv(path, sep="\t", encoding=encoding, low_memory=False)
                if df2.shape[1] > 1:
                    return df2
            return df
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    raise ValueError(f"Could not parse {path} with any encoding.")


# ── Merging ─────────────────────────────────────────────────────────────────

def load_and_merge(
    profile: dict,
    research_questions: dict,
    data_folder: str,
    downloaded_folder: str = "",
) -> pd.DataFrame:
    """
    Load all datasets referenced in profile.json and merge them.

    Falls back to concatenation when no shared columns exist.
    """
    datasets = {}
    for ds_name, ds_info in profile.get("datasets", {}).items():
        fp = ds_info.get("file_path", "")
        if not fp:
            continue
        if not os.path.exists(fp):
            alt = os.path.join(data_folder, os.path.basename(fp))
            if os.path.exists(alt):
                fp = alt
        datasets[ds_name] = load_dataset(fp)
        print(f"  Loaded {ds_name}: {datasets[ds_name].shape}")

    if downloaded_folder and os.path.isdir(downloaded_folder):
        for f in os.listdir(downloaded_folder):
            fpath = os.path.join(downloaded_folder, f)
            if f.endswith((".csv", ".tsv", ".xlsx", ".xls")):
                name = f"downloaded_{Path(f).stem}"
                datasets[name] = load_dataset(fpath)
                print(f"  Loaded {name}: {datasets[name].shape}")

    if not datasets:
        raise ValueError("No datasets loaded.")
    if len(datasets) == 1:
        return list(datasets.values())[0]

    relationships = profile.get("data_context", {}).get("dataset_relationships", [])
    return _auto_merge(datasets, relationships)


def _auto_merge(datasets: dict, relationships: list) -> pd.DataFrame:
    dfs = list(datasets.values())
    result = dfs[0]
    for df in dfs[1:]:
        shared = list(set(result.columns) & set(df.columns))
        if shared:
            key_cols = sorted(shared, key=lambda c: result[c].isna().sum())[:3]
            try:
                result = result.merge(df, on=key_cols, how="outer",
                                      suffixes=("", "_dup"))
                dup_cols = [c for c in result.columns if c.endswith("_dup")]
                result.drop(columns=dup_cols, inplace=True)
            except Exception as e:
                print(f"  Warning: merge failed on {key_cols}: {e}")
                result = pd.concat([result, df], axis=0, ignore_index=True)
        else:
            print("  Warning: no shared columns, concatenating rows.")
            result = pd.concat([result, df], axis=0, ignore_index=True)
    print(f"  Merged dataset shape: {result.shape}")
    return result


# ── Derived Variables ───────────────────────────────────────────────────────

def create_derived_variables(df: pd.DataFrame, derived_specs: list) -> pd.DataFrame:
    """
    Create derived variables from research_questions.json specs.

    Each spec: {name, derivation, source_columns}.
    Tries df.eval() first, then falls back to direct Python eval.
    """
    df = df.copy()
    for spec in derived_specs:
        name = spec["name"]
        derivation = spec["derivation"]
        source_cols = spec.get("source_columns", [])

        missing = [c for c in source_cols if c not in df.columns]
        if missing:
            print(f"  Warning: Cannot create '{name}' — missing columns: {missing}")
            continue

        try:
            df[name] = df.eval(derivation)
        except Exception:
            try:
                local_vars = {col: df[col] for col in source_cols}
                local_vars["np"] = np
                df[name] = eval(derivation, {"__builtins__": {}}, local_vars)
            except Exception as e:
                print(f"  Error creating '{name}': {e}")
                continue

        print(f"  Created '{name}': mean={df[name].mean():.4f}, "
              f"std={df[name].std():.4f}, N_valid={df[name].notna().sum()}")
    return df


# ── Missingness & Exclusions ───────────────────────────────────────────────

def document_missingness(df: pd.DataFrame, analysis_vars: list) -> dict:
    """Classify missingness for each variable as OK / CAUTION / HIGH."""
    result = {}
    for col in analysis_vars:
        if col not in df.columns:
            result[col] = {"status": "COLUMN_NOT_FOUND", "pct_missing": None}
            continue
        n_miss = int(df[col].isna().sum())
        pct = round(n_miss / len(df) * 100, 2)
        if pct < 5:
            status = "OK — complete-case acceptable"
        elif pct < 20:
            status = "CAUTION — consider imputation in sensitivity"
        else:
            status = "HIGH — exclude from primary analysis"
        result[col] = {
            "n_missing": n_miss,
            "pct_missing": pct,
            "n_valid": int(len(df) - n_miss),
            "status": status,
        }
    return result


def apply_exclusions(
    df: pd.DataFrame,
    outcome_col: str,
    exposure_col: str,
    required_cols: Optional[list] = None,
) -> tuple:
    """
    Exclude rows missing outcome, exposure, or required covariates.

    Returns (clean_df, exclusion_log_dict).
    """
    n_start = len(df)
    reasons = []

    mask = df[outcome_col].notna()
    n = (~mask).sum()
    if n > 0:
        reasons.append(f"Missing outcome ({outcome_col}): {n}")

    mask &= df[exposure_col].notna()
    n = (~df[exposure_col].notna() & mask).sum()
    # recalculate after combining
    n_miss_exp = ((~df[exposure_col].notna()) & df[outcome_col].notna()).sum()
    if n_miss_exp > 0:
        reasons.append(f"Missing exposure ({exposure_col}): {n_miss_exp}")

    mask = df[outcome_col].notna() & df[exposure_col].notna()
    if required_cols:
        for col in required_cols:
            if col in df.columns:
                col_miss = (~df[col].notna() & mask).sum()
                if col_miss > 0:
                    reasons.append(f"Missing covariate ({col}): {col_miss}")
                mask &= df[col].notna()

    clean = df[mask].copy().reset_index(drop=True)
    n_excluded = n_start - len(clean)
    print(f"  Exclusions: {n_start} → {len(clean)} ({n_excluded} excluded)")
    for r in reasons:
        print(f"    {r}")
    return clean, {"n_start": n_start, "n_final": len(clean),
                    "n_excluded": n_excluded, "reasons": reasons}


def save_analytic_dataset(df: pd.DataFrame, output_path: str):
    """Save the analytic dataset to CSV."""
    df.to_csv(output_path, index=False)
    print(f"  Saved analytic dataset: {output_path} "
          f"({df.shape[0]} rows, {df.shape[1]} cols)")
