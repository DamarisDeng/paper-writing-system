#!/usr/bin/env python3
"""
Validate research_questions.json against profile.json and variable_types.json.

Usage:
    python validate_research_questions.py <output_folder>

Example:
    python validate_research_questions.py exam_paper

Exit codes:
    0 — all checks pass
    1 — validation errors found
    2 — file not found or invalid JSON
"""

import json
import sys
import os

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def collect_all_columns(variable_types: dict) -> dict[str, dict]:
    """Return {col_name: {datasets: [ds1, ds2], type: semantic_type}} for every column."""
    cols: dict[str, dict] = {}
    for ds_name, ds_cols in variable_types.items():
        for col_name, col_type in ds_cols.items():
            if col_name not in cols:
                cols[col_name] = {"datasets": [], "type": col_type}
            cols[col_name]["datasets"].append(ds_name)
    return cols


def get_column_profile(profile: dict, col_name: str) -> dict | None:
    """Find the profile stats for a column across all datasets."""
    for ds_name, ds_data in profile.get("datasets", {}).items():
        if col_name in ds_data.get("columns", {}):
            return ds_data["columns"][col_name]
    return None

# ---------------------------------------------------------------------------
# Validation checks — each returns a list of (severity, message) tuples
# ---------------------------------------------------------------------------

def check_schema(rq: dict) -> list[tuple[str, str]]:
    """Verify all required fields and types are present."""
    issues = []

    # primary_question
    pq = rq.get("primary_question")
    if not isinstance(pq, dict):
        issues.append(("ERROR", "primary_question is missing or not an object"))
        return issues  # can't continue

    required_pq = ["question", "population", "exposure_or_intervention",
                    "comparator", "outcome", "study_design", "rationale"]
    for field in required_pq:
        val = pq.get(field)
        if not val or not str(val).strip():
            issues.append(("ERROR", f"primary_question.{field} is missing or empty"))

    # secondary_questions
    sqs = rq.get("secondary_questions")
    if not isinstance(sqs, list) or len(sqs) == 0:
        issues.append(("ERROR", "secondary_questions is missing or empty"))
    else:
        if len(sqs) < 2:
            issues.append(("WARN", f"Only {len(sqs)} secondary question(s); expected 2-3"))
        for i, sq in enumerate(sqs):
            for field in ["question", "variables_involved", "analysis_type", "rationale"]:
                if field not in sq:
                    issues.append(("ERROR", f"secondary_questions[{i}] missing field: {field}"))
            if not isinstance(sq.get("variables_involved"), list):
                issues.append(("ERROR", f"secondary_questions[{i}].variables_involved must be a list"))

    # data_acquisition_requirements (optional)
    dar = rq.get("data_acquisition_requirements")
    if dar is not None:
        if not isinstance(dar, list):
            issues.append(("ERROR", "data_acquisition_requirements must be a list"))
        else:
            for i, item in enumerate(dar):
                for field in ["variable", "source_column", "target_file", "action"]:
                    if field not in item:
                        issues.append(("ERROR", f"data_acquisition_requirements[{i}] missing field: {field}"))
                # Check target_file path format
                target = item.get("target_file", "")
                if target and "/2_research_question_and_analysis/downloaded/" not in target:
                    issues.append(("WARN", f"data_acquisition_requirements[{i}].target_file should use <output_folder>/2_research_question_and_analysis/downloaded/ convention"))

    # feasibility_assessment
    fa = rq.get("feasibility_assessment")
    if not isinstance(fa, dict):
        issues.append(("ERROR", "feasibility_assessment is missing or not an object"))
    else:
        for section in ["strengths", "limitations", "required_assumptions"]:
            items = fa.get(section)
            if not isinstance(items, list) or len(items) == 0:
                issues.append(("ERROR", f"feasibility_assessment.{section} is missing or empty"))
        if isinstance(fa.get("limitations"), list) and len(fa["limitations"]) < 2:
            issues.append(("WARN", f"Only {len(fa['limitations'])} limitation(s); need >= 2 with specifics"))

    # variable_roles
    vr = rq.get("variable_roles")
    if not isinstance(vr, dict):
        issues.append(("ERROR", "variable_roles is missing or not an object"))
    else:
        for role in ["outcome_variables", "exposure_variables", "covariates",
                      "stratification_variables", "excluded_variables"]:
            if role not in vr:
                issues.append(("ERROR", f"variable_roles.{role} is missing"))
        if not isinstance(vr.get("excluded_variables"), dict):
            issues.append(("ERROR", "variable_roles.excluded_variables must be an object {col: reason}"))

    return issues


def check_column_coverage(rq: dict, all_columns: dict[str, dict]) -> list[tuple[str, str]]:
    """Every column in variable_types.json must appear in exactly one role. Columns in roles but not in data are allowed if they're downloadable."""
    issues = []
    vr = rq.get("variable_roles", {})

    # Collect downloadable variables
    downloadable = set()
    for req in rq.get("data_acquisition_requirements", []):
        downloadable.add(req.get("variable", ""))

    assigned: dict[str, str] = {}  # col -> role
    list_roles = ["outcome_variables", "exposure_variables", "covariates", "stratification_variables"]
    for role in list_roles:
        for col in vr.get(role, []):
            if col in assigned:
                issues.append(("ERROR", f'"{col}" assigned to both {assigned[col]} and {role}'))
            assigned[col] = role

    for col in vr.get("excluded_variables", {}):
        if col in assigned:
            issues.append(("ERROR", f'"{col}" assigned to both {assigned[col]} and excluded_variables'))
        assigned[col] = "excluded_variables"

    # Missing from roles
    for col in all_columns:
        if col not in assigned:
            issues.append(("ERROR", f'Column "{col}" exists in variable_types.json but is not assigned any role'))

    # Extra columns (in roles but not in data) — allowed if downloadable
    for col in assigned:
        if col not in all_columns and col not in downloadable:
            issues.append(("ERROR", f'Column "{col}" is in variable_roles but does not exist in variable_types.json'))

    return issues


def check_column_references(rq: dict, all_columns: dict[str, dict]) -> list[tuple[str, str]]:
    """All column names referenced in secondary_questions.variables_involved must exist."""
    issues = []
    for i, sq in enumerate(rq.get("secondary_questions", [])):
        for v in sq.get("variables_involved", []):
            if v not in all_columns:
                issues.append(("ERROR", f'secondary_questions[{i}].variables_involved references non-existent column: "{v}"'))
    return issues


def check_identifier_roles(rq: dict, all_columns: dict[str, dict]) -> list[tuple[str, str]]:
    """Identifiers should not be classified as outcome or exposure variables."""
    issues = []
    vr = rq.get("variable_roles", {})

    for col in vr.get("outcome_variables", []):
        if col in all_columns and all_columns[col]["type"] == "identifier":
            issues.append(("ERROR", f'Outcome variable "{col}" is typed as identifier in variable_types.json — identifiers are join keys, not outcomes'))

    for col in vr.get("exposure_variables", []):
        if col in all_columns and all_columns[col]["type"] == "identifier":
            issues.append(("ERROR", f'Exposure variable "{col}" is typed as identifier in variable_types.json — identifiers are join keys, not exposures'))

    return issues


def check_outcome_is_analyzable(rq: dict, all_columns: dict[str, dict], profile: dict) -> list[tuple[str, str]]:
    """Outcome variables must be numeric or binary with analyzable data, OR listed in data_acquisition_requirements for download."""
    issues = []
    vr = rq.get("variable_roles", {})
    allowed_outcome_types = {"numeric", "binary"}

    # Collect outcomes that will be downloaded
    downloadable_outcomes = set()
    for req in rq.get("data_acquisition_requirements", []):
        var = req.get("variable", "")
        downloadable_outcomes.add(var)

    for col in vr.get("outcome_variables", []):
        if col in downloadable_outcomes:
            # This outcome will be downloaded from Archive Links — skip type/missingness checks
            # But verify source_column exists in data
            for req in rq.get("data_acquisition_requirements", []):
                if req.get("variable") == col:
                    src = req.get("source_column", "")
                    if src and src not in all_columns and "archive" not in src.lower():
                        issues.append(("WARN", f'data_acquisition_requirements for "{col}" references source_column "{src}" which is not in the data — this may be intentional for URL columns'))
            continue

        if col not in all_columns:
            continue  # caught by coverage check

        col_type = all_columns[col]["type"]
        if col_type not in allowed_outcome_types:
            issues.append(("ERROR",
                f'Outcome variable "{col}" has type "{col_type}" — outcomes must be numeric or binary'))

        # Check missingness
        col_profile = get_column_profile(profile, col)
        if col_profile:
            miss_pct = col_profile.get("missing_pct", 0)
            if miss_pct > 50:
                issues.append(("ERROR",
                    f'Outcome variable "{col}" has {miss_pct}% missing values — too high for a primary outcome'))
            elif miss_pct > 30:
                issues.append(("WARN",
                    f'Outcome variable "{col}" has {miss_pct}% missing values — risky for a primary outcome'))

    return issues


def check_exposure_is_analyzable(rq: dict, all_columns: dict[str, dict], profile: dict) -> list[tuple[str, str]]:
    """Exposure variables must be categorical, binary, numeric, or datetime — not text or identifier."""
    issues = []
    vr = rq.get("variable_roles", {})
    allowed_exposure_types = {"categorical", "binary", "numeric", "datetime"}

    for col in vr.get("exposure_variables", []):
        if col not in all_columns:
            continue

        col_type = all_columns[col]["type"]
        if col_type not in allowed_exposure_types:
            issues.append(("ERROR",
                f'Exposure variable "{col}" has type "{col_type}" — exposures must be categorical, binary, numeric, or datetime'))

        col_profile = get_column_profile(profile, col)
        if col_profile:
            miss_pct = col_profile.get("missing_pct", 0)
            if miss_pct > 50:
                issues.append(("ERROR",
                    f'Exposure variable "{col}" has {miss_pct}% missing values — too high for a primary exposure'))

    return issues


def check_outcome_not_denominator(rq: dict, profile: dict) -> list[tuple[str, str]]:
    """Heuristic: outcome variables whose names suggest they are population counts or denominators are likely misclassified."""
    issues = []
    vr = rq.get("variable_roles", {})
    denominator_keywords = ["population", "estimate", "denominator", "census", "count of total",
                            "n_total", "sample_size", "base"]

    for col in vr.get("outcome_variables", []):
        col_lower = col.lower()
        for kw in denominator_keywords:
            if kw in col_lower:
                issues.append(("ERROR",
                    f'Outcome variable "{col}" looks like a population denominator (matched keyword "{kw}") — '
                    f'denominators are covariates for rate calculation, not outcomes'))
                break

    return issues


def check_question_specificity(rq: dict, all_columns: dict[str, dict]) -> list[tuple[str, str]]:
    """Primary question fields should reference at least some actual column names."""
    issues = []
    pq = rq.get("primary_question", {})

    # Combine all text fields from primary question
    pq_text = " ".join(str(v) for v in pq.values())

    # Count how many actual column names appear
    referenced = [col for col in all_columns if col in pq_text]
    if len(referenced) == 0:
        issues.append(("WARN", "Primary question text does not reference any actual column names from the data — may be too vague for downstream use"))

    return issues


def check_derived_variables(rq: dict, all_columns: dict[str, dict]) -> list[tuple[str, str]]:
    """If derived_variables are present, validate their structure."""
    issues = []
    dv = rq.get("variable_roles", {}).get("derived_variables")
    if dv is None:
        return issues  # optional field

    if not isinstance(dv, list):
        issues.append(("ERROR", "variable_roles.derived_variables must be a list"))
        return issues

    for i, item in enumerate(dv):
        for field in ["name", "derivation", "source_columns"]:
            if field not in item:
                issues.append(("ERROR", f"derived_variables[{i}] missing field: {field}"))
        # Check source columns exist
        for src in item.get("source_columns", []):
            if src not in all_columns:
                issues.append(("ERROR", f'derived_variables[{i}].source_columns references non-existent column: "{src}"'))

    return issues


def check_data_acquisition(rq: dict, all_columns: dict[str, dict]) -> list[tuple[str, str]]:
    """Validate data_acquisition_requirements if present."""
    issues = []
    dar = rq.get("data_acquisition_requirements")
    if not dar:
        return issues  # optional field

    if not isinstance(dar, list):
        return [("ERROR", "data_acquisition_requirements must be a list")]  # already caught in schema

    # Check that source_columns exist in data
    for i, req in enumerate(dar):
        src = req.get("source_column", "")
        if src and src not in all_columns:
            # Allow URL-like columns that may be referenced differently
            if not any(src in col or col in src for col in all_columns):
                issues.append(("WARN",
                    f'data_acquisition_requirements[{i}].source_column "{src}" not found in data columns — verify this is correct'))

        # Check that variables listed here are actually used as outcomes or exposures
        var = req.get("variable", "")
        vr = rq.get("variable_roles", {})
        outcomes = vr.get("outcome_variables", [])
        exposures = vr.get("exposure_variables", [])
        if var and var not in outcomes and var not in exposures:
            issues.append(("WARN",
                f'data_acquisition_requirements[{i}].variable "{var}" is not listed in outcome_variables or exposure_variables'))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_research_questions.py <output_folder>")
        sys.exit(2)

    output_folder = sys.argv[1]

    # Load files
    paths = {
        "research_questions": os.path.join(output_folder, "2_research_question_and_analysis", "research_questions.json"),
        "profile": os.path.join(output_folder, "1_data_profile", "profile.json"),
        "variable_types": os.path.join(output_folder, "1_data_profile", "variable_types.json"),
    }

    for name, path in paths.items():
        if not os.path.exists(path):
            print(f"FATAL: {path} not found")
            sys.exit(2)

    try:
        rq = load_json(paths["research_questions"])
        profile = load_json(paths["profile"])
        variable_types = load_json(paths["variable_types"])
    except json.JSONDecodeError as e:
        print(f"FATAL: Invalid JSON — {e}")
        sys.exit(2)

    all_columns = collect_all_columns(variable_types)

    # Run all checks
    all_issues: list[tuple[str, str]] = []
    checks = [
        ("Schema completeness", check_schema(rq)),
        ("Column coverage", check_column_coverage(rq, all_columns)),
        ("Column references", check_column_references(rq, all_columns)),
        ("Identifier role check", check_identifier_roles(rq, all_columns)),
        ("Outcome analyzability", check_outcome_is_analyzable(rq, all_columns, profile)),
        ("Exposure analyzability", check_exposure_is_analyzable(rq, all_columns, profile)),
        ("Outcome not denominator", check_outcome_not_denominator(rq, profile)),
        ("Question specificity", check_question_specificity(rq, all_columns)),
        ("Data acquisition requirements", check_data_acquisition(rq, all_columns)),
        ("Derived variables", check_derived_variables(rq, all_columns)),
    ]

    print("=" * 60)
    print("RESEARCH QUESTIONS VALIDATION REPORT")
    print("=" * 60)
    print(f"Output folder: {output_folder}")
    print(f"Columns in data: {len(all_columns)}")
    print(f"Datasets: {len(variable_types)}")
    print()

    total_errors = 0
    total_warnings = 0

    for check_name, issues in checks:
        errors = [i for i in issues if i[0] == "ERROR"]
        warnings = [i for i in issues if i[0] == "WARN"]
        total_errors += len(errors)
        total_warnings += len(warnings)

        if issues:
            status = "FAIL" if errors else "WARN"
            print(f"[{status}] {check_name}")
            for severity, msg in issues:
                print(f"  {severity}: {msg}")
        else:
            print(f"[PASS] {check_name}")

        all_issues.extend(issues)

    print()
    print("-" * 60)
    print(f"TOTAL: {total_errors} error(s), {total_warnings} warning(s)")

    if total_errors > 0:
        print("RESULT: FAIL — fix errors before proceeding to study design")
        sys.exit(1)
    elif total_warnings > 0:
        print("RESULT: PASS with warnings — review before proceeding")
        sys.exit(0)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
