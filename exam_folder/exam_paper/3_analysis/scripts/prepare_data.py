"""
Stage 5 - prepare_data.py
Loads raw NIH terminations data, applies exclusions, creates derived variables,
and saves analytic dataset.
"""

import pandas as pd
import numpy as np
import json
import os
import sys

# Set working paths
# scripts/ -> 3_analysis/ -> exam_paper/ -> exam_folder/ -> project
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_DIR = os.path.dirname(SCRIPT_DIR)   # 3_analysis/
EXAM_PAPER_DIR = os.path.dirname(ANALYSIS_DIR)  # exam_paper/
EXAM_FOLDER_DIR = os.path.dirname(EXAM_PAPER_DIR)  # exam_folder/

DATA_PATH = os.path.join(EXAM_FOLDER_DIR, "data", "nih_terminations.csv")
OUTPUT_DIR = ANALYSIS_DIR  # exam_paper/3_analysis/
ANALYTIC_CSV = os.path.join(OUTPUT_DIR, "analytic_dataset.csv")

print("=" * 60)
print("PREPARE DATA - NIH Terminations Analysis")
print("=" * 60)
print(f"Data path: {DATA_PATH}")
print(f"Output dir: {OUTPUT_DIR}")

# --- Load raw data ---
df_raw = pd.read_csv(DATA_PATH)
N_raw = len(df_raw)
print(f"\nRaw dataset: {N_raw} rows, {df_raw.shape[1]} columns")
print(f"Status distribution:\n{df_raw['status'].value_counts()}")
print(f"\nFunding category distribution:\n{df_raw['funding_category'].value_counts()}")

# --- Exclusions ---
exclusion_log = {}

# Exclusion 1: Drop Frozen Funding (N=20)
mask_frozen = df_raw['status'] == '🧊 Frozen Funding'
n_frozen = mask_frozen.sum()
df = df_raw[~mask_frozen].copy()
exclusion_log['frozen_funding'] = int(n_frozen)
print(f"\nExclusion 1 - Frozen Funding: dropped {n_frozen} rows -> N={len(df)}")

# Exclusion 2: Keep only Research Training and Career Development OR Research and Development
mask_keep_category = df['funding_category'].isin([
    'Research Training and Career Development',
    'Research and Development'
])
n_other_category = (~mask_keep_category).sum()
df = df[mask_keep_category].copy()
exclusion_log['other_funding_category'] = int(n_other_category)
print(f"Exclusion 2 - Other funding categories: dropped {n_other_category} rows -> N={len(df)}")

# Exclusion 3: Drop missing total_award
n_missing_award = df['total_award'].isnull().sum()
df = df[df['total_award'].notna()].copy()
exclusion_log['missing_total_award'] = int(n_missing_award)
print(f"Exclusion 3 - Missing total_award: dropped {n_missing_award} rows -> N={len(df)}")

# Exclusion 4: Drop missing funding_category (should be 0 at this point)
n_missing_fc = df['funding_category'].isnull().sum()
df = df[df['funding_category'].notna()].copy()
exclusion_log['missing_funding_category'] = int(n_missing_fc)
print(f"Exclusion 4 - Missing funding_category: dropped {n_missing_fc} rows -> N={len(df)}")

N_analytic = len(df)
print(f"\nAnalytic sample N = {N_analytic}")

# --- Create derived variables ---

# 1. terminated_binary
# 1 = Terminated, 0 = Reinstated/Unfrozen (non-terminated)
terminated_statuses = ['❌ Terminated']
df['terminated_binary'] = (df['status'].isin(terminated_statuses)).astype(int)
print(f"\nOutcome - terminated_binary:")
print(f"  Terminated (1): {df['terminated_binary'].sum()} ({100*df['terminated_binary'].mean():.1f}%)")
print(f"  Non-terminated (0): {(df['terminated_binary'] == 0).sum()} ({100*(1-df['terminated_binary'].mean()):.1f}%)")

# 2. is_training_grant
df['is_training_grant'] = (df['funding_category'] == 'Research Training and Career Development').astype(int)
print(f"\nExposure - is_training_grant:")
print(f"  Training (1): {df['is_training_grant'].sum()} ({100*df['is_training_grant'].mean():.1f}%)")
print(f"  R&D (0): {(df['is_training_grant'] == 0).sum()} ({100*(1-df['is_training_grant'].mean()):.1f}%)")

# 3. log_total_award
df['log_total_award'] = np.log(df['total_award'] + 1)
print(f"\nlog_total_award - mean: {df['log_total_award'].mean():.3f}, sd: {df['log_total_award'].std():.3f}")

# 4. org_type_grouped
print(f"\nUnique org_type values:\n{df['org_type'].value_counts()}")

def group_org_type(ot):
    if pd.isna(ot):
        return 'Other'
    ot_upper = str(ot).upper().strip()
    university_medical_set = {
        'SCHOOLS OF MEDICINE', 'SCHOOLS OF PUBLIC HEALTH',
        'SCHOOLS OF DENTISTRY/ORAL HYGN', 'SCHOOLS OF NURSING',
        'SCHOOLS OF VETERINARY MEDICINE', 'SCHOOLS OF PHARMACY',
        'OVERALL MEDICAL', 'SCHOOL OF MEDICINE & DENTISTRY',
        'SCH ALLIED HEALTH PROFESSIONS', 'SCHOOLS OF OSTEOPATHIC MEDICINE',
        'SCH OF HOME ECON/HUMAN ECOLOGY', 'SCHOOLS OF SOCIAL WELFARE/WORK',
        'SCHOOLS OF OPTOMETRY/OPHT TECH'
    }
    university_other_set = {
        'SCHOOLS OF ARTS AND SCIENCES', 'BIOMED ENGR/COL ENGR/ENGR STA',
        'GRADUATE SCHOOLS', 'UNIVERSITY-WIDE', 'ORGANIZED RESEARCH UNITS',
        'DOMESTIC HIGHER EDUCATION', 'EARTH SCIENCES/RESOURCES',
        'SCHOOLS OF EDUCATION', 'SCHOOLS OF LAW OR CRIMINOLOGY',
        'SCH OF BUSINESS/PUBLIC ADMIN', 'OTHER SPECIALIZED SCHOOLS',
        'PRIMATE CENTERS', 'LIBRARIES'
    }
    hospital_nonprofit_set = {
        'INDEPENDENT HOSPITALS', 'OTHER DOMESTIC NON-PROFITS',
        'RESEARCH INSTITUTES', 'HOSPITALS'
    }

    if ot_upper in university_medical_set:
        return 'University-Medical'
    elif ot_upper in university_other_set:
        return 'University-Other'
    elif ot_upper in hospital_nonprofit_set:
        return 'Hospital-NonProfit'
    else:
        return 'Other'

df['org_type_grouped'] = df['org_type'].apply(group_org_type)
print(f"\norg_type_grouped distribution:\n{df['org_type_grouped'].value_counts()}")

# 5. org_state_region (US Census regions)
northeast = {'ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'}
midwest = {'OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'}
south = {'DE', 'MD', 'DC', 'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'KY', 'TN', 'AL', 'MS', 'AR', 'LA', 'OK', 'TX'}
west = {'MT', 'ID', 'WY', 'CO', 'NM', 'AZ', 'UT', 'NV', 'WA', 'OR', 'CA', 'AK', 'HI'}

def map_region(state):
    if pd.isna(state):
        return 'Unknown'
    s = str(state).strip().upper()
    if s in northeast:
        return 'Northeast'
    elif s in midwest:
        return 'Midwest'
    elif s in south:
        return 'South'
    elif s in west:
        return 'West'
    else:
        return 'Unknown'

df['org_state_region'] = df['org_state'].apply(map_region)
print(f"\norg_state distribution (top 15):\n{df['org_state'].value_counts().head(15)}")
print(f"\norg_state_region distribution:\n{df['org_state_region'].value_counts()}")

# --- Cross-tabulations ---
print("\n--- Outcome by Exposure ---")
crosstab = pd.crosstab(df['is_training_grant'], df['terminated_binary'], margins=True)
print(crosstab)

print("\n--- Termination rate by exposure ---")
for val, label in [(0, 'R&D'), (1, 'Training')]:
    sub = df[df['is_training_grant'] == val]
    term_rate = sub['terminated_binary'].mean() * 100
    print(f"  {label}: N={len(sub)}, terminated={sub['terminated_binary'].sum()} ({term_rate:.1f}%)")

# --- Save analytic dataset ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
df.to_csv(ANALYTIC_CSV, index=False)
print(f"\nSaved analytic dataset: {ANALYTIC_CSV}")
print(f"Final dataset: {len(df)} rows, {df.shape[1]} columns")

# --- Save exclusion log ---
exclusion_summary = {
    "n_raw": N_raw,
    "exclusions": exclusion_log,
    "n_excluded_total": N_raw - N_analytic,
    "n_analytic": N_analytic,
    "outcome_distribution": {
        "terminated": int(df['terminated_binary'].sum()),
        "non_terminated": int((df['terminated_binary'] == 0).sum()),
        "pct_terminated": round(float(df['terminated_binary'].mean() * 100), 2)
    },
    "exposure_distribution": {
        "training_grants": int(df['is_training_grant'].sum()),
        "rd_grants": int((df['is_training_grant'] == 0).sum()),
        "pct_training": round(float(df['is_training_grant'].mean() * 100), 2)
    }
}

exclusion_path = os.path.join(OUTPUT_DIR, "exclusion_log.json")
with open(exclusion_path, 'w') as f:
    json.dump(exclusion_summary, f, indent=2)
print(f"Saved exclusion log: {exclusion_path}")
print("\nDone.")
