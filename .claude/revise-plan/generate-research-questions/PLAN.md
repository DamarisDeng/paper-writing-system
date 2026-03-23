# Revision Plan: generate-research-questions

## Current State

- **Lines**: 447
- **Structure**: SKILL.md only (plus validate_research_questions.py)
- **Naming**: Already follows gerund convention ✓

---

## Core Problems

1. **Borderline 500-line limit** (447 lines, only 53 lines buffer)
2. **PICO format guidelines inline** (lines 125-148, 24 lines)
3. **Feasibility checks inline** (lines 151-209, 58 lines)
4. **Scoring criteria inline** (lines 219-227, 9 lines)
5. **Variable role decision table inline** (lines 257-271, 15 lines)
6. **Output schema inline** (lines 310-386, 76 lines)
7. **Worked example inline** (lines 392-423, 32 lines)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| Inline multi-row table | 257-271 | Extract to reference |
| Inline detailed criteria | 151-209 | Extract to reference |
| Inline schema >50 lines | 310-386 | Extract to reference |
| Inline example >20 lines | 392-423 | Extract to reference |
| No progressive disclosure | — | Should reference |

---

## Target State

- **SKILL.md target**: ~260 lines (42% reduction)
- **New structure**:
  ```
  generate-research-questions/
  ├── SKILL.md (~260 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-7)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (already gerund form)

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract PICO format guidelines** (lines 125-148) to REFERENCE.md
3. **Extract feasibility checks** (lines 151-209) to REFERENCE.md
4. **Extract scoring criteria** (lines 219-227) to REFERENCE.md
5. **Extract variable role table** (lines 257-271) to REFERENCE.md
6. **Extract output schema** (lines 310-386) to REFERENCE.md
7. **Extract worked example** (lines 392-423) to REFERENCE.md
8. **Keep in SKILL.md**: Core instructions, progress tracking
9. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/generate-research-questions/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Generating Research Questions

## Table of Contents

1. [PICO Format Guidelines](#pico-format-guidelines)
2. [Feasibility Validation](#feasibility-validation)
3. [Scoring Criteria](#scoring-criteria)
4. [Variable Role Decision Rules](#variable-role-decision-rules)
5. [Output Schema](#output-schema)
6. [Worked Example](#worked-example)

---

## PICO Format Guidelines

[Content from lines 125-148]

## Feasibility Validation

[Content from lines 151-209]

## Scoring Criteria

[Content from lines 219-227]

## Variable Role Decision Rules

[Content from lines 257-271]

## Output Schema

[Content from lines 310-386]

## Worked Example

[Content from lines 392-423]
```

---

## Files to Modify

- **`workflow/skills/generate-research-questions/SKILL.md`**:
  - Remove lines 125-148 → add link to REFERENCE.md: PICO Format
  - Remove lines 151-209 → add link to REFERENCE.md: Feasibility
  - Remove lines 219-227 → add link to REFERENCE.md: Scoring
  - Remove lines 257-271 → add link to REFERENCE.md: Variable Roles
  - Remove lines 310-386 → add link to REFERENCE.md: Output Schema
  - Remove lines 392-423 → add link to REFERENCE.md: Example
  - Keep core instructions (Steps 1-7)

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 15 | 15 | No change |
| Usage/Progress | 55 | 55 | No change |
| Instructions | 240 | 240 | Core steps |
| PICO guidelines | 24 | 0 | To REFERENCE.md |
| Feasibility checks | 58 | 0 | To REFERENCE.md |
| Scoring criteria | 9 | 0 | To REFERENCE.md |
| Variable table | 15 | 0 | To REFERENCE.md |
| Output schema | 76 | 0 | To REFERENCE.md |
| Worked example | 32 | 0 | To REFERENCE.md |
| Other | 5 | 0 | Clean up |
| **Total** | **447** | **~310** | Add more extraction |

### Additional Extraction

Also extract brief summaries of sections (keep only references)
- Target: ~260 lines

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~260)
- [ ] REFERENCE.md has TOC
- [ ] PICO guidelines moved to REFERENCE.md
- [ ] Feasibility checks moved to REFERENCE.md
- [ ] Scoring criteria moved to REFERENCE.md
- [ ] Variable role table moved to REFERENCE.md
- [ ] Output schema moved to REFERENCE.md
- [ ] Worked example moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
