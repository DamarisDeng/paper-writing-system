# Revision Plan: literature-review

## Current State

- **Lines**: 243
- **Structure**: SKILL.md only
- **Naming**: "literature-review" — noun-phrase form, clear and descriptive ✓

---

## Core Problems

1. **Search category breakdown inline** (lines 69-89, 20 lines)
2. **API usage instructions inline** (lines 94-135, 42 lines)
3. **BibTeX format examples inline** (lines 140-164, 25 lines)
4. **Fallback reference method inline** (lines 176-184, 9 lines)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| Inline detailed list | 69-89 | Extract to reference |
| Inline API docs | 94-135 | Extract to reference |
| Inline examples >15 lines | 140-164 | Extract to reference |
| No progressive disclosure | — | Should reference |

---

## Target State

- **SKILL.md target**: ~140 lines (42% reduction)
- **New structure**:
  ```
  literature-review/
  ├── SKILL.md (~140 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-8)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (keep "literature-review")

---

## Orchestrator Compatibility

Skill is invoked as `/literature-review <output_folder>`. No changes needed — keeping the same name ensures compatibility.

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract search categories** (lines 69-89) to REFERENCE.md
3. **Extract API usage** (lines 94-135) to REFERENCE.md
4. **Extract BibTeX format** (lines 140-164) to REFERENCE.md
5. **Extract fallback strategy** (lines 176-184) to REFERENCE.md
6. **Keep in SKILL.md**: Core instructions, progress tracking
7. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/literature-review/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Literature Review

## Table of Contents

1. [Search Strategy Categories](#search-strategy-categories)
2. [API Usage](#api-usage)
3. [BibTeX Format](#bibtex-format)
4. [Quality Checks](#quality-checks)
5. [Fallback Strategy](#fallback-strategy)

---

## Search Strategy Categories

[Content from lines 69-89]

## API Usage

[Content from lines 94-135]

## BibTeX Format

[Content from lines 140-164]

## Quality Checks

[Content from lines 166-175]

## Fallback Strategy

[Content from lines 176-184]
```

---

## Files to Modify

- **`workflow/skills/literature-review/SKILL.md`**:
  - Remove lines 69-89 → add link to REFERENCE.md: Search Strategy
  - Remove lines 94-135 → add link to REFERENCE.md: API Usage
  - Remove lines 140-164 → add link to REFERENCE.md: BibTeX Format
  - Remove lines 176-184 → add link to REFERENCE.md: Fallback Strategy
  - Keep core instructions (Steps 1-8)

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 12 | 12 | No change |
| Usage/Progress | 40 | 40 | No change |
| Instructions | 120 | 120 | Core steps |
| Search categories | 20 | 0 | To REFERENCE.md |
| API usage | 42 | 0 | To REFERENCE.md |
| BibTeX format | 25 | 0 | To REFERENCE.md |
| Fallback | 9 | 0 | To REFERENCE.md |
| Other | 4 | 0 | Clean up |
| **Total** | **243** | **~172** | Close to target |

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~140)
- [ ] REFERENCE.md has TOC
- [ ] Search categories moved to REFERENCE.md
- [ ] API usage moved to REFERENCE.md
- [ ] BibTeX format moved to REFERENCE.md
- [ ] Fallback strategy moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
- [ ] Orchestrator can still invoke as `/literature-review`
