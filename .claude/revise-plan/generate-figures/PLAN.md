# Revision Plan: generate-figures

## Current State

- **Lines**: 163
- **Structure**: SKILL.md + scripts/ (9 Python templates)
- **Naming**: Already follows gerund convention ✓

---

## Core Problems

1. **No actionable workflow checklist** for the agent
2. **Figure type selection table inline** (lines 82-91, 10 rows)
3. **JAMA style requirements inline** (lines 127-145, 19 rows of checklist)

---

## Best Practice Violations

| Violation | Lines | Reference |
|-----------|-------|-----------|
| No workflow checklist | — | Add actionable checklist |
| Inline table | 82-91 | Extract to reference |
| Inline validation checklist | 127-145 | Extract to reference |

---

## Target State

- **SKILL.md target**: ~130 lines (20% reduction)
- **New structure**:
  ```
  generate-figures/
  ├── SKILL.md (~130 lines)
  │   ├── Usage & Progress Tracking
  │   ├── Core Instructions (Steps 1-8)
  │   ├── Workflow Checklist (NEW)
  │   └── Links to REFERENCE.md
  └── references/
      └── REFERENCE.md (NEW)
  ```
- **New name**: No change (already gerund form)

---

## Revision Steps

1. **Create `references/REFERENCE.md`** with reference content
2. **Extract figure type selection table** (lines 82-91) to REFERENCE.md
3. **Extract JAMA style requirements** (lines 127-145) to REFERENCE.md
4. **Add workflow checklist** to SKILL.md
5. **Keep in SKILL.md**: Core instructions, progress tracking
6. **Add cross-links** to REFERENCE.md sections

---

## Files to Create

- `workflow/skills/generate-figures/references/REFERENCE.md`

### REFERENCE.md Structure

```markdown
# Reference: Generating Figures

## Table of Contents

1. [Figure Type Selection](#figure-type-selection)
2. [JAMA Style Requirements](#jama-style-requirements)
3. [Template Scripts](#template-scripts)

---

## Figure Type Selection

[Content from lines 82-91]

## JAMA Style Requirements

### Publication Quality — Figures

[Content from lines 127-138]

### Publication Quality — Tables

[Content from lines 139-145]

## Template Scripts

Brief descriptions of available templates in scripts/:
- template_table1.tex — Table 1 baseline characteristics
- template_forest.py — Forest plots for regression coefficients
- template_km.py — Kaplan-Meier survival curves
- template_scatter.py — Scatter plots with regression lines
- template_heatmap.py — Correlation heatmaps
- template_multipanel.py — Combined multi-panel figures
```

---

## Files to Modify

- **`workflow/skills/generate-figures/SKILL.md`**:
  - Remove lines 82-91 → add link to REFERENCE.md: Figure Type Selection
  - Remove lines 127-145 → add link to REFERENCE.md: JAMA Style Requirements
  - Add workflow checklist after Step 1
  - Keep core instructions (Steps 1-8)

### Workflow Checklist to Add

```markdown
## Workflow Checklist

- [ ] **Load inputs**: analysis_results.json, ranked_questions.json
- [ ] **Import style**: jama_style.py module
- [ ] **Generate Table 1**: Required baseline characteristics table
- [ ] **Generate primary figure**: Forest plot or appropriate visualization
- [ ] **Generate additional figures**: At least 1 more figure
- [ ] **Create manifest**: manifest.json with all figures/tables
- [ ] **Validate**: Quality checklist (see REFERENCE.md)
- [ ] **Progress checkpoint**: Mark stage complete
```

---

## Line Budget Analysis

| Section | Current | After | Notes |
|---------|---------|-------|-------|
| Frontmatter | 12 | 12 | No change |
| Usage/Progress | 40 | 40 | No change |
| Instructions | 80 | 80 | Core steps |
| Figure type table | 10 | 0 | To REFERENCE.md |
| JAMA checklist | 19 | 0 | To REFERENCE.md |
| Workflow checklist | 0 | 15 | NEW to SKILL.md |
| Other | 12 | 0 | Clean up |
| **Total** | **163** | **~147** | Close to target |

---

## Verification

- [ ] SKILL.md under 500 lines (target: ~130)
- [ ] REFERENCE.md has TOC
- [ ] Figure type table moved to REFERENCE.md
- [ ] JAMA style requirements moved to REFERENCE.md
- [ ] Workflow checklist added to SKILL.md
- [ ] SKILL.md includes links to REFERENCE.md sections
- [ ] No information lost in extraction
