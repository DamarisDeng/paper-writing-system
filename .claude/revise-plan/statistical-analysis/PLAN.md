# Revision Plan: statistical-analysis

## Current State

- **Lines**: 844
- **Structure**: SKILL.md only (plus existing `references/methods.md`)
- **Naming**: Already follows convention ✓
- **Existing reference**: `references/methods.md` (277 lines, has TOC) ✓

---

## Core Problems

1. **69% over 500-line limit** (844 lines target: ~500 lines)
2. **Four full decision trees inline** (Track A: 42 lines, Track B: 26 lines, Track C: 42 lines, Track D: 34 lines = 144 lines)
3. **15+ method specifications inline** (lines 485-500)
4. **Complete output schema inline** (lines 718-845 = 127 lines)
5. **Sensitivity analyses list inline** (lines 597-631 = 34 lines)
6. **JAMA formatting helpers inline** (lines 101-108)
7. **Progress tracking setup inline** (lines 47-72)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| Inline decision trees | 308-500 | Progressive disclosure |
| Inline schema >50 lines | 718-845 | Extract to reference |
| Inline multi-row tables | 579-593 | Extract to reference |
| No link to existing methods.md | — | Should reference |

---

## Target State

- **SKILL.md target**: ~350 lines (49% reduction)
- **New structure**:
  ```
  statistical-analysis/
  ├── SKILL.md (~350 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Instructions (Steps 1-7)
  │   ├── Inline: Progress tracker setup, JAMA formatting helpers
  │   └── Links to REFERENCE.md
  └── references/
      ├── methods.md (keep — already has TOC)
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (keep existing name)

---

## Orchestrator Compatibility

Skill is invoked as `/statistical-analysis <output_folder>`. No changes needed — keeping the same name ensures compatibility.

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with consolidated reference content
2. **Extract model selection decision trees** (lines 308-500) to REFERENCE.md
3. **Extract sensitivity analyses list** (lines 597-631) to REFERENCE.md
4. **Extract output schema** (lines 718-845) to REFERENCE.md
5. **Extract helper function table** (lines 485-500) to REFERENCE.md
6. **Keep in SKILL.md**: Core instructions, progress tracking setup, JAMA formatting (short)
7. **Add cross-link**: "See REFERENCE.md: Model Selection for method decision trees"
8. **Add TOC to REFERENCE.md** (will be >100 lines)

---

## Files to Create

- `workflow/skills/statistical-analysis/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Statistical Analysis

## Table of Contents

1. [Model Selection Decision Tree](#model-selection-decision-tree)
   1.1. [Track A: Explanatory Inference](#track-a---explanatory-inference)
   1.2. [Track B: Prediction](#track-b---prediction)
   1.3. [Track C: Causal Inference](#track-c---causal-inference)
   1.4. [Track D: Survival Analysis](#track-d---survival-analysis)
2. [Tie-Breaking Rules](#tie-breaking-rules)
3. [Helper Functions Reference](#helper-functions-reference)
4. [Sensitivity Analyses](#sensitivity-analyses)
5. [Output Contract Schema](#output-contract-schema)
6. [JAMA Formatting Guide](#jama-formatting-guide)

---

## Model Selection Decision Tree

[Content from lines 308-500]

## Tie-Breaking Rules

[Content from lines 473-482]

## Helper Functions Reference

[Content from lines 485-500]

## Sensitivity Analyses

[Content from lines 597-631]

## Output Contract Schema

[Content from lines 718-845]

## JAMA Formatting Guide

[Content from lines 101-108, 547-552]
```

---

## Files to Modify

- **`workflow/skills/statistical-analysis/SKILL.md`**:
  - Remove lines 308-500 (decision trees) → add link to REFERENCE.md
  - Remove lines 485-500 (helper table) → add link to REFERENCE.md
  - Remove lines 597-631 (sensitivity analyses) → add link to REFERENCE.md
  - Remove lines 718-845 (output schema) → add link to REFERENCE.md
  - Keep lines 101-108 (JAMA formatting) — short enough to keep inline
  - Keep progress tracking setup (lines 47-72) — core to the skill
  - Add section: "For model selection guidance, see REFERENCE.md"

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 18 | 18 | No change |
| Usage/Progress | 50 | 50 | No change |
| Instructions (1-7) | 300 | 300 | Core steps |
| Decision trees | 192 | 0 | To REFERENCE.md |
| Helper table | 15 | 0 | To REFERENCE.md |
| Sensitivity analyses | 34 | 0 | To REFERENCE.md |
| Output schema | 127 | 0 | To REFERENCE.md |
| Other | 108 | 108 | No change |
| **Total** | **844** | **~576** | Still over; need more aggressive extraction |

### Aggressive Extraction Plan

Also extract to REFERENCE.md:
- Lines 485-546: Helper functions + JAMA formatting rules
- Lines 559-594: Assumption checks table
- Lines 163-220: Table 1 generation details

**New target**: ~350 lines

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~350)
- [ ] REFERENCE.md has TOC
- [ ] All four decision trees moved to REFERENCE.md
- [ ] Helper function table moved to REFERENCE.md
- [ ] Sensitivity analyses list moved to REFERENCE.md
- [ ] Output schema moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] Progress tracking setup remains inline (core functionality)
- [ ] No information lost in extraction
- [ ] Existing `methods.md` preserved (already has good content)
