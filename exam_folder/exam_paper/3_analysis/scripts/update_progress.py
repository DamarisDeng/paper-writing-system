"""
Update progress tracking for Stage 5 (Statistical Analysis).
"""
import os
import sys

# Add workflow/scripts to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_DIR = os.path.dirname(SCRIPT_DIR)
EXAM_PAPER_DIR = os.path.dirname(ANALYSIS_DIR)
EXAM_FOLDER_DIR = os.path.dirname(EXAM_PAPER_DIR)
PROJECT_DIR = os.path.dirname(EXAM_FOLDER_DIR)
WORKFLOW_SCRIPTS = os.path.join(PROJECT_DIR, "workflow", "scripts")

sys.path.insert(0, WORKFLOW_SCRIPTS)

from progress_utils import create_stage_tracker, update_step, complete_stage

output_folder = EXAM_PAPER_DIR  # exam_paper/
stage_name = "statistical-analysis"
steps = [
    "copy_helper_scripts",
    "prepare_data",
    "descriptive_stats",
    "write_analysis_plan",
    "primary_analysis",
    "sensitivity_analyses",
    "compile_results"
]

print("Creating stage tracker...")
tracker = create_stage_tracker(output_folder, stage_name, steps)

print("Marking steps complete...")
update_step(output_folder, stage_name, "copy_helper_scripts", "completed",
            outputs=["3_analysis/scripts/utils.py", "3_analysis/scripts/data_utils.py",
                     "3_analysis/scripts/descriptive.py", "3_analysis/scripts/validation.py",
                     "3_analysis/scripts/regression.py"])

update_step(output_folder, stage_name, "prepare_data", "completed",
            outputs=["3_analysis/analytic_dataset.csv", "3_analysis/exclusion_log.json"])

update_step(output_folder, stage_name, "descriptive_stats", "completed",
            outputs=["3_analysis/table1.csv", "3_analysis/analysis_results.json"])

update_step(output_folder, stage_name, "write_analysis_plan", "completed",
            outputs=["3_analysis/analysis_plan.json"])

update_step(output_folder, stage_name, "primary_analysis", "completed",
            outputs=["3_analysis/models/primary_model_summary.txt",
                     "3_analysis/analysis_results.json"])

update_step(output_folder, stage_name, "sensitivity_analyses", "completed",
            outputs=["3_analysis/analysis_results.json"])

update_step(output_folder, stage_name, "compile_results", "completed",
            outputs=["3_analysis/analysis_results.json", "3_analysis/results_summary.md"])

print("Calling complete_stage...")
complete_stage(
    output_folder,
    stage_name,
    expected_outputs=[
        "3_analysis/analytic_dataset.csv",
        "3_analysis/analysis_results.json",
        "3_analysis/models/primary_model_summary.txt",
        "3_analysis/results_summary.md",
        "3_analysis/analysis_plan.json"
    ]
)

print("Progress tracking complete.")
