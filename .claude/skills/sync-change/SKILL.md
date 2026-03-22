---
name: sync-change
description: >
  Synchronizes documentation alignment across the pipeline after non-trivial changes.
  Use this when you modify stage numbers, rename stages, add/remove stages, change output folder names,
  or make other structural changes. Checks and updates README.md, orchestrator SKILL.md, progress_utils.py,
  and individual stage skill files to ensure consistency. Trigger manually via /sync-change.
disable-model-invocation: true
user-invocable: true
argument-hint: [scope]
---

# Sync Change — Documentation Alignment

Ensures all pipeline documentation stays aligned after structural changes. Run this skill **manually** after:
- Adding/removing stages
- Renumbering stages
- Changing output folder names
- Renaming skills
- Modifying stage dependencies

## What Gets Checked

| File | Contains | Must Align With |
|------|----------|-----------------|
| `README.md` | Stage list, folder names | Orchestrator, skills, progress_utils.py |
| `workflow/skills/orchestrator/SKILL.md` | Stage execution order, data flow | README.md, STAGE_MAPPING |
| `workflow/scripts/progress_utils.py` | `STAGE_MAPPING`, `STAGE_TO_FOLDER` | Orchestrator, README.md |
| `workflow/skills/*/SKILL.md` | Individual stage specs | README.md, orchestrator |

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

```python
# Expected stage sections (based on STAGE_MAPPING)
expected_sections = {
    f"Stage {num}": name.replace("_", "-").title()
    for num, name in STAGE_MAPPING.items()
}
```

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

**Key patterns to verify:**
```yaml
| Stage | Skill |
| 1 | load-and-profile |
| 2 | generate-research-questions |
| 3 | score-and-rank |
...
```

## Step 4: Check Individual Skill Files

For each stage in `STAGE_MAPPING`, verify its skill file exists and has consistent metadata:

```python
import os
from pathlib import Path

skills_dir = Path("workflow/skills")

for num, name in STAGE_MAPPING.items():
    skill_path = skills_dir / name / "SKILL.md"
    if not skill_path.exists():
        print(f"MISSING: {skill_path}")
    else:
        # Verify skill mentions correct stage number
        content = skill_path.read_text()
        if f"Stage {num}" not in content:
            print(f"MISMATCH: {skill_path} doesn't mention 'Stage {num}'")
```

## Step 5: Check feedback_utils.py References

Verify stage numbers in comments refer to correct stages:

```python
# Expected comment patterns
# "Stage 2" → generate-research-questions (feasibility check)
# "Stage 3" → score-and-rank (literature search)
# "Stage 5" → statistical-analysis (where feedback originates)
```

## Step 6: Generate Alignment Report

After checking all files, produce a report:

```
ALIGNMENT CHECK REPORT
======================

Source of Truth: progress_utils.py STAGE_MAPPING

✓ README.md: Stage headers match STAGE_MAPPING
✓ Orchestrator: Stage execution table matches
✓ Skill files: All 9 stages have SKILL.md
✓ feedback_utils.py: References are correct

MISALIGNMENTS FOUND:
- README.md line 25: Says "8 stages" instead of "9 stages"
- Orchestrator line 143: Stage table missing score-and-rank entry

ACTIONS TAKEN:
- [ ] Updated README.md stage count
- [ ] Added missing stage to orchestrator table
```

## Step 7: Apply Fixes (If Any)

For each misalignment found:

1. **Read the file** containing the error
2. **Identify the specific line/section** needing update
3. **Apply the fix** using Edit tool
4. **Verify** the fix aligns with source of truth

**Always fix at the source:**
- `progress_utils.py` is the source for stage/folder mappings
- Individual skill SKILL.md is source for that stage's specs
- Orchestrator is source for execution order

## Step 8: Validation

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
