"""
JAMA Network Open Publication-Quality Figure Style

This module provides colorblind-safe color palettes, publication-quality
matplotlib styling, and helper functions for creating consistent figures.

Usage:
    from jama_style import create_figure, get_colors, save_figure

    fig, ax = create_figure(width_type='single')
    colors = get_colors(3)
    ax.plot([1, 2, 3], [1, 4, 9], color=colors[0])
    save_figure(fig, 'output/figure1')
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# =============================================================================
# COLOR PALETTES - Colorblind-Friendly & Grayscale-Safe
# =============================================================================

# Primary JAMA color palette (colorblind-safe, ordered by lightness)
JAMA_COLORS = {
    'crimson': '#AF1E37',      # Primary - dark red
    'dark_gray': '#323232',    # Text, axes
    'medium_gray': '#5A5A5A',  # Secondary text
    'light_gray': '#C8C8C8',   # Grid lines
    'gold': '#C39B32',         # Highlight
    'blue_accent': '#2E5A88',  # Secondary
    'green_accent': '#2E7D32', # Tertiary
}

# Okabe-Ito palette - scientifically designed for colorblind viewers
# Each color is distinct for all forms of colorblindness
OKABE_ITO = {
    'orange': '#E69F00',
    'sky_blue': '#56B4E9',
    'bluish_green': '#009E73',
    'yellow': '#F0E442',
    'blue': '#0072B2',
    'vermilion': '#D55E00',
    'reddish_purple': '#CC79A7',
    'gray': '#999999',
    'black': '#000000',
}

# Ordered palette for multi-group plots (5 colors, grayscale-friendly)
PUBPALETTE_5 = ['#E69F00', '#0072B2', '#009E73', '#D55E00', '#CC79A7']

# Extended palette for up to 8 groups
PUBPALETTE_8 = ['#E69F00', '#0072B2', '#009E73', '#F0E442',
                '#D55E00', '#CC79A7', '#56B4E9', '#999999']

# Diverging palette for heatmaps (centered at neutral)
DIVERGING_PALETTE = ['#D55E00', '#F0E442', '#999999', '#56B4E9', '#0072B2']

# Sequential palette for continuous data (light to dark)
SEQUENTIAL_PALETTE = ['#F7FCF5', '#C7E9C0', '#74C476', '#238B45', '#005A32']


def get_diverging_cmap():
    """Return a colorblind-safe diverging colormap."""
    return LinearSegmentedColormap.from_list(
        'diverging', DIVERGING_PALETTE, N=256)


def get_sequential_cmap():
    """Return a colorblind-safe sequential colormap."""
    return LinearSegmentedColormap.from_list(
        'sequential', SEQUENTIAL_PALETTE, N=256)


# =============================================================================
# FIGURE DIMENSIONS - Golden Ratio & Publication Standards
# =============================================================================

GOLDEN_RATIO = (1 + 5**0.5) / 2  # ~1.618


def get_figure_width(width_type='single'):
    """Return figure width in inches based on column width.

    Args:
        width_type: 'single' (6.5"), 'double' (13.5"), 'half' (3.25"), 'abstract' (3.0")
    """
    widths = {
        'single': 6.5,
        'double': 13.5,
        'half': 3.25,
        'abstract': 3.0,
    }
    return widths.get(width_type, 6.5)


def get_figure_height(width_type='single', height_ratio=None):
    """Return figure height in inches.

    Args:
        width_type: 'single', 'double', 'half', or 'abstract'
        height_ratio: height/width ratio (default: 1/GOLDEN_RATIO)
    """
    width = get_figure_width(width_type)
    if height_ratio is None:
        height_ratio = 1 / GOLDEN_RATIO
    return width * height_ratio


# =============================================================================
# STYLE CONFIGURATION
# =============================================================================

def set_jama_style():
    """
    Apply JAMA Network Open publication-quality visual style to matplotlib.

    Ensures fonts are legible, colors work for colorblind readers,
    layout is clean, and output is print-ready (300 DPI).
    """
    plt.rcParams.update({
        # Font settings - Helvetica/Arial for publication
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.titleweight': 'bold',
        'axes.labelsize': 10,
        'axes.labelweight': 'bold',
        'axes.linewidth': 1.0,
        'axes.edgecolor': '#323232',
        'axes.labelcolor': '#323232',
        'axes.facecolor': 'white',
        'axes.formatter.use_mathtext': True,

        # Tick settings
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'xtick.color': '#5A5A5A',
        'ytick.color': '#5A5A5A',
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,
        'xtick.minor.width': 0.5,
        'ytick.minor.width': 0.5,
        'xtick.direction': 'out',
        'ytick.direction': 'out',

        # Legend settings
        'legend.fontsize': 9,
        'legend.frameon': True,
        'legend.framealpha': 0.9,
        'legend.edgecolor': '#C8C8C8',
        'legend.fancybox': False,
        'legend.borderpad': 0.5,
        'legend.labelspacing': 0.4,

        # Figure settings
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.15,
        'figure.facecolor': 'white',
        'figure.edgecolor': 'none',

        # Grid settings
        'grid.alpha': 0.25,
        'grid.linewidth': 0.5,
        'grid.color': '#C8C8C8',
        'axes.grid': False,

        # Line settings
        'lines.linewidth': 1.5,
        'lines.markersize': 6,
        'lines.markeredgewidth': 0.8,

        # Patch settings
        'patch.linewidth': 0.8,
        'patch.facecolor': '#0072B2',
        'patch.edgecolor': '#323232',
    })

    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['ps.fonttype'] = 42


# =============================================================================
# HELPER FUNCTIONS FOR COMMON PLOT TYPES
# =============================================================================

def create_figure(width_type='single', height_ratio=None, nrows=1, ncols=1):
    """Create a figure with publication-quality dimensions.

    Automatically scales font sizes for multipanel figures to maintain
    legibility. More panels = larger scaling factor.

    Args:
        width_type: 'single', 'double', 'half', or 'abstract'
        height_ratio: height/width ratio (None for golden ratio)
        nrows, ncols: subplot grid dimensions

    Returns:
        fig, axes: Figure and axes objects
    """
    # Apply base style first
    set_jama_style()

    # Auto-scale fonts for multipanel figures
    # More panels = more scaling to maintain legibility
    n_panels = nrows * ncols
    if n_panels > 1:
        # Progressive scaling based on panel count
        if n_panels <= 3:
            scale_factor = 1.2
        elif n_panels <= 6:
            scale_factor = 1.3
        else:
            scale_factor = 1.4

        # Scale all relevant font parameters
        plt.rcParams['font.size'] = int(10 * scale_factor)
        plt.rcParams['axes.labelsize'] = int(10 * scale_factor)
        plt.rcParams['axes.titlesize'] = int(12 * scale_factor)
        plt.rcParams['xtick.labelsize'] = int(9 * scale_factor)
        plt.rcParams['ytick.labelsize'] = int(9 * scale_factor)
        plt.rcParams['legend.fontsize'] = int(9 * scale_factor)

    width = get_figure_width(width_type)
    height = get_figure_height(width_type, height_ratio)

    if nrows > 1:
        height = height * nrows + 0.5 * (nrows - 1)

    fig, axes = plt.subplots(nrows, ncols, figsize=(width, height))

    if nrows * ncols == 1:
        axes = np.array([axes]) if isinstance(axes, plt.Axes) else axes

    return fig, axes


def add_subplot_labels(axes, labels=None, offset_x=-0.1, offset_y=1.05):
    """Add panel labels (A, B, C...) to subplots.

    Uses the current axes.titlesize for scaling, so panel labels
    scale automatically with multipanel font scaling.

    Args:
        axes: Array of axes objects
        labels: List of labels (default: A, B, C, ...)
        offset_x, offset_y: Position offsets relative to axes
    """
    if labels is None:
        labels = [chr(65 + i) for i in range(len(axes))]

    # Use current rcParams for consistent scaling
    label_fontsize = plt.rcParams.get('axes.titlesize', 12)

    for ax, label in zip(axes.flat, labels):
        ax.text(offset_x, offset_y, label, transform=ax.transAxes,
                fontsize=label_fontsize, fontweight='bold',
                va='bottom', ha='right')


def format_axis_labels(ax, xlabel=None, ylabel=None, title=None):
    """Format axis labels with proper styling.

    Args:
        ax: Axes object
        xlabel, ylabel: Axis labels (include units in parentheses)
        title: Plot title (optional - usually use LaTeX caption instead)
    """
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontweight='bold', pad=10)


def format_legend(ax, location='best', title=None, ncol=1, frame=True):
    """Format legend with publication-quality styling.

    Args:
        ax: Axes object
        location: 'best', 'upper right', 'outside', etc.
        title: Legend title (optional)
        ncol: Number of columns
        frame: Whether to show legend frame
    """
    legend = ax.get_legend()
    if legend is None:
        return

    if location == 'outside':
        ax.legend(title=title, loc='upper left',
                 bbox_to_anchor=(1.02, 1), borderaxespad=0,
                 frameon=frame, ncol=ncol)
    else:
        ax.legend(title=title, loc=location, frameon=frame, ncol=ncol)


def add_reference_line(ax, value=0, orientation='horizontal', style='--',
                      color='#5A5A5A', linewidth=0.8, alpha=0.7):
    """Add a reference line (e.g., null value, threshold).

    Args:
        ax: Axes object
        value: Line position
        orientation: 'horizontal' or 'vertical'
        style: Line style ('--', '-', ':')
        color: Line color
        linewidth: Line width
        alpha: Transparency
    """
    if orientation == 'horizontal':
        ax.axhline(y=value, linestyle=style, color=color,
                  linewidth=linewidth, alpha=alpha, zorder=0)
    else:
        ax.axvline(x=value, linestyle=style, color=color,
                  linewidth=linewidth, alpha=alpha, zorder=0)


def save_figure(fig, filepath_stem, formats=['png', 'pdf'], dpi=300):
    """Save figure in multiple formats for publication.

    Args:
        fig: Figure object
        filepath_stem: Base path (without extension)
        formats: List of formats ('png', 'pdf', 'svg', 'eps')
        dpi: Resolution for raster formats
    """
    for fmt in formats:
        output_path = f"{filepath_stem}.{fmt}"
        fig.savefig(output_path, dpi=dpi if fmt in ['png', 'jpg'] else None,
                   bbox_inches='tight', pad_inches=0.15,
                   format=fmt, transparent=False)
        print(f"Saved: {output_path}")

    plt.close(fig)


# =============================================================================
# COLOR PALETTE SELECTION HELPER
# =============================================================================

def get_colors(n_colors, palette='okabe-ito'):
    """Get a colorblind-safe palette for n items.

    Args:
        n_colors: Number of colors needed
        palette: 'okabe-ito', 'jama', 'diverging', or 'sequential'

    Returns:
        List of hex color codes
    """
    if palette == 'okabe-ito':
        base = list(OKABE_ITO.values())[:8]
    elif palette == 'jama':
        base = PUBPALETTE_5
    elif palette == 'diverging':
        return DIVERGING_PALETTE[:n_colors]
    elif palette == 'sequential':
        step = max(1, len(SEQUENTIAL_PALETTE) // n_colors)
        return SEQUENTIAL_PALETTE[::step][:n_colors]
    else:
        base = PUBPALETTE_5

    return [base[i % len(base)] for i in range(n_colors)]


def plot_with_error_bars(ax, x, y, yerr=None, xerr=None, color='#0072B2',
                         label=None, marker='o', capsize=3, alpha=0.8):
    """Create a clean error bar plot.

    Args:
        ax: Axes object
        x, y: Data coordinates
        yerr, xerr: Error bar values
        color: Marker and line color
        label: Legend label
        marker: Marker style
        capsize: Error bar cap size
        alpha: Transparency
    """
    ax.errorbar(x, y, yerr=yerr, xerr=xerr, fmt=marker, color=color,
               label=label, markersize=6, linewidth=1.5, capsize=capsize,
               capthick=1, elinewidth=1.5, alpha=alpha)


# =============================================================================
# COLORBLIND ACCESSIBILITY CHECK
# =============================================================================

def check_colorblind_safe(color_list, verbose=False):
    """
    Check if colors are reasonably distinct for common colorblind types.

    Uses simple RGB distance approximation. For more rigorous testing,
    use the colormath library with CIEDE2000.

    Args:
        color_list: List of hex color codes
        verbose: Print warnings for problematic pairs

    Returns:
        bool: True if all pairs are reasonably distinct
    """
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_distance(c1, c2):
        return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

    rgb_colors = [hex_to_rgb(c) for c in color_list]
    min_distance = float('inf')
    problematic = []

    for i, c1 in enumerate(rgb_colors):
        for c2 in rgb_colors[i+1:]:
            dist = rgb_distance(c1, c2)
            if dist < min_distance:
                min_distance = dist
            if dist < 100:  # Empirical threshold for concern
                problematic.append((color_list[i], color_list[c2 == c1], dist))

    if verbose and problematic:
        for c1, c2, dist in problematic:
            print(f"WARNING: {c1} and {c2} may be indistinguishable (distance: {dist:.1f})")

    return min_distance >= 100
