# Research Workflow Design Tutorial

## Technical Implementation of an Automated Research Pipeline

This tutorial documents the **technical innovations and hard-won solutions** behind the automated research workflow in this project. This is not a theoretical "how to organize agents" guide—it's a practical documentation of real problems encountered in building a 9-stage automated research pipeline.

## The Challenge

Building a long-running AI pipeline that:
- Runs 9 sequential stages with 60+ minute execution time
- Handles interruptions and resumable execution
- Manages token overflow across stages
- Validates outputs with Python (not LLM)
- Survives feedback loops and re-runs

---

## Part 1: Why Build an Automated Research Workflow?

### The Problem

Academic research involves many repetitive, time-consuming tasks:
- Data cleaning and profiling
- Literature searches and citation management
- Statistical analysis and figure generation
- Writing and formatting papers

### The Vision

Describe your research goal once, let AI handle the rest:
- Single prompt triggers entire pipeline
- Zero human intervention from data to final PDF
- Reproducible, documented workflow

### The Technical Challenge

Building a system that:
- Runs reliably for 60+ minutes
- Handles interruptions and resumable execution
- Validates outputs correctly (no hallucinations)
- Manages token limits across many stages

---

## Part 2: System Architecture

### The General Idea: Orchestrator + Skills

```
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator                             │
│  - Coordinates all stages                                    │
│  - Reads progress.json for resume                           │
│  - Handles errors and feedback loops                         │
└─────────────────────────────────────────────────────────────┘
         │         │         │         │         │
         ▼         ▼         ▼         ▼         ▼
    Stage 0    Stage 1    Stage 2    Stage 3    ...
    (Skill)    (Skill)    (Skill)    (Skill)
```

**Linear Workflow with Feedback Loop:**

```
Data Description → Stage 0 (Acquire) → Stage 1 (Profile)
                                              ↓
                                         Stage 2 (Questions)
                                              ↓
                                         Stage 3 (Score & Rank)
                                              ↓
                                         Stage 4 (Acquire Data)
                                              ↓
                                         Stage 5 (Analysis) ───┐
                                              ↓                  │ Feedback
                                         Stage 6 (Figures)       │ Loop
                                              ↓                  │
                                         Stage 7 (References)    │
                                              ↓                  │
                                         Stage 8 (Write Paper)   │
                                              ↓                  │
                                         Stage 9 (Compile) ◄─────┘
                                              ↓
                                         paper.pdf
```

### Key Components

| Component | Description | Location |
|-----------|-------------|----------|
| **Orchestrator** | Master coordinator that runs stages in sequence | `workflow/skills/orchestrator/SKILL.md` |
| **Skills** | Individual pipeline stages with self-contained instructions | `workflow/skills/<stage>/SKILL.md` |
| **Shared Scripts** | Reusable utilities for progress, context, feedback | `workflow/scripts/*.py` |
| **State Files** | JSON files tracking progress, context, decisions | `exam_paper/*.json` |

### Skill Structure

```
workflow/skills/<skill-name>/
├── SKILL.md          # Instructions for Claude (not executable code)
└── *.py              # Helper scripts (actual Python implementation)
```

**SKILL.md Format:**

```yaml
---
name: my-skill
model: medium
description: What this skill does
---

## Usage
/how-to-invoke-this-skill <args>

## Progress Tracking
This skill has N checkpoints:
- step_1: description
- step_2: description

## Steps
1. Step 1 instructions
2. Step 2 instructions
```

---

## Part 3: Technical Deep Dive

This section covers the actual technical challenges encountered in building this system.

### 3.1 State Persistence: File System as Database

**The Problem**: Pipeline runs for 60+ minutes, can be interrupted at any point. How do you resume?

**The Solution**: Use JSON files on disk as atomic state store.

**progress.json structure:**

```python
{
  "stage_name": "statistical_analysis",
  "status": "in_progress",
  "completed_steps": ["step_1", "step_2", "step_3"],
  "all_steps": ["step_1", "step_2", "step_3", "step_4", "step_5"],
  "started_at": "2025-03-23T10:30:00Z",
  "last_updated": "2025-03-23T10:45:00Z"
}
```

**Key Implementation** (from `workflow/scripts/progress_utils.py`):

```python
def create_stage_tracker(output_folder: str, stage_name: str, steps: List[str]) -> Dict[str, Any]:
    """Initialize a new stage progress tracker."""
    progress_dir = _get_progress_dir(output_folder, stage_name)
    os.makedirs(progress_dir, exist_ok=True)

    progress = {
        "stage_name": stage_name,
        "current_step": steps[0] if steps else "initialized",
        "all_steps": steps,
        "completed_steps": [],
        "started_at": _iso_now(),
        "last_updated": _iso_now(),
        "status": "in_progress"
    }

    _save_progress(progress_dir, progress)
    return progress


def update_step(output_folder: str, stage_name: str, step: str, status: str,
                outputs: Optional[List[str]] = None) -> Dict[str, Any]:
    """Update progress for a step within a stage."""
    progress_dir = _get_progress_dir(output_folder, stage_name)
    progress = _load_progress(progress_dir)

    progress["current_step"] = step
    progress["last_updated"] = _iso_now()

    if status == "completed" and step not in progress.get("completed_steps", []):
        progress["completed_steps"].append(step)

    _save_progress(progress_dir, progress)
    return progress
```

**Resume Protocol:**

```python
def get_resume_point(output_folder: str, stage_name: str) -> str:
    """Return the next step to run based on completed_steps."""
    progress = get_progress(output_folder, stage_name)

    if progress is None:
        return "start"

    if progress.get("status") == "completed":
        return "complete"

    completed = progress.get("completed_steps", [])
    all_steps = progress.get("all_steps", [])

    # Find first step not in completed
    for step in all_steps:
        if step not in completed:
            return step

    return "finalize"
```

**Why This Matters**: Immediate disk writes mean you can kill the process at any point and resume from the last completed step. No in-memory state that gets lost on crash.

### 3.2 Python Validation, Not LLM Checking

**The Problem**: LLMs hallucinate when checking "did this work?" and can't reliably verify file existence.

**The Solution**: Python-based file system validation + pre-emptive feasibility checks.

**Output Validation** (from `workflow/scripts/progress_utils.py`):

```python
def _validate_outputs(output_folder: str, expected_outputs: List[str]) -> Dict[str, Any]:
    """Python-based file system validation - not LLM checks"""
    result = {"passed": True, "missing": [], "warnings": []}

    for output_path in expected_outputs:
        full_path = os.path.join(output_folder, output_path)

        if not os.path.exists(full_path):
            result["missing"].append(output_path)
            result["passed"] = False
        elif os.path.getsize(full_path) == 0:
            result["warnings"].append(f"{output_path} exists but is empty")

    return result


def complete_stage(output_folder: str, stage_name: str,
                   expected_outputs: Optional[List[str]] = None) -> Dict[str, Any]:
    """Mark stage complete, optionally validating output files exist."""
    if expected_outputs:
        validation_result = _validate_outputs(output_folder, expected_outputs)

        if not validation_result["passed"]:
            raise ValueError(
                f"Stage {stage_name} validation failed. Missing outputs: "
                f"{validation_result['missing']}"
            )
```

**Pre-Emptive Validation** (from `workflow/scripts/feasibility_validator.py`):

```python
def validate_candidate_feasibility(candidate, variable_types, profile) -> Dict[str, Any]:
    """Reject impossible questions BEFORE literature searches"""
    reasons = []

    # Check 1: Control groups
    control_check = check_control_group(exposures, variable_types, profile)
    if not control_check["passed"]:
        reasons.append("no_control_group")

    # Check 2: Outcome data exists
    outcome_check = check_outcome_available(outcomes, variable_types, profile)
    if not outcome_check["passed"]:
        reasons.append("no_outcome_data")

    # Check 3: Sample size sufficient
    sample_check = check_sample_size(study_design, profile, variable_types)
    if not sample_check["passed"]:
        reasons.append("insufficient_sample")

    return {"feasible": len(reasons) == 0, "reasons": reasons}
```

**Key Insight**: Validate early with Python, not late with LLM. This prevents wasting time on literature searches for infeasible questions.

### 3.3 Token Overflow: Context Bundle + Pruning

**The Problem**: 9 stages × large JSON files = token overflow. Each stage needs all previous context.

**Failed Approaches**:
- Passing full file contents → Token overflow
- Truncating files → Loss of critical information
- Asking LLM to summarize → Inconsistent, unreliable

**The Solution: Two-Part System**

**Part 1: Context Bundle** (from `workflow/scripts/context_manager.py`):

Captures semantic decisions (why) rather than raw outputs (what).

```python
bundle = {
    "meta": {
        "version": "1.0",
        "created_at": "2025-03-23T10:30:00Z",
        "cycle": 1,
        "max_cycles": 2
    },
    "layers": {
        "layer_1_load_and_profile": {
            "stage_name": "load_and_profile",
            "timestamp": "2025-03-23T10:35:00Z",
            "key_decisions": {
                "datasets_identified": {
                    "value": ["data.csv"],
                    "rationale": "Found in data folder"
                }
            },
            "forward_references": {
                "for_generate_research_questions": ["datasets_identified"]
            },
            "stage_summary": "Profiled 1 dataset(s)"
        }
    }
}
```

**Part 2: Forget Mechanism** (Selective Pruning):

```python
PRUNING_RULES = {
    "load_and_profile": {
        "can_prune": ["1_data_profile/profile.json"],  # 44KB file
        "must_preserve": ["1_data_profile/variable_types.json"],
        "summary_in_context": ["datasets_identified"]
    },
    "statistical_analysis": {
        "can_prune": [
            "3_analysis/scripts/*.py",
            "3_analysis/models/*.txt",
            "3_analysis/analytic_dataset.csv"
        ],
        "must_preserve": [
            "3_analysis/analysis_results.json",
            "3_analysis/analysis_plan.json"
        ],
        "summary_in_context": ["model_selected", "key_findings"]
    }
}
```

**Pruning Modes**:
- **Safe**: Only prune after checkpoint stages (statistical_analysis, generate_figures, literature_review)
- **Aggressive**: Prune after every eligible stage
- **Off**: Disable for debugging

**Result**: ~80% token reduction while maintaining full resumability.

### 3.4 Feedback Loop State Management

**The Problem**: When analysis fails, you need to re-run stages 3-5. How do you preserve state?

**The Solution**:

**cycle_state.json** tracks feedback loop iterations:

```python
{
  "current_cycle": 2,
  "max_cycles": 2,
  "failed_candidates": ["candidate_id_1"],
  "failure_reasons": {
    "candidate_id_1": "non_convergence"
  }
}
```

**Stage reset function** (from `workflow/scripts/progress_utils.py`):

```python
def reset_stage_progress(output_folder: str, stage_name: str) -> None:
    """Delete progress.json to enable re-entry in feedback loop"""
    progress_path = _get_progress_path(output_folder, stage_name)
    if os.path.exists(progress_path):
        os.remove(progress_path)
        print(f"[{stage_name}] Progress reset — ready for re-entry")
```

**Fast-Track Mode**:
- Skip web searches (they didn't change)
- Run primary model + Table 1 only
- Apply score penalties to failed candidates

**Protection**: Stages 3-5 files are never pruned during active feedback cycles.

### 3.5 Real Bugs and Fixes

| Bug | Root Cause | Fix |
|-----|------------|-----|
| **Stage 0 skipped datasets** | Only checked "some files exist" | `parse_data_description.py` verifies ALL documented datasets |
| **Reference hallucination** | LLM-generated fake BibTeX | API-first search with structured BibTeX generation |
| **LaTeX compilation fails** | Missing refs, font issues | 3-pass pdflatex + pdftotext verification |
| **SKILL.md too large** | 70+ lines inline Python code | Extract to separate `.py` files |
| **Token overflow** | Accumulated context across 9 stages | Context bundle + pruning system |

**Example: Data Acquisition Bug**

The initial implementation only checked if *some* files existed in the data folder. This caused Stage 0 to skip downloading datasets that were documented in `Data_Description.md` but missing.

**Fix** (`workflow/scripts/parse_data_description.py`):

```python
def check_availability(datasets: List[Dict], data_folder: Path) -> Tuple[List[Dict], List[Dict]]:
    """Check which datasets are already available."""
    available = []
    missing = []

    for dataset in datasets:
        is_available = False

        # Check if any expected files exist
        for pattern in dataset.get("file_patterns", []):
            if '*' in pattern:
                matches = list(data_folder.glob(pattern))
                if matches:
                    is_available = True
                    break
            else:
                if (data_folder / pattern).exists():
                    is_available = True
                    break

        dataset["status"] = "available" if is_available else "missing"

        if is_available:
            available.append(dataset)
        else:
            missing.append(dataset)

    return available, missing
```

Now the script:
1. Parses `Data_Description.md` to extract ALL documented datasets
2. Checks availability against specific file patterns
3. Generates manifest only for missing datasets
4. Exits with code 1 if any datasets are missing (signals orchestrator to run acquire-data)

---

## Part 4: Building Your Own Research Workflow

### Practical Step-by-Step Guide

Based on the patterns and solutions from this project, here's how to build your own automated research workflow:

#### Step 1: Define Your Pipeline Stages

Break down your research process into discrete stages with clear inputs/outputs:

```python
STAGES = [
    {"name": "data_acquisition", "inputs": [], "outputs": ["data/"]},
    {"name": "data_profile", "inputs": ["data/"], "outputs": ["profile.json"]},
    {"name": "analysis", "inputs": ["profile.json"], "outputs": ["results.json"]},
    # ... more stages
]
```

#### Step 2: Implement Progress Tracking

Use the file system as your state store:

```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker, update_step, complete_stage

# At stage start
tracker = create_stage_tracker(output_folder, "stage_name", ["step_1", "step_2"])

# After each step completes
update_step(output_folder, "stage_name", "step_1", "completed",
            outputs=["output1.json"])

# At stage end - validates outputs before marking complete
complete_stage(output_folder, "stage_name",
               expected_outputs=["output1.json", "output2.json"])
```

#### Step 3: Add Python Validation (Not LLM)

Validate early with Python, not late with LLM:

```python
def validate_inputs(inputs):
    """Python-based validation before expensive operations"""
    if not os.path.exists(inputs["data"]):
        raise ValueError(f"Data file missing: {inputs['data']}")
    if os.path.getsize(inputs["data"]) == 0:
        raise ValueError(f"Data file is empty: {inputs['data']}")
```

#### Step 4: Create Skills for Each Stage

Each skill is a local file with instructions:

```yaml
---
name: my-analysis-skill
model: medium
description: Run statistical analysis
---

## Usage
/my-analysis-skill <output_folder>

## Progress Tracking
This skill has 3 checkpoints:
- step_1_load_inputs
- step_2_run_analysis
- step_3_save_results

## Steps
1. Load inputs from previous stage
2. Run analysis with Python scripts
3. Validate outputs and save
```

#### Step 5: Build an Orchestrator

Coordinate stages with progress monitoring:

```python
def run_pipeline(output_folder):
    for stage in STAGES:
        # Check if already completed
        progress = get_progress(output_folder, stage["name"])
        if progress and progress["status"] == "completed":
            continue

        # Run the stage
        run_stage(output_folder, stage["name"])

        # Validate outputs
        if not validate_outputs(stage["outputs"]):
            raise ValueError(f"Stage {stage['name']} failed validation")
```

#### Step 6: Add Error Handling and Feedback Loops

```python
# Feedback loop example
def run_with_feedback(output_folder):
    max_cycles = 2
    for cycle in range(max_cycles):
        try:
            run_pipeline(output_folder)
            break
        except AnalysisError as e:
            if cycle < max_cycles - 1:
                # Penalize failed candidate and retry
                reset_stage_progress(output_folder, "score_and_rank")
            else:
                raise
```

#### Step 7: Manage Token Limits

Use context bundles and selective pruning:

```python
# Extract semantic decisions instead of full outputs
context_bundle = {
    "key_decisions": {
        "model_selected": {"value": "logistic", "rationale": "Binary outcome"},
        "sample_size": {"value": 1000, "rationale": "After exclusions"}
    }
}

# Prune large files after checkpoints
prune_stage_outputs(output_folder, "statistical_analysis", mode="safe")
```

---

## Key Takeaways

1. **File system as state store** - Immediate writes for crash recovery
2. **Python validation, not LLM** - Reliable checking without hallucination
3. **Semantic context propagation** - Capture why, not just what
4. **Selective pruning** - 80% token reduction
5. **Pre-emptive validation** - Fail fast before expensive operations

---

## Further Reading

- `workflow/scripts/progress_utils.py` - Progress tracking implementation
- `workflow/scripts/context_manager.py` - Context bundle and pruning system
- `workflow/scripts/feedback_utils.py` - Feedback loop management
- `workflow/scripts/feasibility_validator.py` - Pre-emptive validation
- `workflow/skills/load-and-profile/SKILL.md` - Example skill structure
