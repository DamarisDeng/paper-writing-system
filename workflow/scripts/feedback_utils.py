"""
feedback_utils.py — Feedback loop utilities for the research question scoring pipeline.

Detects structural analysis failures (non-convergence, violated assumptions,
insufficient power) and provides signals to the score-and-rank stage for
re-ranking candidate questions.

Also manages the decision_log.json audit trail.

NOTE: With the new feasibility filtering in Stage 2 (generate-research-questions),
candidates with data feasibility issues (no control group, missing outcome data,
insufficient sample) are rejected BEFORE expensive literature searches in Stage 3.
This means `data_not_feasible` failures in Stage 5 (statistical-analysis) should be
much rarer. The feedback loop now primarily handles runtime failures (non-convergence,
separation, violated assumptions) that cannot be detected during initial validation.

Usage:
    from feedback_utils import build_feedback_signal, update_decision_log, read_decision_log
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


# ── Feedback Signal Detection ──────────────────────────────────────────────

# Failure patterns checked in analysis_results.json
FAILURE_CHECKS = {
    "data_not_feasible": {
        "description": "Analysis not feasible with available data (missing control group, outcome data, or required structure)",
        "severity": "critical",
    },
    "non_convergence": {
        "description": "Model failed to converge",
        "severity": "critical",
    },
    "complete_separation": {
        "description": "Complete or quasi-complete separation detected in logistic model",
        "severity": "critical",
    },
    "violated_assumptions": {
        "description": "Key model assumptions failed checks",
        "severity": "major",
    },
    "insufficient_n": {
        "description": "Analytic sample too small for the selected method",
        "severity": "major",
    },
    "extreme_effects": {
        "description": "Effect sizes are implausibly large (OR > 50 or < 0.02)",
        "severity": "major",
    },
}


def build_feedback_signal(output_folder: str) -> Optional[Dict[str, Any]]:
    """
    Inspect analysis_results.json for structural failures that indicate
    the research question is not viable with the available data.

    NOTE: With Stage 2 feasibility filtering, `data_not_feasible` failures
    should be rare. This check primarily catches runtime issues that couldn't
    be detected during initial validation (e.g., model non-convergence during
    fitting, data quality issues that only emerge during analysis).

    Args:
        output_folder: Base output directory (e.g., "exam_paper")

    Returns:
        A feedback signal dict if structural issues are found, None if
        analysis looks acceptable. The signal contains:
        - issues: list of {check, description, severity, details}
        - failed_candidate_id: ID of the candidate that was tried
        - recommendation: "retry_next_candidate" or "proceed_with_caution"
    """
    analysis_path = os.path.join(output_folder, "3_analysis", "analysis_results.json")

    if not os.path.exists(analysis_path):
        return {
            "issues": [{"check": "missing_results", "description": "analysis_results.json not found",
                        "severity": "critical", "details": "Analysis stage may have failed entirely"}],
            "failed_candidate_id": _get_current_candidate_id(output_folder),
            "recommendation": "retry_next_candidate"
        }

    try:
        with open(analysis_path, "r") as f:
            results = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "issues": [{"check": "invalid_json", "description": "analysis_results.json is invalid",
                        "severity": "critical", "details": "File exists but cannot be parsed"}],
            "failed_candidate_id": _get_current_candidate_id(output_folder),
            "recommendation": "retry_next_candidate"
        }

    issues = []

    # Check 0: Data feasibility (NEW - checks if analysis is fundamentally not feasible)
    primary = results.get("primary_analysis", {})
    feasibility_report = results.get("feasibility_report", {})

    # Check if primary analysis status is NOT_EXECUTABLE
    if primary.get("status") == "NOT_EXECUTABLE":
        error_info = primary.get("error", {})
        issues.append({
            "check": "data_not_feasible",
            "description": FAILURE_CHECKS["data_not_feasible"]["description"],
            "severity": "critical",
            "details": error_info.get("details", "Analysis not executable") if isinstance(error_info, dict) else str(error_info)
        })

    # Check if feasibility report says can_proceed is false
    if feasibility_report.get("can_proceed") is False:
        blocking_issues = feasibility_report.get("blocking_issues", [])
        issues.append({
            "check": "data_not_feasible",
            "description": FAILURE_CHECKS["data_not_feasible"]["description"],
            "severity": "critical",
            "details": f"Blocking issues: {', '.join(blocking_issues) if blocking_issues else 'Data limitations prevent analysis'}"
        })

    # If we found critical data feasibility issues, return immediately
    if any(i["severity"] == "critical" and i["check"] == "data_not_feasible" for i in issues):
        return {
            "issues": issues,
            "failed_candidate_id": _get_current_candidate_id(output_folder),
            "recommendation": "retry_next_candidate"
        }

    # Check 1: Non-convergence
    primary = results.get("primary_analysis", {})
    model_fit = primary.get("model_fit", {})
    if model_fit.get("converged") is False:
        issues.append({
            "check": "non_convergence",
            "description": FAILURE_CHECKS["non_convergence"]["description"],
            "severity": "critical",
            "details": model_fit.get("convergence_message", "Model did not converge")
        })

    # Check for convergence warnings in notes
    notes = primary.get("notes", "")
    if isinstance(notes, str) and any(kw in notes.lower() for kw in
                                       ["did not converge", "convergence", "singular", "failed to converge"]):
        issues.append({
            "check": "non_convergence",
            "description": FAILURE_CHECKS["non_convergence"]["description"],
            "severity": "critical",
            "details": notes
        })

    # Check 2: Complete separation
    assumption_checks = primary.get("assumption_checks", {})
    separation_check = assumption_checks.get("complete_separation", {})
    if separation_check.get("passed") is False:
        issues.append({
            "check": "complete_separation",
            "description": FAILURE_CHECKS["complete_separation"]["description"],
            "severity": "critical",
            "details": separation_check.get("details", "")
        })

    # Check 3: Violated assumptions (count critical failures)
    failed_assumptions = []
    for check_name, check_result in assumption_checks.items():
        if isinstance(check_result, dict) and check_result.get("passed") is False:
            failed_assumptions.append(check_name)

    if len(failed_assumptions) >= 3:
        issues.append({
            "check": "violated_assumptions",
            "description": FAILURE_CHECKS["violated_assumptions"]["description"],
            "severity": "major",
            "details": f"Failed checks: {', '.join(failed_assumptions)}"
        })

    # Check 4: Insufficient N
    analytic_sample = results.get("analytic_sample", {})
    total_n = analytic_sample.get("total_n", 0)
    exposure_groups = analytic_sample.get("exposure_groups", {})
    min_group_n = min((g.get("n", 0) for g in exposure_groups.values()), default=0) if exposure_groups else 0

    if total_n > 0 and total_n < 20:
        issues.append({
            "check": "insufficient_n",
            "description": FAILURE_CHECKS["insufficient_n"]["description"],
            "severity": "major",
            "details": f"Total N={total_n}, minimum group N={min_group_n}"
        })
    elif min_group_n > 0 and min_group_n < 5:
        issues.append({
            "check": "insufficient_n",
            "description": "A comparison group has fewer than 5 observations",
            "severity": "major",
            "details": f"Minimum group N={min_group_n}"
        })

    # Check 5: Extreme effect sizes
    effect = primary.get("results", {}).get("exposure_effect", {}).get("raw", {})
    estimate = effect.get("estimate")
    if estimate is not None:
        try:
            est = float(estimate)
            method = primary.get("method", "").lower()
            # For logistic/Cox models, check OR/HR bounds
            if any(kw in method for kw in ["logistic", "cox", "poisson", "negbin"]):
                if est > 50 or (est > 0 and est < 0.02):
                    issues.append({
                        "check": "extreme_effects",
                        "description": FAILURE_CHECKS["extreme_effects"]["description"],
                        "severity": "major",
                        "details": f"Estimate={est}, method={method}"
                    })
        except (TypeError, ValueError):
            pass

    # Determine recommendation
    if not issues:
        return None

    critical_count = sum(1 for i in issues if i["severity"] == "critical")
    if critical_count > 0:
        recommendation = "retry_next_candidate"
    else:
        recommendation = "proceed_with_caution"

    return {
        "issues": issues,
        "failed_candidate_id": _get_current_candidate_id(output_folder),
        "recommendation": recommendation
    }


def _get_current_candidate_id(output_folder: str) -> Optional[str]:
    """Read the currently selected candidate ID from ranked_questions.json."""
    ranked_path = os.path.join(output_folder, "2_scoring", "ranked_questions.json")
    if os.path.exists(ranked_path):
        try:
            with open(ranked_path, "r") as f:
                ranked = json.load(f)
            return ranked.get("selection_metadata", {}).get("selected_candidate_id")
        except (json.JSONDecodeError, IOError):
            pass
    return None


# ── Decision Log ───────────────────────────────────────────────────────────

def update_decision_log(output_folder: str, entry: Dict[str, Any]) -> None:
    """
    Append an entry to decision_log.json.

    Each entry records a scoring/selection decision for audit trail purposes.
    The log is append-only.

    Args:
        output_folder: Base output directory
        entry: Decision entry dict with cycle, candidates_scored, selected, etc.
    """
    log_path = os.path.join(output_folder, "decision_log.json")
    log = read_decision_log(output_folder)

    # Add timestamp if not present
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    log.append(entry)

    os.makedirs(output_folder, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    print(f"[decision_log] Entry added: cycle {entry.get('cycle', '?')}, selected {entry.get('selected', '?')}")


def read_decision_log(output_folder: str) -> List[Dict[str, Any]]:
    """
    Read the decision log. Returns empty list if file does not exist.

    Args:
        output_folder: Base output directory

    Returns:
        List of decision entries
    """
    log_path = os.path.join(output_folder, "decision_log.json")
    if not os.path.exists(log_path):
        return []

    try:
        with open(log_path, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []
