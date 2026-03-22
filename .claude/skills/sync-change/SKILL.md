---
name: sync-change
description: >
  Synchronizes documentation alignment across the pipeline after non-trivial changes.
  Use this when you modify stage numbers, rename stages, add/remove stages, change output folder names,
  or make other structural changes. Checks and updates README.md, orchestrator SKILL.md, progress_utils.py,
  and individual stage skill files to ensure consistency. Trigger manually via /sync-change.
disable-model-invocation: true
user-invocable: true
argument-hint: --check-only
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
| `workflow/skills/orchestrator/SKILL.md` | Stage execution order, data flow | README.md, STAGE_MAPPING |
| `workflow/scripts/progress_utils.py` | `STAGE_MAPPING`, `STAGE_TO_FOLDER` | Orchestrator, README.md |
| `workflow/skills/*/SKILL.md` | Individual stage specs | README.md, orchestrator |
| `workflow/scripts/feedback_utils.py` | Stage references | STAGE_MAPPING |

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
