"""
Kaplan-Meier Survival Curve Template for JAMA Network Open

Creates publication-quality Kaplan-Meier survival curves with optional
risk tables and log-rank test p-values.

Usage:
    # Copy this script and modify the data section
    # Requires survival data: time_to_event and event_indicator
"""

import sys
sys.path.insert(0, "workflow/skills/generate-figures/scripts")
from jama_style import get_figure_width, get_colors, save_figure, set_jama_style
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


# =============================================================================
# DATA SECTION - Modify this for your analysis
# =============================================================================

# Group labels
groups = ['Treatment', 'Control']

# Sample sizes at baseline
n_at_risk = {
    0: [100, 100],   # Time 0
    12: [75, 60],    # Time 12
    24: [50, 35],    # Time 24
    36: [30, 20],    # Time 36
}

# Time points for survival curve (months)
time_points = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]

# Survival probabilities (replace with your KM estimates)
survival_curves = {
    'Treatment': [1.0, 0.95, 0.90, 0.85, 0.75, 0.68, 0.62, 0.58, 0.50, 0.45, 0.40, 0.35, 0.30],
    'Control': [1.0, 0.90, 0.82, 0.75, 0.60, 0.52, 0.45, 0.40, 0.35, 0.30, 0.25, 0.22, 0.20],
}

# Log-rank p-value
logrank_p = 0.003


# =============================================================================
# PLOT GENERATION
# =============================================================================

def create_km_curve(survival_curves, time_points, groups, n_at_risk, logrank_p):
    """Create a publication-quality Kaplan-Meier curve.

    Uses GridSpec for precise height control (80% plot, 20% risk table)
    with minimal vertical spacing (hspace=0.05) for tight visual association.
    """
    set_jama_style()
    width = get_figure_width('single')
    height = width * 1.0  # Slightly taller for the two panels

    fig = plt.figure(figsize=(width, height))

    # GridSpec: 4 parts for main plot, 1 part for risk table (80/20 split)
    # hspace=0.05 creates very tight spacing between plot and table
    gs = GridSpec(2, 1, figure=fig, height_ratios=[4, 1], hspace=0.05)

    ax_main = fig.add_subplot(gs[0])
    ax_risk = fig.add_subplot(gs[1])

    colors = get_colors(len(groups), palette='okabe-ito')

    # Plot survival curves
    for group, color in zip(groups, colors):
        survival = survival_curves[group]
        ax_main.step(time_points, survival, where='post', label=group,
                    color=color, linewidth=2)

        # Add censoring marks (optional)
        # ax_main.plot(censor_times, censor_probs, '|', color=color, markersize=10)

    # Format main plot
    ax_main.set_ylabel('Survival Probability')
    ax_main.set_xlabel('Time (months)')
    ax_main.set_ylim(-0.05, 1.05)
    ax_main.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_main.set_xlim(0, max(time_points))

    # Add p-value annotation
    ax_main.text(0.05, 0.05, f'Log-rank \u03c7\u00b2: \u0070 = {logrank_p:.3f}',
                transform=ax_main.transAxes, fontsize=9,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax_main.legend(loc='upper right', frameon=True)
    ax_main.spines['top'].set_visible(False)
    ax_main.spines['right'].set_visible(False)
    ax_main.set_axisbelow(True)
    ax_main.grid(axis='y', alpha=0.25)

    # Risk table
    ax_risk.axis('off')
    risk_times = sorted(n_at_risk.keys())

    # Create table
    table_data = [['Time'] + groups]
    for t in risk_times:
        row = [f'{t} mo'] + [str(n_at_risk[t][i]) for i in range(len(groups))]
        table_data.append(row)

    table = ax_risk.table(cellText=table_data, cellLoc='center',
                         loc='center', colWidths=[0.2] + [0.8/len(groups)]*len(groups))

    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    for i in range(len(table_data)):
        for j in range(len(table_data[0])):
            cell = table[i, j]
            if i == 0:  # Header
                cell.set_facecolor('#E8E8E8')
                cell.set_text_props(weight='bold')

    ax_risk.set_title('Number at Risk', fontsize=9, pad=-10)

    return fig


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    fig = create_km_curve(survival_curves, time_points, groups, n_at_risk, logrank_p)
    save_figure(fig, 'output_folder/4_figures/figures/figure2')
