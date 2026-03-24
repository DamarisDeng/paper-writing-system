#!/usr/bin/env python3
"""
Efficient data profiler that uses smart sampling strategy.

Strategy:
1. Read Data_Description.md first for context
2. Sample first 1000 rows of each file to understand structure
3. Read data dictionary if available (from Excel or sidecar file)
4. Use dictionary info to guide full profiling
5. Only full-load files that need detailed profiling

This dramatically reduces token usage and time for large datasets.

Usage:
    python quick_profile.py <data_folder> <output_folder>
"""

import json
import os
import re
import sys
from pathlib import Path

import pandas as pd


def read_data_description(data_folder: Path) -> dict:
    """Read Data_Description.md for high-level dataset context."""
    desc_path = data_folder / "Data_Description.md"
    if not desc_path.exists():
        return {}

    with open(desc_path) as f:
        content = f.read()

    context = {
        "datasets": {},
        "relationships": []
    }

    # Extract dataset descriptions
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
    for section in sections[1:]:
        lines = section.strip().split('\n')
        if lines:
            name = lines[0].strip()
            desc_match = re.search(r'- \*\*What it contains\*\*:\s*(.+)', section)
            context["datasets"][name] = {
                "description": desc_match.group(1) if desc_match else "",
                "key_variables": []
            }

    return context


def find_data_dictionary(file_path: Path) -> Path | None:
    """Find a data dictionary file for the given data file."""
    parent = file_path.parent
    stem = file_path.stem

    # Look for Excel dictionaries
    for dict_file in parent.glob(f"*dictionary*{stem}*.xlsx"):
        return dict_file
    for dict_file in parent.glob("*dictionary*.xlsx"):
        return dict_file

    # Look for CSV sidecars
    for dict_file in parent.glob(f"{stem}_dictionary.csv"):
        return dict_file
    for dict_file in parent.glob(f"{stem}_data_dict.csv"):
        return dict_file

    return None


def read_dictionary(dict_path: Path) -> dict:
    """Read data dictionary and return variable descriptions."""
    var_info = {}

    try:
        if dict_path.suffix == ".xlsx":
            df = pd.read_excel(dict_path, header=None)
            # Look for Variable | Description pattern
            for _, row in df.iterrows():
                if len(row) >= 2:
                    var_name = str(row.iloc[1]).strip()
                    if var_name and len(var_name) < 50 and var_name.isupper():
                        desc = str(row.iloc[2]) if len(row) > 2 else ""
                        if desc and desc != "nan":
                            var_info[var_name] = desc[:200]  # Truncate long descriptions
        elif dict_path.suffix == ".csv":
            df = pd.read_csv(dict_path)
            # Common column names for dictionaries
            var_col = None
            desc_col = None
            for col in df.columns:
                col_lower = col.lower()
                if "variable" in col_lower or "name" in col_lower:
                    var_col = col
                elif "description" in col_lower or "label" in col_lower:
                    desc_col = col

            if var_col and desc_col:
                for _, row in df.iterrows():
                    var = str(row[var_col]).strip()
                    desc = str(row[desc_col]).strip()
                    if var and var != "nan":
                        var_info[var] = desc[:200]

    except Exception as e:
        print(f"  Warning: Could not read dictionary {dict_path.name}: {e}")

    return var_info


def smart_sample_file(file_path: Path, n_rows: int = 1000) -> dict:
    """Sample first n rows to understand structure efficiently."""
    try:
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path, nrows=n_rows, low_memory=False)
        else:  # xlsx
            df = pd.read_excel(file_path, nrows=n_rows, engine="openpyxl")

        return {
            "sample_shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "has_data": True
        }
    except Exception as e:
        return {
            "has_data": False,
            "error": str(e)
        }


def quick_profile_large_dataset(file_path: Path, dict_info: dict, sample_info: dict) -> dict:
    """Profile a large dataset using sampling and dictionary info.

    Strategy:
    - Use sample for basic stats
    - Use dictionary for semantic meaning
    - Only full-scan if sample is insufficient
    """

    # Load sample (already done in sample_info)
    n_profile_rows = 10000  # Larger sample for stats

    try:
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path, nrows=n_profile_rows, low_memory=False)
        else:
            df = pd.read_excel(file_path, nrows=n_profile_rows, engine="openpyxl")

        # Quick column profiling
        columns = {}
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "missing_count": int(df[col].isna().sum()),
                "missing_pct": round(float(df[col].isna().mean() * 100), 2),
            }

            # Add dictionary description if available
            if col in dict_info:
                col_info["description"] = dict_info[col]

            # Quick value sampling
            non_null = df[col].dropna()
            if len(non_null) > 0:
                col_info["sample_values"] = [
                    str(v) for v in non_null.head(5).unique()
                ]

                # Unique count estimate
                n_unique = non_null.nunique()
                col_info["unique_count_estimate"] = int(n_unique)

                # For numeric: quick stats
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_info["min"] = float(df[col].min())
                    col_info["max"] = float(df[col].max())

            columns[str(col)] = col_info

        return {
            "file_path": str(file_path),
            "profile_method": "sample_based",
            "rows_profiled": n_profile_rows,
            "shape_estimate": [
                n_profile_rows,
                len(df.columns)
            ],
            "columns": columns
        }

    except Exception as e:
        return {
            "file_path": str(file_path),
            "error": str(e),
            "profile_method": "failed"
        }


def main():
    if len(sys.argv) != 3:
        print("Usage: python quick_profile.py <data_folder> <output_folder>")
        sys.exit(1)

    data_folder = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])

    os.makedirs(output_folder, exist_ok=True)

    print("=== Efficient Data Profiling ===\n")

    # Step 1: Read data description for context
    print("Step 1: Reading Data_Description.md for context...")
    data_context = read_data_description(data_folder)
    if data_context:
        print(f"  Found context for {len(data_context['datasets'])} datasets")

    # Step 2: Scan for data files
    print("\nStep 2: Scanning for data files...")
    data_files = []
    skip_dirs = {"__MACOSX", ".git", "downloaded", "repwgt"}

    for f in sorted(data_folder.rglob("*")):
        if any(skip in f.parts for skip in skip_dirs):
            continue
        if any(part.startswith(".") for part in f.parts):
            continue
        if f.suffix.lower() in (".csv", ".xlsx"):
            # Skip metadata files
            if any(kw in f.name.lower() for kw in ("dictionary", "readme", "repwgt")):
                continue
            data_files.append(f)

    print(f"  Found {len(data_files)} data files")

    if not data_files:
        print("No data files found!")
        sys.exit(1)

    # Step 3: Quick sample each file
    print("\nStep 3: Quick sampling of all files...")
    file_profiles = {}

    for f in data_files:
        print(f"  Sampling {f.name}...")
        sample = smart_sample_file(f)

        if sample.get("has_data"):
            file_profiles[str(f)] = {
                "sample_info": sample,
                "full_profile": None
            }

    # Step 4: Read dictionaries and do targeted profiling
    print("\nStep 4: Reading data dictionaries and targeted profiling...")

    all_profiles = {}
    all_types = {}

    for f in data_files:
        if str(f) not in file_profiles:
            continue

        print(f"  Profiling {f.name}...")

        # Find and read dictionary
        dict_path = find_data_dictionary(f)
        dict_info = {}
        if dict_path:
            print(f"    Found dictionary: {dict_path.name}")
            dict_info = read_dictionary(dict_path)
            if dict_info:
                print(f"    Read {len(dict_info)} variable descriptions")

        # Profile using sample + dictionary
        sample_info = file_profiles[str(f)]["sample_info"]
        profile = quick_profile_large_dataset(f, dict_info, sample_info)

        rel_path = str(f.relative_to(data_folder))
        all_profiles[rel_path] = profile

        # Infer types from sample
        for col_name, col_info in profile.get("columns", {}).items():
            dtype = col_info.get("dtype", "object")

            if "numeric" in dtype.lower() or dtype.startswith(("int", "float")):
                # Use unique count estimate to determine subtype
                unique_est = col_info.get("unique_count_estimate", 100)
                if unique_est <= 2:
                    var_type = "binary"
                elif unique_est >= sample_info["sample_shape"][0] * 0.95:
                    var_type = "identifier"
                else:
                    var_type = "numeric"
            else:
                unique_est = col_info.get("unique_count_estimate", 100)
                if unique_est <= 2:
                    var_type = "binary"
                elif unique_est >= sample_info["sample_shape"][0] * 0.95:
                    var_type = "identifier"
                else:
                    var_type = "categorical"

            if rel_path not in all_types:
                all_types[rel_path] = {}
            all_types[rel_path][col_name] = var_type

    # Step 5: Combine with data description context
    output_profile = {"datasets": all_profiles}
    if data_context:
        output_profile["data_context"] = data_context

    # Write outputs
    profile_path = output_folder / "profile.json"
    types_path = output_folder / "variable_types.json"

    with open(profile_path, "w") as f:
        json.dump(output_profile, f, indent=2, default=str)
    print(f"\nWrote {profile_path}")

    with open(types_path, "w") as f:
        json.dump(all_types, f, indent=2)
    print(f"Wrote {types_path}")

    print(f"\n=== Profiling Complete ===")
    print(f"Profiled {len(all_profiles)} datasets")
    print(f"Used smart sampling for efficiency")


if __name__ == "__main__":
    main()
