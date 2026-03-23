# Revision Plan: compile-and-review

## Current State

- **Lines**: 223
- **Structure**: SKILL.md only
- **Naming**: Already follows gerund convention ✓

---

## Core Problems

1. **Error handling table inline** (lines 76-87, 12 rows)
2. **Self-review checklist inline** (lines 99-136, 38 rows)
3. **No actionable workflow checklist** for compilation process

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| No workflow checklist | — | Add actionable checklist |
| Inline multi-row table | 76-87 | Extract to reference |
| Inline checklist | 99-136 | Extract to reference |
| Edge cases inline | 189-201 | Extract to reference |

---

## Target State

- **SKILL.md target**: ~150 lines (33% reduction)
- **New structure**:
  ```
  compile-and-review/
  ├── SKILL.md (~150 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-5)
  │   ├── Workflow Checklist (NEW)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (already gerund form)

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract error handling table** (lines 76-87) to REFERENCE.md
3. **Extract self-review checklist** (lines 99-136) to REFERENCE.md
4. **Extract edge cases** (lines 189-201) to REFERENCE.md
5. **Add workflow checklist** to SKILL.md
6. **Keep in SKILL.md**: Core instructions, progress tracking
7. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/compile-and-review/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Compiling and Reviewing

## Table of Contents

1. [Common Errors and Fixes](#common-errors-and-fixes)
2. [Self-Review Checklist](#self-review-checklist)
3. [Edge Cases](#edge-cases)

---

## Common Errors and Fixes

[Content from lines 76-87]

## Self-Review Checklist

### Content Completeness

[Content from lines 103-112]

### Formatting

[Content from lines 114-122]

### Statistical Consistency

[Content from lines 123-128]

### JAMA Style

[Content from lines 130-136]

## Edge Cases

[Content from lines 189-201]
```

---

## Files to Modify

- **`workflow/skills/compile-and-review/SKILL.md`**:
  - Remove lines 76-87 → add link to REFERENCE.md: Common Errors
  - Remove lines 99-136 → add link to REFERENCE.md: Self-Review Checklist
  - Remove lines 189-201 → add link to REFERENCE.md: Edge Cases
  - Add workflow checklist after Step 1
  - Keep core instructions (Steps 1-5)

### Workflow Checklist to Add

```markdown
## Workflow Checklist

- [ ] **Initial compile**: Run pdflatex + bibtex sequence
- [ ] **Check for errors**: Read paper.log for fatal errors
- [ ] **Fix errors**: Apply fixes (up to 3 retries)
- [ ] **Run self-review**: Complete checklist in REFERENCE.md
- [ ] **Apply revisions**: Fix identified issues
- [ ] **Final compile**: Generate final PDF
- [ ] **Copy to root**: paper.pdf to output root
- [ ] **Create report**: compilation_report.json
- [ ] **Progress checkpoint**: Mark stage complete
```

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 11 | 11 | No change |
| Usage/Progress | 35 | 35 | No change |
| Instructions | 100 | 100 | Core steps |
| Error table | 12 | 0 | To REFERENCE.md |
| Self-review checklist | 38 | 0 | To REFERENCE.md |
| Edge cases | 13 | 0 | To REFERENCE.md |
| Workflow checklist | 0 | 15 | NEW to SKILL.md |
| Other | 14 | 0 | Clean up |
| **Total** | **223** | **~161** | Close to target |

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~150)
- [ ] REFERENCE.md has TOC
- [ ] Error handling table moved to REFERENCE.md
- [ ] Self-review checklist moved to REFERENCE.md
- [ ] Edge cases moved to REFERENCE.md
- [ ] Workflow checklist added to SKILL.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
