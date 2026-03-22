"""
feedback_utils.py — Feedback loop utilities for the research question scoring pipeline.

Detects structural analysis failures (non-convergence, violated assumptions,
insufficient power) and provides signals to the score-and-rank stage for
re-ranking candidate questions.

Also manages the decision_log.json audit trail.

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
