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

Reads from all upstream stage outputs in `<output_folder>/` and the template at `sample/tex/template.tex`. Writes to `<output_folder>/6_paper/`.

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
5. **`sample/tex/template.tex`** — The JAMA Network Open LaTeX template.
6. **`<output_folder>/1_data_profile/profile.json`** — Dataset context for data description.

### Step 2: Copy Assets

1. Copy `references.bib` to `<output_folder>/6_paper/references.bib`.
2. Copy all figure files (`.png` and `.pdf`) from `<output_folder>/4_figures/figures/` to `<output_folder>/6_paper/figures/`.
3. Copy all table `.tex` files from `<output_folder>/4_figures/tables/` to `<output_folder>/6_paper/tables/`.

### Step 3: Draft the Paper

Using the template structure from `sample/tex/template.tex`, write `<output_folder>/6_paper/paper.tex` with these sections:

#### 3.1 Preamble and Metadata

- Copy the full preamble from the template (all `\usepackage`, color definitions, style settings).
- **Font encoding fix**: ensure the preamble contains `\usepackage[T1]{fontenc}` and `\usepackage{lmodern}` (before `\usepackage{times}`). This prevents font-size substitution warnings for fractional sizes (8.5pt, 7.5pt) used in JAMA-style captions.
- **Remove `\usepackage{microtype}`** if present. The `times`/`helvet` fonts have no protrusion tables; loading microtype produces ~20 harmless but noisy warnings with no benefit for these fonts.
- Update `\jamashorttitle{}` with a short version of the paper title.
- Update `\jamasubject{}` with the appropriate subject area (e.g., "Public Health").

#### 3.2 Title and Authors

```latex
{\sffamily\bfseries\fontsize{18}{21}\selectfont\color{jamadarkgray}
Full Title of the Paper: A Descriptive Subtitle\par}
```

- Title: Concise, informative, ≤20 words. Include study design if space permits.
- Authors: List "Junyang Deng; Shupeng Luxu; Nuo Ding; Claude" as the author line.

#### 3.3 Abstract (Structured, 7 Subsections)

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

#### 3.4 Key Points Box

Fill the three fields in the `keypointsbox`:
- **Question**: One-sentence research question.
- **Findings**: Main quantitative result with effect size and CI.
- **Meaning**: Clinical/policy implication in one sentence.

#### 3.5 Introduction (Target: 1.0-1.25 pages, ~400-500 words; 3-5 paragraphs)

Structure:
1. **Opening**: Broad context — burden of disease, prevalence, public health significance.
2. **Background**: What is known — cite 3-4 references from the literature review.
3. **Gap**: What is not known — identify the specific knowledge gap.
4. **Objective**: Clear statement of what this study aims to do.

#### 3.6 Methods (Target: 1.5-1.75 pages, ~600-700 words)

Subsections:
- **Data**: Source, time period, population, sample selection, IRB status ("This study used publicly available, deidentified data and was exempt from institutional review board approval.").
- **Outcome Measures**: Define primary and secondary outcomes from `research_questions.json`.
- **Exposure**: Define the exposure variable and how groups were defined.
- **Covariates**: List all adjustment variables with justification.
- **Statistical Analysis**: Describe methods from `analysis_results.json` → `primary_analysis.method`. State software ("Analyses were performed using Python version 3.x with statsmodels and pandas."), significance level ("Statistical significance was set at 2-sided P < .05."), and any special techniques.

#### 3.7 Results (Target: 2.5-3.5 pages, ~1,000-1,400 words)

Note: Figures and tables within this section will occupy ~0.5-1 page, reducing available word space.

Structure:
1. **Sample description**: Reference Table 1. Report total N, exposure group sizes, key demographics.
2. **Primary analysis**: Report the main finding with effect size, CI, and P value. Reference the primary results figure.
3. **Secondary/sensitivity analyses**: Report additional findings. Reference supplementary tables/figures.

#### 3.8 Discussion (Target: 2.5-3.0 pages, ~1,000-1,200 words; 4-6 paragraphs)

Structure:
1. **Summary**: Restate the main finding in context.
2. **Comparison**: How results compare to prior studies (cite references).
3. **Mechanisms**: Possible explanations for the findings.
4. **Implications**: Clinical, policy, or public health significance.
5. **Limitations** subsection: Honest assessment from `research_questions.json` → `feasibility_assessment.limitations`.
6. **Future directions**: 1-2 sentences on what research should follow.

#### 3.9 Conclusions (Target: ~0.25 pages, ~75-100 words)

2-3 sentences. Summarize the main finding and its primary implication. Do not overstate.

#### 3.10 References

```latex
{\fontsize{8.5}{10.5}\selectfont
\bibliographystyle{vancouver}
\bibliography{references}
}
```

#### 3.11 Supplement (Auto-Generated from Analysis Results)

**CRITICAL**: The supplement must be populated with actual statistical content from `analysis_results.json`, NOT placeholder text. Extract information and generate well-written supplementary content using the LLM.

On a new page after references:
```latex
\clearpage
\section*{Supplement 1}
```

Then generate these sections by extracting from `analysis_results.json`:

---

**eAppendix 1: Statistical Model Specification**

Extract from `analysis_results.json` → `primary_analysis`:
- `method` (e.g., "OLS Linear Regression", "Logistic Regression", "Poisson Regression")
- `outcome` (primary outcome variable)
- `exposure` (primary exposure variable)
- `models[].covariates` (list of adjustment variables)

Generate:
1. **Model equation in proper LaTeX math format** — Use the appropriate form for the method:
   - OLS: `$Y = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \cdots + \beta_k X_k + \epsilon$`
   - Logistic: `$\operatorname{logit}[P(Y=1)] = \beta_0 + \sum_{j=1}^{k} \beta_j X_j$`
   - Poisson: `$\log(\mathbb{E}[Y]) = \beta_0 + \sum_{j=1}^{k} \beta_j X_j$`
   - Cox: `$h(t|X) = h_0(t) \exp(\sum_{j=1}^{k} \beta_j X_j)$`

2. **Variable definitions** — Define each term in the equation:
   - Outcome variable ($Y$): [from `primary_analysis.outcome`]
   - Exposure variable ($X_1$): [from `primary_analysis.exposure`]
   - Covariates ($X_2, \ldots, X_k$): [list from `primary_analysis.models[].covariates`]

3. **Software and packages** — State software used:
   - "Analyses were performed using Python [version] with statsmodels [version] and pandas [version]."
   - Version info can be inferred from typical pipeline setup or use generic "Python 3.x" if not specified

4. **Estimation method** — Brief description:
   - OLS: "Ordinary least squares estimation was used to fit the linear regression model."
   - Logistic: "Maximum likelihood estimation was used to fit the logistic regression model."
   - Include any special techniques (robust standard errors, clustering, etc.)

Example LaTeX structure:
```latex
\subsection*{eAppendix 1. Statistical Model Specification}

The primary analysis used [method] to examine the association between [exposure] and [outcome]. The model was specified as:

\[
\operatorname{logit}[P(Y=1)] = \beta_0 + \beta_1 \text{[Exposure]} + \beta_2 \text{[Covariate}_1] + \beta_3 \text{[Covariate}_2] + \cdots + \beta_k \text{[Covariate}_{k-1}]
\]

where $Y$ represents [outcome description], $\text{[Exposure]}$ indicates [exposure description], and the remaining terms represent adjustment variables: [list covariates from model].

Model parameters were estimated using maximum likelihood. All analyses were performed using Python 3.x with statsmodels.
```

---

**eAppendix 2: Model Assumption Checks and Diagnostic Results**

Extract from `analysis_results.json` → look for any assumption-related fields:
- Check `primary_analysis.assumption_checks` if it exists
- Look for `primary_analysis.model_fit` (R², AIC, BIC, etc.)
- Use `primary_analysis.models[].r_squared`, `adj_r_squared`, `df_resid` for fit statistics

Generate:
1. **Model fit statistics** — Report for each model:
   - Sample size ($N$)
   - Residual degrees of freedom
   - $R^2$ (for OLS) or pseudo-$R^2$ (for logistic)
   - AIC/BIC if available

2. **Assumption checks** — If available in the results, report:
   - Name of each assumption checked
   - Result (passed/failed)
   - Interpretation in plain language
   - Any remedial actions taken

3. **If no formal assumption checks in JSON**, still document:
   - The assumptions inherent to the chosen method
   - "Formal diagnostic tests were not performed; this is a limitation."

Example LaTeX structure:
```latex
\subsection*{eAppendix 2. Model Fit and Assumption Checks}

\textbf{Model Fit Statistics.} Table eTable 1 presents the full model results for all specifications. The primary model (Model [n]) achieved an $R^2$ of [value], indicating that [percent]\% of the variance in [outcome] was explained by the included predictors.

\textbf{Assumption Checks.} [If available: "The following assumptions were evaluated: [list]. [Assumption name] was assessed using [test name]; results indicated [passed/failed] (P = [value])."]

[If assumptions failed: "To address [issue], [remedial action taken] was used."]
```

---

**eTable 1: Full Model Results**

Extract from `analysis_results.json` → `primary_analysis.models[]` and generate a complete coefficient table.

For each model in the array, create rows showing:
- Variable name
- Estimate ($\beta$)
- Standard error (SE)
- 95\% Confidence interval (CI)
- P-value

Use JAMA table style (no vertical rules, booktabs, `\toprule`, `\midrule`, `\bottomrule`):

```latex
\subsection*{eTable 1. Full Model Results for Association Between [Exposure] and [Outcome]}

\begin{table}[H]
\centering
\sffamily\fontsize{8.5}{11}\selectfont
\caption{Complete Regression Results for All Model Specifications}
\label{tab:e1}

\begin{tabularx}{\textwidth}{@{} >{\raggedright\arraybackslash}p{4.5cm}
  *{4}{>{\centering\arraybackslash}X} @{}}

\toprule
\textbf{Variable} & \textbf{Model 1\newline(Unadjusted)} & \textbf{Model 2\newline(Region Adjusted)} & \textbf{Model 3\newline(Fully Adjusted)} \\
\cmidrule(lr){1-1} \cmidrule(lr){2-2} \cmidrule(lr){3-3} \cmidrule(lr){4-4}
& $\beta$ (SE) & $\beta$ (SE) & $\beta$ (SE) \\
\midrule

Intercept & [estimate] ([SE]) & [estimate] ([SE]) & [estimate] ([SE]) \\
[Exposure] & [estimate] ([SE]) & [estimate] ([SE]) & [estimate] ([SE]) \\
[Covariate 1] & & [estimate] ([SE]) & [estimate] ([SE]) \\
[Covariate 2] & & [estimate] ([SE]) & [estimate] ([SE]) \\
\midrule
\multicolumn{4}{@{}l}{\textbf{Model fit}} \\
$N$ & [n] & [n] & [n] \\
$R^2$ & [r2] & [r2] & [r2] \\
\bottomrule
\end{tabularx}

\vspace{4pt}
\begin{flushleft}
\fontsize{7.5}{9.5}\selectfont\rmfamily\color{jamagray}
SE indicates standard error. Model 1 includes [exposure] only. Model 2 adjusts for [covariates]. Model 3 adds [additional covariates].
\end{flushleft}

\end{table}
```

**Important formatting rules:**
- Use `\beta` for the coefficient symbol, never `β`
- Use SE for standard error, CI for confidence interval
- For p-values, use the format from the JSON (e.g., "<0.001" or actual value)
- Escape percent signs: `95\%` not `95%`

---

**eTable 2: Sensitivity Analysis Summary** (if applicable)

Extract from `analysis_results.json` → `sensitivity_analyses[]`

If sensitivity analyses exist, create a comparison table:

```latex
\subsection*{eTable 2. Sensitivity Analysis Results}

\begin{table}[H]
\centering
\sffamily\fontsize{8.5}{11}\selectfont
\caption{Comparison of Primary Analysis With Sensitivity Analyses}
\label{tab:e2}

\begin{tabularx}{\textwidth}{@{} >{\raggedright\arraybackslash}p{5cm}
  *{2}{>{\centering\arraybackslash}X} @{}}

\toprule
\textbf{Analysis} & \textbf{Estimate (95\% CI)} & \textbf{P Value} \\
\midrule
Primary analysis & [estimate] ([CI]) & [p-value] \\
[Sensitivity 1 name] & [estimate] ([CI]) & [p-value] \\
[Sensitivity 2 name] & [estimate] ([CI]) & [p-value] \\
\bottomrule
\end{tabularx}

\vspace{4pt}
\begin{flushleft}
\fontsize{7.5}{9.5}\selectfont\rmfamily\color{jamagray}
CI indicates confidence interval. [Sensitivity analysis descriptions from JSON].
\end{flushleft}

\end{table}
```

If no sensitivity analyses exist, omit this section entirely.

---

**eFigure 1 (Optional)** — If there are supplementary figures in `4_figures/`, include them:
```latex
\subsection*{eFigure 1. [Figure Title]}

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{figures/figureX.pdf}
\caption{[Caption from manifest.json]}
\label{fig:e1}
\end{figure}
```

---

**Content Generation Guidelines:**

1. **Write in natural prose**, not just data dumps. The supplement should be readable.
2. **Use exact values** from `analysis_results.json` — no fabrication.
3. **Interpret results** where appropriate (e.g., "The association remained significant after adjustment...").
4. **Follow LaTeX math rules** from Section 3.12 — use `\beta`, `\leq`, etc., never Unicode.
5. **No placeholder text** — Every section must have actual content based on the analysis.
6. **If a data field is missing**, state what was done instead (e.g., "Formal assumption tests were not conducted.") rather than leaving blanks.

#### 3.12 LaTeX Math and Symbol Rules

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

### Step 4: Writing Style Rules

- **Tense**: Past tense for Methods and Results ("We used...", "The analysis showed..."). Present tense for established facts in Introduction/Discussion.
- **Voice**: Third person preferred. "This study examined..." not "We examined..." (JAMA style).
- **Numbers**: Spell out numbers below 10 at the start of a sentence. Use numerals with units (e.g., "5 mg", "3 years"). Report P values as "P < .05" or "P = .03" (no leading zero).
- **Statistics**: Always report as: "estimate (95% CI, lower-upper; P = .xxx)". Example: "OR, 1.45 (95% CI, 1.22-1.72; P < .001)".
- **Abbreviations**: Define on first use. Standard abbreviations (CI, OR, HR, SD) need not be defined.
- **Citations**: Use `\cite{key}` which produces superscript numbers via natbib.
- **Figures/Tables**: Reference as "Figure 1", "Table 1", "eTable 1" in text. Include figures/tables using `\input{tables/table1.tex}` for tables and `\includegraphics` for figures.
- **Page limit**: Main text ≤10 pages (~3,500-4,000 words excluding references and supplement). Target ~400 words per page accounting for headings, figures, and tables.

### Step 5: Include Figures and Tables

For figures:
```latex
\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{figures/figure1.pdf}
\caption{Descriptive title from manifest.json}
\label{fig:figure1}
\end{figure}
```

For tables, input the pre-generated `.tex` file:
```latex
\input{tables/table1.tex}
```

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
- [ ] **Supplement section is populated** (eAppendix 1 contains actual model equations, not placeholder text)
- [ ] **Model equations present in LaTeX math format** (using `\beta`, `\logit`, etc., not Unicode)
- [ ] **Assumption checks are documented** with interpretations
- [ ] **eTable 1 contains full model results** with all covariates from `analysis_results.json`

**LaTeX compilation validation:**

Run the following command to validate the LaTeX file compiles without fatal errors:
```bash
cd <output_folder>/6_paper && latexmk -pdf -interaction=nonstopmode paper.tex
```

Alternatively, use the traditional pdflatex+bibtex workflow. **You must run exactly 4 commands in sequence — do not skip passes:**
```bash
cd <output_folder>/6_paper
pdflatex -interaction=nonstopmode paper.tex   # pass 1: builds aux, may show ?? in page numbers
bibtex paper                                   # resolves citations
pdflatex -interaction=nonstopmode paper.tex   # pass 2: reads citations + lastpage label
pdflatex -interaction=nonstopmode paper.tex   # pass 3: resolves all cross-references, ?? disappears
```

**Why 3 pdflatex passes are required:**
- Pass 1: Writes `\newlabel{LastPage}` and citation labels to `.aux` — page numbers show `??`
- Pass 2: Reads labels from `.aux`; resolves citations but may still have stale references
- Pass 3: All labels stable — `\pageref{LastPage}` correctly shows total page count

**After compilation, verify there are no `??` in the PDF:**
```bash
pdftotext paper.pdf - | grep "??"
```
If any `??` remain, run `pdflatex` one more time.

**What constitutes a fatal error vs. warning:**
- **Fatal**: Compilation stops with `!` error, PDF not generated, undefined control sequence, missing file errors
- **Warning**: Overfull/underfull hbox boxes, citation warnings, font warnings — these are acceptable for draft
- **`?? in page numbers`**: Not a warning — means too few pdflatex passes. Run another pass.

If compilation fails, check the `.log` file for specific error messages and fix accordingly.

### Step 7: Troubleshooting

**If upstream files are missing:**
- `2_scoring/ranked_questions.json` — Re-run the score-and-rank stage
- `3_analysis/analysis_results.json` — Re-run the statistical-analysis stage
- `4_figures/manifest.json` — Re-run the generate-figures stage
- `5_references/references.bib` — Re-run the literature-review stage
- `template.tex` — Verify `sample/tex/template.tex` exists

**If LaTeX compilation fails:**
1. Check `paper.log` for the specific error (search for `!` which indicates errors)
2. Common issues:
   - Undefined control sequence: Usually a typo or missing package
   - File not found: Check `\includegraphics{}` and `\input{}` paths
   - Missing `$`: Math symbols outside math mode
   - Unicode character: Replace with LaTeX command (see Section 3.12)
3. Fix the error and recompile

**If citation keys don't resolve:**
1. Verify the key in `\cite{key}` matches an `@entry{key,}` in `references.bib`
2. Check for typos in citation keys (case-sensitive)
3. Ensure `references.bib` is in the same directory as `paper.tex`
4. Re-run bibtex after modifying the bibliography

**If figures/tables don't appear:**
1. Verify files exist in `6_paper/figures/` or `6_paper/tables/`
2. Check file paths in `\includegraphics{}` and `\input{}` are relative to `6_paper/`
3. For tables, ensure the `.tex` file is valid LaTeX table code

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
