"""
Stage 5 - descriptive_stats.py
Generates Table 1 (descriptive statistics by is_training_grant exposure)
and saves to analysis_results.json.
"""

import pandas as pd
import numpy as np
import json
import os
from scipy import stats
from tableone import TableOne

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_DIR = os.path.dirname(SCRIPT_DIR)
ANALYTIC_CSV = os.path.join(ANALYSIS_DIR, "analytic_dataset.csv")
OUTPUT_DIR = ANALYSIS_DIR
RESULTS_JSON = os.path.join(OUTPUT_DIR, "analysis_results.json")

print("=" * 60)
print("DESCRIPTIVE STATISTICS - Table 1")
print("=" * 60)

# --- Load analytic dataset ---
df = pd.read_csv(ANALYTIC_CSV)
print(f"Loaded {len(df)} rows")

# --- Prepare variables for Table 1 ---

# top 10 states + other
state_counts = df['org_state'].value_counts()
top10_states = state_counts.head(10).index.tolist()
df['org_state_cat'] = df['org_state'].apply(
    lambda s: s if s in top10_states else 'Other'
)

# activity_code grouping
def group_activity(ac):
    if pd.isna(ac):
        return 'Other'
    ac = str(ac).strip().upper()
    if ac.startswith('R01'):
        return 'R01 (Research)'
    elif ac.startswith('R'):
        return 'Other R (Research)'
    elif ac in ['F30', 'F31', 'F32', 'F33']:
        return 'F (Fellowship)'
    elif ac.startswith('K'):
        return 'K (Career Dev)'
    elif ac.startswith('T'):
        return 'T (Training Inst.)'
    else:
        return 'Other'

df['activity_grouped'] = df['activity_code'].apply(group_activity)
print(f"activity_grouped distribution:\n{df['activity_grouped'].value_counts()}")

# total_award in $millions for display
df['total_award_M'] = df['total_award'] / 1e6

# --- Define Table 1 variables ---
columns_categorical = [
    'org_type_grouped',
    'org_state_cat',
    'activity_grouped',
    'org_state_region',
    'terminated_binary',
]
columns_continuous = ['total_award_M']
columns = columns_continuous + columns_categorical
groupby = 'is_training_grant'

# Rename for display
df_t1 = df[columns + [groupby]].copy()
df_t1['is_training_grant'] = df_t1['is_training_grant'].map({0: 'R&D', 1: 'Training'})

rename_map = {
    'total_award_M': 'Total Award (USD millions)',
    'org_type_grouped': 'Institution Type',
    'org_state_cat': 'State (Top 10)',
    'activity_grouped': 'Activity Code Group',
    'org_state_region': 'US Census Region',
    'terminated_binary': 'Terminated (outcome)',
}
df_t1 = df_t1.rename(columns=rename_map)

columns_display = list(rename_map.values())
columns_cat_display = [rename_map[c] for c in columns_categorical]
columns_cont_display = [rename_map[c] for c in columns_continuous]

# --- Generate TableOne ---
try:
    t1 = TableOne(
        df_t1,
        columns=columns_display,
        categorical=columns_cat_display,
        groupby='is_training_grant',
        pval=True,
        smd=True,
        isnull=False
    )
    print("\n--- TABLE 1 ---")
    print(t1.tabulate(tablefmt='grid'))
    
    # Save as CSV
    t1_csv = os.path.join(OUTPUT_DIR, "table1.csv")
    t1.to_csv(t1_csv)
    print(f"\nSaved Table 1 CSV: {t1_csv}")
    
    table1_success = True
    table1_str = t1.tabulate(tablefmt='simple')
    
except Exception as e:
    print(f"TableOne failed: {e}. Computing manually...")
    table1_success = False
    table1_str = "TableOne generation failed; see manual stats below"

# --- Manual statistics for JSON output ---
print("\n--- Manual Statistics ---")

def chi2_test(df, var, groupby_col):
    """Chi-square test for categorical variable."""
    ct = pd.crosstab(df[groupby_col], df[var])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    return round(p, 4)

def mannwhitney_test(df, var, groupby_col):
    """Mann-Whitney U test for continuous variable."""
    g0 = df[df[groupby_col] == 0][var].dropna()
    g1 = df[df[groupby_col] == 1][var].dropna()
    stat, p = stats.mannwhitneyu(g0, g1, alternative='two-sided')
    return round(p, 4)

descriptive_stats = {}

# Continuous: total_award
for g, label in [(0, 'R&D'), (1, 'Training')]:
    sub = df[df['is_training_grant'] == g]['total_award']
    descriptive_stats[f'total_award_{label}'] = {
        'median': round(float(sub.median()), 0),
        'q25': round(float(sub.quantile(0.25)), 0),
        'q75': round(float(sub.quantile(0.75)), 0),
        'mean': round(float(sub.mean()), 0),
        'sd': round(float(sub.std()), 0),
        'n': int(sub.count())
    }
p_award = mannwhitney_test(df, 'total_award', 'is_training_grant')
descriptive_stats['total_award_pvalue'] = p_award
print(f"Total Award - R&D median: ${df[df['is_training_grant']==0]['total_award'].median()/1e6:.2f}M, Training: ${df[df['is_training_grant']==1]['total_award'].median()/1e6:.2f}M, p={p_award}")

# Categorical: org_type_grouped
print("\nInstitution Type by group:")
ct_org = pd.crosstab(df['is_training_grant'], df['org_type_grouped'])
ct_org_pct = ct_org.div(ct_org.sum(axis=1), axis=0) * 100
for col in ct_org.columns:
    print(f"  {col}: R&D={ct_org.loc[0,col]} ({ct_org_pct.loc[0,col]:.1f}%), Training={ct_org.loc[1,col]} ({ct_org_pct.loc[1,col]:.1f}%)")
p_orgtype = chi2_test(df, 'org_type_grouped', 'is_training_grant')
print(f"  Chi-sq p = {p_orgtype}")

# Categorical: org_state_region
print("\nCensus Region by group:")
ct_region = pd.crosstab(df['is_training_grant'], df['org_state_region'])
ct_region_pct = ct_region.div(ct_region.sum(axis=1), axis=0) * 100
for col in ct_region.columns:
    rd_n = ct_region.loc[0, col] if 0 in ct_region.index else 0
    tr_n = ct_region.loc[1, col] if 1 in ct_region.index else 0
    rd_pct = ct_region_pct.loc[0, col] if 0 in ct_region_pct.index else 0
    tr_pct = ct_region_pct.loc[1, col] if 1 in ct_region_pct.index else 0
    print(f"  {col}: R&D={rd_n} ({rd_pct:.1f}%), Training={tr_n} ({tr_pct:.1f}%)")
p_region = chi2_test(df, 'org_state_region', 'is_training_grant')
print(f"  Chi-sq p = {p_region}")

# Outcome: terminated_binary
print("\nTermination rate by group:")
for g, label in [(0, 'R&D'), (1, 'Training')]:
    sub = df[df['is_training_grant'] == g]
    n = len(sub)
    n_term = sub['terminated_binary'].sum()
    pct = n_term / n * 100
    print(f"  {label}: N={n}, terminated={n_term} ({pct:.1f}%)")
p_outcome = chi2_test(df, 'terminated_binary', 'is_training_grant')
print(f"  Chi-sq p = {p_outcome}")

# Build descriptive stats dict for JSON
table1_data = {
    "n_total": len(df),
    "n_rd": int((df['is_training_grant'] == 0).sum()),
    "n_training": int((df['is_training_grant'] == 1).sum()),
    "total_award": {
        "rd_median_usd": round(float(df[df['is_training_grant']==0]['total_award'].median()), 0),
        "rd_q25_usd": round(float(df[df['is_training_grant']==0]['total_award'].quantile(0.25)), 0),
        "rd_q75_usd": round(float(df[df['is_training_grant']==0]['total_award'].quantile(0.75)), 0),
        "training_median_usd": round(float(df[df['is_training_grant']==1]['total_award'].median()), 0),
        "training_q25_usd": round(float(df[df['is_training_grant']==1]['total_award'].quantile(0.25)), 0),
        "training_q75_usd": round(float(df[df['is_training_grant']==1]['total_award'].quantile(0.75)), 0),
        "p_value_mannwhitney": p_award
    },
    "org_type_grouped": {
        cat: {
            "rd_n": int(ct_org.loc[0, cat]) if 0 in ct_org.index else 0,
            "rd_pct": round(float(ct_org_pct.loc[0, cat]) if 0 in ct_org_pct.index else 0, 1),
            "training_n": int(ct_org.loc[1, cat]) if 1 in ct_org.index else 0,
            "training_pct": round(float(ct_org_pct.loc[1, cat]) if 1 in ct_org_pct.index else 0, 1)
        }
        for cat in ct_org.columns
    },
    "org_type_grouped_pvalue": p_orgtype,
    "org_state_region": {
        reg: {
            "rd_n": int(ct_region.loc[0, reg]) if 0 in ct_region.index else 0,
            "rd_pct": round(float(ct_region_pct.loc[0, reg]) if 0 in ct_region_pct.index else 0, 1),
            "training_n": int(ct_region.loc[1, reg]) if 1 in ct_region.index else 0,
            "training_pct": round(float(ct_region_pct.loc[1, reg]) if 1 in ct_region_pct.index else 0, 1)
        }
        for reg in ct_region.columns
    },
    "org_state_region_pvalue": p_region,
    "terminated_binary": {
        "rd_n_terminated": int(df[df['is_training_grant']==0]['terminated_binary'].sum()),
        "rd_pct_terminated": round(float(df[df['is_training_grant']==0]['terminated_binary'].mean() * 100), 1),
        "training_n_terminated": int(df[df['is_training_grant']==1]['terminated_binary'].sum()),
        "training_pct_terminated": round(float(df[df['is_training_grant']==1]['terminated_binary'].mean() * 100), 1),
        "p_value_chisq": p_outcome
    },
    "table1_generated": table1_success
}

# --- Save/update analysis_results.json ---
if os.path.exists(RESULTS_JSON):
    with open(RESULTS_JSON, 'r') as f:
        results = json.load(f)
else:
    results = {}

results['descriptive_statistics'] = table1_data
results['table1_note'] = "Table 1: Characteristics of NIH grants by funding category (Research Training vs. R&D)"

with open(RESULTS_JSON, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved analysis_results.json: {RESULTS_JSON}")
print("\nDone.")
