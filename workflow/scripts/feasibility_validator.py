#!/usr/bin/env python3
"""
feasibility_validator.py — Rigorous feasibility checking for candidate research questions.

This module provides functions to validate whether a candidate research question
is feasible with the available data BEFORE expensive literature searches are performed.

Each candidate must pass these checks to be marked as "feasible":
- Control Group: At least one exposure group AND one comparison group exists
- Outcome Data: Outcome variable exists or can be derived/acquired
- Sample Size: Total N >= 20 (cross-sectional) or >= 50 (DiD/longitudinal)
- Study Design Match: Required data structure exists for the design
- Variable Availability: All critical variables exist in data

Usage:
    from feasibility_validator import validate_candidate_feasibility

    result = validate_candidate_feasibility(candidate, variable_types, profile)
    if result["feasible"]:
        # Proceed with literature search
    else:
        # Mark as infeasible with reasons
"""

import json
import os
from typing import Dict, List, Any, Optional, Set


# ── Constants ──────────────────────────────────────────────────────────────

# Failure mode codes
FAILURE_NO_CONTROL_GROUP = "no_control_group"
FAILURE_NO_OUTCOME_DATA = "no_outcome_data"
FAILURE_INSUFFICIENT_SAMPLE = "insufficient_sample"
FAILURE_DESIGN_MISMATCH = "design_mismatch"
FAILURE_MISSING_CRITICAL_VARIABLES = "missing_critical_variables"
FAILURE_NEEDS_DOWNLOAD_UNVERIFIED = "needs_download_unverified"

# Study design types
DESIGN_CROSS_SECTIONAL = "cross_sectional"
DESIGN_DID = "difference_in_differences"
DESIGN_LONGITUDINAL = "longitudinal"
DESIGN_COHORT = "cohort"
DESIGN_CASE_CONTROL = "case_control"
DESIGN_ECOLOGICAL = "ecological"

# Minimum sample sizes by design
MIN_SAMPLE_SIZE = {
    DESIGN_CROSS_SECTIONAL: 20,
    DESIGN_DID: 50,
    DESIGN_LONGITUDINAL: 50,
    DESIGN_COHORT: 50,
    DESIGN_CASE_CONTROL: 30,
    DESIGN_ECOLOGICAL: 10,  # State-level can work with fewer
}

# Allowed outcome types
ALLOWED_OUTCOME_TYPES = {"numeric", "binary", "continuous", "categorical", "categorical_nominal"}

# Allowed exposure types
ALLOWED_EXPOSURE_TYPES = {"categorical", "categorical_nominal", "categorical_ordinal",
                          "binary", "numeric", "continuous", "datetime"}

# Forbidden types for outcome/exposure
FORBIDDEN_OUTCOME_TYPES = {"identifier", "text"}
FORBIDDEN_EXPOSURE_TYPES = {"identifier", "text"}


# ── Main Validation Function ─────────────────────────────────────────────────

def validate_candidate_feasibility(
    candidate: Dict[str, Any],
    variable_types: Dict[str, Any],
    profile: Dict[str, Any],
    data_acquisition_requirements: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Validate a candidate research question for data feasibility.

    Runs all feasibility checks and returns a detailed result.

    Args:
        candidate: Candidate question dict from research_questions.json
        variable_types: Contents of variable_types.json
        profile: Contents of profile.json
        data_acquisition_requirements: Optional list of data acquisition requirements

    Returns:
        Dict with keys:
        - feasible (bool): True if all checks pass
        - reasons (List[str]): List of failure mode codes if not feasible
        - details (Dict[str, Any]): Detailed check results for audit trail
    """
    reasons = []
    details = {
        "checks_performed": [],
        "control_group_check": None,
        "outcome_check": None,
        "sample_size_check": None,
        "design_match_check": None,
        "variable_availability_check": None,
    }

    variable_roles = candidate.get("variable_roles", {})
    study_design = candidate.get("study_design", "").lower()

    # Extract outcomes and exposures
    outcomes = _get_role_values(variable_roles, "outcome_variables", "outcome")
    exposures = _get_role_values(variable_roles, "exposure_variables", "exposure")
    covariates = _get_role_values(variable_roles, "covariates", "confounders")

    # Check 1: Control Group
    control_check = check_control_group(exposures, variable_types, profile)
    details["control_group_check"] = control_check
    details["checks_performed"].append("control_group")
    if not control_check["passed"]:
        reasons.append(FAILURE_NO_CONTROL_GROUP)

    # Check 2: Outcome Data
    outcome_check = check_outcome_available(
        outcomes,
        variable_types,
        profile,
        data_acquisition_requirements or []
    )
    details["outcome_check"] = outcome_check
    details["checks_performed"].append("outcome_data")
    if not outcome_check["passed"]:
        reasons.append(FAILURE_NO_OUTCOME_DATA)

    # Check 3: Sample Size
    sample_check = check_sample_size(study_design, profile, variable_types)
    details["sample_size_check"] = sample_check
    details["checks_performed"].append("sample_size")
    if not sample_check["passed"]:
        reasons.append(FAILURE_INSUFFICIENT_SAMPLE)

    # Check 4: Study Design Match
    design_check = check_design_match(study_design, variable_types, profile, outcomes, exposures)
    details["design_match_check"] = design_check
    details["checks_performed"].append("design_match")
    if not design_check["passed"]:
        reasons.append(FAILURE_DESIGN_MISMATCH)

    # Check 5: Variable Availability (all critical variables exist)
    variable_check = check_variable_availability(
        outcomes + exposures + covariates,
        variable_types,
        profile
    )
    details["variable_availability_check"] = variable_check
    details["checks_performed"].append("variable_availability")
    if not variable_check["passed"]:
        reasons.append(FAILURE_MISSING_CRITICAL_VARIABLES)

    # Determine overall feasibility
    feasible = len(reasons) == 0

    return {
        "feasible": feasible,
        "reasons": reasons,
        "details": details
    }


# ── Individual Check Functions ───────────────────────────────────────────────

def check_control_group(
    exposure_variables: List[str],
    variable_types: Dict[str, Any],
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify that a comparison/control group exists in the data.

    For categorical/binary exposures: check for at least 2 groups with adequate size.
    For numeric exposures: check for sufficient variation.
    For datetime exposures: check for time variation (pre/post periods).

    Args:
        exposure_variables: List of exposure variable names
        variable_types: Contents of variable_types.json
        profile: Contents of profile.json

    Returns:
        Dict with "passed" (bool), "reason" (str), and "details" (dict)
    """
    if not exposure_variables:
        return {
            "passed": False,
            "reason": "No exposure variables defined",
            "details": {"exposure_variables": []}
        }

    all_columns = _collect_all_columns(variable_types)

    for exposure in exposure_variables:
        if exposure not in all_columns:
            # Exposure might be in data_acquisition_requirements - skip this check
            continue

        col_type = all_columns[exposure]["type"]
        col_profile = _get_column_profile(profile, exposure)

        if col_type in {"binary", "categorical", "categorical_nominal", "categorical_ordinal"}:
            # Check for at least 2 groups
            if col_profile:
                # Try top_values first (dict format with counts)
                top_values = col_profile.get("top_values", {})
                if isinstance(top_values, dict) and top_values:
                    num_groups = len([k for k, v in top_values.items() if v and v > 0])
                    if num_groups < 2:
                        return {
                            "passed": False,
                            "reason": f"Exposure '{exposure}' has only {num_groups} group(s); need at least 2 for comparison",
                            "details": {"exposure": exposure, "groups": num_groups, "top_values": top_values}
                        }

                    # Check group sizes
                    counts = list(top_values.values())
                    if counts:
                        min_count = min(counts)
                        if min_count < 5:
                            return {
                                "passed": False,
                                "reason": f"Exposure '{exposure}' has a group with only {min_count} observations; too small for comparison",
                                "details": {"exposure": exposure, "min_group_size": min_count}
                            }
                else:
                    # Fall back to sample_values (list format) - estimate groups from unique values
                    sample_values = col_profile.get("sample_values", [])
                    if isinstance(sample_values, list):
                        unique_values = len(set(sample_values))
                        if unique_values < 2:
                            return {
                                "passed": False,
                                "reason": f"Exposure '{exposure}' has only {unique_values} unique value(s) in sample; need at least 2 for comparison",
                                "details": {"exposure": exposure, "unique_values": unique_values}
                            }
                        # Check non_null_count for minimum group size estimate
                        non_null_count = col_profile.get("non_null_count", 0)
                        if non_null_count > 0 and non_null_count < 5:
                            return {
                                "passed": False,
                                "reason": f"Exposure '{exposure}' has only {non_null_count} non-null observations; too small for comparison",
                                "details": {"exposure": exposure, "non_null_count": non_null_count}
                            }
        elif col_type in {"numeric", "continuous"}:
            # Check for variation
            if col_profile:
                std = col_profile.get("std")
                if std is not None and std == 0:
                    return {
                        "passed": False,
                        "reason": f"Exposure '{exposure}' has no variation (std=0); cannot be used for comparison",
                        "details": {"exposure": exposure, "std": std}
                    }
        elif col_type == "datetime":
            # Check for time variation
            if col_profile:
                unique_count = col_profile.get("unique_count", 0)
                if unique_count < 2:
                    return {
                        "passed": False,
                        "reason": f"Exposure '{exposure}' has only {unique_count} unique time value(s); need at least 2",
                        "details": {"exposure": exposure, "unique_times": unique_count}
                    }

    return {
        "passed": True,
        "reason": "Adequate comparison groups exist",
        "details": {"exposure_variables": exposure_variables}
    }


def check_outcome_available(
    outcome_variables: List[str],
    variable_types: Dict[str, Any],
    profile: Dict[str, Any],
    data_acquisition_requirements: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verify that outcome variable exists or can be derived/acquired.

    An outcome is available if:
    1. It exists in variable_types.json with an allowed type, OR
    2. It's listed in data_acquisition_requirements with a valid source

    Args:
        outcome_variables: List of outcome variable names
        variable_types: Contents of variable_types.json
        profile: Contents of profile.json
        data_acquisition_requirements: List of data acquisition requirements

    Returns:
        Dict with "passed" (bool), "reason" (str), and "details" (dict)
    """
    if not outcome_variables:
        return {
            "passed": False,
            "reason": "No outcome variables defined",
            "details": {"outcome_variables": []}
        }

    all_columns = _collect_all_columns(variable_types)
    downloadable_vars = {req.get("variable", "") for req in data_acquisition_requirements}

    for outcome in outcome_variables:
        # Check if outcome is downloadable
        if outcome in downloadable_vars:
            # Verify there's a valid source column
            source_col = None
            for req in data_acquisition_requirements:
                if req.get("variable") == outcome:
                    source_col = req.get("source_column", "")
                    break

            # If source column exists in data, consider outcome available via download
            if source_col and source_col in all_columns:
                # Valid download requirement - skip further checks for this outcome
                continue
            elif source_col:
                # Source column specified but not found in data
                return {
                    "passed": False,
                    "reason": f"Outcome '{outcome}' requires download but source column '{source_col}' not found in data",
                    "details": {"outcome": outcome, "source_column": source_col, "status": "needs_download_unverified"}
                }

        # Check if outcome exists in data
        if outcome not in all_columns:
            return {
                "passed": False,
                "reason": f"Outcome '{outcome}' not found in variable_types.json and not in data_acquisition_requirements",
                "details": {"outcome": outcome, "available_vars": list(all_columns.keys())}
            }

        # Check outcome type
        col_type = all_columns[outcome]["type"]
        if col_type in FORBIDDEN_OUTCOME_TYPES:
            return {
                "passed": False,
                "reason": f"Outcome '{outcome}' has type '{col_type}' which is not allowed for outcomes",
                "details": {"outcome": outcome, "type": col_type}
            }

        # Check for analyzability (missingness, variation)
        col_profile = _get_column_profile(profile, outcome)
        if col_profile:
            miss_pct = col_profile.get("null_percentage", col_profile.get("missing_pct", 0))
            if miss_pct > 50:
                return {
                    "passed": False,
                    "reason": f"Outcome '{outcome}' has {miss_pct}% missing values; too high for analysis",
                    "details": {"outcome": outcome, "missing_pct": miss_pct}
                }

            # Check variation
            if col_type == "binary":
                top_values = col_profile.get("top_values", {})
                if isinstance(top_values, dict) and len(top_values) >= 1:
                    counts = list(top_values.values())
                    if counts:
                        total = sum(counts)
                        if total > 0:
                            max_pct = max(counts) / total
                            if max_pct > 0.99:
                                return {
                                    "passed": False,
                                    "reason": f"Outcome '{outcome}' has >99% in one category; insufficient variation",
                                    "details": {"outcome": outcome, "max_category_pct": max_pct}
                                }
            elif col_type in {"numeric", "continuous"}:
                std = col_profile.get("std")
                if std is not None and std == 0:
                    return {
                        "passed": False,
                        "reason": f"Outcome '{outcome}' has no variation (std=0); cannot be analyzed",
                        "details": {"outcome": outcome, "std": std}
                    }

    return {
        "passed": True,
        "reason": "All outcome variables are available and analyzable",
        "details": {"outcome_variables": outcome_variables}
    }


def check_sample_size(
    study_design: str,
    profile: Dict[str, Any],
    variable_types: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify sufficient sample size for the study design.

    Args:
        study_design: Study design string from candidate
        profile: Contents of profile.json
        variable_types: Contents of variable_types.json

    Returns:
        Dict with "passed" (bool), "reason" (str), and "details" (dict)
    """
    # Determine design type
    design_type = DESIGN_ECOLOGICAL  # default
    if "difference-in-differences" in study_design or "diff-in-diff" in study_design or "did" in study_design.lower():
        design_type = DESIGN_DID
    elif "longitudinal" in study_design or "panel" in study_design.lower():
        design_type = DESIGN_LONGITUDINAL
    elif "cohort" in study_design.lower():
        design_type = DESIGN_COHORT
    elif "case-control" in study_design or "case control" in study_design:
        design_type = DESIGN_CASE_CONTROL
    elif "cross-sectional" in study_design:
        design_type = DESIGN_CROSS_SECTIONAL

    # Get total sample size
    datasets = profile.get("datasets", [])
    total_n = 0
    dataset_counts = {}

    if isinstance(datasets, list):
        for ds in datasets:
            row_count = ds.get("row_count", 0)
            filename = ds.get("filename", "unknown")
            if row_count and row_count > 0:
                total_n = max(total_n, row_count)  # Use largest dataset
                dataset_counts[filename] = row_count

    # Check against minimum
    min_required = MIN_SAMPLE_SIZE.get(design_type, 20)

    if total_n < min_required:
        return {
            "passed": False,
            "reason": f"Sample size N={total_n} is below minimum {min_required} for {design_type} design",
            "details": {
                "total_n": total_n,
                "min_required": min_required,
                "design_type": design_type,
                "dataset_counts": dataset_counts
            }
        }

    return {
        "passed": True,
        "reason": f"Sample size N={total_n} meets minimum for {design_type} design",
        "details": {
            "total_n": total_n,
            "min_required": min_required,
            "design_type": design_type
        }
    }


def check_design_match(
    study_design: str,
    variable_types: Dict[str, Any],
    profile: Dict[str, Any],
    outcome_variables: List[str],
    exposure_variables: List[str]
) -> Dict[str, Any]:
    """
    Verify that the required data structure exists for the study design.

    Args:
        study_design: Study design string from candidate
        variable_types: Contents of variable_types.json
        profile: Contents of profile.json
        outcome_variables: List of outcome variable names
        exposure_variables: List of exposure variable names

    Returns:
        Dict with "passed" (bool), "reason" (str), and "details" (dict)
    """
    design_lower = study_design.lower()

    # Check for time series requirements
    if any(kw in design_lower for kw in ["difference-in-differences", "diff-in-diff", "did", "longitudinal", "time series", "interrupted time"]):
        # Need time variable and multiple time points
        has_time_variable = False
        has_multiple_time_points = False

        all_columns = _collect_all_columns(variable_types)

        for col_name, col_info in all_columns.items():
            if col_info["type"] == "datetime":
                has_time_variable = True
                col_profile = _get_column_profile(profile, col_name)
                if col_profile:
                    unique_count = col_profile.get("unique_count", 0)
                    if unique_count > 1:
                        has_multiple_time_points = True
                        break

        if not has_time_variable:
            return {
                "passed": False,
                "reason": f"Study design '{study_design}' requires time/longitudinal data but no datetime variable found",
                "details": {"required": "datetime variable", "design": study_design}
            }

        if not has_multiple_time_points:
            return {
                "passed": False,
                "reason": f"Study design '{study_design}' requires multiple time points but only 1 found",
                "details": {"required": "multiple time points", "design": study_design}
            }

    # Check for panel data requirements (multiple entities observed over time)
    if "panel" in design_lower or "longitudinal" in design_lower or "did" in design_lower.lower():
        # Need identifier for entities + time variable
        has_id_variable = False
        has_time_variable = False

        all_columns = _collect_all_columns(variable_types)

        for col_name, col_info in all_columns.items():
            if col_info["type"] == "identifier":
                # Check if it has multiple values (not just one entity)
                col_profile = _get_column_profile(profile, col_name)
                if col_profile:
                    unique_count = col_profile.get("unique_count", 0)
                    if unique_count > 1:
                        has_id_variable = True
            elif col_info["type"] == "datetime":
                has_time_variable = True

        if not has_id_variable and not has_time_variable:
            return {
                "passed": False,
                "reason": f"Study design '{study_design}' requires panel data (entity + time identifiers)",
                "details": {"required": "entity identifier + time variable", "design": study_design}
            }

    # Check for ecological study requirements
    if "ecological" in design_lower:
        # Check that data is aggregate-level, not individual
        all_columns = _collect_all_columns(variable_types)
        has_id_columns = any(col_info["type"] == "identifier" for col_info in all_columns.values())

        # This is more of a warning than a hard failure
        if has_id_columns:
            # Could be individual data - check if it's actually aggregated
            pass  # Ecological studies can still have identifiers (state, region)

    return {
        "passed": True,
        "reason": f"Data structure supports '{study_design}' design",
        "details": {"design": study_design}
    }


def check_variable_availability(
    required_variables: List[str],
    variable_types: Dict[str, Any],
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify that all critical variables exist in the data.

    Args:
        required_variables: List of all variable names used in the question
        variable_types: Contents of variable_types.json
        profile: Contents of profile.json

    Returns:
        Dict with "passed" (bool), "reason" (str), and "details" (dict)
    """
    all_columns = _collect_all_columns(variable_types)
    missing_variables = []
    found_variables = []

    for var in required_variables:
        if var in all_columns:
            found_variables.append(var)
        else:
            # Variable might be derived or acquired - check if it's in excluded_variables
            # which is fine (it means we know about it and chose not to use it)
            missing_variables.append(var)

    # If too many variables are missing, that's a problem
    # But some might be legitimately excluded or derived

    # Calculate what percentage of required variables exist
    if len(required_variables) > 0:
        exist_pct = len(found_variables) / len(required_variables)
        if exist_pct < 0.5:
            return {
                "passed": False,
                "reason": f"Less than 50% of required variables found in data ({len(found_variables)}/{len(required_variables)})",
                "details": {
                    "found": found_variables,
                    "missing": missing_variables,
                    "total_required": len(required_variables)
                }
            }

    return {
        "passed": True,
        "reason": f"Critical variables are available ({len(found_variables)}/{len(required_variables)} found)",
        "details": {
            "found": found_variables,
            "missing": missing_variables,
            "total_required": len(required_variables)
        }
    }


# ── Helper Functions ─────────────────────────────────────────────────────────

def _collect_all_columns(variable_types: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Collect all columns from variable_types.json into a flat dict.

    Handles both schema formats:
    1. Current: {datasets: [{filename: ds_name, variables: {col_name: {type: ...}}}]}
    2. Legacy: {dataset_name: {col_name: {type: ...}}}

    Returns:
        Dict mapping column_name to {type: semantic_type, datasets: [ds_names]}
    """
    cols: Dict[str, Dict[str, Any]] = {}

    # Handle current schema (datasets array format)
    if "datasets" in variable_types and isinstance(variable_types["datasets"], list):
        for ds_info in variable_types["datasets"]:
            ds_name = ds_info.get("filename", "unknown")
            ds_vars = ds_info.get("variables", {})
            for col_name, col_info in ds_vars.items():
                col_type = col_info if isinstance(col_info, str) else col_info.get("type", "unknown")
                if col_name not in cols:
                    cols[col_name] = {"type": col_type, "datasets": []}
                cols[col_name]["datasets"].append(ds_name)
        return cols

    # Handle legacy schema (flat dict of datasets)
    for ds_name, ds_cols in variable_types.items():
        if ds_name in ("total_datasets", "generated_at"):
            continue
        for col_name, col_type in ds_cols.items():
            if isinstance(col_type, dict):
                col_type = col_type.get("type", "unknown")
            if col_name not in cols:
                cols[col_name] = {"type": col_type, "datasets": []}
            cols[col_name]["datasets"].append(ds_name)

    return cols


def _get_column_profile(profile: Dict[str, Any], col_name: str) -> Optional[Dict[str, Any]]:
    """
    Find the profile stats for a column across all datasets.

    Handles both schema formats:
    1. Current: {datasets: [{filename: ds_name, columns: [{name: col_name, ...}]}]}
    2. Legacy: {datasets: {ds_name: {columns: {col_name: {...}}}}}
    """
    datasets = profile.get("datasets", [])

    # Handle current schema (array of dataset objects)
    if isinstance(datasets, list):
        for ds_data in datasets:
            columns = ds_data.get("columns", [])
            if isinstance(columns, list):
                for col_info in columns:
                    if col_info.get("name") == col_name:
                        return col_info
            elif isinstance(columns, dict) and col_name in columns:
                return columns[col_name]
        return None

    # Handle legacy schema (dict of datasets)
    for ds_data in datasets.values():
        if col_name in ds_data.get("columns", {}):
            return ds_data["columns"][col_name]
    return None


def _get_role_values(
    variable_roles: Dict[str, Any],
    role_name: str,
    legacy_name: Optional[str] = None
) -> List[str]:
    """
    Get values from variable_roles dict, handling both new and legacy formats.

    Args:
        variable_roles: The variable_roles dict from a candidate
        role_name: New format key (e.g., "outcome_variables")
        legacy_name: Legacy format key (e.g., "outcome"), or None

    Returns:
        List of variable names for the role
    """
    # Try new format first
    if role_name in variable_roles:
        val = variable_roles[role_name]
        return val if isinstance(val, list) else [val]
    # Try legacy format
    if legacy_name and legacy_name in variable_roles:
        val = variable_roles[legacy_name]
        return val if isinstance(val, list) else [val]
    return []


# ── Batch Processing ─────────────────────────────────────────────────────────

def validate_all_candidates(
    candidates: List[Dict[str, Any]],
    variable_types: Dict[str, Any],
    profile: Dict[str, Any],
    data_acquisition_requirements: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Validate all candidate questions and return annotated results.

    Args:
        candidates: List of candidate question dicts
        variable_types: Contents of variable_types.json
        profile: Contents of profile.json
        data_acquisition_requirements: Optional list of data acquisition requirements

    Returns:
        List of candidate dicts with added feasibility fields:
        - status: "feasible" or "infeasible"
        - infeasibility_reason: comma-separated failure modes (if infeasible)
        - feasibility_details: Full validation result dict
    """
    results = []

    for candidate in candidates:
        validation_result = validate_candidate_feasibility(
            candidate,
            variable_types,
            profile,
            data_acquisition_requirements or []
        )

        # Annotate the candidate with feasibility status
        annotated = candidate.copy()
        if validation_result["feasible"]:
            annotated["status"] = "feasible"
            # Clear any previous infeasibility_reason
            if "infeasibility_reason" in annotated:
                del annotated["infeasibility_reason"]
        else:
            annotated["status"] = "infeasible"
            annotated["infeasibility_reason"] = ",".join(validation_result["reasons"])

        annotated["feasibility_details"] = validation_result["details"]
        results.append(annotated)

    return results


# ── Command Line Interface ───────────────────────────────────────────────────

def main():
    """CLI for validating research questions."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python feasibility_validator.py <output_folder>")
        print("Validates candidates in research_questions.json")
        sys.exit(2)

    output_folder = sys.argv[1]

    # Load files
    rq_path = os.path.join(output_folder, "2_research_question", "research_questions.json")
    profile_path = os.path.join(output_folder, "1_data_profile", "profile.json")
    vt_path = os.path.join(output_folder, "1_data_profile", "variable_types.json")

    for path in [rq_path, profile_path, vt_path]:
        if not os.path.exists(path):
            print(f"FATAL: {path} not found")
            sys.exit(2)

    with open(rq_path) as f:
        rq_data = json.load(f)
    with open(profile_path) as f:
        profile = json.load(f)
    with open(vt_path) as f:
        variable_types = json.load(f)

    candidates = rq_data.get("candidate_questions", [])
    data_acq_reqs = rq_data.get("data_acquisition_requirements", [])

    # Validate all candidates
    results = validate_all_candidates(
        candidates,
        variable_types,
        profile,
        data_acq_reqs
    )

    # Print summary
    print("=" * 60)
    print("FEASIBILITY VALIDATION REPORT")
    print("=" * 60)

    feasible_count = sum(1 for r in results if r.get("status") == "feasible")
    infeasible_count = len(results) - feasible_count

    print(f"\nTotal candidates: {len(results)}")
    print(f"Feasible: {feasible_count}")
    print(f"Infeasible: {infeasible_count}")
    print()

    for result in results:
        candidate_id = result.get("candidate_id", "?")
        status = result.get("status", "unknown")
        question = result.get("question", "")[:80]

        status_symbol = "✓" if status == "feasible" else "✗"
        print(f"{status_symbol} {candidate_id}: {status}")

        if status == "infeasible":
            reasons = result.get("infeasibility_reason", "")
            print(f"   Reasons: {reasons}")

        print(f"   Question: {question}...")
        print()

    # Exit with error if no feasible candidates
    if feasible_count == 0:
        print("ERROR: No feasible candidates found!")
        sys.exit(1)


if __name__ == "__main__":
    main()
