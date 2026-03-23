# Revision Plan: acquire-data

## Current State

- **Lines**: 308
- **Structure**: SKILL.md only
- **Naming**: "acquire-data" — verb-noun form, follows existing pattern ✓

---

## Core Problems

1. **Manifest schema inline** (lines 43-76, 34 lines)
2. **Download function code inline** (lines 152-190, 39 lines)
3. **Verification function code inline** (lines 206-224, 19 lines)
4. **Fallback logic inline** (lines 279-296, 18 lines)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| Inline JSON schema | 43-76 | Extract to reference |
| Inline code >15 lines | 152-190 | Extract to reference |
| Inline code | 206-224 | Extract to reference |
| No progressive disclosure | — | Should reference |

---

## Target State

- **SKILL.md target**: ~180 lines (42% reduction)
- **New structure**:
  ```
  acquire-data/
  ├── SKILL.md (~180 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-5)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (keep "acquire-data")

---

## Orchestrator Compatibility

Skill is invoked as `/acquire-data <output_folder> <manifest_path>` in two places:
- Stage 0: Documented data acquisition
- Stage 4: Supplementary data acquisition

No changes needed — keeping the same name ensures compatibility.

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract manifest schema** (lines 43-76) to REFERENCE.md
3. **Extract download function** (lines 152-190) to REFERENCE.md
4. **Extract verification function** (lines 206-224) to REFERENCE.md
5. **Extract fallback logic** (lines 279-296) to REFERENCE.md
6. **Keep in SKILL.md**: Core instructions, progress tracking
7. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/acquire-data/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Acquire Data

## Table of Contents

1. [Manifest Schema](#manifest-schema)
2. [Download Function](#download-function)
3. [Verification Function](#verification-function)
4. [Fallback URLs](#fallback-urls)
5. [Output Contract](#output-contract)

---

## Manifest Schema

[Content from lines 43-76]

## Download Function

[Content from lines 152-190]

## Verification Function

[Content from lines 206-224]

## Fallback URLs

[Content from lines 279-296]

## Output Contract

[Content from lines 298-309]
```

---

## Files to Modify

- **`workflow/skills/acquire-data/SKILL.md`**:
  - Remove lines 43-76 → add link to REFERENCE.md: Manifest Schema
  - Remove lines 152-190 → add link to REFERENCE.md: Download Function
  - Remove lines 206-224 → add link to REFERENCE.md: Verification
  - Remove lines 279-296 → add link to REFERENCE.md: Fallback URLs
  - Keep core instructions (Steps 1-5)

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 11 | 11 | No change |
| Usage/Progress | 50 | 50 | No change |
| Instructions | 140 | 140 | Core steps |
| Manifest schema | 34 | 0 | To REFERENCE.md |
| Download code | 39 | 0 | To REFERENCE.md |
| Verification code | 19 | 0 | To REFERENCE.md |
| Fallback logic | 18 | 0 | To REFERENCE.md |
| Other | 15 | 0 | Clean up |
| **Total** | **308** | **~201** | Close to target |

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~180)
- [ ] REFERENCE.md has TOC
- [ ] Manifest schema moved to REFERENCE.md
- [ ] Download function moved to REFERENCE.md
- [ ] Verification function moved to REFERENCE.md
- [ ] Fallback logic moved to REFERENCE.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
- [ ] Orchestrator can still invoke as `/acquire-data`
