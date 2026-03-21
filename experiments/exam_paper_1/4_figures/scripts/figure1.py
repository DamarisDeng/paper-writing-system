#!/usr/bin/env python3
"""
Figure 1: Association Between HCW Vaccine Mandates and COVID-19 Mortality
Forest plot showing adjusted mean differences
"""
import sys
sys.path.insert(0, 'exam_paper/4_figures/scripts')

import matplotlib.pyplot as plt
import numpy as np
import json
from jama_style import set_jama_style, save_figure, JAMA_COLORS

set_jama_style()

# Load analysis results
with open("exam_paper/3_analysis/analysis_results.json") as f:
    results = json.load(f)

# Extract model coefficients for forest plot
primary = results["primary_analysis"]
models = primary["models"]

# Get the fully adjusted model (Model 3)
fully_adjusted = models[2]  # Model 3 is fully adjusted

# Create figure
fig, ax = plt.subplots(figsize=(6, 3.5))

# Variables to plot (excluding intercept)
variables = []
estimates = []
ci_lowers = []
ci_uppers = []
labels = []

for coef in fully_adjusted["coefficients"]:
    if coef["variable"] != "intercept":
        variables.append(coef["variable"])
        estimates.append(coef["estimate"])
        ci_lowers.append(coef["ci_lower"])
        ci_uppers.append(coef["ci_upper"])

        # Create readable labels
        if coef["variable"] == "mandate":
            labels.append("HCW mandate")
        elif coef["variable"] == "log10_population":
            labels.append("Log₁₀(Population)")
        else:
            labels.append(coef["variable"].replace("_", " ").title())

# Focus on mandate for primary visualization (simpler figure)
y_pos = [0]
x = [estimates[0]]
xerr = [[estimates[0] - ci_lowers[0]], [ci_uppers[0] - estimates[0]]]

# Plot
colors = [JAMA_COLORS['crimson'] if estimates[0] < 0 else JAMA_COLORS['blue_accent']]
ax.barh(y_pos, x, height=0.5, color=colors, alpha=0.7)

# Add error bars
ax.errorbar(x, y_pos, xerr=xerr, fmt='none', ecolor=JAMA_COLORS['dark_gray'],
            capsize=4, capthick=1.5, linewidth=1.5)

# Add reference line at x=0
ax.axvline(x=0, color=JAMA_COLORS['dark_gray'], linestyle='--', linewidth=1, alpha=0.5)

# Add value label
label_text = f"{estimates[0]:.1f} ({ci_lowers[0]:.1f}, {ci_uppers[0]:.1f})"
x_pos = estimates[0] + (3 if estimates[0] < 0 else -3)
ha_align = 'left' if estimates[0] < 0 else 'right'
ax.text(x_pos, 0, label_text, va='center', ha=ha_align,
        fontsize=9, fontweight='bold', color=JAMA_COLORS['dark_gray'])

# Formatting
ax.set_yticks(y_pos)
ax.set_yticklabels([labels[0]])
ax.set_xlabel("Difference in Mortality Rate (per 100,000)", fontweight='bold')
ax.set_ylabel("")  # No y-axis label needed
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Set x-axis limits with some padding
xlim = max(abs(ci_lowers[0]), abs(ci_uppers[0])) * 1.3
ax.set_xlim(-xlim, xlim)

# Add n annotation
ax.text(0.02, 0.98, f"N = 52 states", transform=ax.transAxes,
        fontsize=8, va='top', ha='left', style='italic',
        color=JAMA_COLORS['medium_gray'])

plt.tight_layout()
save_figure(fig, "exam_paper/4_figures/figures/figure1")
print("Figure 1: HCW Mandate Effect on COVID-19 Mortality")
