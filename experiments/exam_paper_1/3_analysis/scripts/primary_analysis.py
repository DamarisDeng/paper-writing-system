#!/usr/bin/env python3
"""
Primary Analysis
Linear regression models examining association between HCW mandates and COVID-19 mortality
"""
import pandas as pd
import numpy as np
import json

# Simple OLS regression implementation
class OLSRegression:
    """Simple OLS regression without statsmodels dependency"""
    def __init__(self, X, y, var_names=None):
        # Add intercept
        self.X = np.column_stack([np.ones(len(X)), X])
        self.y = np.array(y)
        self.var_names = var_names if var_names else [f"X{i}" for i in range(X.shape[1])]
        self.n, self.k = self.X.shape
        self.fit()

    def fit(self):
        # OLS estimator: beta = (X'X)^(-1)X'y
        XtX = np.dot(self.X.T, self.X)
        Xty = np.dot(self.X.T, self.y)
        self.beta = np.linalg.solve(XtX, Xty)

        # Residuals
        self.residuals = self.y - np.dot(self.X, self.beta)
        self.df_resid = self.n - self.k

        # Residual variance
        self.sigma2 = np.sum(self.residuals**2) / self.df_resid

        # Variance-covariance matrix
        self.vcv = self.sigma2 * np.linalg.inv(XtX)

        # Standard errors
        self.se = np.sqrt(np.diag(self.vcv))

        # t-statistics
        self.t = self.beta / self.se

        # p-values (two-tailed, using normal approximation)
        from math import erf, sqrt
        def norm_cdf(z):
            return 0.5 * (1 + np.vectorize(lambda x: erf(x/sqrt(2)))(z))
        self.p_values = 2 * (1 - norm_cdf(np.abs(self.t)))

        # R-squared
        y_mean = np.mean(self.y)
        ss_tot = np.sum((self.y - y_mean)**2)
        ss_res = np.sum(self.residuals**2)
        self.r2 = 1 - ss_res / ss_tot

        # Adjusted R-squared
        self.r2_adj = 1 - (1 - self.r2) * (self.n - 1) / self.df_resid

        # 95% CI
        z_crit = 1.96
        self.ci_lower = self.beta - z_crit * self.se
        self.ci_upper = self.beta + z_crit * self.se

    def summary(self):
        """Return summary as dict"""
        summary = {
            "model": "OLS Regression",
            "n": self.n,
            "df_resid": int(self.df_resid),
            "r_squared": round(self.r2, 3),
            "adj_r_squared": round(self.r2_adj, 3),
            "coefficients": []
        }
        for i, name in enumerate(["intercept"] + self.var_names):
            summary["coefficients"].append({
                "variable": name,
                "estimate": round(self.beta[i], 4),
                "se": round(self.se[i], 4),
                "t_statistic": round(self.t[i], 3),
                "p_value": round(self.p_values[i], 3) if self.p_values[i] > 0.001 else "<0.001",
                "ci_lower": round(self.ci_lower[i], 4),
                "ci_upper": round(self.ci_upper[i], 4)
            })
        return summary

# Load data
df = pd.read_csv("exam_paper/3_analysis/analytic_dataset.csv")

print("Running primary analysis...")

results = {
    "primary_analysis": {
        "method": "OLS Linear Regression",
        "outcome": "COVID-19 mortality rate (per 100,000)",
        "exposure": "HCW mandate status",
        "models": []
    }
}

# Model 1: Unadjusted
print("\nModel 1: Unadjusted")
y = df['mortality_rate_per_100k'].values
X = df[['mandate']].values
model1 = OLSRegression(X, y, var_names=["mandate"])
summary1 = model1.summary()
summary1["model_name"] = "Model 1: Unadjusted"
summary1["covariates"] = ["None (mandate only)"]
results["primary_analysis"]["models"].append(summary1)
print(f"  Mandate effect: {summary1['coefficients'][1]['estimate']} (95% CI: {summary1['coefficients'][1]['ci_lower']} to {summary1['coefficients'][1]['ci_upper']})")
print(f"  R² = {summary1['r_squared']}")

# Model 2: Adjusted for region
print("\nModel 2: Adjusted for region")
# Create region dummies
region_dummies = pd.get_dummies(df['region'], drop_first=True)
X_region = np.column_stack([df[['mandate']].values, region_dummies.values])
var_names_region = ["mandate"] + list(region_dummies.columns)
model2 = OLSRegression(X_region, y, var_names=var_names_region)
summary2 = model2.summary()
summary2["model_name"] = "Model 2: Adjusted for Region"
summary2["covariates"] = ["Mandate", "Region (Midwest, South, West; reference=Northeast)"]
results["primary_analysis"]["models"].append(summary2)
print(f"  Mandate effect: {summary2['coefficients'][1]['estimate']} (95% CI: {summary2['coefficients'][1]['ci_lower']} to {summary2['coefficients'][1]['ci_upper']})")
print(f"  R² = {summary2['r_squared']}")

# Model 3: Adjusted for region and population
print("\nModel 3: Adjusted for region and population")
# Log transform population for better scaling
pop_log = np.log10(df['population_2021'].values)
X_full = np.column_stack([df[['mandate']].values, region_dummies.values, pop_log])
var_names_full = ["mandate"] + list(region_dummies.columns) + ["log10_population"]
model3 = OLSRegression(X_full, y, var_names=var_names_full)
summary3 = model3.summary()
summary3["model_name"] = "Model 3: Fully Adjusted"
summary3["covariates"] = ["Mandate", "Region", "Log10(Population)"]
results["primary_analysis"]["models"].append(summary3)
print(f"  Mandate effect: {summary3['coefficients'][1]['estimate']} (95% CI: {summary3['coefficients'][1]['ci_lower']} to {summary3['coefficients'][1]['ci_upper']})")
print(f"  R² = {summary3['r_squared']}")

# Save results
with open("exam_paper/3_analysis/primary_analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

# Save model summaries to text file
with open("exam_paper/3_analysis/models/primary_model_summary.txt", "w") as f:
    f.write("=" * 60 + "\n")
    f.write("PRIMARY ANALYSIS RESULTS\n")
    f.write("Association Between HCW Vaccine Mandates and COVID-19 Mortality\n")
    f.write("July-October 2021, 52 U.S. States/ Territories\n")
    f.write("=" * 60 + "\n\n")

    for model in results["primary_analysis"]["models"]:
        f.write(f"\n{model['model_name']}\n")
        f.write("-" * 60 + "\n")
        f.write(f"N = {model['n']}\n")
        f.write(f"R² = {model['r_squared']}\n")
        f.write(f"Adjusted R² = {model['adj_r_squared']}\n")
        f.write(f"Covariates: {', '.join(model['covariates'])}\n\n")
        f.write(f"{'Variable':<25} {'Estimate':>10} {'SE':>8} {'t':>8} {'p-value':>10} {'95% CI':>20}\n")
        f.write("-" * 60 + "\n")
        for coef in model['coefficients']:
            ci = f"[{coef['ci_lower']}, {coef['ci_upper']}]"
            f.write(f"{coef['variable']:<25} {coef['estimate']:>10.2f} {coef['se']:>8.2f} {coef['t_statistic']:>8.2f} {str(coef['p_value']):>10} {ci:>20}\n")
        f.write("\n")

# Sensitivity analysis: Subgroup by test-out option
print("\n\nSensitivity Analysis: Subgroup by Test-Out Option")
mandate_df = df[df['mandate'] == 1].copy()
y_mandate = mandate_df['mortality_rate_per_100k'].values
X_testout = mandate_df[['test_out_option']].values
model_testout = OLSRegression(X_testout, y_mandate, var_names=["test_out_option"])
summary_testout = model_testout.summary()
summary_testout["model_name"] = "Sensitivity: Test-Out Option (Mandate States Only)"
summary_testout["covariates"] = ["Test-out option"]
summary_testout["subgroup_note"] = "Analysis restricted to 16 states with mandates"
results["sensitivity_analysis"] = {
    "test_out_option": summary_testout
}
print(f"  Test-out effect: {summary_testout['coefficients'][1]['estimate']} (95% CI: {summary_testout['coefficients'][1]['ci_lower']} to {summary_testout['coefficients'][1]['ci_upper']})")
print(f"  R² = {summary_testout['r_squared']}")

# Sensitivity analysis: Early adopter
print("\nSensitivity Analysis: Early vs Late Adopter")
y_early = mandate_df['mortality_rate_per_100k'].values
X_early = mandate_df[['early_adopter']].values
model_early = OLSRegression(X_early, y_early, var_names=["early_adopter"])
summary_early = model_early.summary()
summary_early["model_name"] = "Sensitivity: Early Adopter (July vs August)"
summary_early["covariates"] = ["Early adopter (July=1, August=0)"]
summary_early["subgroup_note"] = "Analysis restricted to 16 states with mandates"
results["sensitivity_analysis"]["early_adopter"] = summary_early
print(f"  Early adopter effect: {summary_early['coefficients'][1]['estimate']} (95% CI: {summary_early['coefficients'][1]['ci_lower']} to {summary_early['coefficients'][1]['ci_upper']})")
print(f"  R² = {summary_early['r_squared']}")

# Save complete results
with open("exam_paper/3_analysis/analysis_results.json", "w") as f:
    json.dump({
        "analytic_sample": {
            "total_n": len(df),
            "excluded_n": 0,
            "exposure_groups": {
                "mandate_states": {"n": int(df['mandate'].sum())},
                "non_mandate_states": {"n": int((df['mandate'] == 0).sum())}
            }
        },
        "descriptive_statistics": json.load(open("exam_paper/3_analysis/descriptive_stats.json"))["descriptive_statistics"],
        "primary_analysis": results["primary_analysis"],
        "sensitivity_analyses": [
            {
                "name": "Test-out option comparison",
                "description": "Comparison of mortality rates among mandate states with vs without test-out option",
                "results": summary_testout
            },
            {
                "name": "Early adopter comparison",
                "description": "Comparison of mortality rates among mandate states announcing in July vs August 2021",
                "results": summary_early
            }
        ],
        "scripts_used": [
            "scripts/prepare_data.py",
            "scripts/descriptive_stats.py",
            "scripts/primary_analysis.py"
        ]
    }, f, indent=2)

print("\n\n=== PRIMARY ANALYSIS SUMMARY ===")
print(f"Outcome: COVID-19 mortality rate per 100,000 (July-Oct 2021)")
print(f"\nModel 3 (Fully Adjusted):")
print(f"  Mandate coefficient: {summary3['coefficients'][1]['estimate']}")
print(f"  95% CI: [{summary3['coefficients'][1]['ci_lower']}, {summary3['coefficients'][1]['ci_upper']}]")
print(f"  p-value: {summary3['coefficients'][1]['p_value']}")
print(f"  R²: {summary3['r_squared']}")
print(f"\nInterpretation: States with HCW mandates had {abs(summary3['coefficients'][1]['estimate']):.1f} fewer deaths per 100,000")
print(f"during the study period compared to states without mandates, after adjusting for region and population.")

print("\nResults saved to:")
print("  - exam_paper/3_analysis/analysis_results.json")
print("  - exam_paper/3_analysis/models/primary_model_summary.txt")
