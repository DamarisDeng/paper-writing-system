"""
Scatter Plot with Regression Line Template for JAMA Network Open

Creates publication-quality scatter plots showing relationships between
continuous variables, with optional regression line and 95% CI band.

Usage:
    # Copy this script and modify the data section
    x = [independent variable values]
    y = [dependent variable values]
"""

import sys
sys.path.insert(0, "workflow/skills/generate-figures/scripts")
from jama_style import create_figure, get_colors, save_figure
import numpy as np
from scipy import stats
from scipy.stats import t


# =============================================================================
# DATA SECTION - Modify this for your analysis
# =============================================================================

# Generate sample data (replace with your actual data)
np.random.seed(42)
x = np.random.normal(50, 15, 100)
y = 0.7 * x + 10 + np.random.normal(0, 8, 100)

# Axis labels (include units in parentheses)
xlabel = 'Age (years)'
ylabel = 'Systolic Blood Pressure (mm Hg)'


# =============================================================================
# PLOT GENERATION
# =============================================================================

def calculate_regression_ci(x, y, confidence=0.95):
    """Calculate regression line and confidence band."""
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Calculate predictions
    x_pred = np.linspace(x.min(), x.max(), 100)
    y_pred = slope * x_pred + intercept

    # Calculate confidence interval
    residuals = y - (slope * x + intercept)
    std_residuals = np.std(residuals)

    # Standard error of prediction
    se_pred = std_residuals * np.sqrt(1/len(x) +
                                     (x_pred - np.mean(x))**2 /
                                     np.sum((x - np.mean(x))**2))

    # Critical t-value
    t_crit = t.ppf((1 + confidence) / 2, len(x) - 2)

    # Confidence band
    ci_width = t_crit * se_pred

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'x_pred': x_pred,
        'y_pred': y_pred,
        'ci_lower': y_pred - ci_width,
        'ci_upper': y_pred + ci_width
    }


def create_scatter_plot(x, y, xlabel, ylabel):
    """Create a publication-quality scatter plot with regression line."""
    fig, axes = create_figure(width_type='single')
    ax = axes.flat[0]  # Handle array return for single panel

    # Get colors
    colors = get_colors(2, palette='okabe-ito')
    scatter_color = colors[0]
    ci_color = colors[0]

    # Calculate regression
    reg = calculate_regression_ci(x, y)

    # Plot scatter points
    ax.scatter(x, y, color=scatter_color, alpha=0.6, s=30,
              edgecolor='#323232', linewidth=0.5, label='Data')

    # Plot regression line
    ax.plot(reg['x_pred'], reg['y_pred'], color='#323232',
           linewidth=2, label=f'Regression line')

    # Plot 95% CI band
    ax.fill_between(reg['x_pred'], reg['ci_lower'], reg['ci_upper'],
                   color=ci_color, alpha=0.2, label='95% CI')

    # Format axes
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Add R² and p-value to legend
    ax.legend(loc='upper left', frameon=True,
             title=f"R\u00b2 = {reg['r_squared']:.2f}, \u0070 = {reg['p_value']:.3f}",
             title_fontsize=9)

    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='both', alpha=0.25)

    return fig, ax


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    fig, ax = create_scatter_plot(x, y, xlabel, ylabel)
    save_figure(fig, 'output_folder/4_figures/figures/figure3')
