# JAMA Network Open style module
# Okabe-Ito colorblind-safe palette
JAMA_BLUE = "#0072B2"
JAMA_ORANGE = "#E69F00"
JAMA_GREEN = "#009E73"
JAMA_RED = "#D55E00"
JAMA_GRAY = "#999999"
PHI_RATIO = 1.618
FONT = "Arial"

import matplotlib
matplotlib.rcParams.update({
    'font.family': FONT,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'font.size': 10,
    'axes.labelsize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    # Enhanced aesthetic settings
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'grid.alpha': 0.2,
    'grid.linewidth': 0.5,
    'grid.linestyle': '--',
    'legend.framealpha': 0.9,
    'legend.fancybox': False,
    'legend.edgecolor': '#CCCCCC',
    'legend.borderpad': 0.4,
    'legend.labelspacing': 0.4,
    'axes.linewidth': 0.9,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'axes.unicode_minus': False,
})
