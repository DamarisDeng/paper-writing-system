"""
Stage 5 - finalize_results.py
Fix the predicted probability extraction, re-run Hosmer-Lemeshow correctly,
compile final analysis_results.json, and write results_summary.md.
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy import stats

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_DIR = os.path.dirname(SCRIPT_DIR)
ANALYTIC_CSV = os.path.join(ANALYSIS_DIR, "analytic_dataset.csv")
MODELS_DIR = os.path.join(ANALYSIS_DIR, "models")
RESULTS_JSON = os.path.join(ANALYSIS_DIR, "analysis_results.json")
SUMMARY_MD = os.path.join(ANALYSIS_DIR, "results_summary.md")

print("=" * 60)
print("FINALIZE RESULTS")
print("=" * 60)

# --- Load data ---
df = pd.read_csv(ANALYTIC_CSV)
df['org_type_grouped'] = pd.Categorical(
    df['org_type_grouped'],
    categories=['University-Medical', 'University-Other', 'Hospital-NonProfit', 'Other']
)
df['org_state_region'] = pd.Categorical(
    df['org_state_region'],
    categories=['Northeast', 'Midwest', 'South', 'West', 'Unknown']
)

formula_primary = (
    "terminated_binary ~ is_training_grant "
    "+ C(org_type_grouped, Treatment('University-Medical')) "
    "+ log_total_award "
    "+ C(org_state_region, Treatment('Northeast'))"
)

model = smf.logit(formula_primary, data=df).fit(method='bfgs', maxiter=200, disp=False)

# Correctly compute predicted probabilities using predict()
pred_probs = model.predict(df)
print(f"Predicted probability range: {pred_probs.min():.4f} - {pred_probs.max():.4f}")
print(f"Mean predicted prob: {pred_probs.mean():.4f}, Observed rate: {df['terminated_binary'].mean():.4f}")

# --- Hosmer-Lemeshow test (correct implementation) ---
n_groups = 10
df_hl = df[['terminated_binary']].copy()
df_hl['pred_prob'] = pred_probs.values
df_hl['decile'] = pd.qcut(df_hl['pred_prob'], q=n_groups, labels=False, duplicates='drop')

hl_groups = df_hl.groupby('decile').agg(
    n=('terminated_binary', 'count'),
    obs_events=('terminated_binary', 'sum'),
    mean_pred=('pred_prob', 'mean')
).reset_index()
hl_groups['exp_events'] = hl_groups['n'] * hl_groups['mean_pred']
hl_groups['exp_nonevents'] = hl_groups['n'] - hl_groups['exp_events']
hl_groups['obs_nonevents'] = hl_groups['n'] - hl_groups['obs_events']

# HL chi-square
hl_stat = sum(
    (hl_groups['obs_events'] - hl_groups['exp_events'])**2 / hl_groups['exp_events'].clip(lower=0.001) +
    (hl_groups['obs_nonevents'] - hl_groups['exp_nonevents'])**2 / hl_groups['exp_nonevents'].clip(lower=0.001)
)
hl_df = len(hl_groups) - 2
hl_p = 1 - stats.chi2.cdf(hl_stat, hl_df)
print(f"Hosmer-Lemeshow: chi2={hl_stat:.3f}, df={hl_df}, p={hl_p:.4f}")
print(hl_groups[['n', 'obs_events', 'exp_events', 'mean_pred']].round(3).to_string())

# --- Extract OR and 95% CI ---
params = model.params
conf = model.conf_int()
pvals = model.pvalues

or_table = pd.DataFrame({
    'coef': params,
    'OR': np.exp(params),
    'CI_lower': np.exp(conf[0]),
    'CI_upper': np.exp(conf[1]),
    'p_value': pvals
})

print("\n--- PRIMARY MODEL ESTIMATES ---")
print(or_table[['OR', 'CI_lower', 'CI_upper', 'p_value']].round(4).to_string())

# Primary estimate
pe = or_table.loc['is_training_grant']
print(f"\nPRIMARY: OR={pe['OR']:.4f}, 95% CI ({pe['CI_lower']:.4f}-{pe['CI_upper']:.4f}), p={pe['p_value']:.6f}")

# --- Load existing results ---
with open(RESULTS_JSON, 'r') as f:
    results = json.load(f)

# Update primary analysis with corrected HL
results['primary_analysis']['hosmer_lemeshow'] = {
    "statistic": round(float(hl_stat), 4),
    "df": int(hl_df),
    "p_value": round(float(hl_p), 4),
    "note": "Values computed using model.predict() for probabilities"
}
results['primary_analysis']['predicted_prob_range'] = {
    "min": round(float(pred_probs.min()), 4),
    "max": round(float(pred_probs.max()), 4),
    "mean": round(float(pred_probs.mean()), 4)
}

# --- Check for complete separation ---
separation_check = {
    "min_predicted_prob": round(float(pred_probs.min()), 6),
    "max_predicted_prob": round(float(pred_probs.max()), 6),
    "all_probs_in_0_1": bool((pred_probs >= 0).all() and (pred_probs <= 1).all()),
    "standard_errors_available": not np.isnan(model.bse).any(),
    "convergence": bool(model.mle_retvals.get('converged', True))
}
print(f"\nSeparation check: {separation_check}")
results['primary_analysis']['separation_check'] = separation_check

# --- Write results_summary.md ---
desc = results.get('descriptive_statistics', {})
pa = results['primary_analysis']
pe_res = pa['primary_estimate']
sa1 = results['sensitivity_analyses']['SA1_subgroup_by_org_type']
sa2 = results['sensitivity_analyses']['SA2_no_region_adjustment']
sa3 = results['sensitivity_analyses']['SA3_state_fixed_effects']

# Format p-value
def fmt_p(p):
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"

md_content = f"""# Statistical Analysis Results

## Study: NIH Grant Terminations (2025 Federal Funding Actions)

**Date**: 2026-03-24
**Analyst**: Automated pipeline (Stage 5)

---

## 1. Analytic Sample

- **Total raw records**: 5,419
- **Excluded - Frozen Funding status**: 20
- **Excluded - Other funding categories**: 173
- **Excluded - Missing total_award**: 6
- **Analytic sample**: N = {pa['n_obs']}

### Outcome
- Terminated (1): {desc.get('terminated_binary', {}).get('rd_n_terminated', 'N/A') + desc.get('terminated_binary', {}).get('training_n_terminated', 0) if isinstance(desc.get('terminated_binary', {}), dict) else 'N/A'} ({desc.get('terminated_binary', {}).get('rd_pct_terminated', 'N/A')}% in R&D; {desc.get('terminated_binary', {}).get('training_pct_terminated', 'N/A')}% in Training)
- Non-terminated (0): Remaining grants

### Exposure
- Training grants: {desc.get('n_training', 'N/A')} ({round(desc.get('n_training', 0)/pa['n_obs']*100, 1)}%)
- R&D grants: {desc.get('n_rd', 'N/A')} ({round(desc.get('n_rd', 0)/pa['n_obs']*100, 1)}%)

---

## 2. Table 1: Characteristics by Grant Type

| Variable | R&D (N={desc.get('n_rd', 'N/A')}) | Training (N={desc.get('n_training', 'N/A')}) | p-value |
|----------|--------|----------|---------|
| Terminated, n (%) | {desc.get('terminated_binary', {}).get('rd_n_terminated', 'N/A')} ({desc.get('terminated_binary', {}).get('rd_pct_terminated', 'N/A')}%) | {desc.get('terminated_binary', {}).get('training_n_terminated', 'N/A')} ({desc.get('terminated_binary', {}).get('training_pct_terminated', 'N/A')}%) | {fmt_p(desc.get('terminated_binary', {}).get('p_value_chisq', 1))} |
| Total Award, median USD | ${desc.get('total_award', {}).get('rd_median_usd', 'N/A'):,.0f} | ${desc.get('total_award', {}).get('training_median_usd', 'N/A'):,.0f} | {fmt_p(desc.get('total_award', {}).get('p_value_mannwhitney', 1))} |
| University-Medical, n (%) | {desc.get('org_type_grouped', {}).get('University-Medical', {}).get('rd_n', 'N/A')} ({desc.get('org_type_grouped', {}).get('University-Medical', {}).get('rd_pct', 'N/A')}%) | {desc.get('org_type_grouped', {}).get('University-Medical', {}).get('training_n', 'N/A')} ({desc.get('org_type_grouped', {}).get('University-Medical', {}).get('training_pct', 'N/A')}%) | {fmt_p(desc.get('org_type_grouped_pvalue', 1))} |
| University-Other, n (%) | {desc.get('org_type_grouped', {}).get('University-Other', {}).get('rd_n', 'N/A')} ({desc.get('org_type_grouped', {}).get('University-Other', {}).get('rd_pct', 'N/A')}%) | {desc.get('org_type_grouped', {}).get('University-Other', {}).get('training_n', 'N/A')} ({desc.get('org_type_grouped', {}).get('University-Other', {}).get('training_pct', 'N/A')}%) | |
| Hospital/NonProfit, n (%) | {desc.get('org_type_grouped', {}).get('Hospital-NonProfit', {}).get('rd_n', 'N/A')} ({desc.get('org_type_grouped', {}).get('Hospital-NonProfit', {}).get('rd_pct', 'N/A')}%) | {desc.get('org_type_grouped', {}).get('Hospital-NonProfit', {}).get('training_n', 'N/A')} ({desc.get('org_type_grouped', {}).get('Hospital-NonProfit', {}).get('training_pct', 'N/A')}%) | |
| Northeast region, n (%) | {desc.get('org_state_region', {}).get('Northeast', {}).get('rd_n', 'N/A')} ({desc.get('org_state_region', {}).get('Northeast', {}).get('rd_pct', 'N/A')}%) | {desc.get('org_state_region', {}).get('Northeast', {}).get('training_n', 'N/A')} ({desc.get('org_state_region', {}).get('Northeast', {}).get('training_pct', 'N/A')}%) | {fmt_p(desc.get('org_state_region_pvalue', 1))} |
| South region, n (%) | {desc.get('org_state_region', {}).get('South', {}).get('rd_n', 'N/A')} ({desc.get('org_state_region', {}).get('South', {}).get('rd_pct', 'N/A')}%) | {desc.get('org_state_region', {}).get('South', {}).get('training_n', 'N/A')} ({desc.get('org_state_region', {}).get('South', {}).get('training_pct', 'N/A')}%) | |

---

## 3. Primary Analysis

**Model**: Logistic regression
**Formula**: terminated_binary ~ is_training_grant + org_type_grouped + log(total_award+1) + org_state_region
**Reference categories**: University-Medical (org_type), Northeast (region)

### Primary Estimate: Training vs. R&D Grants

| | OR | 95% CI | p-value |
|-|----|----|---------|
| **Training vs. R&D** | **{pe_res['OR']:.3f}** | **{pe_res['OR_CI_lower']:.3f}–{pe_res['OR_CI_upper']:.3f}** | **{fmt_p(pe_res['p_value'])}** |

**Interpretation**: After adjusting for institution type, total award amount, and US Census region,
research training and career development grants had an odds ratio of {pe_res['OR']:.2f} (95% CI: {pe_res['OR_CI_lower']:.2f}–{pe_res['OR_CI_upper']:.2f}, p={fmt_p(pe_res['p_value'])})
for termination compared to R&D grants. This association was **not statistically significant** at p<0.05.

### Unadjusted Termination Rates
- R&D: 16.2% terminated
- Training: 30.1% terminated
- Crude OR (unadjusted): ~2.2

### Model Fit
- N = {pa['n_obs']}
- Pseudo R² (McFadden) = {pa['pseudo_r2_mcfadden']}
- Log-likelihood = {pa['log_likelihood']}
- AIC = {pa['aic']:.1f}
- Hosmer-Lemeshow p = {fmt_p(pa['hosmer_lemeshow']['p_value'])}
- Convergence: {pa.get('separation_check', {}).get('convergence', True)}

### All Covariate Estimates

| Covariate | OR | 95% CI | p-value |
|-----------|----|--------|---------|"""

# Add all estimates
for var_name, est in pe_res.items() if False else pa['all_estimates'].items():
    if isinstance(est, dict) and 'OR' in est:
        clean_name = var_name.replace('_T_', ' vs ').replace('C(org_type_grouped,_Treatment(\'University-Medical\'))', 'Org Type').replace("C(org_state_region,_Treatment('Northeast'))", 'Region')
        md_content += f"\n| {clean_name} | {est['OR']:.3f} | {est['CI_lower']:.3f}–{est['CI_upper']:.3f} | {fmt_p(est['p_value'])} |"

md_content += f"""

---

## 4. Sensitivity Analyses

### SA1: Subgroup by Institution Type

| Subgroup | N | OR | 95% CI | p-value |
|----------|---|----|--------|---------|"""

for grp, res in sa1.items():
    if isinstance(res, dict) and 'OR' in res:
        md_content += f"\n| {grp} | {res['n']} | {res['OR']:.3f} | {res['CI_lower']:.3f}–{res['CI_upper']:.3f} | {fmt_p(res['p_value'])} |"
    elif isinstance(res, dict) and res.get('skipped'):
        md_content += f"\n| {grp} | — | — | — | Insufficient events |"
    elif isinstance(res, dict) and 'OR' not in res:
        # Hospital-NonProfit had NaN CIs due to sparse data
        md_content += f"\n| {grp} | — | — | — | Model unstable (sparse data) |"

md_content += f"""

### SA2: Without Region Adjustment

| | OR | 95% CI | p-value |
|-|----|--------|---------|
| Training vs. R&D | {sa2.get('OR', 'N/A'):.3f} | {sa2.get('CI_lower', 'N/A'):.3f}–{sa2.get('CI_upper', 'N/A'):.3f} | {fmt_p(sa2.get('p_value', 1))} |

### SA3: State Fixed Effects (Top 15 States)

| | OR | 95% CI | p-value |
|-|----|--------|---------|
| Training vs. R&D | {sa3.get('OR', 'N/A'):.3f} | {sa3.get('CI_lower', 'N/A'):.3f}–{sa3.get('CI_upper', 'N/A'):.3f} | {fmt_p(sa3.get('p_value', 1))} |

---

## 5. Key Findings

1. **Crude rates**: Training grants had markedly higher termination rates (30.1% vs 16.2%).

2. **Adjusted analysis**: After controlling for institution type, award amount, and geographic region,
   the OR for training vs. R&D grants was {pe_res['OR']:.2f} (95% CI: {pe_res['OR_CI_lower']:.2f}–{pe_res['OR_CI_upper']:.2f}, p={fmt_p(pe_res['p_value'])}).
   This association was **not statistically significant**.

3. **Geographic effects**: Region was a strong predictor. South region showed dramatically higher
   termination odds (OR ~25) vs Northeast. This regional confounding substantially attenuated
   the training-grant association.

4. **Award amount**: Higher award amounts were protective (OR=0.66 per log-unit increase).

5. **Institution type**: Hospital/NonProfit institutions had much higher termination odds (OR~10.5)
   vs. University-Medical schools.

6. **Sensitivity**: Without region adjustment (SA2), training grants showed OR=1.24 (p=0.02),
   suggesting region is a key confounder. With state FE (SA3), OR=1.09 (p=0.45) — consistent
   with primary model after geographic adjustment.

7. **Conclusion**: The unadjusted association between training grants and termination is largely
   explained by geographic distribution differences. After adjustment, no statistically significant
   independent association was detected.

---

## 6. Statistical Notes

- Analysis restricted to Training and R&D grants (excluded Small Business, Other Transactions, Construction)
- Possibly Unfrozen Funding coded as non-terminated (conservative assumption)
- Frozen Funding status excluded (n=20; outcome ambiguous)
- log(total_award+1) transformation handles right-skew and potential zeros
- Region used instead of all 50 states to avoid perfect multicollinearity and sparse cells
- Hospital-NonProfit subgroup (SA1) showed unstable estimates due to sparse cells by region
"""

with open(SUMMARY_MD, 'w') as f:
    f.write(md_content)
print(f"\nSaved results_summary.md: {SUMMARY_MD}")

# Update JSON with corrected values
with open(RESULTS_JSON, 'w') as f:
    json.dump(results, f, indent=2)
print(f"Updated analysis_results.json: {RESULTS_JSON}")
print("\nDone.")
