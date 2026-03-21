"""
progress_utils.py — Central progress tracking utility for pipeline stages.

Provides consistent progress tracking API for all skills, integration with
Claude Code task management (TaskCreate/TaskUpdate), resume protocol support,
and output file validation before marking stages complete.

Usage pattern in skills:
    from progress_utils import create_stage_tracker, update_step, complete_stage

    # At stage start
    tracker = create_stage_tracker(output_folder, "load_and_profile",
                                   ["step_1_profile", "step_2_save"])

    # After each step
    update_step(output_folder, "load_and_profile", "step_1_profile", "completed")

    # At stage end (validates outputs)
    complete_stage(output_folder, "load_and_profile",
                   expected_outputs=["1_data_profile/profile.json"])
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# ── Constants ──────────────────────────────────────────────────────────────

STAGE_MAPPING = {
    "1": "load_and_profile",
    "2": "generate_research_questions",
    "3": "acquire_data",
    "4": "statistical_analysis",
    "5": "generate_figures",
    "6": "literature_review",
    "7": "write_paper",
    "8": "compile_and_review",
}

STAGE_TO_FOLDER = {
    "load_and_profile": "1_data_profile",
    "generate_research_questions": "2_research_question",
    "acquire_data": "2_research_question",
    "statistical_analysis": "3_analysis",
    "generate_figures": "4_figures",
    "literature_review": "5_references",
    "write_paper": "6_paper",
    "compile_and_review": "",  # paper.pdf is at root
}


# ── Core Functions ─────────────────────────────────────────────────────────

def create_stage_tracker(
    output_folder: str,
    stage_name: str,
    steps: List[str],
    notes: str = ""
) -> Dict[str, Any]:
    """
    Initialize a new stage progress tracker.

    Args:
        output_folder: Base output directory (e.g., "exam_paper")
        stage_name: Stage identifier (e.g., "load_and_profile")
        steps: List of step identifiers for this stage
        notes: Optional initial notes

    Returns:
        The created progress dict
    """
    progress_dir = _get_progress_dir(output_folder, stage_name)
    os.makedirs(progress_dir, exist_ok=True)

    progress = {
        "stage_name": stage_name,
        "stage_number": _get_stage_number(stage_name),
        "current_step": steps[0] if steps else "initialized",
        "all_steps": steps,
        "completed_steps": [],
        "started_at": _iso_now(),
        "last_updated": _iso_now(),
        "outputs": [],
        "status": "in_progress",
        "notes": notes
    }

    _save_progress(progress_dir, progress)
    print(f"[{stage_name}] Progress tracker created at {progress_dir}")
    return progress


def update_step(
    output_folder: str,
    stage_name: str,
    step: str,
    status: str,
    notes: str = "",
    outputs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update progress for a step within a stage.

    Args:
        output_folder: Base output directory
        stage_name: Stage identifier
        step: Step identifier being updated
        status: One of "in_progress", "completed", "failed", "skipped"
        notes: Optional notes about this step
        outputs: Optional list of output files produced by this step

    Returns:
        The updated progress dict
    """
    progress_dir = _get_progress_dir(output_folder, stage_name)
    progress = _load_progress(progress_dir)

    if progress is None:
        # Create new tracker if doesn't exist
        progress = create_stage_tracker(output_folder, stage_name, [step])
        progress["all_steps"] = [step]  # Will be expanded as we go

    progress["current_step"] = step
    progress["last_updated"] = _iso_now()

    # Update status tracking
    if status == "completed" and step not in progress.get("completed_steps", []):
        if "completed_steps" not in progress:
            progress["completed_steps"] = []
        progress["completed_steps"].append(step)
        progress["status"] = "in_progress"  # Still in stage until complete_stage called

    elif status == "failed":
        progress["status"] = "failed"

    elif status == "skipped" and step not in progress.get("completed_steps", []):
        if "completed_steps" not in progress:
            progress["completed_steps"] = []
        progress["completed_steps"].append(f"{step}_skipped")

    # Update notes
    if notes:
        existing_notes = progress.get("notes", "")
        progress["notes"] = f"{existing_notes}\n{notes}" if existing_notes else notes

    # Update outputs
    if outputs:
        if "outputs" not in progress:
            progress["outputs"] = []
        progress["outputs"].extend(outputs)
        progress["outputs"] = list(set(progress["outputs"]))  # Dedupe

    _save_progress(progress_dir, progress)
    status_symbol = {"completed": "✓", "in_progress": "→", "failed": "✗", "skipped": "○"}.get(status, "•")
    print(f"[{stage_name}] {status_symbol} Step: {step}")

    return progress


def complete_stage(
    output_folder: str,
    stage_name: str,
    validate_outputs: bool = True,
    expected_outputs: Optional[List[str]] = None,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Mark stage complete, optionally validating output files exist.

    Args:
        output_folder: Base output directory
        stage_name: Stage identifier
        validate_outputs: Whether to check that output files exist
        expected_outputs: List of expected output file paths (relative to output_folder)
        notes: Optional completion notes

    Returns:
        The final progress dict

    Raises:
        ValueError: If validation fails and outputs are missing
    """
    progress_dir = _get_progress_dir(output_folder, stage_name)
    progress = _load_progress(progress_dir)

    if progress is None:
        progress = create_stage_tracker(output_folder, stage_name, [])

    validation_result = {"passed": True, "missing": [], "warnings": []}

    if validate_outputs and expected_outputs:
        validation_result = _validate_outputs(output_folder, expected_outputs)

        if not validation_result["passed"]:
            progress["status"] = "failed"
            progress["validation_errors"] = validation_result["missing"]
            _save_progress(progress_dir, progress)
            raise ValueError(
                f"Stage {stage_name} validation failed. Missing outputs: "
                f"{validation_result['missing']}"
            )

    progress["status"] = "completed"
    progress["completed_at"] = _iso_now()

    if notes:
        existing_notes = progress.get("notes", "")
        progress["notes"] = f"{existing_notes}\n{notes}" if existing_notes else notes

    if validation_result["warnings"]:
        progress["warnings"] = validation_result["warnings"]

    _save_progress(progress_dir, progress)
    print(f"[{stage_name}] ✓ Stage complete")

    return progress


def get_progress(output_folder: str, stage_name: str) -> Optional[Dict[str, Any]]:
    """
    Read current progress state for a stage.

    Args:
        output_folder: Base output directory
        stage_name: Stage identifier

    Returns:
        Progress dict if exists, None otherwise
    """
    progress_dir = _get_progress_dir(output_folder, stage_name)
    return _load_progress(progress_dir)


def get_resume_point(output_folder: str, stage_name: str) -> str:
    """
    Return the next step to run based on completed_steps.

    Args:
        output_folder: Base output directory
        stage_name: Stage identifier

    Returns:
        The next step identifier to run, or "complete" if stage is done
    """
    progress = get_progress(output_folder, stage_name)

    if progress is None:
        return "start"

    if progress.get("status") == "completed":
        return "complete"

    completed = progress.get("completed_steps", [])
    all_steps = progress.get("all_steps", [])

    # Find first step not in completed
    for step in all_steps:
        if step not in completed and not any(s.startswith(f"{step}_skipped") for s in completed):
            return step

    # If all steps marked as completed but stage not marked complete
    if len(completed) >= len(all_steps):
        return "finalize"

    return progress.get("current_step", "unknown")


def is_stage_complete(output_folder: str, stage_name: str) -> bool:
    """
    Check if a stage is marked as complete.

    Args:
        output_folder: Base output directory
        stage_name: Stage identifier

    Returns:
        True if stage status is "completed"
    """
    progress = get_progress(output_folder, stage_name)
    return progress is not None and progress.get("status") == "completed"


def get_all_progress(output_folder: str) -> Dict[str, Dict[str, Any]]:
    """
    Read progress for all stages in the pipeline.

    Args:
        output_folder: Base output directory

    Returns:
        Dict mapping stage_name to progress dict
    """
    all_progress = {}

    for stage_name in STAGE_MAPPING.values():
        progress = get_progress(output_folder, stage_name)
        if progress:
            all_progress[stage_name] = progress

    return all_progress


# ── Helper Functions ───────────────────────────────────────────────────────

def _get_stage_number(stage_name: str) -> str:
    """Get the numeric stage number from stage name."""
    for num, name in STAGE_MAPPING.items():
        if name == stage_name:
            return num
    return "0"


def _get_progress_dir(output_folder: str, stage_name: str) -> str:
    """
    Get the directory where progress.json should be stored for a stage.

    For most stages, this is the stage's output folder.
    For acquire-data (stage 3), it shares with generate-research-questions.
    """
    folder_name = STAGE_TO_FOLDER.get(stage_name, "")
    if folder_name:
        return os.path.join(output_folder, folder_name)
    return output_folder


def _get_progress_path(progress_dir: str) -> str:
    """Get the full path to progress.json."""
    return os.path.join(progress_dir, "progress.json")


def _load_progress(progress_dir: str) -> Optional[Dict[str, Any]]:
    """Load progress from JSON file if it exists."""
    progress_path = _get_progress_path(progress_dir)
    if not os.path.exists(progress_path):
        return None

    try:
        with open(progress_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_progress(progress_dir: str, progress: Dict[str, Any]) -> None:
    """Save progress to JSON file."""
    progress_path = _get_progress_path(progress_dir)
    os.makedirs(progress_dir, exist_ok=True)

    with open(progress_path, "w") as f:
        json.dump(progress, f, indent=2)


def _iso_now() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_outputs(output_folder: str, expected_outputs: List[str]) -> Dict[str, Any]:
    """
    Validate that expected output files exist and have content.

    Args:
        output_folder: Base output directory
        expected_outputs: List of expected file paths (relative to output_folder)

    Returns:
        Dict with "passed", "missing", and "warnings" keys
    """
    result = {"passed": True, "missing": [], "warnings": []}

    for output_path in expected_outputs:
        full_path = os.path.join(output_folder, output_path)

        if not os.path.exists(full_path):
            result["missing"].append(output_path)
            result["passed"] = False
        elif os.path.getsize(full_path) == 0:
            result["warnings"].append(f"{output_path} exists but is empty")

    return result


# ── Pipeline-level Tracking ─────────────────────────────────────────────────

class PipelineTracker:
    """
    Pipeline-level progress tracker for the orchestrator.

    Maintains pipeline_log.json with overall status and per-stage tracking.
    Integrates with stage-level progress.json files.
    """

    def __init__(self, output_folder: str, data_folder: str = ""):
        self.output_folder = output_folder
        self.data_folder = data_folder
        self.log_path = os.path.join(output_folder, "pipeline_log.json")
        self._log = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        """Load existing log or create new one."""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return {
            "started_at": _iso_now(),
            "data_folder": self.data_folder,
            "output_folder": self.output_folder,
            "overall_status": "in_progress",
            "stages": {}
        }

    def _save(self) -> None:
        """Save the pipeline log."""
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "w") as f:
            json.dump(self._log, f, indent=2)

    def start_stage(self, stage_number: str, stage_name: str) -> None:
        """Log the start of a stage."""
        stage_key = f"{stage_number}_{stage_name}"
        self._log["stages"][stage_key] = {
            "status": "in_progress",
            "started_at": _iso_now(),
            "outputs": [],
            "notes": ""
        }
        self._save()

    def complete_stage(
        self,
        stage_number: str,
        stage_name: str,
        status: str,
        outputs: List[str] = None,
        notes: str = ""
    ) -> None:
        """Log the completion of a stage."""
        stage_key = f"{stage_number}_{stage_name}"

        if stage_key not in self._log["stages"]:
            self.start_stage(stage_number, stage_name)

        self._log["stages"][stage_key].update({
            "status": status,
            "completed_at": _iso_now(),
        })

        if outputs:
            self._log["stages"][stage_key]["outputs"] = outputs

        if notes:
            existing_notes = self._log["stages"][stage_key].get("notes", "")
            self._log["stages"][stage_key]["notes"] = (
                f"{existing_notes}\n{notes}" if existing_notes else notes
            )

        self._save()

    def fail_stage(self, stage_number: str, stage_name: str, error: str) -> None:
        """Log a stage failure."""
        stage_key = f"{stage_number}_{stage_name}"
        self._log["stages"][stage_key] = {
            "status": "failed",
            "started_at": self._log["stages"].get(stage_key, {}).get("started_at", _iso_now()),
            "completed_at": _iso_now(),
            "error": error,
            "outputs": [],
            "notes": ""
        }
        self._save()

    def complete_pipeline(self, overall_status: str = "success") -> None:
        """Mark the entire pipeline as complete."""
        self._log["completed_at"] = _iso_now()
        self._log["overall_status"] = overall_status
        self._save()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of pipeline progress."""
        completed = sum(1 for s in self._log["stages"].values()
                       if s.get("status") == "completed" or s.get("status") == "success")
        failed = sum(1 for s in self._log["stages"].values()
                    if s.get("status") == "failed")
        total = len(self._log["stages"])

        return {
            "overall_status": self._log.get("overall_status", "in_progress"),
            "stages_completed": completed,
            "stages_failed": failed,
            "stages_total": total,
            "stages": self._log["stages"]
        }

    def print_summary(self) -> None:
        """Print a human-readable summary of pipeline progress."""
        summary = self.get_summary()
        print("\n" + "=" * 60)
        print("PIPELINE PROGRESS SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Stages: {summary['stages_completed']}/{summary['stages_total']} complete")
        if summary['stages_failed'] > 0:
            print(f"Failed: {summary['stages_failed']}")

        for stage_key, stage_info in summary['stages'].items():
            status_symbol = {
                "completed": "✓",
                "success": "✓",
                "in_progress": "→",
                "failed": "✗",
                "degraded": "⚠"
            }.get(stage_info.get("status", "?"), "?")
            print(f"  {status_symbol} {stage_key}: {stage_info.get('status', '?')}")
        print("=" * 60 + "\n")


# ── Convenience Functions for Claude Code Integration ──────────────────────

def create_task_for_stage(
    output_folder: str,
    stage_name: str,
    steps: List[str]
) -> Dict[str, Any]:
    """
    Create a task tracker for a stage (for Claude Code TaskCreate integration).

    This is a helper that returns a dict with stage info that can be used
    to create Claude Code tasks. The actual TaskCreate/TaskUpdate calls
    must be made by the skill/agent using this utility.

    Returns:
        Dict with stage metadata for task creation
    """
    return {
        "stage_name": stage_name,
        "stage_number": _get_stage_number(stage_name),
        "total_steps": len(steps),
        "steps": steps,
        "output_folder": output_folder
    }


def suggest_task_subject(stage_name: str) -> str:
    """Generate a task subject for a stage."""
    subjects = {
        "load_and_profile": "Load and profile dataset",
        "generate_research_questions": "Generate research questions",
        "acquire_data": "Acquire external data",
        "statistical_analysis": "Run statistical analysis",
        "generate_figures": "Generate figures and tables",
        "literature_review": "Conduct literature review",
        "write_paper": "Write paper",
        "compile_and_review": "Compile and review paper"
    }
    return subjects.get(stage_name, f"Execute {stage_name}")
