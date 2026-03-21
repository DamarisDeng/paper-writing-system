"""
JAMA Network Open Visualization Style
Publication-ready matplotlib configuration for JAMA figures
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# JAMA Network Open color palette
JAMA_COLORS = {
    'crimson': '#AF1E37',
    'dark_gray': '#323232',
    'medium_gray': '#5A5A5A',
    'light_gray': '#C8C8C8',
    'gold': '#C39B32',
    'blue_accent': '#2E5A88',
    'green_accent': '#2E7D32',
}

# Ordered palette for multi-group plots (grayscale-friendly)
JAMA_PALETTE = ['#AF1E37', '#2E5A88', '#5A5A5A', '#C39B32', '#2E7D32', '#C8C8C8']

def set_jama_style():
    """Apply JAMA Network Open visual style to matplotlib."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
        'font.size': 9,
        'axes.titlesize': 11,
        'axes.titleweight': 'bold',
        'axes.labelsize': 9,
        'axes.labelweight': 'bold',
        'axes.linewidth': 0.8,
        'axes.edgecolor': '#323232',
        'axes.labelcolor': '#323232',
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'xtick.color': '#5A5A5A',
        'ytick.color': '#5A5A5A',
        'legend.fontsize': 8,
        'legend.frameon': False,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5,
    })
    mpl.rcParams['pdf.fonttype'] = 42  # Editable text in PDF
    mpl.rcParams['ps.fonttype'] = 42

def save_figure(fig, filepath_stem):
    """Save figure as both PNG (300 DPI) and PDF."""
    fig.savefig(f"{filepath_stem}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{filepath_stem}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {filepath_stem}.png and {filepath_stem}.pdf")
