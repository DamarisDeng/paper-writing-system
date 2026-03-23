---
name: write-paper
model: high
description: >
  Draft a complete JAMA Network Open paper in LaTeX using the template and
  all upstream outputs. Produces paper.tex with structured abstract (7
  subsections), Key Points box, Introduction, Methods, Results, Discussion,
  Limitations, Conclusions, and Supplement. Follows JAMA writing conventions.
  Triggers on: "write paper", "draft paper", "write the manuscript",
  "generate LaTeX", or any request to produce the paper from analysis results.
argument-hint: <output_folder>
---

# Write Paper

Draft a complete JAMA Network Open research paper in LaTeX, integrating all upstream analysis outputs.

## Usage

```
/write-paper <output_folder>
```

Reads from all upstream stage outputs in `<output_folder>/` and the template at `workflow/skills/write-paper/templates/template.tex`. Writes to `<output_folder>/6_paper/`.

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/6_paper/progress.json`.

**Steps tracked:**
- `step_1_load_inputs`: Load all upstream outputs and template
- `step_2_copy_assets`: Copy figures, tables, references to stage folder
- `step_3_draft_paper`: Write complete paper.tex content
- `step_4_validate`: Validate LaTeX structure and completeness

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

| If `progress.json` says last completed is... | Resume at |
|----------------------------------------------|-----------|
| `step_1_load_inputs` | Step 2: Copy assets |
| `step_2_copy_assets` | Step 3: Draft paper |
| `step_3_draft_paper` | Step 4: Validate |
| `step_4_validate` | Complete (skip) |

## Instructions

You are a medical writer experienced in drafting JAMA Network Open research articles. Write a complete, publication-ready manuscript integrating statistical results, figures, tables, and references.

**Initialize progress tracker at start:**
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker

tracker = create_stage_tracker(output_folder, "write_paper",
    ["step_1_load_inputs", "step_2_copy_assets", "step_3_draft_paper", "step_4_validate"])
```

### Step 1: Load All Inputs

Read these files:

1. **`<output_folder>/2_scoring/ranked_questions.json`** — Research questions, variable roles, study design.
1b. **`<output_folder>/decision_log.json`** (if exists) — Question selection audit trail. Use to describe the question selection process in the Methods section (e.g., number of candidates considered, scoring approach, any feedback cycles).
2. **`<output_folder>/3_analysis/analysis_results.json`** — All statistical results.
3. **`<output_folder>/4_figures/manifest.json`** — List of figures and tables with titles and file paths.
4. **`<output_folder>/5_references/references.bib`** — Bibliography entries.
5. **`workflow/skills/write-paper/templates/template.tex`** — The JAMA Network Open LaTeX template.
6. **`<output_folder>/1_data_profile/profile.json`** — Dataset context for data description.

### Step 2: Copy Assets

1. Copy `references.bib` to `<output_folder>/6_paper/references.bib`.
2. Copy all figure files (`.png` and `.pdf`) from `<output_folder>/4_figures/figures/` to `<output_folder>/6_paper/figures/`.
3. Copy all table `.tex` files from `<output_folder>/4_figures/tables/` to `<output_folder>/6_paper/tables/`.

### Step 3: Draft the Paper

Using the template structure from `workflow/skills/write-paper/templates/template.tex`, write `<output_folder>/6_paper/paper.tex` with these sections:

#### 3.1 Preamble and Metadata

- Copy the full preamble from the template (all `\usepackage`, color definitions, style settings).
- Update `\jamashorttitle{}` with a short version of the paper title.
- Update `\jamasubject{}` with the appropriate subject area (e.g., "Public Health").

#### 3.2 Title and Authors

```latex
{\sffamily\bfseries\fontsize{18}{21}\selectfont\color{jamadarkgray}
Full Title of the Paper: A Descriptive Subtitle\par}
```

- Title: Concise, informative, ≤20 words. Include study design if space permits.
- Authors: List "AI-Generated Research Paper; Claude, Anthropic" as the author line.

#### 3.3 Abstract (Structured, 7 Subsections)

Use the template's `\abslabel{}` and `\absrule` commands. See `references/REFERENCE.md: Abstract Structure` for the complete table of subsections and content requirements.

#### 3.4 Key Points Box

Fill the three fields: Question, Findings, Meaning. See `references/REFERENCE.md: Section Requirements`.

#### 3.5-3.9 Main Sections (Introduction, Methods, Results, Discussion, Conclusions)

See `references/REFERENCE.md: Section Requirements` for detailed content requirements and target lengths for each section.

#### 3.10 References, Supplement, LaTeX Math Rules

See `references/REFERENCE.md: LaTeX Math and Symbol Rules` for critical LaTeX math formatting rules (always use LaTeX commands, never Unicode).

### Step 6: Validate

Before saving, verify:

- [ ] `paper.tex` is valid LaTeX (balanced braces, environments, commands)
- [ ] All `\cite{}` keys match entries in `references.bib`
- [ ] All `\includegraphics{}` paths point to files that exist in `6_paper/figures/`
- [ ] All `\input{}` paths point to files that exist in `6_paper/tables/`
- [ ] Abstract contains all 7 required subsections
- [ ] Key Points box has Question, Findings, and Meaning
- [ ] Statistical results in text match `analysis_results.json` values exactly
- [ ] No placeholder text remains (search for "TODO", "XXX", "PLACEHOLDER")
- [ ] `references.bib` is copied to `<output_folder>/6_paper/`
- [ ] No Unicode math symbols (check with grep commands above)

**LaTeX compilation validation:**

Run the following command to validate the LaTeX file compiles without fatal errors:
```bash
cd <output_folder>/6_paper && latexmk -pdf -interaction=nonstopmode paper.tex
```

Alternatively, use the traditional pdflatex+bibtex workflow:
```bash
cd <output_folder>/6_paper
pdflatex -interaction=nonstopmode paper.tex
bibtex paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
```

**What constitutes a fatal error vs. warning:**
- **Fatal**: Compilation stops with `!` error, PDF not generated, undefined control sequence, missing file errors
- **Warning**: Overfull/underfull hbox boxes, citation warnings, font warnings — these are acceptable for draft

If compilation fails, check the `.log` file for specific error messages and fix accordingly.

### Step 7: Troubleshooting

See `references/REFERENCE.md: Troubleshooting` for common issues and solutions related to:
- Missing upstream files
- LaTeX compilation failures
- Citation resolution
- Figure/table display issues

The reference also includes writing style rules.

**Progress checkpoint - Mark stage complete:**
```python
from progress_utils import complete_stage

complete_stage(output_folder, "write_paper",
               expected_outputs=["6_paper/paper.tex", "6_paper/references.bib"])
```

## Output Contract

**`<output_folder>/6_paper/paper.tex`** — Complete LaTeX source file.

**`<output_folder>/6_paper/references.bib`** — Copy of bibliography.

**`<output_folder>/6_paper/figures/`** — Copies of all figure files (.png, .pdf).

**`<output_folder>/6_paper/tables/`** — Copies of all LaTeX table files (.tex).
