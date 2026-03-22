---
name: sync-change
description: >
  Synchronizes documentation alignment across the pipeline after non-trivial changes.
  Use this when you modify stage numbers, rename stages, add/remove stages, change output folder names,
  or make other structural changes. Checks and updates README.md, orchestrator SKILL.md, progress_utils.py,
  and individual stage skill files to ensure consistency. Detects non-trivial contradictions across sources
  and presents resolution options. Trigger manually via /sync-change.
disable-model-invocation: true
user-invocable: true
argument-hint: [--check-only] [--contradictions-only] [--detect-contradictions]
---

# Sync Change — Documentation Alignment

Ensures all pipeline documentation stays aligned after structural changes. Run this skill **manually** after:
- Adding/removing stages
- Renumbering stages
- Changing output folder names
- Renaming skills
- Modifying stage dependencies
- Creating new stage skills

## What Gets Checked

| File | Contains | Must Align With |
|------|----------|-----------------|
| `README.md` | Stage list, folder names | Orchestrator, skills, progress_utils.py |
| `workflow/skills/orchestrator/SKILL.md` | Stage execution order, data flow, model assignments | README.md, STAGE_MAPPING, skill frontmatter |
| `workflow/scripts/progress_utils.py` | `STAGE_MAPPING`, `STAGE_TO_FOLDER` | Orchestrator, README.md |
| `workflow/skills/*/SKILL.md` | Individual stage specs, model levels | README.md, orchestrator |
| `workflow/scripts/feedback_utils.py` | Stage references | STAGE_MAPPING |

**With `--detect-contradictions` flag**: Also checks for non-trivial semantic contradictions:
- Stage numbering gaps (e.g., Stage 0 in orchestrator but not in STAGE_MAPPING)
- Folder name mismatches across documentation sources
- Input/output path contradictions
- Feedback loop stage reference inconsistencies
- Model level conflicts between skill frontmatter and orchestrator table
- Dependency ordering issues

## Step 1: Detect Current Structure

Read the source of truth from `progress_utils.py`:

```python
import sys
sys.path.insert(0, "workflow/scripts")
from progress_utils import STAGE_MAPPING, STAGE_TO_FOLDER

# Current pipeline structure
print("STAGE_MAPPING:")
for num, name in STAGE_MAPPING.items():
    print(f"  {num}: {name}")

print("\nSTAGE_TO_FOLDER:")
for name, folder in STAGE_TO_FOLDER.items():
    print(f"  {name}: {folder}")
```

This is the **source of truth** — all other docs should derive from this.

## Step 2: Check README.md Alignment

Verify `README.md` section headers and content:

**Common misalignments to fix:**
- Stage numbers in headers (e.g., "### Stage 4:" should match STAGE_MAPPING)
- Output folder references in text
- Stage count in overview text
- Directory structure diagram

**Check these patterns in README.md:**
- `### Stage N:` headers
- `` `N_stage_folder/` `` paths
- Stage count in "Quick Start" section
- Directory structure tree

## Step 3: Check Orchestrator Alignment

Verify `workflow/skills/orchestrator/SKILL.md`:

**Check alignment points:**
- Stage execution table (lines ~140-150)
- Time budget table (lines ~210-225)
- Data flow diagram (lines ~230-253)
- Feedback loop references (stages to reset)

## Step 4: Check Individual Skill Files

For each stage in `STAGE_MAPPING`, verify its skill file exists and has consistent metadata:

```python
from pathlib import Path

skills_dir = Path("workflow/skills")

for num, name in STAGE_MAPPING.items():
    skill_path = skills_dir / name / "SKILL.md"
    if not skill_path.exists():
        print(f"MISSING: {skill_path}")
```

## Step 5: Check Skill Implementation Compatibility

**NEW:** Verify that stage skills are properly integrated with `progress_utils.py` and `feedback_utils.py`.

Each stage skill MUST:

### 5.1: Use progress_utils.py Functions

Check that the skill uses these functions from `progress_utils.py`:

```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker, update_step, complete_stage
```

**Required functions:**
- `create_stage_tracker(output_folder, stage_name, steps)` — Initialize progress
- `update_step(output_folder, stage_name, step_id, status, ...)` — Mark step completion
- `complete_stage(output_folder, stage_name, expected_outputs=[])` — Mark stage complete

**Stage name format:** Use `stage_name` matching STAGE_MAPPING keys (e.g., "load_and_profile", "generate_research_questions")

### 5.2: Progress File Location

Verify that each skill writes `progress.json` to the correct folder based on `STAGE_TO_FOLDER`:

| Stage Name | Progress Location |
|------------|-------------------|
| load_and_profile | `1_data_profile/progress.json` |
| generate_research_questions | `2_research_question/progress.json` |
| score_and_rank | `2_scoring/progress.json` |
| acquire_data | `2_research_question/progress.json` (shares with stage 2) |
| statistical_analysis | `3_analysis/progress.json` |
| generate_figures | `4_figures/progress.json` |
| literature_review | `5_references/progress.json` |
| write_paper | `6_paper/progress.json` |
| compile_and_review | (root folder) |

### 5.3: Feedback Loop Integration

Check if the stage participates in the feedback loop:

**Stages 3-5 (score-and-rank, acquire-data, statistical-analysis)** are feedback loop stages:
- Must check `cycle_state.json` for `current_cycle > 1`
- Must support fast-track mode when re-running
- Must use `reset_stage_progress()` when starting fresh

**Check for this pattern in feedback-aware skills:**
```python
from feedback_utils import get_cycle_state
cycle_state = get_cycle_state(output_folder)
fast_track = cycle_state.get("current_cycle", 1) > 1
```

### 5.4: New Skill Compatibility Checklist

When a **new stage skill** is created, verify it includes:

1. **Progress tracking setup** (early in the skill):
   ```python
   tracker = create_stage_tracker(output_folder, "stage_name", ["step_1", "step_2", ...])
   ```

2. **Step completion calls** after each step:
   ```python
   update_step(output_folder, "stage_name", "step_1", "completed",
               outputs=["path/to/output.json"])
   ```

3. **Stage completion validation** at the end:
   ```python
   complete_stage(output_folder, "stage_name",
                  expected_outputs=["folder/required_output.json"])
   ```

4. **Feedback loop awareness** (if applicable):
   - Read `cycle_state.json` at start
   - Implement fast-track mode logic
   - Handle re-runs gracefully

## Step 6: Check feedback_utils.py References

Verify stage numbers in comments refer to correct stages:

```python
# Expected mappings from STAGE_MAPPING
# "1" → load_and_profile
# "2" → generate_research_questions
# "3" → score_and_rank
# "4" → acquire_data
# "5" → statistical-analysis (feedback originates here)
# ...
```

## Step 7: Generate Alignment Report

After checking all files, produce a report:

```
ALIGNMENT CHECK REPORT
======================

Source of Truth: progress_utils.py STAGE_MAPPING

✓ README.md: Stage headers match STAGE_MAPPING
✓ Orchestrator: Stage execution table matches
✓ Skill files: All stages have SKILL.md
✓ Progress utils: All skills use progress_utils.py functions
✓ Feedback loop: Stages 3-5 implement cycle_state check

MISALIGNMENTS FOUND:
- README.md line 25: Says "8 stages" instead of "9 stages"
- skill-name/SKILL.md: Missing create_stage_tracker() call
- skill-name/SKILL.md: Doesn't use complete_stage() for validation

ACTIONS TAKEN:
- [ ] Updated README.md stage count
- [ ] Added progress tracking to skill-name/SKILL.md
```

## Step 8: Apply Fixes (If Any)

For each misalignment found:

1. **Read the file** containing the error
2. **Identify the specific line/section** needing update
3. **Apply the fix** using Edit tool
4. **Verify** the fix aligns with source of truth

**Always fix at the source:**
- `progress_utils.py` is the source for stage/folder mappings
- Individual skill SKILL.md is source for that stage's specs
- Orchestrator is source for execution order

## Step 9: Validation

After fixes, re-run checks to confirm alignment:

```python
# Quick validation
from progress_utils import STAGE_MAPPING, STAGE_TO_FOLDER

# Verify STAGE_TO_FOLDER has all stages from STAGE_MAPPING
stage_names = set(STAGE_MAPPING.values())
folder_names = set(STAGE_TO_FOLDER.keys())
assert stage_names.issubset(folder_names), "Missing folder mappings"

print("✓ All alignments verified")
```

## Step 10: Contradiction Detection

**NEW**: Detect non-trivial semantic contradictions across pipeline documentation that cannot be resolved through simple alignment checks.

### 10.1 Contradiction Types

| Pattern | Description | Severity |
|---------|-------------|----------|
| Stage numbering gaps | Stage referenced in docs but not in STAGE_MAPPING | HIGH |
| Folder name mismatches | STAGE_TO_FOLDER vs documented folders | HIGH |
| Input/output contradictions | Different inputs/outputs across sources | MEDIUM |
| Feedback loop references | Sources disagree on loop stages | HIGH |
| Model level conflicts | Frontmatter `model:` vs orchestrator table | MEDIUM |
| Dependency inconsistencies | Impossible/circular dependencies | CRITICAL |

### 10.2 Detection Functions

Implement detection by reading all sources and checking for patterns:

```python
import sys
sys.path.insert(0, "workflow/scripts")
from progress_utils import STAGE_MAPPING, STAGE_TO_FOLDER
import re
from pathlib import Path

def detect_stage_numbering_gaps():
    """
    Check for stages referenced in orchestrator/CLAUDE.md that aren't in STAGE_MAPPING.
    Returns: list of contradictions found
    """
    contradictions = []

    # Read orchestrator for stage references
    orchestrator_path = Path("workflow/skills/orchestrator/SKILL.md")
    with open(orchestrator_path) as f:
        orchestrator_content = f.read()

    # Find all stage number mentions (e.g., "Stage 0", "Stage 10")
    stage_refs = set(re.findall(r'Stage (\d+)', orchestrator_content))

    # Check against STAGE_MAPPING
    for ref in stage_refs:
        if ref not in STAGE_MAPPING:
            contradictions.append({
                "type": "Stage numbering gap",
                "severity": "HIGH",
                "description": f"Stage {ref} referenced in orchestrator but not in STAGE_MAPPING",
                "sources": [
                    f"workflow/skills/orchestrator/SKILL.md: references Stage {ref}",
                    f"workflow/scripts/progress_utils.py: STAGE_MAPPING missing key '{ref}'"
                ]
            })

    return contradictions


def detect_folder_name_mismatches():
    """
    Check STAGE_TO_FOLDER against documented folders in README.md and CLAUDE.md.
    """
    contradictions = []

    # Read README for folder documentation
    readme_path = Path("Readme.md")
    with open(readme_path) as f:
        readme_content = f.read()

    # Extract documented folder structure (e.g., `1_data_profile/`, `2_research_question/`)
    documented_folders = set(re.findall(r'(\d+_[a-z_]+)/', readme_content))

    # Check STAGE_TO_FOLDER entries
    for stage_name, folder in STAGE_TO_FOLDER.items():
        if folder:  # Skip empty string (compile_and_review)
            if folder not in documented_folders:
                contradictions.append({
                    "type": "Folder name mismatch",
                    "severity": "MEDIUM",
                    "description": f"Folder '{folder}' for stage '{stage_name}' not found in README documentation",
                    "sources": [
                        f"workflow/scripts/progress_utils.py: STAGE_TO_FOLDER['{stage_name}'] = '{folder}'",
                        f"Readme.md: folder not documented"
                    ]
                })

    # Check for documented folders without STAGE_TO_FOLDER entries
    stage_folders = set(f for f in STAGE_TO_FOLDER.values() if f)
    for folder in documented_folders:
        if folder not in stage_folders:
            contradictions.append({
                "type": "Orphaned folder",
                "severity": "MEDIUM",
                "description": f"Folder '{folder}' documented in README but no stage maps to it",
                "sources": [
                    f"Readme.md: documents {folder}/",
                    f"workflow/scripts/progress_utils.py: STAGE_TO_FOLDER has no entry for '{folder}'"
                ]
            })

    return contradictions


def detect_input_output_contradictions():
    """
    Parse data flow tables and find path disagreements across sources.
    """
    contradictions = []

    # Read CLAUDE.md pipeline stages table
    claude_path = Path(".claude/CLAUDE.md")
    with open(claude_path) as f:
        claude_content = f.read()

    # Read orchestrator data flow section
    orchestrator_path = Path("workflow/skills/orchestrator/SKILL.md")
    with open(orchestrator_path) as f:
        orchestrator_content = f.read()

    # Extract input/output patterns (simplified - would need more parsing in practice)
    # Look for discrepancies like "exam_paper/2_scoring/" vs "exam_paper/2_research_question/"

    # Example: acquire-data output location varies
    if "0_data_acquisition/" in claude_content and "Stage 0" not in STAGE_MAPPING:
        contradictions.append({
            "type": "Input/output contradiction",
            "severity": "HIGH",
            "description": "Stage 0 outputs to 0_data_acquisition/ but Stage 0 not in STAGE_MAPPING",
            "sources": [
                f".claude/CLAUDE.md: documents 0_data_acquisition/ as Stage 0 output",
                f"workflow/scripts/progress_utils.py: no Stage 0 in STAGE_MAPPING"
            ]
        })

    return contradictions


def detect_feedback_loop_contradictions():
    """
    Check which stages are in feedback loop across sources.
    """
    contradictions = []

    # Read CLAUDE.md feedback loop description
    claude_path = Path(".claude/CLAUDE.md")
    with open(claude_path) as f:
        claude_content = f.read()

    # Read orchestrator feedback loop section
    orchestrator_path = Path("workflow/skills/orchestrator/SKILL.md")
    with open(orchestrator_path) as f:
        orchestrator_content = f.read()

    # Extract feedback loop stage mentions
    claude_stages = set(re.findall(r'[Ss]tage[s]? (\d+)[-–](\d+)', claude_content))
    orchestrator_stages = set(re.findall(r'[Ss]tage[s]? (\d+)[-–](\d+)', orchestrator_content))

    # Check for mismatches
    if claude_stages != orchestrator_stages:
        contradictions.append({
            "type": "Feedback loop contradiction",
            "severity": "HIGH",
            "description": f"Feedback loop stages differ: CLAUDE.md={claude_stages}, orchestrator={orchestrator_stages}",
            "sources": [
                f".claude/CLAUDE.md: stages {claude_stages}",
                f"workflow/skills/orchestrator/SKILL.md: stages {orchestrator_stages}"
            ]
        })

    return contradictions


def detect_model_level_conflicts():
    """
    Compare skill frontmatter `model:` vs orchestrator table.
    """
    contradictions = []

    # Read orchestrator model level table
    orchestrator_path = Path("workflow/skills/orchestrator/SKILL.md")
    with open(orchestrator_path) as f:
        orchestrator_content = f.read()

    # Extract model assignments from orchestrator table
    # Pattern: "Stage N. Name | level | model | rationale"
    orchestrator_models = {}
    for match in re.finditer(
        r'\|\s*(\d+)\.\s+([^|]+)\s*\|\s*(high|medium|low)',
        orchestrator_content,
        re.IGNORECASE
    ):
        stage_num, stage_name, model = match.groups()
        orchestrator_models[stage_num] = model.strip().lower()

    # Read each skill's frontmatter
    skills_dir = Path("workflow/skills")
    for stage_num, stage_name in STAGE_MAPPING.items():
        skill_path = skills_dir / stage_name / "SKILL.md"
        if skill_path.exists():
            with open(skill_path) as f:
                content = f.read()
                # Extract model from frontmatter
                model_match = re.search(r'^model:\s*(high|medium|low)', content, re.MULTILINE)
                if model_match:
                    skill_model = model_match.group(1).lower()
                    orch_model = orchestrator_models.get(stage_num)

                    if orch_model and skill_model != orch_model:
                        contradictions.append({
                            "type": "Model level conflict",
                            "severity": "MEDIUM",
                            "description": f"Stage {stage_num} ({stage_name}): skill frontmatter says '{skill_model}' but orchestrator table says '{orch_model}'",
                            "sources": [
                                f"workflow/skills/{stage_name}/SKILL.md: model: {skill_model}",
                                f"workflow/skills/orchestrator/SKILL.md: Stage {stage_num} model = {orch_model}"
                            ]
                        })

    return contradictions


def detect_dependency_inconsistencies():
    """
    Build dependency graphs and check for cycles or impossible ordering.
    """
    contradictions = []

    # Build dependency map from CLAUDE.md pipeline table
    claude_path = Path(".claude/CLAUDE.md")
    with open(claude_path) as f:
        claude_content = f.read()

    # Parse table to understand dependencies (e.g., Stage N depends on Stage N-1 output)
    # Look for circular references or impossible dependencies

    # Example: Stage 5 depends on Stage 2 output (skip-back dependency)
    # This is valid but worth noting as "non-sequential"

    return contradictions


def run_all_detections():
    """Run all contradiction detection functions."""
    all_contradictions = []
    all_contradictions.extend(detect_stage_numbering_gaps())
    all_contradictions.extend(detect_folder_name_mismatches())
    all_contradictions.extend(detect_input_output_contradictions())
    all_contradictions.extend(detect_feedback_loop_contradictions())
    all_contradictions.extend(detect_model_level_conflicts())
    all_contradictions.extend(detect_dependency_inconsistencies())
    return all_contradictions
```

### 10.3 User Presentation Template

For each contradiction found, present to the user:

```
CONTRADICTION: [Type]

Severity: [HIGH/MEDIUM/LOW]

[Description]

Conflicting Sources:
  [Source A]: [What it says] (line X or reference)
  [Source B]: [What it says instead] (line Y or reference)

Implications:
  - [Impact on pipeline execution]
  - [Potential failures or confusion]

Resolution Options:
  [A] Use Source A as truth - [what changes, which files updated]
  [B] Use Source B as truth - [what changes, which files updated]
  [C] Merge/compromise - [how to resolve, e.g., document subdirectory conventions]
  [D] Custom - [user specifies custom resolution]

Which option? [A/B/C/D or skip]:
```

### 10.4 Resolution Application

Based on user choice:

- **A/B**: Update conflicting sources to match chosen source of truth
  - Read the source file(s)
  - Apply Edit tool to fix contradictions
  - Verify changes align

- **C**: Apply merge logic
  - Document the discrepancy (e.g., add comment explaining convention)
  - Update both sources to reflect the agreed-upon approach

- **D**: Prompt user for custom resolution
  - Ask user to specify what the correct resolution should be
  - Apply as specified

- **skip**: Leave contradiction unresolved but logged

### 10.5 Contradiction Detection Report

After processing all contradictions, generate a report:

```
CONTRADICTION DETECTION REPORT
==============================

Total contradictions found: N
  - HIGH: X
  - MEDIUM: Y
  - LOW: Z

Resolved: R
Skipped: S
Remaining: (R+S)

CONTRADICTIONS BY TYPE:
- Stage numbering gaps: N1
- Folder name mismatches: N2
- Input/output contradictions: N3
- Feedback loop contradictions: N4
- Model level conflicts: N5
- Dependency inconsistencies: N6

ACTIONS TAKEN:
- [ ] Updated progress_utils.py to include Stage 0
- [ ] Fixed folder mapping for acquire_data stage
- [ ] Documented feedback loop stages consistently

UNRESOLVED:
- (list any skipped contradictions)
```

## Output

The skill produces:
1. **Alignment report** (printed to console)
2. **Any file edits** (applied via Edit tool)
3. **Final validation** (pass/fail)

## Usage Examples

**After adding a new stage:**
```
/sync-change
```
→ Detects new stage in progress_utils.py, prompts to update README.md and orchestrator

**Full sync with contradiction detection:**
```
/sync-change --detect-contradictions
```
→ Runs alignment checks AND detects non-trivial contradictions across sources

**Only detect contradictions (skip alignment):**
```
/sync-change --contradictions-only
```
→ Skips basic alignment checks, only runs contradiction detection

**Check contradictions without applying fixes:**
```
/sync-change --check-only --detect-contradictions
```
→ Reports all alignment issues and contradictions without making changes

**After renumbering stages:**
```
/sync-change --renumber
```
→ Updates all stage references across docs

**Just checking alignment:**
```
/sync-change --check-only
```
→ Reports misalignments without making changes

**After creating a new stage skill:**
```
/sync-change --verify-skill skill-name
```
→ Verifies the new skill is compatible with progress_utils.py and feedback_utils.py
