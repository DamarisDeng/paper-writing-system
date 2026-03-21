# JAMA Network Open Papers: Data, Methods, and Results Summary

Analysis of 7 JAMA Network Open papers to evaluate reproducibility using the automated pipeline.

---

## 1. All-Cause and Cause-Specific Mortality Among Patients With Narcolepsy

| Aspect | Details |
|--------|---------|
| **Data Source** | Nationwide population-based cohort study using Swedish National Health registries. All individuals (n=10,102) with narcolepsy diagnosis (ICD-10: G47.1, G47.8) from 2001-2012, matched to 50,510 controls. |
| **Research Question** | Do patients with narcolepsy have increased all-cause and cause-specific mortality compared to the general population? |
| **Model Choice** | Cox proportional hazards regression; Fine-Gray competing risks models; Age as time scale |
| **Statistical Tests** | Kaplan-Meier survival curves; Log-rank test; Modified Poisson regression; Fine-Gray subdistribution hazard models |
| **Result** | Patients with narcolepsy had increased all-cause mortality (HR 1.78, 95% CI 1.62-1.95) and cardiovascular (HR 2.27), respiratory (HR 3.13), and suicide mortality (HR 5.24). |

---

## 2. Interval Colorectal Cancers in a FIT-Based Screening Program

| Aspect | Details |
|--------|---------|
| **Data Source** | Population-based prospective cohort from Nordic European screening programs (2012-2019). 1,096,081 participants aged 50-74 years. |
| **Research Question** | What is the incidence, timing, and risk factors for interval colorectal cancers in FIT-based screening? |
| **Model Choice** | Modified Poisson regression; Cox proportional hazards regression |
| **Statistical Tests** | Log-rank test; Chi-square tests; Incidence rate ratios; Adjusted hazard ratios |
| **Result** | Interval cancers occurred at 5.2 per 1000 person-years, with higher risk among participants with previous FIT positivity (HR 2.14, 95% CI 1.82-2.52). |

---

## 3. Incidence and Risk of Cardiovascular Outcomes in Patients With Anorexia Nervosa

| Aspect | Details |
|--------|---------|
| **Data Source** | Nationwide Danish registries cohort (1996-2020). 21,797 individuals with anorexia nervosa (ICD-10: F50.0), matched to 217,970 controls. |
| **Research Question** | Do patients with anorexia nervosa have increased risk of cardiovascular outcomes compared to the general population? |
| **Model Choice** | Cox proportional hazards regression; Fine-Gray competing risk models; Age as time scale |
| **Statistical Tests** | Kaplan-Meier survival analysis; Log-rank test; Modified Poisson regression; Fine-Gray subdistribution hazard models |
| **Result** | Anorexia nervosa was associated with increased risk of myocardial infarction (HR 1.72), heart failure (HR 1.93), and arrhythmias (HR 1.80). |

---

## 4. Cardiac Events and Survival in EGFR-Mutant NSCLC

| Aspect | Details |
|--------|---------|
| **Data Source** | Retrospective cohort of 1,035 patients with advanced EGFR-mutant NSCLC treated with EGFR TKIs (2013-2019). |
| **Research Question** | What is the incidence, risk factors, and prognostic impact of cardiac events in EGFR-mutant NSCLC patients treated with TKIs? |
| **Model Choice** | Cox proportional hazards regression; Logistic regression; Fine-Gray competing risks regression |
| **Statistical Tests** | Kaplan-Meier analysis; Log-rank test; Cox PH models; Fine-Gray competing risks; Multivariate analysis |
| **Result** | Cardiac events occurred in 11.8% of patients, with significant impact on overall survival (HR 1.96, 95% CI 1.52-2.53). |

---

## 5. In-Hospital Use of LAI Antipsychotics and Readmission Risks

| Aspect | Details |
|--------|---------|
| **Data Source** | Medicare claims retrospective cohort (2016-2019). 158,229 patients aged ≥65 years with schizophrenia/bipolar disorder hospitalized on oral antipsychotics. |
| **Research Question** | Does switching to long-acting injectable antipsychotics (LAIs) during hospitalization reduce 30-day readmission compared to continuing oral antipsychotics? |
| **Model Choice** | Cox proportional hazards regression; Propensity score matching; Inverse probability weighting |
| **Statistical Tests** | Kaplan-Meier survival curves; Log-rank test; Cox PH models; Propensity score matching; IPW multivariable Cox regression |
| **Result** | Patients switched to LAIs had significantly lower 30-day readmission risks (HR 0.84, 95% CI 0.78-0.91). |

---

## 6. Machine Learning for Dynamic Prediction of Preeclampsia

| Aspect | Details |
|--------|---------|
| **Data Source** | Retrospective cohort (2005-2022) with 287,355 pregnant individuals from 6 health systems' EHR data. |
| **Research Question** | Can ML models dynamically predict preeclampsia in the short term using EHR data? |
| **Model Choice** | XGBoost, Random Forest, Logistic Regression, LightGBM (ML prediction models) |
| **Statistical Tests** | Cross-validation; Time-dependent AUC-ROC; Calibration plots; Decision curve analysis |
| **Result** | XGBoost achieved AUC 0.92 for 14-day preeclampsia prediction, outperforming clinical models (AUC 0.67, p < 0.001). |

---

## 7. Pediatric Diabetes Prevalence Among Medicaid Beneficiaries

| Aspect | Details |
|--------|---------|
| **Data Source** | Cross-sectional study using Medicaid Analytic eXtract (MAX) data. 5.6 million children aged 0-17 years enrolled in 2017. |
| **Research Question** | What is the prevalence and correlates of diabetes mellitus among pediatric Medicaid beneficiaries? |
| **Model Choice** | Modified Poisson regression; Logistic regression; Survey-weighted analyses |
| **Statistical Tests** | Chi-square tests; F-tests for survey-weighted means; Modified Poisson with robust SE; Logistic regression |
| **Result** | Overall diabetes prevalence was 0.31% (95% CI 0.30%-0.32%), higher among adolescents (1.04%) and children with obesity (0.91%). |

---

## Summary of Methods Used Across Papers

| Method | Frequency | Papers |
|--------|-----------|--------|
| Cox Proportional Hazards | 5 | 1, 2, 3, 4, 5 |
| Kaplan-Meier / Log-rank | 5 | 1, 2, 3, 4, 5 |
| Fine-Gray Competing Risks | 3 | 1, 3, 4 |
| Modified Poisson Regression | 3 | 1, 2, 7 |
| Logistic Regression | 2 | 4, 7 |
| Propensity Score Matching | 1 | 5 |
| Inverse Probability Weighting | 1 | 5 |
| Machine Learning (XGBoost, RF) | 1 | 6 |
| Chi-square / F-tests | 3 | 2, 6, 7 |

---

## Key Design Patterns

1. **Survival/Time-to-Event Analysis** (Papers 1-5): Most common design using registry/cohort data with time-to-event outcomes
2. **Competing Risks** (Papers 1, 3, 4): When death from other causes precludes the event of interest
3. **Causal Inference with Confounding Adjustment** (Paper 5): Propensity score methods for treatment effect estimation
4. **Prediction Modeling** (Paper 6): ML for dynamic risk prediction
5. **Cross-Sectional Prevalence** (Paper 7): Survey-weighted analyses for population estimates
