# Statistical Analysis Results

## Study: NIH Grant Terminations (2025 Federal Funding Actions)

**Date**: 2026-03-24
**Analyst**: Automated pipeline (Stage 5)

---

## 1. Analytic Sample

- **Total raw records**: 5,419
- **Excluded - Frozen Funding status**: 20
- **Excluded - Other funding categories**: 173
- **Excluded - Missing total_award**: 6
- **Analytic sample**: N = 5219

### Outcome
- Terminated (1): 1063 (16.2% in R&D; 30.1% in Training)
- Non-terminated (0): Remaining grants

### Exposure
- Training grants: 1559 (29.9%)
- R&D grants: 3661 (70.1%)

---

## 2. Table 1: Characteristics by Grant Type

| Variable | R&D (N=3661) | Training (N=1559) | p-value |
|----------|--------|----------|---------|
| Terminated, n (%) | 594 (16.2%) | 469 (30.1%) | <0.001 |
| Total Award, median USD | $2,087,857 | $274,032 | <0.001 |
| University-Medical, n (%) | 2724 (74.4%) | 1063 (68.2%) | <0.001 |
| University-Other, n (%) | 726 (19.8%) | 437 (28.0%) | |
| Hospital/NonProfit, n (%) | 193 (5.3%) | 55 (3.5%) | |
| Northeast region, n (%) | 1926 (52.6%) | 724 (46.4%) | <0.001 |
| South region, n (%) | 348 (9.5%) | 270 (17.3%) | |

---

## 3. Primary Analysis

**Model**: Logistic regression
**Formula**: terminated_binary ~ is_training_grant + org_type_grouped + log(total_award+1) + org_state_region
**Reference categories**: University-Medical (org_type), Northeast (region)

### Primary Estimate: Training vs. R&D Grants

| | OR | 95% CI | p-value |
|-|----|----|---------|
| **Training vs. R&D** | **1.109** | **0.902–1.365** | **0.325** |

**Interpretation**: After adjusting for institution type, total award amount, and US Census region,
research training and career development grants had an odds ratio of 1.11 (95% CI: 0.90–1.36, p=0.325)
for termination compared to R&D grants. This association was **not statistically significant** at p<0.05.

### Unadjusted Termination Rates
- R&D: 16.2% terminated
- Training: 30.1% terminated
- Crude OR (unadjusted): ~2.2

### Model Fit
- N = 5219
- Pseudo R² (McFadden) = 0.2948
- Log-likelihood = -1860.3129
- AIC = 3740.6
- Hosmer-Lemeshow p = <0.001
- Convergence: True

### All Covariate Estimates

| Covariate | OR | 95% CI | p-value |
|-----------|----|--------|---------|
| Intercept | 24.604 | 9.362–64.659 | <0.001 |
| Org Type vs University-Other | 1.219 | 0.999–1.488 | 0.051 |
| Org Type vs Hospital-NonProfit | 10.515 | 7.687–14.384 | <0.001 |
| Org Type vs Other | 0.725 | 0.160–3.278 | 0.676 |
| Region vs Midwest | 2.540 | 2.053–3.144 | <0.001 |
| Region vs South | 25.230 | 19.962–31.887 | <0.001 |
| Region vs West | 0.861 | 0.667–1.113 | 0.254 |
| Region vs Unknown | 106.348 | 21.161–534.479 | <0.001 |
| is_training_grant | 1.109 | 0.902–1.365 | 0.325 |
| log_total_award | 0.664 | 0.621–0.711 | <0.001 |

---

## 4. Sensitivity Analyses

### SA1: Subgroup by Institution Type

| Subgroup | N | OR | 95% CI | p-value |
|----------|---|----|--------|---------|
| University-Medical | 3787 | 1.223 | 0.939–1.593 | 0.136 |
| University-Other | 1163 | 1.168 | 0.774–1.761 | 0.460 |
| Hospital-NonProfit | 248 | 0.778 | nan–nan | nan |
| Other | — | — | — | Insufficient events |

### SA2: Without Region Adjustment

| | OR | 95% CI | p-value |
|-|----|--------|---------|
| Training vs. R&D | 1.236 | 1.034–1.477 | 0.020 |

### SA3: State Fixed Effects (Top 15 States)

| | OR | 95% CI | p-value |
|-|----|--------|---------|
| Training vs. R&D | 1.090 | 0.872–1.361 | 0.450 |

---

## 5. Key Findings

1. **Crude rates**: Training grants had markedly higher termination rates (30.1% vs 16.2%).

2. **Adjusted analysis**: After controlling for institution type, award amount, and geographic region,
   the OR for training vs. R&D grants was 1.11 (95% CI: 0.90–1.36, p=0.325).
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
