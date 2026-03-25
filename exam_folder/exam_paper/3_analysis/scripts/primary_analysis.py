"""
Stage 5 - primary_analysis.py
Fits primary logistic regression and sensitivity analyses for NIH terminations.
Saves model summaries, estimates, and updates analysis_results.json.
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

os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 60)
print("PRIMARY ANALYSIS - Logistic Regression")
print("=" * 60)

# --- Load data ---
df = pd.read_csv(ANALYTIC_CSV)
print(f"Loaded {len(df)} rows")

# Verify key variables
print(f"\nOutcome distribution:\n{df['terminated_binary'].value_counts()}")
print(f"\nExposure distribution:\n{df['is_training_grant'].value_counts()}")
print(f"\norg_type_grouped distribution:\n{df['org_type_grouped'].value_counts()}")
print(f"\norg_state_region distribution:\n{df['org_state_region'].value_counts()}")

# Ensure reference categories are set (use CategoricalDtype for control)
df['org_type_grouped'] = pd.Categorical(
    df['org_type_grouped'],
    categories=['University-Medical', 'University-Other', 'Hospital-NonProfit', 'Other']
)
df['org_state_region'] = pd.Categorical(
    df['org_state_region'],
    categories=['Northeast', 'Midwest', 'South', 'West', 'Unknown']
)

def fit_logistic(formula, data, label="Model"):
    """Fit logistic regression and return result object with OR table."""
    print(f"\n--- {label} ---")
    print(f"Formula: {formula}")
    try:
        model = smf.logit(formula, data=data).fit(
            method='bfgs',
            maxiter=200,
            disp=False
        )
        
        # Extract OR table
        params = model.params
        conf = model.conf_int()
        pvals = model.pvalues
        
        or_table = pd.DataFrame({
            'coef': params,
            'OR': np.exp(params),
            'CI_lower': np.exp(conf[0]),
            'CI_upper': np.exp(conf[1]),
            'p_value': pvals,
            'z_stat': model.tvalues
        })
        
        print(f"N obs: {int(model.nobs)}")
        print(f"Converged: {model.mle_retvals.get('converged', 'N/A') if hasattr(model, 'mle_retvals') else model.mle_retvals}")
        print(f"Log-likelihood: {model.llf:.4f}")
        print(f"Pseudo R2 (McFadden): {model.prsquared:.4f}")
        
        # Print primary estimate
        if 'is_training_grant' in or_table.index:
            row = or_table.loc['is_training_grant']
            print(f"\nPRIMARY ESTIMATE - is_training_grant:")
            print(f"  OR = {row['OR']:.3f} (95% CI: {row['CI_lower']:.3f}-{row['CI_upper']:.3f}), p={row['p_value']:.4f}")
        
        print("\nAll estimates:")
        print(or_table[['OR', 'CI_lower', 'CI_upper', 'p_value']].round(4).to_string())
        
        return model, or_table
    except Exception as e:
        print(f"ERROR fitting {label}: {e}")
        import traceback; traceback.print_exc()
        return None, None

def extract_estimates(or_table, label="model"):
    """Extract key estimates as a serializable dict."""
    if or_table is None:
        return {"error": "Model failed to fit"}
    
    result = {}
    for idx, row in or_table.iterrows():
        # Clean index name
        var_name = str(idx).replace('[', '_').replace(']', '').replace('.', '_').replace(' ', '_')
        result[var_name] = {
            "OR": round(float(row['OR']), 4),
            "CI_lower": round(float(row['CI_lower']), 4),
            "CI_upper": round(float(row['CI_upper']), 4),
            "p_value": round(float(row['p_value']), 6),
            "coef": round(float(row['coef']), 6)
        }
    return result

# ============================================================
# PRIMARY MODEL
# ============================================================
formula_primary = (
    "terminated_binary ~ is_training_grant "
    "+ C(org_type_grouped, Treatment('University-Medical')) "
    "+ log_total_award "
    "+ C(org_state_region, Treatment('Northeast'))"
)

model_primary, or_primary = fit_logistic(formula_primary, df, "PRIMARY MODEL")

if model_primary is not None:
    # Save model summary
    summary_path = os.path.join(MODELS_DIR, "primary_model_summary.txt")
    with open(summary_path, 'w') as f:
        f.write(str(model_primary.summary()))
        f.write("\n\n--- ODDS RATIOS ---\n")
        f.write(or_primary[['OR', 'CI_lower', 'CI_upper', 'p_value']].round(4).to_string())
    print(f"\nSaved model summary: {summary_path}")

    # Check for complete separation
    print("\n--- Assumption Checks ---")
    print(f"Predicted probability range: {model_primary.fittedvalues.min():.4f} - {model_primary.fittedvalues.max():.4f}")
    
    # Hosmer-Lemeshow test (manual implementation)
    n_groups = 10
    df_hl = df[['terminated_binary']].copy()
    df_hl['pred_prob'] = model_primary.fittedvalues
    df_hl['decile'] = pd.qcut(df_hl['pred_prob'], q=n_groups, labels=False, duplicates='drop')
    hl_groups = df_hl.groupby('decile').agg(
        n=('terminated_binary', 'count'),
        obs_events=('terminated_binary', 'sum'),
        mean_pred=('pred_prob', 'mean')
    ).reset_index()
    hl_groups['exp_events'] = hl_groups['n'] * hl_groups['mean_pred']
    hl_groups['exp_nonevents'] = hl_groups['n'] - hl_groups['exp_events']
    hl_groups['obs_nonevents'] = hl_groups['n'] - hl_groups['obs_events']
    
    hl_stat = sum(
        (hl_groups['obs_events'] - hl_groups['exp_events'])**2 / hl_groups['exp_events'].clip(lower=0.001) +
        (hl_groups['obs_nonevents'] - hl_groups['exp_nonevents'])**2 / hl_groups['exp_nonevents'].clip(lower=0.001)
    )
    hl_df = len(hl_groups) - 2
    hl_p = 1 - stats.chi2.cdf(hl_stat, hl_df)
    print(f"Hosmer-Lemeshow test: chi2={hl_stat:.3f}, df={hl_df}, p={hl_p:.4f}")
    print(f"  (p>0.05 indicates adequate fit)")

# ============================================================
# SENSITIVITY ANALYSIS 1: Subgroup by org_type_grouped
# ============================================================
print("\n" + "=" * 60)
print("SENSITIVITY ANALYSIS 1: Subgroup by Institution Type")
print("=" * 60)

sa1_formula = "terminated_binary ~ is_training_grant + log_total_award + C(org_state_region, Treatment('Northeast'))"
sa1_results = {}

for grp in df['org_type_grouped'].cat.categories:
    sub = df[df['org_type_grouped'] == grp].copy()
    if sub['is_training_grant'].sum() < 5 or sub['terminated_binary'].sum() < 5:
        print(f"  {grp}: Insufficient events, skipping")
        sa1_results[str(grp)] = {"skipped": True, "reason": "insufficient events"}
        continue
    
    model_sa1, or_sa1 = fit_logistic(sa1_formula, sub, f"SA1: {grp}")
    if model_sa1 is not None and 'is_training_grant' in or_sa1.index:
        row = or_sa1.loc['is_training_grant']
        sa1_results[str(grp)] = {
            "n": len(sub),
            "n_terminated": int(sub['terminated_binary'].sum()),
            "OR": round(float(row['OR']), 4),
            "CI_lower": round(float(row['CI_lower']), 4),
            "CI_upper": round(float(row['CI_upper']), 4),
            "p_value": round(float(row['p_value']), 6)
        }
    else:
        sa1_results[str(grp)] = {"error": "Model failed"}

# ============================================================
# SENSITIVITY ANALYSIS 2: No region adjustment
# ============================================================
print("\n" + "=" * 60)
print("SENSITIVITY ANALYSIS 2: Without Region Adjustment")
print("=" * 60)

sa2_formula = (
    "terminated_binary ~ is_training_grant "
    "+ C(org_type_grouped, Treatment('University-Medical')) "
    "+ log_total_award"
)

model_sa2, or_sa2 = fit_logistic(sa2_formula, df, "SA2: No Region")

# ============================================================
# SENSITIVITY ANALYSIS 3: State fixed effects (top 15 states)
# ============================================================
print("\n" + "=" * 60)
print("SENSITIVITY ANALYSIS 3: State Fixed Effects (Top 15 States)")
print("=" * 60)

top15_states = df['org_state'].value_counts().head(15).index.tolist()
df['org_state_fe'] = df['org_state'].apply(lambda s: s if s in top15_states else 'Other')
df['org_state_fe'] = pd.Categorical(df['org_state_fe'])

# Pick largest state as reference (NY)
sa3_formula = (
    "terminated_binary ~ is_training_grant "
    "+ C(org_type_grouped, Treatment('University-Medical')) "
    "+ log_total_award "
    "+ C(org_state_fe, Treatment('NY'))"
)

model_sa3, or_sa3 = fit_logistic(sa3_formula, df, "SA3: State FE Top 15")

# ============================================================
# COMPILE RESULTS
# ============================================================
print("\n" + "=" * 60)
print("COMPILING RESULTS")
print("=" * 60)

# Primary result
if model_primary is not None and 'is_training_grant' in or_primary.index:
    row = or_primary.loc['is_training_grant']
    primary_result = {
        "n_obs": int(model_primary.nobs),
        "converged": bool(model_primary.mle_retvals.get('converged', True)),
        "log_likelihood": round(float(model_primary.llf), 4),
        "pseudo_r2_mcfadden": round(float(model_primary.prsquared), 4),
        "aic": round(float(model_primary.aic), 4),
        "bic": round(float(model_primary.bic), 4),
        "primary_estimate": {
            "variable": "is_training_grant",
            "label": "Training vs. R&D",
            "OR": round(float(row['OR']), 4),
            "OR_CI_lower": round(float(row['CI_lower']), 4),
            "OR_CI_upper": round(float(row['CI_upper']), 4),
            "p_value": round(float(row['p_value']), 6),
            "coef": round(float(row['coef']), 6)
        },
        "all_estimates": extract_estimates(or_primary),
        "hosmer_lemeshow": {
            "statistic": round(float(hl_stat), 4),
            "df": int(hl_df),
            "p_value": round(float(hl_p), 4)
        },
        "formula": formula_primary
    }
else:
    primary_result = {"error": "Primary model failed"}

# Sensitivity 2
if model_sa2 is not None and 'is_training_grant' in or_sa2.index:
    row2 = or_sa2.loc['is_training_grant']
    sa2_result = {
        "n_obs": int(model_sa2.nobs),
        "OR": round(float(row2['OR']), 4),
        "CI_lower": round(float(row2['CI_lower']), 4),
        "CI_upper": round(float(row2['CI_upper']), 4),
        "p_value": round(float(row2['p_value']), 6),
        "formula": sa2_formula
    }
else:
    sa2_result = {"error": "SA2 failed"}

# Sensitivity 3
if model_sa3 is not None and 'is_training_grant' in or_sa3.index:
    row3 = or_sa3.loc['is_training_grant']
    sa3_result = {
        "n_obs": int(model_sa3.nobs),
        "OR": round(float(row3['OR']), 4),
        "CI_lower": round(float(row3['CI_lower']), 4),
        "CI_upper": round(float(row3['CI_upper']), 4),
        "p_value": round(float(row3['p_value']), 6),
        "formula": sa3_formula
    }
else:
    sa3_result = {"error": "SA3 failed"}

# Load existing results and update
if os.path.exists(RESULTS_JSON):
    with open(RESULTS_JSON, 'r') as f:
        results = json.load(f)
else:
    results = {}

results['primary_analysis'] = primary_result
results['sensitivity_analyses'] = {
    "SA1_subgroup_by_org_type": sa1_results,
    "SA2_no_region_adjustment": sa2_result,
    "SA3_state_fixed_effects": sa3_result
}
results['analysis_method'] = "Logistic regression (statsmodels Logit)"
results['analysis_date'] = "2026-03-24"

with open(RESULTS_JSON, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved analysis_results.json: {RESULTS_JSON}")

# Print summary
print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
if 'primary_estimate' in primary_result:
    pe = primary_result['primary_estimate']
    print(f"PRIMARY RESULT:")
    print(f"  N = {primary_result['n_obs']}")
    print(f"  Training vs R&D: OR = {pe['OR']} (95% CI: {pe['OR_CI_lower']}-{pe['OR_CI_upper']}), p = {pe['p_value']:.6f}")
print(f"\nSENSITIVITY 2 (no region):")
if 'OR' in sa2_result:
    print(f"  OR = {sa2_result['OR']} (95% CI: {sa2_result['CI_lower']}-{sa2_result['CI_upper']}), p = {sa2_result['p_value']:.6f}")
print(f"\nSENSITIVITY 3 (state FE):")
if 'OR' in sa3_result:
    print(f"  OR = {sa3_result['OR']} (95% CI: {sa3_result['CI_lower']}-{sa3_result['CI_upper']}), p = {sa3_result['p_value']:.6f}")
print("\nDone.")
