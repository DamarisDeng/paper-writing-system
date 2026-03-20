#!/usr/bin/env python3
"""Load and profile datasets from a folder, producing profile.json and variable_types.json."""

import json
import os
import sys
from pathlib import Path

import pandas as pd


def scan_data_files(data_folder: str) -> list[Path]:
    """Find all CSV and XLSX files in the data folder, skipping hidden files."""
    folder = Path(data_folder)
    files = []
    for f in sorted(folder.iterdir()):
        if f.name.startswith("."):
            continue
        if f.suffix.lower() in (".csv", ".xlsx"):
            files.append(f)
    return files


def load_file(path: Path) -> pd.DataFrame:
    """Load a CSV or XLSX file into a DataFrame, handling multi-row headers in XLSX."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)

    # XLSX: detect multi-row headers / metadata rows
    df_raw = pd.read_excel(path, header=None, engine="openpyxl")

    # Heuristic: find the first row where most cells are non-null strings
    # (likely the header row). Skip rows that are title/metadata.
    header_row = _find_header_row(df_raw)

    if header_row == 0:
        df = pd.read_excel(path, header=0, engine="openpyxl")
    else:
        # Check if there's a multi-row header (next row has values that look
        # like sub-headers: short strings, year numbers, or mostly NaN with a few labels)
        next_row = header_row + 1
        if next_row < len(df_raw) and _is_subheader_row(df_raw.iloc[next_row], df_raw.iloc[header_row]):
            df = pd.read_excel(path, header=[header_row, next_row], engine="openpyxl")
            # Flatten multi-level columns, filtering out pandas auto-generated names
            def _flatten_col(parts):
                clean = []
                for c in parts:
                    s = str(c)
                    if s == "nan" or c is None or s.startswith("Unnamed:"):
                        continue
                    clean.append(s)
                return " ".join(clean).strip() if clean else str(parts[0])

            df.columns = [_flatten_col(col) for col in df.columns]
        else:
            df = pd.read_excel(path, header=header_row, engine="openpyxl")

    return df


def _find_header_row(df: pd.DataFrame, max_check: int = 10) -> int:
    """Find the most likely header row index.

    Looks for the first row that has mostly short strings (headers)
    and is followed by data rows (containing numbers or diverse values).
    """
    n_cols = df.shape[1]
    for i in range(min(max_check, len(df))):
        row = df.iloc[i]
        non_null = row.notna()
        non_null_count = non_null.sum()
        # Need at least 30% of columns filled
        if non_null_count < n_cols * 0.3:
            continue
        str_vals = [v for v in row if isinstance(v, str) and len(v.strip()) > 0]
        # A header row should be mostly strings
        if len(str_vals) >= non_null_count * 0.4:
            # Check if the next non-empty row has actual data (numbers or diverse types)
            for j in range(i + 1, min(i + 3, len(df))):
                data_row = df.iloc[j]
                has_numbers = any(isinstance(v, (int, float)) and not pd.isna(v) for v in data_row)
                if has_numbers:
                    return i
    return 0


def _is_subheader_row(row: pd.Series, header_row: pd.Series) -> bool:
    """Check if a row is a sub-header row (provides additional labels for columns
    that have NaN or generic names in the main header row).

    Indicators: the row has mostly NaN with a few short values (years, labels),
    and fills in gaps where the header row has NaN.
    """
    non_null = row.dropna()
    if len(non_null) == 0:
        return False

    # If the header row has NaN values and this row has values in those positions,
    # it's likely a sub-header
    header_nan_mask = header_row.isna()
    fills_gaps = row[header_nan_mask].notna().any() if header_nan_mask.any() else False

    # Sub-header values should be short (labels, years, etc.)
    short_values = sum(1 for v in non_null if len(str(v)) < 30)
    mostly_short = short_values / len(non_null) > 0.8

    return fills_gaps and mostly_short


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Light cleaning: strip whitespace, drop empty rows/cols, standardize col names."""
    # Standardize column names
    df.columns = [str(c).strip().replace("  ", " ") for c in df.columns]

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # Drop fully empty rows and columns
    df = df.dropna(how="all", axis=0)
    df = df.dropna(how="all", axis=1)

    # Attempt date parsing on object columns that look like dates
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(20)
        if len(sample) > 0:
            try:
                parsed = pd.to_datetime(sample, format="mixed")
                if parsed.notna().sum() == len(sample):
                    df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
            except (ValueError, TypeError):
                pass

    return df


def infer_variable_type(series: pd.Series, n_rows: int) -> str:
    """Infer the semantic type of a column."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    non_null = series.dropna()
    n_unique = non_null.nunique()

    if pd.api.types.is_numeric_dtype(series):
        if n_unique <= 2:
            return "binary"
        if n_rows > 10 and n_unique >= n_rows * 0.95:
            return "identifier"
        return "numeric"

    # String columns
    if n_unique <= 2:
        return "binary"

    if n_rows > 10 and n_unique >= n_rows * 0.95:
        avg_len = non_null.astype(str).str.len().mean()
        if avg_len > 50:
            return "text"
        return "identifier"

    avg_len = non_null.astype(str).str.len().mean()
    if avg_len > 50 and n_unique > 20:
        return "text"

    return "categorical"


def profile_column(series: pd.Series, var_type: str) -> dict:
    """Generate profiling stats for a single column."""
    info = {
        "dtype": str(series.dtype),
        "missing_count": int(series.isna().sum()),
        "missing_pct": round(float(series.isna().mean() * 100), 2),
        "unique_count": int(series.nunique()),
    }

    # Sample values: first 5 non-null unique values
    non_null_unique = series.dropna().unique()
    sample = [_safe_value(v) for v in non_null_unique[:5]]
    info["sample_values"] = sample

    if var_type == "numeric" or pd.api.types.is_numeric_dtype(series):
        desc = series.describe()
        for stat in ("mean", "std", "min", "max"):
            if stat in desc:
                info[stat] = round(float(desc[stat]), 4)
        if "50%" in desc:
            info["median"] = round(float(desc["50%"]), 4)

    if var_type in ("categorical", "binary"):
        top = series.value_counts().head(10)
        info["top_values"] = {_safe_value(k): int(v) for k, v in top.items()}

    return info


def _safe_value(v) -> str:
    """Convert a value to a JSON-safe string."""
    if pd.isna(v):
        return "NaN"
    if isinstance(v, (pd.Timestamp,)):
        return v.isoformat()
    return str(v)


def profile_dataset(df: pd.DataFrame, file_path: str) -> tuple[dict, dict]:
    """Profile a single dataframe, returning (profile_dict, types_dict)."""
    n_rows = len(df)
    columns_profile = {}
    types = {}

    for col in df.columns:
        var_type = infer_variable_type(df[col], n_rows)
        types[col] = var_type
        columns_profile[col] = profile_column(df[col], var_type)

    dataset_profile = {
        "file_path": file_path,
        "shape": [int(df.shape[0]), int(df.shape[1])],
        "columns": columns_profile,
    }

    return dataset_profile, types


def main():
    if len(sys.argv) != 3:
        print("Usage: python load_and_profile.py <data_folder> <output_folder>")
        sys.exit(1)

    data_folder = sys.argv[1]
    output_folder = sys.argv[2]

    if not os.path.isdir(data_folder):
        print(f"Error: data folder '{data_folder}' does not exist")
        sys.exit(1)

    os.makedirs(output_folder, exist_ok=True)

    files = scan_data_files(data_folder)
    if not files:
        print(f"No CSV or XLSX files found in '{data_folder}'")
        sys.exit(1)

    print(f"Found {len(files)} data file(s): {[f.name for f in files]}")

    all_profiles = {}
    all_types = {}

    for path in files:
        print(f"\nLoading {path.name}...")
        try:
            df = load_file(path)
            df = clean_dataframe(df)
            print(f"  Shape: {df.shape}")
            profile, types = profile_dataset(df, str(path))
            all_profiles[path.name] = profile
            all_types[path.name] = types
        except Exception as e:
            print(f"  ERROR loading {path.name}: {e}")
            continue

    profile_out = {"datasets": all_profiles}

    profile_path = os.path.join(output_folder, "profile.json")
    types_path = os.path.join(output_folder, "variable_types.json")

    with open(profile_path, "w") as f:
        json.dump(profile_out, f, indent=2, default=str)
    print(f"\nWrote {profile_path}")

    with open(types_path, "w") as f:
        json.dump(all_types, f, indent=2)
    print(f"Wrote {types_path}")


if __name__ == "__main__":
    main()
