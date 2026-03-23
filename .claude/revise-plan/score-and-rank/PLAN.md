# Revision Plan: score-and-rank

## Current State

- **Lines**: 331
- **Structure**: SKILL.md only
- **Naming**: "score-and-rank" — verb-noun form, follows existing pattern ✓

---

## Core Problems

1. **Fast-track mode logic inline** (lines 66-107, 42 lines)
2. **Scoring formula details inline** (lines 148-169, 22 lines)
3. **Feedback penalty rules inline** (lines 173-191, 19 lines)
4. **Output schemas inline** (lines 199-248, 50 lines)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| Inline complex logic | 66-107 | Extract to reference |
| Inline formula details | 148-169 | Extract to reference |
| Inline rules | 173-191 | Extract to reference |
| Inline schemas | 199-248 | Extract to reference |

---

## Target State

- **SKILL.md target**: ~200 lines (40% reduction)
- **New structure**:
  ```
  score-and-rank/
  ├── SKILL.md (~200 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-6)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (keep "score-and-rank")

---

## Orchestrator Compatibility

Skill is invoked as `/score-and-rank <output_folder>`. No changes needed — keeping the same name ensures compatibility.

Also invoked by orchestrator during feedback loop (fast-track mode).

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract fast-track mode logic** (lines 66-107) to REFERENCE.md
3. **Extract scoring formula** (lines 148-169) to REFERENCE.md
4. **Extract feedback penalties** (lines 173-191) to REFERENCE.md
5. **Extract output schemas** (lines 199-248) to REFERENCE.md
6. **Keep in SKILL.md**: Core instructions, progress tracking
7. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/score-and-rank/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Score and Rank

## Table of Contents

1. [Fast-Track Mode](#fast-track-mode)
2. [Feasibility Filtering](#feasibility-filtering)
3. [Literature Search](#literature-search)
4. [Scoring Formula](#scoring-formula)
5. [Feedback Penalties](#feedback-penalties)
6. [Output Schemas](#output-schemas)

---

## Fast-Track Mode

[Content from lines 66-107]

## Feasibility Filtering

[Content from lines 80-115]

## Literature Search

[Content from lines 119-144]

## Scoring Formula

[Content from lines 148-169]

## Feedback Penalties

[Content from lines 173-191]

## Output Schemas

[Content from lines 199-248]
```

---

## Files to Modify

- **`workflow/skills/score-and-rank/SKILL.md`**:
  - Remove lines 66-107 → add link to REFERENCE.md: Fast-Track Mode
  - Remove lines 148-169 → add link to REFERENCE.md: Scoring Formula
  - Remove lines 173-191 → add link to REFERENCE.md: Feedback Penalties
  - Remove lines 199-248 → add link to REFERENCE.md: Output Schemas
  - Keep core instructions (Steps 1-6)

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 14 | 14 | No change |
| Usage/Progress | 45 | 45 | No change |
| Instructions | 180 | 180 | Core steps |
| Fast-track logic | 42 | 0 | To REFERENCE.md |
| Scoring formula | 22 | 0 | To REFERENCE.md |
| Feedback penalties | 19 | 0 | To REFERENCE.md |
| Output schemas | 50 | 0 | To REFERENCE.md |
| Other | 10 | 0 | Clean up |
| **Total** | **331** | **~239** | Add more extraction |

### Additional Extraction

Also extract brief content summaries
- Target: ~200 lines

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~200)
- [ ] REFERENCE.md has TOC
- [ ] Fast-track logic moved to REFERENCE.md
- [ ] Scoring formula moved to REFERENCE.md
- [ ] Feedback penalties moved to REFERENCE.md
- [ ] Output schemas moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
- [ ] Orchestrator can still invoke as `/score-and-rank`
