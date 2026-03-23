"""
Heatmap Template for JAMA Network Open

Creates publication-quality heatmaps for correlation matrices or other 2D data.
Uses colorblind-safe diverging color palette.

Usage:
    # Copy this script and modify the data section
    # data = 2D array or correlation matrix
"""

import sys
sys.path.insert(0, "workflow/skills/generate-figures/scripts")
from jama_style import create_figure, get_diverging_cmap, save_figure
import numpy as np


# =============================================================================
# DATA SECTION - Modify this for your analysis
# =============================================================================

# Example: Correlation matrix
# Row/column labels
labels = ['Age', 'BMI', 'SBP', 'DBP', 'Cholesterol', 'Glucose']

# Correlation matrix (replace with your data)
np.random.seed(42)
data = np.array([
    [1.00, 0.15, 0.45, 0.38, 0.12, 0.28],
    [0.15, 1.00, 0.32, 0.25, 0.18, 0.52],
    [0.45, 0.32, 1.00, 0.72, 0.08, 0.21],
    [0.38, 0.25, 0.72, 1.00, 0.05, 0.15],
    [0.12, 0.18, 0.08, 0.05, 1.00, 0.35],
    [0.28, 0.52, 0.21, 0.15, 0.35, 1.00],
])

# Value range for colormap (for correlations: -1 to 1)
vmin, vmax = -1, 1

# Colorbar label
cbar_label = 'Correlation Coefficient'


# =============================================================================
# PLOT GENERATION
# =============================================================================

def create_heatmap(data, labels, vmin, vmax, cbar_label):
    """Create a publication-quality heatmap."""
    fig, ax = create_figure(width_type='single', height_ratio=0.9)

    # Get diverging colormap
    cmap = get_diverging_cmap()

    # Plot heatmap
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect='auto')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label, fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    # Add correlation values in cells
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            # Choose text color based on cell brightness
            value = data[i, j]
            if abs(value) > 0.5:
                text_color = 'white'
            else:
                text_color = '#323232'

            ax.text(j, i, f'{value:.2f}', ha='center', va='center',
                   fontsize=8, color=text_color)

    # Set ticks and labels
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_yticklabels(labels)

    # Remove borders
    for spine in ax.spines.values():
        spine.set_visible(False)

    return fig, ax


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    fig, ax = create_heatmap(data, labels, vmin, vmax, cbar_label)
    save_figure(fig, 'output_folder/4_figures/figures/figure4')
