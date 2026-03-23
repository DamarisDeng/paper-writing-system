"""
Forest Plot Template for JAMA Network Open

Creates a publication-quality forest plot showing odds ratios, hazard ratios,
or beta coefficients with 95% confidence intervals.

Usage:
    # Copy this script to your output folder and modify the data section
    estimates = [1.25, 0.87, 1.52, 0.95]
    ci_lower = [0.98, 0.65, 1.15, 0.72]
    ci_upper = [1.59, 1.17, 2.01, 1.25]
    labels = ['Variable A', 'Variable B', 'Variable C', 'Variable D']
"""

import sys
sys.path.insert(0, "workflow/skills/generate-figures/scripts")
from jama_style import create_figure, get_colors, add_reference_line, save_figure
import numpy as np


# =============================================================================
# DATA SECTION - Modify this for your analysis
# =============================================================================

# Example: Logistic regression results
estimates = [1.25, 0.87, 1.52, 0.95, 1.10]
ci_lower = [0.98, 0.65, 1.15, 0.72, 0.85]
ci_upper = [1.59, 1.17, 2.01, 1.25, 1.42]
labels = ['Age (per 10 years)', 'Female sex', 'Hypertension',
          'Diabetes', 'Smoking status']

# Reference line value (1 for OR/HR, 0 for beta coefficients)
ref_value = 1
x_label = 'Odds Ratio (95% CI)'


# =============================================================================
# PLOT GENERATION
# =============================================================================

def create_forest_plot(estimates, ci_lower, ci_upper, labels, ref_value, x_label):
    """Create a publication-quality forest plot."""
    fig, ax = create_figure(width_type='single', height_ratio=0.6)

    # Get colors (alternating for visual distinction)
    colors = get_colors(len(estimates), palette='okabe-ito')

    # Plot data
    y_pos = np.arange(len(labels))
    for i, (est, low, high, color) in enumerate(zip(estimates, ci_lower, ci_upper, colors)):
        # Horizontal line for CI
        ax.plot([low, high], [i, i], color='#323232', linewidth=1.5, zorder=1)
        # Point estimate marker
        ax.plot(est, i, 'o', color=color, markersize=8,
                markeredgecolor='#323232', markeredgewidth=1, zorder=2)

    # Reference line at null value
    add_reference_line(ax, value=ref_value, orientation='vertical',
                      style='--', linewidth=1)

    # Format axes
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel(x_label)
    ax.set_ylim(-0.5, len(labels) - 0.5)

    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='x', alpha=0.25)

    return fig, ax


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    fig, ax = create_forest_plot(estimates, ci_lower, ci_upper, labels, ref_value, x_label)
    save_figure(fig, 'output_folder/4_figures/figures/figure1')
