"""
Multi-Panel Figure Template for JAMA Network Open

Creates publication-quality figures with multiple panels (A, B, C, etc.).
Supports various combinations of plot types in a single figure.

Usage:
    # Copy this script and modify each panel's data section
    # Adjust nrows and ncols as needed
"""

import sys
sys.path.insert(0, "workflow/skills/generate-figures/scripts")
from jama_style import create_figure, add_subplot_labels, get_colors, save_figure
import numpy as np


# =============================================================================
# DATA SECTION - Modify this for your analysis
# =============================================================================

# Panel A: Bar chart data
categories_a = ['Control', 'Treatment A', 'Treatment B']
values_a = [10.2, 15.8, 13.5]
errors_a = [1.2, 1.5, 1.3]

# Panel B: Line plot data
x_b = [1, 2, 3, 4, 5, 6, 7, 8]
y_b = [10, 12, 8, 15, 18, 14, 20, 22]

# Panel C: Scatter data
x_c = np.random.normal(50, 15, 50)
y_c = 0.7 * x_c + 10 + np.random.normal(0, 8, 50)


# =============================================================================
# PLOT GENERATION
# =============================================================================

def create_panel_a(ax):
    """Create Panel A: Bar chart with error bars."""
    colors = get_colors(len(categories_a))

    bars = ax.bar(categories_a, values_a, yerr=errors_a, capsize=4,
                 color=colors, edgecolor='#323232', linewidth=0.8, alpha=0.85)

    ax.set_ylabel('Outcome Value (units)')
    ax.set_title('Panel A', fontweight='bold', fontsize=10)

    # Add n values above bars
    for bar, val, err in zip(bars, values_a, errors_a):
        ax.text(bar.get_x() + bar.get_width()/2, val + err + 0.5,
               f'n={np.random.randint(20, 50)}', ha='center', va='bottom',
               fontsize=8, color='#5A5A5A')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y', alpha=0.25)


def create_panel_b(ax):
    """Create Panel B: Line plot."""
    color = get_colors(1)[0]

    ax.plot(x_b, y_b, color=color, linewidth=2, marker='o',
           markersize=6, markeredgecolor='#323232', markeredgewidth=0.8)

    ax.set_xlabel('Time (days)')
    ax.set_ylabel('Response (units)')
    ax.set_title('Panel B', fontweight='bold', fontsize=10)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='both', alpha=0.25)


def create_panel_c(ax):
    """Create Panel C: Scatter plot."""
    color = get_colors(1, palette='okabe-ito')[1]

    ax.scatter(x_c, y_c, color=color, alpha=0.6, s=30,
              edgecolor='#323232', linewidth=0.5)

    ax.set_xlabel('Independent Variable (units)')
    ax.set_ylabel('Dependent Variable (units)')
    ax.set_title('Panel C', fontweight='bold', fontsize=10)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='both', alpha=0.25)


def create_multipanel_figure():
    """Create a figure with multiple panels."""
    # Create figure with 2 rows, 2 columns (showing 3 panels)
    fig, axes = create_figure(width_type='double', nrows=2, ncols=2)

    # Flatten axes for easier access
    axes_flat = axes.flatten()

    # Create each panel
    create_panel_a(axes_flat[0])
    create_panel_b(axes_flat[1])
    create_panel_c(axes_flat[2])

    # Hide the 4th panel if not needed
    axes_flat[3].axis('off')

    # Add panel labels
    active_panels = [axes_flat[0], axes_flat[1], axes_flat[2]]
    add_subplot_labels(np.array(active_panels), labels=['A', 'B', 'C'],
                      offset_x=-0.15, offset_y=1.05)

    # Adjust spacing
    fig.tight_layout(w_pad=2.5, h_pad=2.5)

    return fig


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    fig = create_multipanel_figure()
    save_figure(fig, 'output_folder/4_figures/figures/figure5')
