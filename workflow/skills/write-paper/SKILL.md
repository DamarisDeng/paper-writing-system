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

1. **`<output_folder>/2_research_question/research_questions.json`** — Research questions, variable roles, study design.
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

#### 3.5 Introduction (3-5 Paragraphs)

Structure:
1. **Opening**: Broad context — burden of disease, prevalence, public health significance.
2. **Background**: What is known — cite 3-4 references from the literature review.
3. **Gap**: What is not known — identify the specific knowledge gap.
4. **Objective**: Clear statement of what this study aims to do.

#### 3.6 Methods

Subsections:
- **Data**: Source, time period, population, sample selection, IRB status ("This study used publicly available, deidentified data and was exempt from institutional review board approval.").
- **Outcome Measures**: Define primary and secondary outcomes from `research_questions.json`.
- **Exposure**: Define the exposure variable and how groups were defined.
- **Covariates**: List all adjustment variables with justification.
- **Statistical Analysis**: Describe methods from `analysis_results.json` → `primary_analysis.method`. State software ("Analyses were performed using Python version 3.x with statsmodels and pandas."), significance level ("Statistical significance was set at 2-sided P < .05."), and any special techniques.

#### 3.7 Results

Structure:
1. **Sample description**: Reference Table 1. Report total N, exposure group sizes, key demographics.
2. **Primary analysis**: Report the main finding with effect size, CI, and P value. Reference the primary results figure.
3. **Secondary/sensitivity analyses**: Report additional findings. Reference supplementary tables/figures.

#### 3.8 Discussion (4-6 Paragraphs)

Structure:
1. **Summary**: Restate the main finding in context.
2. **Comparison**: How results compare to prior studies (cite references).
3. **Mechanisms**: Possible explanations for the findings.
4. **Implications**: Clinical, policy, or public health significance.
5. **Limitations** subsection: Honest assessment from `research_questions.json` → `feasibility_assessment.limitations`.
6. **Future directions**: 1-2 sentences on what research should follow.

#### 3.9 Conclusions

2-3 sentences. Summarize the main finding and its primary implication. Do not overstate.

#### 3.10 References

```latex
{\fontsize{8.5}{10.5}\selectfont
\bibliographystyle{vancouver}
\bibliography{references}
}
```

#### 3.11 Supplement

On a new page after references:
```latex
\clearpage
\section*{Supplement 1}
\subsection*{eAppendix 1. Statistical Models and Methods Details}
% Detailed model specifications, equations, assumption checks

\subsection*{eTable 1. Supplementary Table Title}
% Additional table from analysis

\subsection*{eFigure 1. Supplementary Figure Title}
% Additional figure from analysis
```

### Step 4: Writing Style Rules

- **Tense**: Past tense for Methods and Results ("We used...", "The analysis showed..."). Present tense for established facts in Introduction/Discussion.
- **Voice**: Third person preferred. "This study examined..." not "We examined..." (JAMA style).
- **Numbers**: Spell out numbers below 10 at the start of a sentence. Use numerals with units (e.g., "5 mg", "3 years"). Report P values as "P < .05" or "P = .03" (no leading zero).
- **Statistics**: Always report as: "estimate (95% CI, lower-upper; P = .xxx)". Example: "OR, 1.45 (95% CI, 1.22-1.72; P < .001)".
- **Abbreviations**: Define on first use. Standard abbreviations (CI, OR, HR, SD) need not be defined.
- **Citations**: Use `\cite{key}` which produces superscript numbers via natbib.
- **Figures/Tables**: Reference as "Figure 1", "Table 1", "eTable 1" in text. Include figures/tables using `\input{tables/table1.tex}` for tables and `\includegraphics` for figures.
- **Page limit**: Main text ≤10 pages (excluding references and supplement).

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
