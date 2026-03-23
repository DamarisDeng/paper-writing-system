# Revision Plan: write-paper

## Current State

- **Lines**: 319
- **Structure**: SKILL.md + templates/template.tex
- **Naming**: "write-paper" — verb-noun form, follows existing pattern ✓

---

## Core Problems

1. **Abstract structure table inline** (lines 100-108, 9 rows)
2. **Section requirements detailed inline** (lines 117-156, 40 lines)
3. **LaTeX math symbol rules inline** (lines 182-217, 36 lines)
4. **Troubleshooting section inline** (lines 274-302, 29 lines)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| Inline multi-row table | 100-108 | Extract to reference |
| Inline detailed specs | 117-156 | Extract to reference |
| Inline formatting rules | 182-217 | Extract to reference |
| Inline troubleshooting | 274-302 | Extract to reference |

---

## Target State

- **SKILL.md target**: ~200 lines (37% reduction)
- **New structure**:
  ```
  write-paper/
  ├── SKILL.md (~200 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-7)
  │   └── Links to REFERENCE.md
  ├── templates/
  │   └── template.tex
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (keep "write-paper")

---

## Orchestrator Compatibility

Skill is invoked as `/write-paper <output_folder>`. No changes needed — keeping the same name ensures compatibility.

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract abstract structure table** (lines 100-108) to REFERENCE.md
3. **Extract section requirements** (lines 117-156) to REFERENCE.md
4. **Extract LaTeX math rules** (lines 182-217) to REFERENCE.md
5. **Extract troubleshooting** (lines 274-302) to REFERENCE.md
6. **Keep in SKILL.md**: Core instructions, progress tracking
7. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/write-paper/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Write Paper

## Table of Contents

1. [Abstract Structure](#abstract-structure)
2. [Section Requirements](#section-requirements)
3. [LaTeX Math Symbols](#latex-math-symbols)
4. [Writing Style Rules](#writing-style-rules)
5. [Troubleshooting](#troubleshooting)

---

## Abstract Structure

[Content from lines 100-108]

## Section Requirements

[Content from lines 117-156]

## LaTeX Math Symbols

[Content from lines 182-217]

## Writing Style Rules

[Content from lines 209-218]

## Troubleshooting

[Content from lines 274-302]
```

---

## Files to Modify

- **`workflow/skills/write-paper/SKILL.md`**:
  - Remove lines 100-108 → add link to REFERENCE.md: Abstract Structure
  - Remove lines 117-156 → add link to REFERENCE.md: Section Requirements
  - Remove lines 182-217 → add link to REFERENCE.md: LaTeX Math
  - Remove lines 274-302 → add link to REFERENCE.md: Troubleshooting
  - Keep core instructions (Steps 1-7)

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 13 | 13 | No change |
| Usage/Progress | 45 | 45 | No change |
| Instructions | 180 | 180 | Core steps |
| Abstract table | 9 | 0 | To REFERENCE.md |
| Section requirements | 40 | 0 | To REFERENCE.md |
| LaTeX rules | 36 | 0 | To REFERENCE.md |
| Troubleshooting | 29 | 0 | To REFERENCE.md |
| Other | 15 | 0 | Clean up |
| **Total** | **319** | **~238** | Close to target |

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~200)
- [ ] REFERENCE.md has TOC
- [ ] Abstract structure moved to REFERENCE.md
- [ ] Section requirements moved to REFERENCE.md
- [ ] LaTeX math rules moved to REFERENCE.md
- [ ] Troubleshooting moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
- [ ] Orchestrator can still invoke as `/write-paper`
