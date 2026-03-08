# Data Description

## Household Pulse Survey (HPS) microdata

- **Data Download**: Download the data from the website using the following script to the folder `data/HPS_PUF`:

```bash
cd data/HPS_PUF
for wk in {31..39}; do
  url="https://www2.census.gov/programs-surveys/demo/datasets/hhp/2021/wk${wk}/HPS_Week${wk}_PUF_CSV.zip"
  echo "Downloading Week ${wk}..."
  wget -c "$url"
done

for z in *.zip; do
  unzip -n "$z"
done
```

- **Dataset name**: Household Pulse Survey Public Use Files in the folder `HPS_PUF`. Files included per folder: Each release provides (i) the PUF microdata, (ii) a replicate weight file, and (iii) a data dictionary.  ￼

- **What it contains**: Individual-level microdata (responses to survey questions) designed for rapid measurement of household experiences during the pandemic. The PUF supports custom tabulations and includes the needed fields for outcomes and covariates (e.g., vaccination measures, demographics, geography) depending on wave content.  ￼


## State population (denominator for mortality rates)

- **Dataset name**: `NST-EST2024-POP.xlsx`￼

- **What it contains**: Annual resident population estimates for the U.S., states (and DC; often Puerto Rico), usually reported as of July 1 each year, along with related tables/datasets for population change and components of change (births, deaths, migration) depending on the file you select.  ￼￼


## State COVID-19 deaths time series

- **Dataset name**: `United_States_COVID-19_Cases_and_Deaths_by_State_over_Time_-_hiyb-zgc2_-_Archive_Repository.csv`

- **What it contains**: Daily (time series) state-level aggregate counts of COVID-19 cases and deaths reported by jurisdictions; the dataset compiles the most recent numbers reported by states/territories and is dependent on timely/accurate jurisdiction reporting.  ￼

## Policy table (state HCW vaccine mandate features)

- **Dataset name**: `hcw_mandates_table.csv`

- **What it contains**: A state-by-policy record that captures (at least) the mandate announcement date and whether there was a test-out option (and any additional mandate details used for stratification/robustness in the study).  ￼
