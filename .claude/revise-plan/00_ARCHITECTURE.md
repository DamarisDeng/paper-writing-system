# Skill Revision Architecture

This document provides templates and conventions for revising skills in the paper-writing-system.

---

## Table of Contents

1. [Revision Goals](#revision-goals)
2. [Naming Conventions](#naming-conventions)
3. [Progressive Disclosure Pattern](#progressive-disclosure-pattern)
4. [Reference File Structure](#reference-file-structure)
5. [Workflow Checklist Template](#workflow-checklist-template)
6. [TOC Template for Reference Files](#toc-template-for-reference-files)
7. [Orchestrator Compatibility](#orchestrator-compatibility)

---

## Revision Goals

1. **Token Efficiency**: SKILL.md files should be under 500 lines
2. **Progressive Disclosure**: Core instructions in SKILL.md, reference material in REFERENCE.md
3. **Discoverability**: REFERENCE.md files should have TOCs for files >100 lines
4. **Actionable Checklists**: Skills should include workflow checklists
5. **Naming Consistency**: Use existing `verb-noun` pattern (DO NOT rename to gerund form)

---

## Naming Conventions

### Current Naming Pattern (Keep As-Is)

**DO NOT rename skills.** The existing `verb-noun` pattern is consistent and clear:

| Skill | Current Name | ✓ Correct |
|-------|--------------|-----------|
| acquire-data | acquire-data | ✓ verb-noun |
| load-and-profile | load-and-profile | ✓ verb-noun |
| generate-research-questions | generate-research-questions | ✓ verb-noun |
| score-and-rank | score-and-rank | ✓ verb-noun |
| statistical-analysis | statistical-analysis | ✓ noun-phrase (accepted) |
| generate-figures | generate-figures | ✓ verb-noun |
| literature-review | literature-review | ✓ noun-phrase (accepted) |
| write-paper | write-paper | ✓ verb-noun |
| compile-and-review | compile-and-review | ✓ verb-noun |
| orchestrator | orchestrator | ✓ noun (accepted) |

**Renaming is NOT recommended** because:
- Requires updating orchestrator skill invocations
- Requires renaming skill directories
- Breaks existing user patterns
- Adds no functional value

---

## Orchestrator Compatibility

Skills are invoked by orchestrator using `/skill-name` format:

```
/acquire-data <output_folder> <manifest_path>
/load-and-profile <data_folder>
/generate-research-questions <output_folder>
/score-and-rank <output_folder>
/statistical-analysis <output_folder>
/generate-figures <output_folder>
/literature-review <output_folder>
/write-paper <output_folder>
/compile-and-review <output_folder>
```

**Important**: If you MUST rename a skill, you must update:
1. The skill directory name
2. The `name:` field in SKILL.md frontmatter
3. Orchestrator invocations (4+ places)
4. `progress_utils.py` STAGE_MAPPING (for internal tracking)

**Recommendation**: Keep existing names to avoid breaking changes.

---

## Progressive Disclosure Pattern

### SKILL.md Structure

```markdown
---
name: skill-name
model: medium
description: >
  One-line summary. What triggers this skill?
  Use this skill when...
argument-hint: <arguments>
---

# Skill Title

One-sentence description of what this skill does.

## Usage

```
/skill-name <arguments>
```

Reads from `<input_path>`. Writes to `<output_path>`.

## Progress Tracking

[Progress tracking details]

## Instructions

You are a [role]. Follow these steps:

### Step 1: [Brief Name]
[Core instructions - inline only if <5 lines]

For detailed guidance, see REFERENCE.md.

### Step 2: [Brief Name]
...

## Output Contract

[`<output_path>/file.json` structure]
```

### REFERENCE.md Structure (for files >100 lines)

```markdown
# Reference: [Skill Name]

## Table of Contents

1. [Section 1](#section-1)
2. [Section 2](#section-2)
...

---

## Section 1

[Detailed reference content]
```

---

## Reference File Structure

### When to Create REFERENCE.md

Create `references/REFERENCE.md` when SKILL.md has:
- Detailed decision trees or flowcharts
- Multi-row tables
- Long code examples (>10 lines)
- Troubleshooting guides
- Format specifications (e.g., LaTeX, BibTeX)
- Multiple configuration options

### File Location

```
workflow/skills/<skill-name>/
├── SKILL.md              # Core instructions (<500 lines)
└── references/
    └── REFERENCE.md      # Detailed reference material (with TOC)
```

---

## Workflow Checklist Template

For complex skills with multi-step workflows, include an actionable checklist:

```markdown
## Workflow Checklist

Use this checklist to execute the skill systematically:

- [ ] **Step 1**: [Action] → [Expected output]
- [ ] **Step 2**: [Action] → [Expected output]
- [ ] **Step 3**: [Action] → [Expected output]
...
- [ ] **Validation**: [What to verify before completion]
```

---

## TOC Template for Reference Files

For REFERENCE.md files >100 lines, include a table of contents at the top:

```markdown
# Reference: [Skill Name]

## Table of Contents

1. [Topic 1](#topic-1)
2. [Topic 2](#topic-2)
3. [Topic 3](#topic-3)
   3.1. [Subtopic 3a](#subtopic-3a)
   3.2. [Subtopic 3b](#subtopic-3b)
4. [Output Contract](#output-contract)
5. [Troubleshooting](#troubleshooting)

---

## Topic 1

[Content]
```

---

## Common Extraction Patterns

### Tables

Extract multi-row tables (>3 rows) to REFERENCE.md:

**SKILL.md:**
> See REFERENCE.md: [Table Name] for the complete table.

**REFERENCE.md:**
> ### [Table Name]
> [Full table]

### Decision Trees

Extract complex decision trees to REFERENCE.md:

**SKILL.md:**
> See REFERENCE.md: Model Selection Decision Tree for method selection guidance.

**REFERENCE.md:**
> ### Model Selection Decision Tree
> [Full decision tree]

### Code Examples

Keep short examples (≤5 lines) inline. Extract longer examples:

**SKILL.md:**
> For complete implementation examples, see REFERENCE.md: Code Examples.

**REFERENCE.md:**
> ### Code Examples
> [Full code examples]

---

## Verification Checklist

After revising a skill, verify:

- [ ] SKILL.md is under 500 lines
- [ ] REFERENCE.md has a TOC (if >100 lines)
- [ ] All critical information is preserved
- [ ] SKILL.md links to REFERENCE.md where appropriate
- [ ] Progressive disclosure is implemented
- [ ] Naming follows gerund convention (if renaming)
- [ ] Workflow checklist included (for complex skills)
