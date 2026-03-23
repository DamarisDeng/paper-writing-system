# Reference: Writing Paper

## Table of Contents

1. [Abstract Structure](#abstract-structure)
2. [Section Requirements](#section-requirements)
3. [LaTeX Math and Symbol Rules](#latex-math-and-symbol-rules)
4. [Troubleshooting](#troubleshooting)

---

## Abstract Structure

Use the template's `\abslabel{}` and `\absrule` commands:

| Subsection | Content | Length |
|-----------|---------|--------|
| IMPORTANCE | Why this study matters — gap in knowledge | 1-2 sentences |
| OBJECTIVE | Research aim, starting with "To determine..." or "To evaluate..." | 1 sentence |
| DESIGN, SETTING, AND PARTICIPANTS | Study design, data source, time period, sample size, eligibility | 2-3 sentences |
| EXPOSURE | Primary exposure/intervention description | 1 sentence |
| MAIN OUTCOMES AND MEASURES | Primary outcome definition and analytic approach | 1-2 sentences |
| RESULTS | Key demographics (N, age, sex), then main findings with effect sizes and CIs | 3-4 sentences |
| CONCLUSIONS AND RELEVANCE | Interpretation and implications | 1-2 sentences |

---

## Section Requirements

### Key Points Box

Fill the three fields in the `keypointsbox`:
- **Question**: One-sentence research question.
- **Findings**: Main quantitative result with effect size and CI.
- **Meaning**: Clinical/policy implication in one sentence.

### Introduction (Target: 1.0-1.25 pages, ~400-500 words; 3-5 paragraphs)

Structure:
1. **Opening**: Broad context — burden of disease, prevalence, public health significance.
2. **Background**: What is known — cite 3-4 references from the literature review.
3. **Gap**: What is not known — identify the specific knowledge gap.
4. **Objective**: Clear statement of what this study aims to do.

### Methods (Target: 1.5-1.75 pages, ~600-700 words)

Subsections:
- **Data**: Source, time period, population, sample selection, IRB status ("This study used publicly available, deidentified data and was exempt from institutional review board approval.").
- **Outcome Measures**: Define primary and secondary outcomes from `research_questions.json`.
- **Exposure**: Define the exposure variable and how groups were defined.
- **Covariates**: List all adjustment variables with justification.
- **Statistical Analysis**: Describe methods from `analysis_results.json` → `primary_analysis.method`. State software ("Analyses were performed using Python version 3.x with statsmodels and pandas."), significance level ("Statistical significance was set at 2-sided P < .05."), and any special techniques.

### Results (Target: 2.5-3.5 pages, ~1,000-1,400 words)

Note: Figures and tables within this section will occupy ~0.5-1 page, reducing available word space.

Structure:
1. **Sample description**: Reference Table 1. Report total N, exposure group sizes, key demographics.
2. **Primary analysis**: Report the main finding with effect size, CI, and P value. Reference the primary results figure.
3. **Secondary/sensitivity analyses**: Report additional findings. Reference supplementary tables/figures.

### Discussion (Target: 2.5-3.0 pages, ~1,000-1,200 words; 4-6 paragraphs)

Structure:
1. **Summary**: Restate the main finding in context.
2. **Comparison**: How results compare to prior studies (cite references).
3. **Mechanisms**: Possible explanations for the findings.
4. **Implications**: Clinical, policy, or public health significance.
5. **Limitations** subsection: Honest assessment from `research_questions.json` → `feasibility_assessment.limitations`.
6. **Future directions**: 1-2 sentences on what research should follow.

### Conclusions (Target: ~0.25 pages, ~75-100 words)

2-3 sentences. Summarize the main finding and its primary implication. Do not overstate.

### Supplement

On a new page after references:
```latex
\clearpage
\section*{Supplement 1}
\subsection*{eAppendix 1. Statistical Models and Methods Details}
\subsection*{eTable 1. Supplementary Table Title}
\subsection*{eFigure 1. Supplementary Figure Title}
```

---

## LaTeX Math and Symbol Rules

**CRITICAL**: Always use LaTeX commands, NEVER Unicode characters for mathematical symbols. Unicode characters (β, α, χ², ≥, ≤, μ, σ) cause LaTeX compilation failures or inconsistent rendering.

| Symbol | Use | NEVER |
|--------|-----|-------|
| Greek letters | `\alpha`, `\beta`, `\chi`, `\mu`, `\sigma`, `\kappa`, `\lambda`, `\tau` | `α`, `β`, `χ`, `μ`, `σ`, `κ`, `λ`, `τ` |
| Comparisons | `\geq`, `\leq`, `\approx`, `\neq`, `\pm` | `≥`, `≤`, `≈`, `≠`, `±` |
| Superscript | `^2`, `^{2}` | `²` |
| Subscript | `_2`, `_{2}` | `₂` |
| Math mode | `$\beta = 0.5$` or `\(\beta = 0.5\)` | `β = 0.5` (plain text) |
| P-value | `$P < .05$` or `\textit{P} < .05` | `P < .05` (no formatting) |
| CI notation | `95\% CI` (with escaped percent) | `95% CI` (unescaped) |

**Before finalizing paper.tex, search for common Unicode patterns and replace with LaTeX:**
```bash
grep -n '[αβγδεζηθικλμνξοπρστυφχψω]' paper.tex
grep -n '[≥≤≈≠±]' paper.tex
grep -n '[²³¹₀₁₂₃₄₅₆₇₈₉]' paper.tex
```

**Examples of correct usage:**
- "β coefficient (95% CI, 0.12-0.45)" → `$\beta$ coefficient (95\% CI, 0.12-0.45)"
- "P ≤ .05" → "$P \leq .05$"
- "H₂O" → "H$_2$O"
- "χ² test" → "$\chi^2$ test"

---

## Troubleshooting

### If Upstream Files Are Missing

- `2_scoring/ranked_questions.json` — Re-run the score-and-rank stage
- `3_analysis/analysis_results.json` — Re-run the statistical-analysis stage
- `4_figures/manifest.json` — Re-run the generate-figures stage
- `5_references/references.bib` — Re-run the literature-review stage
- `template.tex` — Verify `workflow/skills/write-paper/templates/template.tex` exists

### If LaTeX Compilation Fails

1. Check `paper.log` for the specific error (search for `!` which indicates errors)
2. Common issues:
   - Undefined control sequence: Usually a typo or missing package
   - File not found: Check `\includegraphics{}` and `\input{}` paths
   - Missing `$`: Math symbols outside math mode
   - Unicode character: Replace with LaTeX command (see LaTeX Math Rules)
3. Fix the error and recompile

### If Citation Keys Don't Resolve

1. Verify the key in `\cite{key}` matches an `@entry{key,}` in `references.bib`
2. Check for typos in citation keys (case-sensitive)
3. Ensure `references.bib` is in the same directory as `paper.tex`
4. Re-run bibtex after modifying the bibliography

### If Figures/Tables Don't Appear

1. Verify files exist in `6_paper/figures/` or `6_paper/tables/`
2. Check file paths in `\includegraphics{}` and `\input{}` are relative to `6_paper/`
3. For tables, ensure the `.tex` file is valid LaTeX table code

### Writing Style Rules

- **Tense**: Past tense for Methods and Results ("We used...", "The analysis showed..."). Present tense for established facts in Introduction/Discussion.
- **Voice**: Third person preferred. "This study examined..." not "We examined..." (JAMA style).
- **Numbers**: Spell out numbers below 10 at the start of a sentence. Use numerals with units (e.g., "5 mg", "3 years"). Report P values as "P < .05" or "P = .03" (no leading zero).
- **Statistics**: Always report as: "estimate (95% CI, lower-upper; P = .xxx)". Example: "OR, 1.45 (95% CI, 1.22-1.72; P < .001)".
- **Abbreviations**: Define on first use. Standard abbreviations (CI, OR, HR, SD) need not be defined.
- **Citations**: Use `\cite{key}` which produces superscript numbers via natbib.
- **Figures/Tables**: Reference as "Figure 1", "Table 1", "eTable 1" in text.
- **Page limit**: Main text ≤10 pages (~3,500-4,000 words excluding references and supplement).
