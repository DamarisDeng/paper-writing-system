# Pipeline Audit & Improvement Plan

**Date:** 2026-03-20
**Status:** Draft — pending implementation
**Trigger:** End-to-end pipeline run produced poor output quality across all stages.

---

## 1. Stage-by-Stage Audit

| Stage | Name | Current Approach | Core Problem |
|-------|------|-----------------|--------------|
| 1 | Load & Profile | `load_and_profile.py` + LLM type corrections | LLM re-evaluates variable types that should follow deterministic rules |
| 2 | Research Questions | Opus LLM → PICO JSON + validation script | Group balance and exposure quality not computationally verified before PICO is locked |
| 3 | Acquire Data | Haiku LLM + download scripts | Hardcoded fallback URLs may be stale; no temporal overlap check between downloaded data and main dataset |
| 4 | Statistical Analysis | LLM generates ad-hoc Python scripts per run | Method selection drifts; assumption checks (VIF, Hosmer-Lemeshow) not guaranteed; no multiple-testing correction |
| 5 | Generate Figures | LLM writes matplotlib code per run | Silent failures on column name changes; no colorblind safety check; manifest not validated against disk |
| 6 | Literature Review | Haiku search + BibTeX syntax validation | Hallucinated references with plausible-looking DOIs; 12 refs is below JAMA norm of 20–40 |
| 7 | Write Paper | Opus reads raw upstream JSONs → paper.tex | No validated intermediate schema; key name drift silently drops values; number formatting inside LLM prompt |
| 8 | Compile & Review | pdflatex sequence + LLM "self-review" | Self-review is narrated, not programmatically verified (page count, unresolved refs, placeholder text) |

---

## 2. Per-Stage Improvement Plan

### Stage 1 — Load & Profile

**Problem in detail:**
`load_and_profile.py` correctly reads data, but the SKILL.md instructs the LLM to apply "type corrections" based on column names and sample values. This is a deterministic classification problem being given to a language model.

**Concrete fixes:**
1. Add a `type_rules.py` decision tree: if a column has ≤12 unique values and dtype is numeric → flag as potential categorical; if column name matches regex `(date|time|year|month|day)` → coerce to datetime; if all values are 0/1 → binary.
2. LLM role becomes **only**: write the `data_context.summary` string (a 2–3 sentence plain-language description of the dataset). Remove all other LLM involvement from Stage 1.
3. Store `type_overrides.json` alongside `profile.json` so downstream stages can reference the deterministic decisions.

**Replace with Python:** Yes — type inference, missingness stats, cardinality counts.
**Keep LLM:** Only for the human-readable dataset summary.

---

### Stage 2 — Research Questions

**Problem in detail:**
PICO formulation is correctly an Opus task. However, the instruction "exposure must have balanced groups" is prose in SKILL.md — the LLM may generate a PICO with a severely imbalanced exposure (e.g., 98% unexposed) that will produce unstable regression estimates.

**Concrete fixes:**
1. Before Opus is called, run `exposure_check.py`:
   - Compute group sizes and % of each level for all candidate categorical exposures.
   - Compute % missing for all candidate continuous outcomes.
   - Compute Cramér's V between candidate exposure and candidate outcome to check for complete separation.
   - Write results to `exam_paper/2_research_question/exposure_stats.json`.
2. Pass `exposure_stats.json` into the Opus prompt so the model has quantitative evidence when choosing exposure/outcome.
3. `validate_research_questions.py` already exists — extend it to also check that the chosen exposure has no group with < 5% of sample (warn if so and note in Limitations).

**Replace with Python:** Exposure statistics computation.
**Keep LLM:** PICO formulation and rationale.

---

### Stage 3 — Acquire Data

**Problem in detail:**
The skill falls back to hardcoded URLs (e.g., NY Times GitHub COVID data) that may be stale or temporally misaligned with the main dataset. A dataset from 2010–2015 should not be supplemented with 2020 COVID data.

**Concrete fixes:**
1. Remove hardcoded fallback URLs from SKILL.md. If download fails, skip gracefully and note in `profile.json` under `external_data_status: "unavailable"`.
2. After any successful download, run `temporal_check.py`:
   - Parse date columns in downloaded data; compute min/max date range.
   - Compare against main dataset date range from `profile.json`.
   - If overlap < 20%, set `external_data_status: "misaligned"` and exclude from analysis.
3. Store download provenance (URL, retrieval date, row count, date range) in `exam_paper/2_research_question/downloaded/provenance.json`.

**Replace with Python:** Temporal overlap check, provenance logging.
**Keep LLM (Haiku):** Deciding which supplementary datasets to seek and constructing search queries.

---

### Stage 4 — Statistical Analysis

**Problem in detail:**
This is the highest-fragility stage. The LLM writes fresh Python analysis code on every run. Method selection is described in SKILL.md prose, meaning the LLM interprets the rules rather than executing them. Assumption checks are instructed but not enforced. Multiple testing correction is absent for secondary research questions.

**Concrete fixes:**
1. Build `workflow/scripts/analysis_templates/` with pre-written, tested scripts:
   - `linear_regression.py` — OLS with VIF, residual normality test, Cook's distance.
   - `logistic_regression.py` — logistic with Hosmer-Lemeshow, ROC-AUC, VIF.
   - `cox_regression.py` — Cox PH with Schoenfeld residuals, KM curves.
   - `poisson_regression.py` — Poisson/NB with dispersion test.
   - `descriptive_stats.py` — Table 1 generator (mean±SD for continuous, n/% for categorical, p-values via t-test/chi-square).
2. Write `select_analysis.py` as a deterministic decision tree:
   - Reads `variable_types.json` + `research_questions.json`.
   - Selects the correct template script based on outcome type.
   - Returns `method_selection.json` with chosen method, covariates list, sensitivity analysis plan.
3. Assumption check outputs must be written to `exam_paper/3_analysis/assumption_checks/` — if they don't exist, Stage 4 is considered failed.
4. For secondary research questions (if > 1), apply Bonferroni correction: divide α by number of secondary tests. Store corrected thresholds in `analysis_results.json`.
5. LLM role becomes: write the `methods_narrative` field in `analysis_results.json` (plain-language description of what was run). No code generation.

**Replace with Python:** All of it — method selection, script execution, assumption checks, Table 1.
**Keep LLM (Sonnet):** Methods narrative prose only.

---

### Stage 5 — Generate Figures

**Problem in detail:**
LLM writes matplotlib code each run. If a column name changed between Stage 1 and Stage 4 (e.g., renamed during cleaning), the generated figure code silently fails or produces a blank plot. No colorblind safety is checked. The `manifest.json` lists intended figures but is not validated against what was actually written to disk.

**Concrete fixes:**
1. Build `workflow/scripts/figure_factory/` with a Python class per figure type:
   - `KaplanMeierFigure`, `ForestPlotFigure`, `ScatterWithRegressionFigure`, `BarChartFigure`, `ROCCurveFigure`.
   - Each class takes a standardized dict from `analysis_results.json` and produces a `.png` + `.pdf`.
   - All figures use a shared style sheet (`jama_style.mplstyle`) enforcing: 300 DPI, grayscale-compatible palette, no chart junk.
2. Colorblind safety: palette must pass `colorspacious` or manually chosen from JAMA-approved discrete palette.
3. Post-generation, run `validate_figures.py`:
   - For each figure listed in `manifest.json`, assert the `.png` and `.pdf` exist on disk.
   - Assert file size > 5KB (catches blank plots).
   - Log actual generated files vs manifest; flag discrepancies as Stage 5 failures.
4. LLM role: write figure captions only.

**Replace with Python:** All figure generation code.
**Keep LLM (Sonnet):** Figure caption prose.

---

### Stage 6 — Literature Review

**Problem in detail:**
Haiku is used to search for and format references. LLM models hallucinate plausible-looking DOIs and author lists. BibTeX validation checks syntax but cannot verify that a paper exists. JAMA papers typically cite 20–40 references; current pipeline produces ~12.

**Concrete fixes:**
1. Replace LLM-driven search with PubMed E-utilities API (deterministic HTTP):
   - Build search query from PICO fields in `research_questions.json`.
   - Call `esearch.fcgi` → `efetch.fcgi` to retrieve real PubMed records.
   - Parse returned XML to extract title, authors, journal, year, DOI, PMID.
   - Write directly to `.bib` format — no LLM involvement in reference generation.
2. DOI cross-validation: for each entry with a DOI, send a HEAD request to `https://doi.org/<doi>` and confirm HTTP 200/301. Flag non-resolving DOIs for removal.
3. Target ≥ 20 references. If PubMed returns < 20, broaden query (remove MeSH terms one at a time) until threshold met or query is exhausted.
4. Maintain `workflow/references/base_references.bib` as a curated fallback of 15 foundational public health methods papers (always included).
5. LLM role: none in reference retrieval. Haiku may be used to write 1-sentence annotations for the top 5 references if needed.

**Replace with Python:** Entire reference search and BibTeX generation.
**Keep LLM:** Optional annotation only.

---

### Stage 7 — Write Paper

**Problem in detail:**
Opus reads raw upstream JSONs (`analysis_results.json`, `profile.json`, `manifest.json`, `references.bib`) and writes `paper.tex` in a single pass. This is the single most fragile step:
- Key names in `analysis_results.json` are not standardized across runs (LLM-generated keys vary).
- Numeric formatting (rounding, CI direction, p-value display) happens inside the LLM prompt.
- If a figure listed in `manifest.json` was not actually generated, the LLM includes a broken `\includegraphics` reference.
- No validated intermediate structure exists between raw results and LaTeX.

**Concrete fixes:** See Stage 6.5 below. After Stage 6.5 produces `manuscript_schema.json`, Stage 7 changes to:
1. Opus reads only `manuscript_schema.json` (not raw upstream JSONs directly).
2. All numeric values arrive pre-formatted as strings (e.g., `"OR = 1.42 (95% CI, 1.18–1.71); P = .003"`).
3. All figure paths are validated to exist before the prompt is constructed.
4. A `paper_template_variables.json` maps schema fields to LaTeX template slots — LLM fills prose, not numbers.
5. Word count check: if paper body > 3000 words, instruct LLM to condense before finalizing.

**Replace with Python:** Value extraction, formatting, figure path validation (all in Stage 6.5).
**Keep LLM (Opus):** Prose writing of all sections.

---

### Stage 8 — Compile & Review

**Problem in detail:**
LaTeX compilation is correctly deterministic (pdflatex → bibtex → pdflatex → pdflatex). The "self-review" step where the LLM reads the compiled PDF and narrates feedback is theater: it cannot reliably count pages, detect `??` references, or catch `TODO` placeholders programmatically.

**Concrete fixes:**
1. Write `post_compile_check.py` that runs after successful compilation:
   - **Page count:** Use `PyPDF2` or `pdfinfo` to extract page count; assert ≤ 10 pages excluding references and supplement.
   - **Unresolved references:** `grep -c '??' paper.aux` — assert count = 0.
   - **Placeholder text:** `grep -iE 'TODO|FIXME|PLACEHOLDER|\[INSERT\]' paper.tex` — assert count = 0.
   - **Figure existence:** For each `\includegraphics` in paper.tex, assert the file exists on disk.
   - **Abstract word count:** Parse abstract from paper.tex, assert ≤ 350 words (JAMA limit).
2. If any check fails, write a structured `review_failures.json` and pass it back to Stage 7 for targeted revision (not a full rewrite).
3. LLM "self-review" is removed entirely.

**Replace with Python:** All post-compile checking.
**Keep LLM:** Targeted revision of specific failing sections only, if programmatic checks fail.

---

## 3. Steps to Replace with Python (Summary)

The following operations are currently delegated to LLMs but should be pure Python:

| Operation | Current Owner | Correct Owner |
|-----------|--------------|---------------|
| Variable type inference | LLM (Stage 1) | `type_rules.py` decision tree |
| Exposure group balance computation | None (gap) | `exposure_check.py` |
| Temporal overlap check for external data | None (gap) | `temporal_check.py` |
| Statistical method selection | LLM prose (Stage 4) | `select_analysis.py` decision tree |
| Run regression analysis | LLM-generated scripts (Stage 4) | Pre-written `analysis_templates/` |
| Assumption checks (VIF, H-L, Schoenfeld) | Instructed but not enforced | Required output of template scripts |
| Multiple testing correction | None | Applied in `select_analysis.py` |
| Table 1 generation | LLM-generated code (Stage 4/5) | `descriptive_stats.py` |
| Figure code generation | LLM-generated matplotlib (Stage 5) | `figure_factory/` class library |
| Manifest validation | None | `validate_figures.py` |
| Reference search & BibTeX generation | LLM (Stage 6) | PubMed E-utilities API calls |
| DOI validation | None | HEAD requests to doi.org |
| Numeric value extraction & formatting | LLM (Stage 7) | `assemble_manuscript_schema.py` |
| Post-compile checks | LLM narration (Stage 8) | `post_compile_check.py` |

---

## 4. New Stage 6.5 — Manuscript Schema Assembly

### Rationale
Stage 7 (Write Paper) is asked to simultaneously: extract values from upstream JSONs, format numbers to JAMA style, validate figure paths, and write publication-quality prose. This conflation is why Stage 7 produces the worst output. The solution is a mandatory intermediate representation.

### Specification

**Stage number:** 6.5 (runs between Literature Review and Write Paper)
**Executor:** Python script — `workflow/scripts/assemble_manuscript_schema.py`
**Model:** None (no LLM call)
**Input files:**
- `exam_paper/3_analysis/analysis_results.json`
- `exam_paper/2_research_question/research_questions.json`
- `exam_paper/1_data_profile/profile.json`
- `exam_paper/4_figures/manifest.json`
- `exam_paper/5_references/references.bib`

**Output:** `exam_paper/6_paper/manuscript_schema.json`

### Schema Structure

```json
{
  "meta": {
    "dataset_name": "string",
    "analysis_date": "YYYY-MM-DD",
    "schema_version": "1.0"
  },
  "study": {
    "design": "cross-sectional | cohort | case-control | ...",
    "setting": "string",
    "sample_size": 12345,
    "sample_size_formatted": "12,345",
    "date_range": "2010–2020",
    "primary_outcome": "string (plain language)",
    "primary_exposure": "string (plain language)"
  },
  "pico": {
    "population": "string",
    "intervention_exposure": "string",
    "comparator": "string",
    "outcome": "string"
  },
  "table1": {
    "caption": "Baseline Characteristics of Study Participants",
    "rows": [
      {
        "variable": "Age, mean (SD), y",
        "overall": "45.2 (12.1)",
        "exposed": "46.1 (11.8)",
        "unexposed": "44.3 (12.3)",
        "p_value": ".03"
      }
    ]
  },
  "primary_result": {
    "method": "logistic regression",
    "effect_measure": "OR",
    "effect_size": 1.42,
    "ci_lower": 1.18,
    "ci_upper": 1.71,
    "p_value": 0.003,
    "formatted": "OR = 1.42 (95% CI, 1.18–1.71); P = .003",
    "direction": "increased",
    "interpretation": "was associated with increased odds of [outcome]"
  },
  "secondary_results": [
    {
      "question": "string",
      "formatted": "string",
      "corrected_alpha": 0.0167
    }
  ],
  "sensitivity_analyses": [
    {
      "description": "string",
      "formatted": "string"
    }
  ],
  "figures": [
    {
      "id": "fig1",
      "path_png": "exam_paper/4_figures/figures/fig1_km_curve.png",
      "path_pdf": "exam_paper/4_figures/figures/fig1_km_curve.pdf",
      "exists_on_disk": true,
      "caption": "string",
      "latex_label": "fig:km_curve"
    }
  ],
  "tables": [
    {
      "id": "tab2",
      "path": "exam_paper/4_figures/tables/tab2_regression.tex",
      "exists_on_disk": true,
      "caption": "string",
      "latex_label": "tab:regression"
    }
  ],
  "references": {
    "count": 24,
    "bib_path": "exam_paper/5_references/references.bib"
  },
  "limitations": [
    "string"
  ],
  "abstract_bullets": {
    "importance": "string (1–2 sentences)",
    "objective": "string (1 sentence)",
    "design_setting_participants": "string (2–3 sentences)",
    "main_outcomes_and_measures": "string (1–2 sentences)",
    "results": "string (2–3 sentences with pre-formatted statistics)",
    "conclusions": "string (1–2 sentences)"
  }
}
```

### Formatting Rules (Applied in Python)

All numeric formatting follows JAMA style and must be applied deterministically before the schema is written:

- **P-values:** Drop leading zero. Round to 3 decimal places. If < .001, write `P < .001`. Write as `P = .003` not `p = 0.003`.
- **Confidence intervals:** Write as `95% CI, lower–upper` using en dash. Round to 2 decimal places for ORs/HRs, 1 decimal for means.
- **Effect sizes:** OR, RR, HR rounded to 2 decimal places. Mean differences to 1 decimal.
- **Sample sizes:** Formatted with commas (12,345).
- **Percentages:** One decimal place, no leading zero if < 10%.
- **Table 1 p-values:** Displayed as `< .001` or rounded to 2 decimal places.

### Validation Before Stage 7 Proceeds

`assemble_manuscript_schema.py` must assert before writing:
1. `primary_result.formatted` is a non-empty string.
2. All figures with `exists_on_disk: false` are removed from the figures list (not passed to LLM).
3. `references.count` ≥ 10.
4. `table1.rows` has ≥ 5 rows.

If any assertion fails, the script raises an error and Stage 7 is blocked until fixed.

---

## 5. Implementation Priority

Ordered by expected quality impact:

| Priority | Stage | Change | Difficulty |
|----------|-------|--------|------------|
| 1 | 6.5 (new) | Add `manuscript_schema.json` assembly | Medium |
| 2 | 7 | Rewrite SKILL.md to read only from schema | Low |
| 3 | 4 | Replace ad-hoc LLM scripts with `analysis_templates/` | High |
| 4 | 6 | Switch to PubMed E-utilities API | Medium |
| 5 | 8 | Add `post_compile_check.py` | Low |
| 6 | 5 | Replace LLM figure code with `figure_factory/` | Medium |
| 7 | 1 | Move type inference to `type_rules.py` | Low |
| 8 | 3 | Add `temporal_check.py` | Low |
| 9 | 2 | Add `exposure_check.py` | Low |

---

## 6. Revised Pipeline Architecture

```
Stage 1: Load & Profile
  └── Python: type inference, missingness, cardinality
  └── LLM (Sonnet): dataset summary prose only

Stage 2: Research Questions
  └── Python: exposure_check.py (group sizes, Cramér's V)
  └── LLM (Opus): PICO formulation with quantitative evidence

Stage 3: Acquire Data
  └── LLM (Haiku): identify data sources, construct queries
  └── Python: download, temporal_check.py, provenance.json

Stage 4: Statistical Analysis
  └── Python: select_analysis.py (deterministic method selection)
  └── Python: analysis_templates/ (pre-written, tested scripts)
  └── Python: assumption checks (required outputs)
  └── LLM (Sonnet): methods narrative prose only

Stage 5: Generate Figures
  └── Python: figure_factory/ (deterministic figure classes)
  └── Python: validate_figures.py (manifest vs disk)
  └── LLM (Sonnet): figure captions only

Stage 6: Literature Review
  └── Python: PubMed E-utilities API search
  └── Python: DOI validation (HTTP HEAD)
  └── LLM: none (optional annotation only)

Stage 6.5: Manuscript Schema Assembly  ← NEW
  └── Python only: assemble_manuscript_schema.py
  └── Output: manuscript_schema.json (fully validated, pre-formatted)

Stage 7: Write Paper
  └── Input: manuscript_schema.json only
  └── LLM (Opus): prose writing around pre-formatted values

Stage 8: Compile & Review
  └── Python: pdflatex compilation sequence (unchanged)
  └── Python: post_compile_check.py (page count, refs, placeholders)
  └── LLM: targeted revision only if checks fail
```

---

*End of audit document.*
