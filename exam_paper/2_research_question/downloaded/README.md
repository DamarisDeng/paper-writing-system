# Downloaded Data Files

## covid_state_timeseries.csv

**Source:** New York Times COVID-19 Data Repository (GitHub)
**URL:** https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv
**Download Date:** 2026-03-20
**Original Source:** The New York Times, based on reports from state and local health agencies

### Study Period
**Date Range:** July 1, 2021 to October 31, 2021 (12-week period following HCW mandate announcements)
**Original Data Range:** January 21, 2020 to present

### Data Characteristics
- **Total Rows:** 6,805 (filtered to study period)
- **Number of States/Territories:** 56 (50 states + DC + 5 territories)
- **Columns:**
  - `date`: Date of observation (daily)
  - `state`: State or territory name
  - `fips`: Federal Information Processing Standards code
  - `cases`: Cumulative confirmed COVID-19 cases
  - `deaths`: Cumulative confirmed COVID-19 deaths

### Data Processing Notes
- Data was filtered to the 12-week study period (July-October 2021) corresponding to the post-mandate announcement window
- Cumulative counts were preserved; weekly or period-specific incidence can be derived by differencing
- Territories (Guam, Puerto Rico, etc.) are included but may be excluded from analysis depending on population data availability

### Data Quality Notes
- NY Times data is widely used in research and updated regularly
- Reporting consistency varies by state
- Death counts may be subject to retrospective revision
- For the purposes of this analysis, focus on the 50 states + DC where mandate and population data are available

### Related Files
- Research questions: `../research_questions.json`
- Population data: `../../1_data_profile/profile.json` (from NST-EST2024-POP.xlsx)
- Mandate data: `../../1_data_profile/profile.json` (from hcw_mandates_table.csv)
