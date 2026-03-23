# Reference: Compile and Review

## Table of Contents

1. [Common LaTeX Errors and Fixes](#common-latex-errors-and-fixes)
2. [Self-Review Checklist](#self-review-checklist)
3. [Edge Cases](#edge-cases)

---

## Common LaTeX Errors and Fixes

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

---

## Self-Review Checklist

### Content Completeness

- [ ] Title is present and descriptive
- [ ] Abstract has all 7 JAMA subsections (Importance, Objective, Design/Setting/Participants, Exposure, Main Outcomes, Results, Conclusions)
- [ ] Key Points box has Question, Findings, and Meaning
- [ ] Introduction ends with a clear study objective
- [ ] Methods describes data source, outcomes, exposures, covariates, and statistical analysis
- [ ] Results begins with sample description and references Table 1
- [ ] Discussion includes comparison to prior literature
- [ ] Limitations subsection is present and substantive
- [ ] Conclusions section exists

### Formatting

- [ ] Paper is ≤10 pages (excluding references and supplement)
- [ ] All figures render correctly (no broken image placeholders)
- [ ] All tables render correctly (proper alignment, no overflow)
- [ ] References are numbered and formatted in Vancouver style
- [ ] No "??" markers (unresolved references)
- [ ] No "[?]" markers (unresolved citations)
- [ ] Page numbers are correct

### Statistical Consistency

- [ ] Numbers in abstract match numbers in results text
- [ ] Effect sizes in Key Points match primary analysis results
- [ ] Sample sizes are consistent throughout (abstract = methods = results)
- [ ] P-values are formatted correctly (P = .03, P < .001 — no leading zero)
- [ ] All CIs are reported as "95% CI, lower-upper"

### JAMA Style

- [ ] No first-person pronouns ("we", "our") — use "This study" or passive voice
- [ ] Past tense in Methods and Results
- [ ] Superscript citation numbers
- [ ] JAMA header bar and footer appear on all pages
- [ ] Section headings in crimson sans-serif

---

## Edge Cases

### BibTeX Not Available

If `bibtex` is not installed, use manual bibliography:
```latex
\begin{thebibliography}{99}
\bibitem{Smith2023} Smith JA, Doe JB. Title. \textit{JAMA}. 2023;329(12):1023-1034.
\end{thebibliography}
```

### Figures Missing

If figure files are missing from `6_paper/figures/`, attempt to copy them from `4_figures/figures/`. If still missing, comment out the `\includegraphics` line and add a placeholder note.

### Package Not Installed

If a LaTeX package is missing, either install it via `tlmgr install <package>` or remove the dependency and use a simpler alternative.
