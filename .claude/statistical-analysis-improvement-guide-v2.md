# Improving `statistical-analysis/SKILL.md` — Revised Guide (Minimal)

This guide makes **two additions** and **one schema change** to the existing skill. Everything else stays as-is.

---

## What's Changing

| Change | New file | Purpose |
|--------|----------|---------|
| 1. Analysis plan | `3_analysis/analysis_plan.json` | Persists the expensive reasoning (model choice, covariates, sensitivity strategy) before computation starts. Resume point after context loss. |
| 2. Progress tracker | `3_analysis/progress.json` | Tracks which sub-step completed last. Tiny file, updated after each sub-step. |
| 3. Formatted output block | *(schema change to existing result files)* | Adds JAMA-formatted strings alongside raw numbers so Stage 7 doesn't re-derive formatting. |

---

## Change 1: Add `analysis_plan.json`

### Where in the skill

Insert a new **Step 3b** between the current Step 3 (Descriptive Statistics) and Step 4 (Primary Analysis). The plan is written *after* the data is prepared and described, but *before* any model is fit.

Why here and not earlier: the plan needs to know the analytic sample size, missingness rates, and exposure group sizes from Steps 2–3 to make a sound model choice. It can't be written before the data is loaded.

### What the skill should say

```markdown
### Step 3b: Write the Analysis Plan

Before fitting any models, save the complete analysis strategy to
`<output_folder>/3_analysis/analysis_plan.json`. This file captures
the reasoning that is expensive to reproduce — model selection,
covariate rationale, sensitivity strategy — so that if context
compacts, the model can re-read this file and proceed directly to
computation without re-deriving the plan.

Walk through the model selection decision tree (Step 4's table) and
record the result. Also specify the sensitivity analyses you intend
to run.

Save to `<output_folder>/3_analysis/analysis_plan.json`:

```json
{
  "created_at": "ISO-8601",

  "analytic_sample_summary": {
    "total_n": 44312,
    "exposure_groups": {
      "vaccinated": 28100,
      "unvaccinated": 16212
    }
  },

  "model_selection": {
    "outcome_variable": "hospitalization",
    "outcome_type": "binary",
    "exposure_variable": "vaccination_status",
    "covariates": ["age", "sex", "race", "comorbidity_index"],
    "clustering_detected": false,
    "clustering_variable": null,
    "study_design": "cross-sectional",
    "selected_method": "Logistic regression",
    "python_class": "statsmodels.Logit",
    "cov_type": null,
    "rationale": "Binary outcome, cross-sectional design, no clustering detected. Covariates selected based on variable_roles from research_questions.json."
  },

  "sensitivity_analyses_planned": [
    {
      "name": "Subgroup by age group",
      "description": "Stratified logistic regression for age <65 vs ≥65",
      "why": "Effect may differ by age due to differential vaccine efficacy"
    },
    {
      "name": "Alternative covariate set",
      "description": "Add income and education as additional covariates",
      "why": "Assess sensitivity to potential socioeconomic confounding"
    }
  ],

  "table1_grouping_variable": "vaccination_status",
  "table1_comparison_test_strategy": "t-test for normal continuous, Wilcoxon for skewed, chi-square for categorical"
}
```

**After saving this file, update `progress.json` (see Change 2).**

The remaining steps (4, 5, 6) execute this plan. If context compacts
at any point after this step, re-read `analysis_plan.json` and
continue from the next incomplete step per `progress.json`.
```

### What to change in Step 4 (Primary Analysis)

Add this line at the top of Step 4:

```markdown
Read `<output_folder>/3_analysis/analysis_plan.json` → `model_selection`
to determine the method, covariates, and clustering strategy. Do NOT
re-derive the model choice — use what the plan specifies.
```

This ensures that even after context loss, the model fitting step doesn't hallucinate a different model choice.

---

## Change 2: Add `progress.json`

### Where in the skill

Insert a new section **"Resume Protocol"** near the top of the skill, right after the Usage section and before Step 1.

### What the skill should say

```markdown
## Resume Protocol

If you are resuming after context compaction or picking up mid-stage:

1. Read `<output_folder>/3_analysis/progress.json` (if it exists).
2. Find the last completed step.
3. Read `analysis_plan.json` (if it exists) to restore the analysis strategy.
4. Continue from the next incomplete step. **Never re-run a completed step.**

| If `progress.json` says last completed is... | Resume at |
|----------------------------------------------|-----------|
| `step_2_prepare_data` | Step 3: Descriptive stats |
| `step_3_descriptive_stats` | Step 3b: Write analysis plan |
| `step_3b_analysis_plan` | Step 4: Primary analysis (read plan first) |
| `step_4_primary_analysis` | Step 5: Sensitivity analyses |
| `step_5_sensitivity` | Step 6: Compile and validate |

If `progress.json` does not exist, start from Step 1.
```

### How to update progress.json

Add this instruction to the end of **every** sub-step (Steps 2, 3, 3b, 4, 5, 6):

```markdown
**Checkpoint:** Update `<output_folder>/3_analysis/progress.json`:
```json
{
  "current_step": "step_3b_analysis_plan",
  "completed_steps": ["step_2_prepare_data", "step_3_descriptive_stats", "step_3b_analysis_plan"],
  "last_updated": "ISO-8601",
  "notes": "Logistic regression selected; binary outcome, no clustering"
}
```
```

---

## Change 3: Add Formatted Output Block

### Where in the skill

Modify the output schema in **Step 4** (Primary Analysis) and **Step 3** (Descriptive Statistics). This is a schema change to existing outputs, not a new file.

### Primary analysis results

In the Step 4 output section, add a `formatted` block alongside the raw results:

```markdown
In the primary analysis output, include both raw and formatted values:

```json
{
  "method": "Logistic regression",
  "outcome": "hospitalization",
  "exposure": "vaccination_status",
  "results": {
    "exposure_effect": {
      "raw": {
        "estimate": 1.45,
        "ci_lower": 1.22,
        "ci_upper": 1.72,
        "p_value": 0.00032,
        "se": 0.11
      },
      "formatted": {
        "estimate_str": "1.45",
        "ci_str": "1.22-1.72",
        "p_str": "< .001",
        "interpretation": "OR = 1.45 (95% CI, 1.22-1.72; P < .001)",
        "jama_sentence": "Vaccination was associated with significantly higher odds of hospitalization (OR, 1.45; 95% CI, 1.22-1.72; P < .001)."
      }
    }
  }
}
```

**JAMA p-value formatting rules:**
- p < .001 → report as "< .001"
- .001 ≤ p < .01 → 3 decimal places (e.g., ".003")
- .01 ≤ p ≤ 1 → 2 decimal places (e.g., ".03")
- No leading zero (`.03` not `0.03`)
```

### Descriptive statistics (Table 1)

In the Step 3 output section, add a `table1_formatted` array:

```markdown
Include a pre-formatted Table 1 array that Stage 5 can render directly:

```json
{
  "table1_formatted": [
    {
      "variable": "Age, mean (SD)",
      "overall": "45.0 (12.0)",
      "group_1": "45.2 (12.1)",
      "group_2": "44.8 (11.9)",
      "p_value": ".03",
      "test": "t-test"
    },
    {
      "variable": "Female sex, No. (%)",
      "overall": "15336 (49.3)",
      "group_1": "6234 (50.2)",
      "group_2": "9102 (48.6)",
      "p_value": ".01",
      "test": "χ²"
    }
  ]
}
```

This follows JAMA Table 1 conventions and can be consumed by
Stage 5 (generate-figures) without recomputation.
```

---

## What NOT to Change

- **No input validation step.** The orchestrator handles this.
- **No `analysis_manifest.json`.** Not needed — Stage 5 and 7 read the same files they do now, plus `analysis_plan.json` for the Methods section.
- **No `data_preparation_report.json`.** The data prep details stay in the scripts and analytic_dataset.csv.
- **No `assumption_checks.json`.** Assumption check results stay in the model summary .txt files where they already go.
- **No separate `descriptive_statistics.json`.** Table 1 data stays in the existing output structure.
- **No merged `analysis_results.json` replacement.** Keep writing `analysis_results.json` as before — it's what downstream stages expect. The only change is adding the `formatted` blocks to its schema.

---

## Updated `3_analysis/` Directory After Changes

```
3_analysis/
├── analysis_plan.json              ← NEW (written at Step 3b)
├── progress.json                   ← NEW (updated after each sub-step)
├── analytic_dataset.csv            ← unchanged
├── analysis_results.json           ← unchanged structure, adds formatted blocks
├── scripts/
│   ├── prepare_data.py
│   ├── descriptive_stats.py
│   ├── primary_analysis.py
│   └── sensitivity_*.py
└── models/
    └── primary_model_summary.txt
```
---

## Downstream Impact

| Stage | Impact | Action needed |
|-------|--------|---------------|
| Stage 5 (generate-figures) | Can optionally read `table1_formatted` from `analysis_results.json` | Minor — opportunistic improvement, not required |
| Stage 7 (write-paper) | Can read `analysis_plan.json` for Methods section; can use `formatted.jama_sentence` for Results | Minor — read one extra file |
| Orchestrator | Validation check should also verify `analysis_plan.json` exists | One-line addition to validation table |

---