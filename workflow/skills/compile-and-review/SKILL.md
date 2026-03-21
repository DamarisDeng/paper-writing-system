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

Reads from `<output_folder>/6_paper/`. Writes final PDF to `<output_folder>/paper.pdf`.

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

If compilation fails, follow this diagnostic process:

#### 2.1 Read the Log File

Read `<output_folder>/6_paper/paper.log` and identify errors. Focus on lines starting with `!` (fatal errors) and `LaTeX Warning` (non-fatal but important).

#### 2.2 Common Errors and Fixes

| Error Pattern | Cause | Fix |
|--------------|-------|-----|
| `! Undefined control sequence` | Missing package or typo in command | Add `\usepackage{}` or fix command name |
| `! Missing $ inserted` | Math symbol outside math mode | Wrap in `$...$` or use text-mode alternative |
| `! File not found` | Wrong figure/table path | Check paths in `\includegraphics` and `\input` |
| `! Extra alignment tab character` | Too many `&` in table row | Match column count to table spec |
| `! Misplaced \noalign` | `\hline` or `\toprule` in wrong position | Check table environment structure |
| `! LaTeX Error: Unknown float option 'H'` | Missing float package | Add `\usepackage{float}` |
| `Citation undefined` | BibTeX key mismatch | Verify `\cite{key}` matches `references.bib` entry |
| `Overfull \hbox` | Content too wide | Adjust table widths, wrap text, or use `\sloppy` |
| `! Emergency stop` | Fatal syntax error | Check last successful line and fix syntax near that point |

#### 2.3 Fix and Retry

1. Edit `paper.tex` to fix the identified error(s).
2. Re-run the full compilation sequence.
3. Repeat up to 3 times total.

If after 3 retries the paper still won't compile:
- Remove the problematic section (e.g., a figure that won't render).
- Add a comment in the source noting what was removed.
- Compile the reduced version.

### Step 3: Self-Review Checklist

After successful compilation, review the generated PDF against this checklist:

#### Content Completeness
- [ ] Title is present and descriptive
- [ ] Abstract has all 7 JAMA subsections (Importance, Objective, Design/Setting/Participants, Exposure, Main Outcomes, Results, Conclusions)
- [ ] Key Points box has Question, Findings, and Meaning
- [ ] Introduction ends with a clear study objective
- [ ] Methods describes data source, outcomes, exposures, covariates, and statistical analysis
- [ ] Results begins with sample description and references Table 1
- [ ] Discussion includes comparison to prior literature
- [ ] Limitations subsection is present and substantive
- [ ] Conclusions section exists

#### Formatting
- [ ] Paper is ≤10 pages (excluding references and supplement)
- [ ] All figures render correctly (no broken image placeholders)
- [ ] All tables render correctly (proper alignment, no overflow)
- [ ] References are numbered and formatted in Vancouver style
- [ ] No "??" markers (unresolved references)
- [ ] No "[?]" markers (unresolved citations)
- [ ] Page numbers are correct

#### Statistical Consistency
- [ ] Numbers in abstract match numbers in results text
- [ ] Effect sizes in Key Points match primary analysis results
- [ ] Sample sizes are consistent throughout (abstract = methods = results)
- [ ] P-values are formatted correctly (P = .03, P < .001 — no leading zero)
- [ ] All CIs are reported as "95% CI, lower-upper"

#### JAMA Style
- [ ] No first-person pronouns ("we", "our") — use "This study" or passive voice
- [ ] Past tense in Methods and Results
- [ ] Superscript citation numbers
- [ ] JAMA header bar and footer appear on all pages
- [ ] Section headings in crimson sans-serif

### Step 4: Apply Revisions

If the self-review identifies issues:

1. Edit `paper.tex` to fix each issue.
2. Re-run the full compilation sequence.
3. Verify fixes in the new PDF.

Common revision tasks:
- Fix inconsistent numbers between abstract and results.
- Add missing subsections.
- Fix formatting issues (overfull boxes, misaligned tables).
- Remove any remaining placeholder text.

### Step 5: Finalize

1. **Copy the final PDF** to the output root:
   ```bash
   cp <output_folder>/6_paper/paper.pdf <output_folder>/paper.pdf
   ```

2. **Create a compilation report** at `<output_folder>/6_paper/compilation_report.json`:
   ```json
   {
     "compilation_attempts": 2,
     "errors_fixed": [
       {"error": "Undefined citation 'Smith2023'", "fix": "Added missing BibTeX entry"}
     ],
     "warnings_remaining": [
       "Overfull \\hbox (2.3pt too wide) on page 4"
     ],
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

3. **Verify the final PDF** exists and is >10KB (a real PDF, not empty/corrupt).

**Progress checkpoint - Mark stage complete:**
```python
from progress_utils import complete_stage

complete_stage(output_folder, "compile_and_review",
               expected_outputs=["paper.pdf"])  # The primary deliverable at root
```

### Step 6: Handle Edge Cases

**BibTeX not available**: If `bibtex` is not installed, use `\begin{thebibliography}` with manually formatted entries as fallback:
```latex
\begin{thebibliography}{99}
\bibitem{Smith2023} Smith JA, Doe JB. Title. \textit{JAMA}. 2023;329(12):1023-1034.
\end{thebibliography}
```

**Figures missing**: If figure files are missing from `6_paper/figures/`, attempt to copy them from `4_figures/figures/`. If still missing, comment out the `\includegraphics` line and add a placeholder note.

**Package not installed**: If a LaTeX package is missing, either install it via `tlmgr install <package>` or remove the dependency and use a simpler alternative.

## Output Contract

**`<output_folder>/paper.pdf`** — The final compiled paper. This is the primary deliverable of the entire pipeline.

**`<output_folder>/6_paper/paper.pdf`** — Same PDF in the stage directory.

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
