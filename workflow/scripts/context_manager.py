"""
context_manager.py — Context management system for the paper writing pipeline.

Provides a two-component system:
1. Context Bundle: Layered semantic decision store that propagates high-value reasoning
2. Forget Mechanism: Selective context pruning with checkpoints

This module reduces token overflow during pipeline execution by:
- Capturing semantic decisions (why) rather than just raw outputs (what)
- Enabling pruning of verbose intermediate files after checkpoints
- Providing a compressed context view for downstream stages

Usage:
    from context_manager import (
        create_context_bundle,
        add_layer,
        get_context_for_stage,
        prune_stage_outputs,
        can_prune_stage,
        get_context_bundle
    )

    # Initialize at pipeline start
    bundle = create_context_bundle(output_folder)

    # After each stage completes
    add_layer(output_folder, stage_name, context_decisions)

    # Query relevant context for a stage
    context = get_context_for_stage(output_folder, current_stage_name)

    # Prune outputs after checkpoint (if safe)
    if can_prune_stage(output_folder, stage_name):
        prune_stage_outputs(output_folder, stage_name, mode="aggressive")
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set


# ── Constants ──────────────────────────────────────────────────────────────

CONTEXT_BUNDLE_FILE = "context_bundle.json"
CONTEXT_CONFIG_FILE = "context_config.json"

# Stage ordering for dependency tracking
STAGE_ORDER = [
    "load_and_profile",
    "generate_research_questions",
    "score_and_rank",
    "acquire_data",
    "statistical_analysis",
    "generate_figures",
    "literature_review",
    "write_paper",
    "compile_and_review"
]

# Mapping of stage to layer key
STAGE_TO_LAYER = {
    "load_and_profile": "layer_1_load_and_profile",
    "generate_research_questions": "layer_2_research_questions",
    "score_and_rank": "layer_3_selection_scoring",
    "acquire_data": "layer_4_data_acquisition",
    "statistical_analysis": "layer_5_analysis_strategy",
    "generate_figures": "layer_6_visualization_strategy",
    "literature_review": "layer_7_literature_strategy",
    "write_paper": "layer_8_writing_strategy",
    "compile_and_review": "layer_9_compilation_strategy"
}

# Pruning rules: what can be pruned after each stage completes
PRUNING_RULES = {
    "load_and_profile": {
        "can_prune": ["1_data_profile/profile.json"],
        "must_preserve": ["1_data_profile/variable_types.json", "1_data_profile/progress.json"],
        "summary_in_context": ["datasets_identified", "variable_classification_strategy", "data_limitations"]
    },
    "generate_research_questions": {
        "can_prune": [],
        "must_preserve": ["2_research_question/research_questions.json", "2_research_question/progress.json"],
        "summary_in_context": ["candidate_questions_summary", "feasibility_filters_applied"]
    },
    "score_and_rank": {
        "can_prune": ["2_scoring/scoring_details.json"],
        "must_preserve": ["2_scoring/ranked_questions.json", "2_scoring/progress.json"],
        "summary_in_context": ["selection_rationale", "composite_scores", "literature_findings"]
    },
    "acquire_data": {
        "can_prune": [],
        "must_preserve": ["2_research_question/download_report.json", "data/README.md"],
        "summary_in_context": ["data_acquired", "external_sources"]
    },
    "statistical_analysis": {
        "can_prune": [
            "3_analysis/scripts/*.py",
            "3_analysis/models/*.txt",
            "3_analysis/models/*.rds",
            "3_analysis/analytic_dataset.csv"
        ],
        "must_preserve": [
            "3_analysis/analysis_results.json",
            "3_analysis/analysis_plan.json",
            "3_analysis/progress.json"
        ],
        "summary_in_context": ["model_selected", "key_findings", "assumptions_checked"]
    },
    "generate_figures": {
        "can_prune": ["4_figures/scripts/*.py", "4_figures/figures/*.png"],
        "must_preserve": ["4_figures/manifest.json", "4_figures/tables/*.tex", "4_figures/progress.json"],
        "summary_in_context": ["figures_created", "tables_created"]
    },
    "literature_review": {
        "can_prune": ["5_references/search_log.json", "5_references/raw_results.json"],
        "must_preserve": ["5_references/references.bib", "5_references/progress.json"],
        "summary_in_context": ["key_references", "literature_gaps"]
    },
    "write_paper": {
        "can_prune": [],
        "must_preserve": ["6_paper/paper.tex", "6_paper/progress.json"],
        "summary_in_context": ["paper_structure", "key_sections"]
    },
    "compile_and_review": {
        "can_prune": [],
        "must_preserve": ["paper.pdf", "6_paper/paper.tex"],
        "summary_in_context": ["compilation_status", "page_count"]
    }
}


# ── Context Bundle Management ───────────────────────────────────────────────

def create_context_bundle(
    output_folder: str,
    cycle: int = 1,
    max_cycles: int = 2
) -> Dict[str, Any]:
    """
    Initialize a new context bundle for the pipeline run.

    Args:
        output_folder: Base output directory (e.g., "exam_paper")
        cycle: Current feedback loop cycle (default: 1)
        max_cycles: Maximum feedback loop cycles (default: 2)

    Returns:
        The created context bundle dict
    """
    bundle_path = os.path.join(output_folder, CONTEXT_BUNDLE_FILE)
    os.makedirs(output_folder, exist_ok=True)

    now = _iso_now()

    bundle = {
        "meta": {
            "version": "1.0",
            "created_at": now,
            "last_updated": now,
            "pipeline_stage": "initialized",
            "cycle": cycle,
            "max_cycles": max_cycles,
            "completed_stages": []
        },
        "layers": {}
    }

    _save_bundle(bundle_path, bundle)
    print(f"[context_bundle] Created at {bundle_path}")

    return bundle


def add_layer(
    output_folder: str,
    stage_name: str,
    decisions: Dict[str, Any],
    cycle: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add a semantic decision layer to the context bundle.

    Each stage adds exactly one layer capturing *why* decisions were made.
    Layers are never modified once added.

    Args:
        output_folder: Base output directory
        stage_name: Stage identifier (e.g., "load_and_profile")
        decisions: Dict containing key_decisions, forward_references
        cycle: Optional cycle number (defaults to reading from bundle)

    Returns:
        The updated context bundle

    Expected decisions schema:
    {
        "key_decisions": {
            "decision_1": { "value": ..., "rationale": "..." },
            "decision_2": { "value": ..., "rationale": "..." }
        },
        "forward_references": {
            "for_stage_N": ["context_key_1", "context_key_2"]
        },
        "outputs_produced": ["file1.json", "file2.json"],
        "stage_summary": "Brief summary of what was accomplished"
    }
    """
    bundle_path = os.path.join(output_folder, CONTEXT_BUNDLE_FILE)
    bundle = _load_bundle(bundle_path)

    if bundle is None:
        bundle = create_context_bundle(output_folder)

    layer_key = STAGE_TO_LAYER.get(stage_name, f"layer_{stage_name}")

    # Add cycle suffix if in feedback loop
    if cycle is None:
        cycle = bundle["meta"].get("cycle", 1)

    if cycle > 1:
        layer_key = f"{layer_key}_cycle_{cycle}"

    # Create the layer
    layer = {
        "stage_name": stage_name,
        "cycle": cycle,
        "timestamp": _iso_now(),
        "key_decisions": decisions.get("key_decisions", {}),
        "forward_references": decisions.get("forward_references", {}),
        "outputs_produced": decisions.get("outputs_produced", []),
        "stage_summary": decisions.get("stage_summary", "")
    }

    # Add the layer (never modify existing layers)
    bundle["layers"][layer_key] = layer

    # Update metadata
    bundle["meta"]["last_updated"] = _iso_now()
    bundle["meta"]["pipeline_stage"] = stage_name

    if stage_name not in bundle["meta"]["completed_stages"]:
        bundle["meta"]["completed_stages"].append(stage_name)

    _save_bundle(bundle_path, bundle)
    print(f"[context_bundle] Added layer: {layer_key}")

    return bundle


def get_context_bundle(output_folder: str) -> Optional[Dict[str, Any]]:
    """
    Read the current context bundle.

    Args:
        output_folder: Base output directory

    Returns:
        Context bundle dict or None if not exists
    """
    bundle_path = os.path.join(output_folder, CONTEXT_BUNDLE_FILE)
    return _load_bundle(bundle_path)


def get_context_for_stage(
    output_folder: str,
    stage_name: str,
    include_raw: bool = False
) -> Dict[str, Any]:
    """
    Query relevant context layers for a given stage.

    Returns only the context that the stage needs, based on forward_references.

    Args:
        output_folder: Base output directory
        stage_name: Current stage requesting context
        include_raw: If True, include raw key_decisions (not just summaries)

    Returns:
        Dict with relevant context from previous stages
    """
    bundle = get_context_bundle(output_folder)

    if bundle is None:
        return {"error": "No context bundle found", "available_layers": []}

    # Find the current stage's position
    try:
        current_idx = STAGE_ORDER.index(stage_name)
    except ValueError:
        current_idx = len(STAGE_ORDER)

    # Get all completed layers
    relevant_layers = {}
    for layer_key, layer_data in bundle["layers"].items():
        layer_stage = layer_data.get("stage_name")
        if layer_stage in STAGE_ORDER:
            layer_idx = STAGE_ORDER.index(layer_stage)
            if layer_idx < current_idx:
                relevant_layers[layer_key] = layer_data

    # Build context based on forward references
    context = {
        "meta": {
            "current_stage": stage_name,
            "cycle": bundle["meta"].get("cycle", 1),
            "available_layers": list(relevant_layers.keys())
        },
        "summaries": {},
        "decisions": {} if include_raw else None
    }

    for layer_key, layer_data in relevant_layers.items():
        # Always include stage summary
        context["summaries"][layer_key] = {
            "stage": layer_data.get("stage_name"),
            "summary": layer_data.get("stage_summary"),
            "timestamp": layer_data.get("timestamp")
        }

        # Include decisions if requested and if this layer is referenced
        if include_raw:
            context["decisions"][layer_key] = layer_data.get("key_decisions", {})

    return context


# ── Pruning / Forget Mechanism ───────────────────────────────────────────────

def can_prune_stage(
    output_folder: str,
    stage_name: str,
    mode: str = "safe"
) -> bool:
    """
    Check if it's safe to prune outputs for a given stage.

    Feedback loop protection: Stages 3-5 cannot be pruned if
    current_cycle < max_cycles (may re-run).

    Args:
        output_folder: Base output directory
        stage_name: Stage to check
        mode: Pruning mode ("safe", "aggressive", "off")

    Returns:
        True if pruning is allowed
    """
    if mode == "off":
        return False

    # Check feedback loop state
    cycle_state = _get_cycle_state(output_folder)
    current_cycle = cycle_state.get("current_cycle", 1)
    max_cycles = cycle_state.get("max_cycles", 2)

    # Stages in feedback loop (3-5) cannot be pruned if may re-run
    feedback_stages = ["score_and_rank", "acquire_data", "statistical_analysis"]
    if stage_name in feedback_stages and current_cycle < max_cycles:
        print(f"[context] Skipping prune for {stage_name}: feedback loop active (cycle {current_cycle}/{max_cycles})")
        return False

    # Safe mode: only prune after explicit checkpoint stages
    if mode == "safe":
        checkpoint_stages = ["statistical_analysis", "generate_figures", "literature_review"]
        return stage_name in checkpoint_stages

    # Aggressive mode: prune any stage with rules defined
    return stage_name in PRUNING_RULES


def prune_stage_outputs(
    output_folder: str,
    stage_name: str,
    mode: str = "safe",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Execute pruning rules for a completed stage.

    Removes files that are no longer needed while preserving
    files required for resume and downstream stages.

    Args:
        output_folder: Base output directory
        stage_name: Completed stage to prune
        mode: Pruning mode ("safe", "aggressive", "off")
        dry_run: If True, report what would be pruned without actually deleting

    Returns:
        Pruning report with deleted, preserved, and skipped files
    """
    if not can_prune_stage(output_folder, stage_name, mode):
        return {"status": "skipped", "reason": "Pruning not allowed for this stage/mode"}

    rules = PRUNING_RULES.get(stage_name, {})
    can_prune = rules.get("can_prune", [])
    must_preserve = rules.get("must_preserve", [])

    report = {
        "stage": stage_name,
        "mode": mode,
        "dry_run": dry_run,
        "timestamp": _iso_now(),
        "deleted": [],
        "preserved": [],
        "skipped": [],
        "space_freed_kb": 0
    }

    for pattern in can_prune:
        # Expand glob patterns
        matching_files = _glob_files(output_folder, pattern)

        for file_path in matching_files:
            # Check if file is in must_preserve
            rel_path = os.path.relpath(file_path, output_folder)

            if any(_matches_pattern(rel_path, p) for p in must_preserve):
                report["preserved"].append(rel_path)
                continue

            if not os.path.exists(file_path):
                report["skipped"].append(rel_path)
                continue

            # Get file size before deletion
            size_kb = os.path.getsize(file_path) / 1024

            if dry_run:
                report["deleted"].append(rel_path)
                report["space_freed_kb"] += size_kb
            else:
                try:
                    os.remove(file_path)
                    report["deleted"].append(rel_path)
                    report["space_freed_kb"] += size_kb
                    print(f"[context] Pruned: {rel_path} ({size_kb:.1f} KB)")
                except OSError as e:
                    report["skipped"].append(f"{rel_path} ({e})")

    # Record pruning action in config
    if not dry_run and report["deleted"]:
        _record_pruning(output_folder, stage_name, mode, report)

    return report


def _record_pruning(
    output_folder: str,
    stage_name: str,
    mode: str,
    report: Dict[str, Any]
) -> None:
    """Record a pruning action in context_config.json."""
    config_path = os.path.join(output_folder, CONTEXT_CONFIG_FILE)
    config = _load_config(config_path)

    if config is None:
        config = {
            "version": "1.0",
            "created_at": _iso_now(),
            "pruning_mode": mode,
            "pruning_history": []
        }

    config["pruning_history"].append({
        "stage": stage_name,
        "timestamp": report["timestamp"],
        "mode": mode,
        "files_deleted": report["deleted"],
        "space_freed_kb": report["space_freed_kb"]
    })
    config["last_pruning"] = _iso_now()

    _save_config(config_path, config)
    print(f"[context_config] Pruning recorded for {stage_name}")


def get_pruning_summary(output_folder: str) -> Dict[str, Any]:
    """
    Get a summary of pruning actions performed.

    Args:
        output_folder: Base output directory

    Returns:
        Pruning summary with total space freed, files deleted, etc.
    """
    config = _load_config(os.path.join(output_folder, CONTEXT_CONFIG_FILE))

    if config is None:
        return {"total_space_freed_kb": 0, "total_files_deleted": 0, "actions": []}

    total_space = sum(a.get("space_freed_kb", 0) for a in config.get("pruning_history", []))
    total_files = sum(len(a.get("files_deleted", [])) for a in config.get("pruning_history", []))

    return {
        "pruning_mode": config.get("pruning_mode", "unknown"),
        "total_space_freed_kb": total_space,
        "total_files_deleted": total_files,
        "actions": config.get("pruning_history", [])
    }


# ── Context Query Utilities ─────────────────────────────────────────────────

def get_decision(
    output_folder: str,
    decision_key: str,
    stage_name: Optional[str] = None
) -> Any:
    """
    Query a specific decision from the context bundle.

    Args:
        output_folder: Base output directory
        decision_key: Key to look for in key_decisions
        stage_name: Optional specific stage to search (searches all if None)

    Returns:
        The decision value or None if not found
    """
    bundle = get_context_bundle(output_folder)
    if bundle is None:
        return None

    for layer_key, layer_data in bundle["layers"].items():
        if stage_name is not None and layer_data.get("stage_name") != stage_name:
            continue

        key_decisions = layer_data.get("key_decisions", {})
        if decision_key in key_decisions:
            return key_decisions[decision_key]

    return None


def get_forward_references(
    output_folder: str,
    for_stage: str
) -> List[str]:
    """
    Get all context keys that forward-reference a given stage.

    Args:
        output_folder: Base output directory
        for_stage: Stage to find references for

    Returns:
        List of context keys from previous stages
    """
    bundle = get_context_bundle(output_folder)
    if bundle is None:
        return []

    references = []
    for layer_data in bundle["layers"].values():
        forward_refs = layer_data.get("forward_references", {})
        stage_refs = forward_refs.get(f"for_{for_stage}", [])
        references.extend(stage_refs)

    return references


def summarize_context(output_folder: str) -> str:
    """
    Generate a human-readable summary of the context bundle.

    Args:
        output_folder: Base output directory

    Returns:
        Formatted summary string
    """
    bundle = get_context_bundle(output_folder)
    if bundle is None:
        return "No context bundle found."

    lines = [
        "=" * 60,
        "CONTEXT BUNDLE SUMMARY",
        "=" * 60,
        f"Version: {bundle['meta']['version']}",
        f"Created: {bundle['meta']['created_at']}",
        f"Last Updated: {bundle['meta']['last_updated']}",
        f"Cycle: {bundle['meta']['cycle']}/{bundle['meta']['max_cycles']}",
        f"Completed Stages: {', '.join(bundle['meta']['completed_stages'])}",
        "",
        "LAYERS:",
    ]

    for layer_key, layer_data in bundle["layers"].items():
        stage = layer_data.get("stage_name", "unknown")
        summary = layer_data.get("stage_summary", "No summary")
        decisions = layer_data.get("key_decisions", {})
        lines.append(f"  [{layer_key}]")
        lines.append(f"    Stage: {stage}")
        lines.append(f"    Summary: {summary}")
        lines.append(f"    Decisions: {len(decisions)} key decisions")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


# ── Helper Functions ───────────────────────────────────────────────────────

def _load_bundle(path: str) -> Optional[Dict[str, Any]]:
    """Load context bundle from JSON file."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_bundle(path: str, bundle: Dict[str, Any]) -> None:
    """Save context bundle to JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(bundle, f, indent=2)


def _load_config(path: str) -> Optional[Dict[str, Any]]:
    """Load context config from JSON file."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_config(path: str, config: Dict[str, Any]) -> None:
    """Save context config to JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)


def _get_cycle_state(output_folder: str) -> Dict[str, Any]:
    """Read the feedback cycle state from cycle_state.json."""
    cycle_path = os.path.join(output_folder, "cycle_state.json")
    if os.path.exists(cycle_path):
        try:
            with open(cycle_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"current_cycle": 1, "max_cycles": 2}


def _glob_files(base_path: str, pattern: str) -> List[str]:
    """Find files matching a glob pattern relative to base_path."""
    from glob import glob

    full_pattern = os.path.join(base_path, pattern)
    matches = glob(full_pattern, recursive=True)
    return [m for m in matches if os.path.isfile(m)]


def _matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file path matches a glob pattern."""
    from fnmatch import fnmatch

    # Normalize path separators
    normalized_path = file_path.replace("\\", "/")
    normalized_pattern = pattern.replace("\\", "/")

    return fnmatch(normalized_path, normalized_pattern)


def _iso_now() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Integration Helper for progress_utils ───────────────────────────────────

def extract_context_decisions(
    stage_name: str,
    output_folder: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Helper to extract context decisions from common stage outputs.

    This is called by complete_stage_with_context to automatically
    extract relevant decisions from stage output files.

    Args:
        stage_name: Stage identifier
        output_folder: Base output directory
        **kwargs: Stage-specific data for context extraction

    Returns:
        Dict with key_decisions, forward_references, outputs_produced, stage_summary
    """
    decisions = {
        "key_decisions": {},
        "forward_references": {},
        "outputs_produced": [],
        "stage_summary": kwargs.get("summary", f"Completed {stage_name}")
    }

    # Stage-specific extraction logic
    if stage_name == "load_and_profile":
        decisions.update(_extract_profile_context(output_folder, kwargs))

    elif stage_name == "generate_research_questions":
        decisions.update(_extract_questions_context(output_folder, kwargs))

    elif stage_name == "score_and_rank":
        decisions.update(_extract_scoring_context(output_folder, kwargs))

    elif stage_name == "statistical_analysis":
        decisions.update(_extract_analysis_context(output_folder, kwargs))

    elif stage_name == "generate_figures":
        decisions.update(_extract_figures_context(output_folder, kwargs))

    elif stage_name == "literature_review":
        decisions.update(_extract_literature_context(output_folder, kwargs))

    elif stage_name == "write_paper":
        decisions.update(_extract_writing_context(output_folder, kwargs))

    return decisions


def _extract_profile_context(output_folder: str, kwargs: Dict) -> Dict:
    """Extract context from load_and_profile stage."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from progress_utils import STAGE_TO_FOLDER

    folder = STAGE_TO_FOLDER.get("load_and_profile", "1_data_profile")
    profile_path = os.path.join(output_folder, folder, "profile.json")

    context = {
        "key_decisions": {
            "datasets_identified": {"value": [], "rationale": "Datasets found in data folder"},
            "variable_classification_strategy": {"value": "automatic", "rationale": "Variables classified by dtype and inspection"},
            "data_limitations_identified": {"value": [], "rationale": "Data quality issues noted"}
        },
        "forward_references": {
            "for_generate_research_questions": ["datasets_identified", "available_variables"],
            "for_statistical_analysis": ["variable_types", "data_limitations"]
        }
    }

    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r") as f:
                profile = json.load(f)

            datasets = list(profile.get("datasets", {}).keys())
            context["key_decisions"]["datasets_identified"]["value"] = datasets

            data_context = profile.get("data_context", {})
            if data_context.get("data_quality_notes"):
                context["key_decisions"]["data_limitations_identified"]["value"] = data_context["data_quality_notes"]

            context["stage_summary"] = f"Profiled {len(datasets)} dataset(s)"
        except (json.JSONDecodeError, IOError):
            pass

    # Add outputs from kwargs if provided
    if "outputs" in kwargs:
        context["outputs_produced"] = kwargs["outputs"]

    return context


def _extract_questions_context(output_folder: str, kwargs: Dict) -> Dict:
    """Extract context from generate_research_questions stage."""
    questions_path = os.path.join(output_folder, "2_research_question", "research_questions.json")

    context = {
        "key_decisions": {
            "candidate_count": {"value": 0, "rationale": "Number of candidate questions generated"},
            "feasible_count": {"value": 0, "rationale": "Candidates passing feasibility check"}
        },
        "forward_references": {
            "for_score_and_rank": ["all_candidates", "preliminary_scores"]
        },
        "outputs_produced": ["2_research_question/research_questions.json"]
    }

    if os.path.exists(questions_path):
        try:
            with open(questions_path, "r") as f:
                questions = json.load(f)

            candidates = questions.get("candidate_questions", [])
            feasible = [c for c in candidates if c.get("status") != "infeasible"]

            context["key_decisions"]["candidate_count"]["value"] = len(candidates)
            context["key_decisions"]["feasible_count"]["value"] = len(feasible)
            context["stage_summary"] = f"Generated {len(candidates)} candidates, {len(feasible)} feasible"
        except (json.JSONDecodeError, IOError):
            pass

    return context


def _extract_scoring_context(output_folder: str, kwargs: Dict) -> Dict:
    """Extract context from score_and_rank stage."""
    ranked_path = os.path.join(output_folder, "2_scoring", "ranked_questions.json")

    context = {
        "key_decisions": {
            "selected_candidate_id": {"value": "unknown", "rationale": "ID of selected question"},
            "composite_score": {"value": 0.0, "rationale": "Final composite score"},
            "selection_rationale": {"value": "", "rationale": "Why this candidate was selected"}
        },
        "forward_references": {
            "for_statistical_analysis": ["primary_question", "variable_roles", "feasibility_assessment"],
            "for_literature_review": ["primary_question", "selection_rationale"],
            "for_write_paper": ["selected_question", "selection_metadata"]
        },
        "outputs_produced": ["2_scoring/ranked_questions.json", "2_scoring/scoring_details.json"]
    }

    if os.path.exists(ranked_path):
        try:
            with open(ranked_path, "r") as f:
                ranked = json.load(f)

            selection = ranked.get("selection_metadata", {})
            context["key_decisions"]["selected_candidate_id"]["value"] = selection.get("selected_candidate_id", "unknown")
            context["key_decisions"]["composite_score"]["value"] = selection.get("composite_score", 0.0)
            context["key_decisions"]["selection_rationale"]["value"] = selection.get("selection_rationale", "")
            context["stage_summary"] = f"Selected candidate {selection.get('selected_candidate_id', '?')} with score {selection.get('composite_score', 0.0)}"
        except (json.JSONDecodeError, IOError):
            pass

    return context


def _extract_analysis_context(output_folder: str, kwargs: Dict) -> Dict:
    """Extract context from statistical_analysis stage."""
    results_path = os.path.join(output_folder, "3_analysis", "analysis_results.json")

    context = {
        "key_decisions": {
            "primary_method": {"value": "unknown", "rationale": "Statistical method used"},
            "analytic_n": {"value": 0, "rationale": "Sample size for analysis"},
            "key_finding": {"value": "", "rationale": "Primary result summary"}
        },
        "forward_references": {
            "for_generate_figures": ["descriptive_stats", "primary_analysis_results"],
            "for_write_paper": ["effect_estimate", "confidence_interval", "p_value"]
        },
        "outputs_produced": ["3_analysis/analysis_results.json", "3_analysis/analysis_plan.json"]
    }

    if os.path.exists(results_path):
        try:
            with open(results_path, "r") as f:
                results = json.load(f)

            primary = results.get("primary_analysis", {})
            context["key_decisions"]["primary_method"]["value"] = primary.get("method", "unknown")

            analytic = results.get("analytic_sample", {})
            context["key_decisions"]["analytic_n"]["value"] = analytic.get("total_n", 0)

            effect = primary.get("results", {}).get("exposure_effect", {})
            estimate = effect.get("raw", {}).get("estimate")
            ci = effect.get("raw", {}).get("ci")
            p_val = effect.get("raw", {}).get("p_value")

            if estimate is not None:
                context["key_decisions"]["key_finding"]["value"] = f"Estimate: {estimate}, CI: {ci}, p: {p_val}"

            context["stage_summary"] = f"Analysis using {primary.get('method', '?')} with N={analytic.get('total_n', 0)}"
        except (json.JSONDecodeError, IOError):
            pass

    return context


def _extract_figures_context(output_folder: str, kwargs: Dict) -> Dict:
    """Extract context from generate_figures stage."""
    manifest_path = os.path.join(output_folder, "4_figures", "manifest.json")

    context = {
        "key_decisions": {
            "figures_count": {"value": 0, "rationale": "Number of figures generated"},
            "tables_count": {"value": 0, "rationale": "Number of tables generated"}
        },
        "forward_references": {
            "for_write_paper": ["figure_files", "table_files"]
        },
        "outputs_produced": ["4_figures/manifest.json"]
    }

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            figures = manifest.get("figures", [])
            tables = manifest.get("tables", [])

            context["key_decisions"]["figures_count"]["value"] = len(figures)
            context["key_decisions"]["tables_count"]["value"] = len(tables)
            context["stage_summary"] = f"Generated {len(figures)} figures, {len(tables)} tables"
        except (json.JSONDecodeError, IOError):
            pass

    return context


def _extract_literature_context(output_folder: str, kwargs: Dict) -> Dict:
    """Extract context from literature_review stage."""
    bib_path = os.path.join(output_folder, "5_references", "references.bib")

    context = {
        "key_decisions": {
            "reference_count": {"value": 0, "rationale": "Number of references collected"}
        },
        "forward_references": {
            "for_write_paper": ["references", "citation_keys"]
        },
        "outputs_produced": ["5_references/references.bib"]
    }

    if os.path.exists(bib_path):
        try:
            with open(bib_path, "r") as f:
                content = f.read()

            # Count @article entries
            ref_count = content.count("@article")
            context["key_decisions"]["reference_count"]["value"] = ref_count
            context["stage_summary"] = f"Collected {ref_count} references"
        except IOError:
            pass

    return context


def _extract_writing_context(output_folder: str, kwargs: Dict) -> Dict:
    """Extract context from write_paper stage."""
    tex_path = os.path.join(output_folder, "6_paper", "paper.tex")

    context = {
        "key_decisions": {
            "paper_structure": {"value": "IMRaD", "rationale": "Paper structure used"}
        },
        "forward_references": {
            "for_compile_and_review": ["tex_file", "references"]
        },
        "outputs_produced": ["6_paper/paper.tex"]
    }

    if os.path.exists(tex_path):
        try:
            with open(tex_path, "r") as f:
                content = f.read()

            # Detect sections
            sections = [s for s in ["\\section{Abstract}", "\\section{Introduction}", "\\section{Methods}", "\\section{Results}", "\\section{Discussion}"] if s in content]
            context["key_decisions"]["paper_structure"]["value"] = ", ".join([s.split("{")[1].split("}")[0] for s in sections[:3]])
            context["stage_summary"] = f"Paper written with {len(sections)} main sections"
        except IOError:
            pass

    return context
