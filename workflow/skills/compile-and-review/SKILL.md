---
name: compile-and-review
model: low
description: >
  Compile the LaTeX paper to PDF using pdflatex + bibtex, fix compilation
  errors (up to 3 retries), run a self-review checklist, apply revisions,
  and recompile. Copies final paper.pdf to the output root.
  Triggers on: "compile paper", "build PDF", "compile and review",
  "finalize paper", or any request to produce the final PDF from paper.tex.
argument-hint: <output_folder>
---

# Compile and Review

Compile `paper.tex` to PDF, fix any errors, run a self-review checklist, revise, and produce the final `paper.pdf`.

## Usage

```
/compile-and-review <output_folder>
```

Reads from `<output_folder>/6_paper/`. Writes final PDF to `<output_folder>/paper.pdf` while keeping `<output_folder>/6_paper/paper.pdf`.

## Progress Tracking

This skill uses `progress_utils.py` for stage-level progress tracking. Progress is saved to `<output_folder>/6_paper/progress.json`.

**Steps tracked:**
- `step_1_compile`: Initial LaTeX compilation
- `step_2_fix_errors`: Handle compilation errors (up to 3 retries)
- `step_3_self_review`: Run self-review checklist
- `step_4_apply_revisions`: Apply revisions and recompile
- `step_5_finalize`: Copy PDF and create compilation report

**Resume protocol:** If interrupted, read `progress.json` and continue from the last incomplete step.

## Instructions

You are a LaTeX typesetting expert and manuscript reviewer. Your job is to compile the paper, fix any issues, and ensure the final PDF meets JAMA Network Open standards.

**Initialize progress tracker at start:**
```python
import sys; sys.path.insert(0, "workflow/scripts")
from progress_utils import create_stage_tracker

tracker = create_stage_tracker(output_folder, "compile_and_review",
    ["step_1_compile", "step_2_fix_errors", "step_3_self_review",
     "step_4_apply_revisions", "step_5_finalize"])
```

### Step 1: Initial Compilation

Run the full LaTeX compilation sequence from the `<output_folder>/6_paper/` directory:

```bash
cd <output_folder>/6_paper && \
pdflatex -interaction=nonstopmode paper.tex && \
bibtex paper && \
pdflatex -interaction=nonstopmode paper.tex && \
pdflatex -interaction=nonstopmode paper.tex
```

The triple pdflatex run ensures cross-references, citations, and page numbers are fully resolved.

### Step 2: Handle Compilation Errors (Up to 3 Retries)

See `references/REFERENCE.md: Common LaTeX Errors and Fixes` for the complete error table and fixes.

### Step 3: Self-Review Checklist

See `references/REFERENCE.md: Self-Review Checklist` for the complete review checklist including content completeness, formatting, statistical consistency, and JAMA style.

### Step 6: Handle Edge Cases

See `references/REFERENCE.md: Edge Cases` for handling missing BibTeX, missing figures, and missing packages.

## Output Contract

**`<output_folder>/paper.pdf`** — The final compiled paper at output root (copied from stage folder).

**`<output_folder>/6_paper/paper.pdf`** — The same PDF remains in the stage folder for reference.

**`<output_folder>/6_paper/compilation_report.json`** — Compilation and review report:
```json
{
  "compilation_attempts": 1,
  "errors_fixed": [],
  "warnings_remaining": [],
  "review_checklist": {
    "content_complete": true,
    "formatting_correct": true,
    "statistics_consistent": true,
    "jama_style_compliant": true
  },
  "final_page_count": 8,
  "pdf_size_bytes": 524288
}
```
