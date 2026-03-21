#!/usr/bin/env python3
"""
Figure 2: COVID-19 Mortality Rates by Mandate Status and Region
Grouped bar chart showing mortality rates
"""
import sys
sys.path.insert(0, 'exam_paper/4_figures/scripts')

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from jama_style import set_jama_style, save_figure, JAMA_COLORS

set_jama_style()

# Load analytic dataset
df = pd.read_csv("exam_paper/3_analysis/analytic_dataset.csv")

# Aggregate mortality rate by mandate status and region
agg = df.groupby(['mandate', 'region'])['mortality_rate_per_100k'].mean().reset_index()
agg['mandate_label'] = agg['mandate'].map({0: 'No Mandate', 1: 'HCW Mandate'})

# Create figure
fig, ax = plt.subplots(figsize=(6, 3.5))

# Get unique regions and mandate status
regions = ['Northeast', 'Midwest', 'South', 'West']
mandate_statuses = ['No Mandate', 'HCW Mandate']

x = np.arange(len(regions))
width = 0.35

# Plot bars
for i, status in enumerate(mandate_statuses):
    data = agg[agg['mandate_label'] == status]
    # Make sure all regions are represented
    values = []
    for region in regions:
        region_data = data[data['region'] == region]['mortality_rate_per_100k']
        if len(region_data) > 0:
            values.append(region_data.values[0])
        else:
            values.append(0)

    offset = width * (i - 0.5)
    bars = ax.bar(x + offset, values, width, label=status,
                   color=JAMA_COLORS['blue_accent'] if i == 0 else JAMA_COLORS['crimson'],
                   alpha=0.7, edgecolor='white', linewidth=0.5)

# Formatting
ax.set_ylabel("Mortality Rate (per 100,000)", fontweight='bold')
ax.set_xlabel("Census Region", fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(regions)
ax.legend(frameon=False, loc='upper right')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
save_figure(fig, "exam_paper/4_figures/figures/figure2")
print("Figure 2: Mortality Rates by Mandate Status and Region")
