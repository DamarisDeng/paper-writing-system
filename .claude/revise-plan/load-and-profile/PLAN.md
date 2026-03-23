# Revision Plan: load-and-profile

## Current State

- **Lines**: 186
- **Structure**: SKILL.md + load_and_profile.py
- **Naming**: Already follows gerund convention ✓

---

## Core Problems

1. **Variable reclassification rules inline** (lines 88-93, 6 rows)
2. **Data context structure inline** (lines 94-106, 13 lines)
3. **Enrichment guidelines inline** (lines 107-112, 6 rows)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| Inline rules | 88-93 | Extract to reference |
| Inline structure | 94-106 | Extract to reference |
| Inline guidelines | 107-112 | Extract to reference |
| No progressive disclosure | — | Should reference |

---

## Target State

- **SKILL.md target**: ~140 lines (25% reduction)
- **New structure**:
  ```
  load-and-profile/
  ├── SKILL.md (~140 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-5)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (already gerund form)

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract variable reclassification rules** (lines 88-93) to REFERENCE.md
3. **Extract data context structure** (lines 94-106) to REFERENCE.md
4. **Extract enrichment guidelines** (lines 107-112) to REFERENCE.md
5. **Keep in SKILL.md**: Core instructions, progress tracking
6. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/load-and-profile/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Loading and Profiling Data

## Table of Contents

1. [Variable Reclassification Rules](#variable-reclassification-rules)
2. [Data Context Structure](#data-context-structure)
3. [Enrichment Guidelines](#enrichment-guidelines)
4. [Output Contract](#output-contract)

---

## Variable Reclassification Rules

[Content from lines 88-93]

## Data Context Structure

[Content from lines 94-106]

## Enrichment Guidelines

[Content from lines 107-112]

## Output Contract

[Content from lines 152-186]
```

---

## Files to Modify

- **`workflow/skills/load-and-profile/SKILL.md`**:
  - Remove lines 88-93 → add link to REFERENCE.md: Variable Rules
  - Remove lines 94-106 → add link to REFERENCE.md: Data Context
  - Remove lines 107-112 → add link to REFERENCE.md: Enrichment
  - Keep core instructions (Steps 1-5)

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 9 | 9 | No change |
| Usage/Progress | 40 | 40 | No change |
| Instructions | 80 | 80 | Core steps |
| Variable rules | 6 | 0 | To REFERENCE.md |
| Data context | 13 | 0 | To REFERENCE.md |
| Enrichment | 6 | 0 | To REFERENCE.md |
| Other | 32 | 0 | Clean up |
| **Total** | **186** | **~129** | Under target |

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~140)
- [ ] REFERENCE.md has TOC
- [ ] Variable reclassification rules moved to REFERENCE.md
- [ ] Data context structure moved to REFERENCE.md
- [ ] Enrichment guidelines moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
