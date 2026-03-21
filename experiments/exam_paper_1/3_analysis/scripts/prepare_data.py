#!/usr/bin/env python3
"""
Prepare Analytic Dataset
Merges mandate data, population data, and COVID-19 surveillance data
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Set paths
output_dir = Path("exam_paper/3_analysis")
output_dir.mkdir(exist_ok=True)
scripts_dir = output_dir / "scripts"
scripts_dir.mkdir(exist_ok=True)

# Load datasets
print("Loading datasets...")

# 1. HCW mandates data
mandates = pd.read_csv("exam_folder_sample/data/hcw_mandates_table.csv")
print(f"  Mandates: {len(mandates)} states")

# 2. Population data (2021 estimates for denominator)
# The Excel file has complex multi-row headers, need to parse carefully
pop = pd.read_excel("exam_folder_sample/data/NST-EST2024-POP.xlsx", header=None, skiprows=2)
# Column 0 has geographic area with leading dots for states
# Columns 1-6 have population data for different years
# Rename columns based on position
pop.columns = ['geographic_area', 'base_2020', 'pop_2020', 'pop_2021', 'pop_2022', 'pop_2023', 'pop_2024']

# Clean state names (remove leading dots)
pop['geographic_area'] = pop['geographic_area'].str.replace(r'^\.', '', regex=True)

# Filter to states only (exclude regions and US total)
# States are those not in the exclusion list
exclusions = ['United States', 'Northeast', 'Midwest', 'South', 'West']
pop = pop[~pop['geographic_area'].isin(exclusions)].copy()

# Keep only state name and 2021 population
state_pop_raw = pop[['geographic_area', 'pop_2021']].dropna().copy()
state_pop_raw.columns = ['state_name', 'population_2021']
print(f"  Population: {len(state_pop_raw)} states")

# Get list of state names from population data
state_names = state_pop_raw['state_name'].tolist()

# 3. COVID-19 data (filtered to study period)
covid = pd.read_csv("exam_paper/2_research_question/downloaded/covid_state_timeseries.csv")
covid['date'] = pd.to_datetime(covid['date'])
# Filter to 50 states + DC
covid = covid[covid['state'].isin(state_names + ["District of Columbia"])].copy()
print(f"  COVID: {len(covid)} observations")

# Create state abbreviation mapping
state_abbr_to_name = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
    'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina',
    'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
    'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
    'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

state_name_to_abbr = {v: k for k, v in state_abbr_to_name.items()}

# Add state names to mandates
mandates['state_name'] = mandates['State'].map(state_abbr_to_name)

# Create state-level analysis dataset
print("\nCreating state-level analytic dataset...")

# Use state_pop_raw from above (already has state_name and population_2021)

# Get COVID deaths by state for study period
# Calculate weekly deaths during the study period
covid_study = covid[(covid['date'] >= '2021-07-01') & (covid['date'] <= '2021-10-31')].copy()

# Aggregate to state level - get first and last values to calculate period-specific deaths
state_deaths = covid_study.groupby('state').agg({
    'deaths': ['min', 'max'],  # deaths at start and end of period
    'cases': ['min', 'max']
}).reset_index()

# Flatten column names
state_deaths.columns = ['state', 'deaths_start', 'deaths_end', 'cases_start', 'cases_end']

# Calculate period-specific deaths and cases
state_deaths['deaths_period'] = state_deaths['deaths_end'] - state_deaths['deaths_start']
state_deaths['cases_period'] = state_deaths['cases_end'] - state_deaths['cases_start']
state_deaths['state_name'] = state_deaths['state'].apply(
    lambda x: x if x != 'District of Columbia' else 'District of Columbia'
)

# Create mandate indicator
state_deaths['mandate'] = state_deaths['state_name'].isin(mandates['state_name']).astype(int)

# Merge with population data
analytic = state_deaths.merge(state_pop_raw, on='state_name', how='left')

# Calculate mortality rate per 100,000
analytic['mortality_rate_per_100k'] = (analytic['deaths_period'] / analytic['population_2021']) * 100000

# Calculate case rate per 100,000
analytic['case_rate_per_100k'] = (analytic['cases_period'] / analytic['population_2021']) * 100000

# Add mandate details from mandates table
analytic = analytic.merge(
    mandates[['state_name', 'Test-out option', 'Date of announcement', 'Main scope']],
    on='state_name', how='left'
)

# Create derived variables
analytic['test_out_option'] = (analytic['Test-out option'] == 'Yes').astype(int)
analytic['Date of announcement'] = pd.to_datetime(analytic['Date of announcement'])
analytic['early_adopter'] = (analytic['Date of announcement'].dt.month == 7).astype(int)
analytic['broad_scope'] = analytic['Main scope'].str.contains(
    'congregate|long-term|skilled nursing', case=False, na=False
).astype(int)

# Region classification
northeast = ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire', 'Rhode Island', 'Vermont',
             'New Jersey', 'New York', 'Pennsylvania']
midwest = ['Illinois', 'Indiana', 'Iowa', 'Kansas', 'Michigan', 'Minnesota', 'Missouri',
           'Nebraska', 'North Dakota', 'Ohio', 'South Dakota', 'Wisconsin']
south = ['Alabama', 'Arkansas', 'Delaware', 'District of Columbia', 'Florida', 'Georgia',
         'Kentucky', 'Louisiana', 'Maryland', 'Mississippi', 'North Carolina', 'Oklahoma',
         'South Carolina', 'Tennessee', 'Texas', 'Virginia', 'West Virginia']
west = ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho', 'Montana', 'Nevada',
        'New Mexico', 'Oregon', 'Utah', 'Washington', 'Wyoming']

def get_region(state):
    if state in northeast:
        return 'Northeast'
    elif state in midwest:
        return 'Midwest'
    elif state in south:
        return 'South'
    else:
        return 'West'

analytic['region'] = analytic['state_name'].apply(get_region)

# Clean and save
analytic = analytic[['state_name', 'state', 'mandate', 'test_out_option', 'early_adopter',
                     'broad_scope', 'region', 'population_2021', 'deaths_period', 'cases_period',
                     'mortality_rate_per_100k', 'case_rate_per_100k',
                     'Date of announcement', 'Main scope', 'Test-out option']].copy()

analytic.columns = ['state_name', 'state_abbr', 'mandate', 'test_out_option', 'early_adopter',
                    'broad_scope', 'region', 'population_2021', 'deaths_period', 'cases_period',
                    'mortality_rate_per_100k', 'case_rate_per_100k',
                    'announcement_date', 'mandate_scope', 'test_out_option_text']

# Save analytic dataset
analytic.to_csv(output_dir / "analytic_dataset.csv", index=False)

# Print summary
print(f"\nAnalytic dataset created:")
print(f"  Total N: {len(analytic)}")
print(f"  Mandate states: {analytic['mandate'].sum()}")
print(f"  Non-mandate states: {(analytic['mandate'] == 0).sum()}")
print(f"\nMortality rate (per 100k):")
print(f"  Overall: Mean={analytic['mortality_rate_per_100k'].mean():.2f}, SD={analytic['mortality_rate_per_100k'].std():.2f}")
print(f"  Mandate states: Mean={analytic[analytic['mandate']==1]['mortality_rate_per_100k'].mean():.2f}")
print(f"  Non-mandate states: Mean={analytic[analytic['mandate']==0]['mortality_rate_per_100k'].mean():.2f}")

print(f"\nMissing data:")
print(analytic.isnull().sum())

print("\nDataset saved to:", output_dir / "analytic_dataset.csv")
