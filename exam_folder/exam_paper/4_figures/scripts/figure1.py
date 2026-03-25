"""
Figure 1: Forest plot of adjusted odds ratios from primary logistic regression.
JAMA Network Open style.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json
import os
import sys

# Load JAMA style
sys.path.insert(0, os.path.dirname(__file__))
import jama_style
from jama_style import JAMA_BLUE, JAMA_GRAY, JAMA_RED, JAMA_ORANGE, PHI_RATIO

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = "/Users/damarisdeng/projects/paper-writing-system/exam_folder/exam_paper"
RESULTS_PATH = os.path.join(BASE, "3_analysis", "analysis_results.json")
OUT_DIR = os.path.join(BASE, "4_figures", "figures")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
with open(RESULTS_PATH) as f:
    results = json.load(f)

est = results["primary_analysis"]["all_estimates"]

# ── Build ordered rows for the forest plot ────────────────────────────────────
# Each row: (label, OR, CI_lower, CI_upper, p_value, color, is_header)
rows = []

# Section: Primary Exposure
rows.append(("Primary Exposure", None, None, None, None, None, True))
rows.append((
    "Training vs. R&D",
    est["is_training_grant"]["OR"],
    est["is_training_grant"]["CI_lower"],
    est["is_training_grant"]["CI_upper"],
    est["is_training_grant"]["p_value"],
    JAMA_BLUE,
    False
))

# Section: Institutional Type (ref = University-Medical)
rows.append(("Institutional Type (ref: University-Medical)", None, None, None, None, None, True))
rows.append((
    "Hospital/NonProfit",
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Hospital-NonProfit"]["OR"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Hospital-NonProfit"]["CI_lower"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Hospital-NonProfit"]["CI_upper"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Hospital-NonProfit"]["p_value"],
    JAMA_GRAY,
    False
))
rows.append((
    "University-Other",
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_University-Other"]["OR"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_University-Other"]["CI_lower"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_University-Other"]["CI_upper"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_University-Other"]["p_value"],
    JAMA_GRAY,
    False
))
rows.append((
    "Other",
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Other"]["OR"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Other"]["CI_lower"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Other"]["CI_upper"],
    est["C(org_type_grouped,_Treatment('University-Medical'))_T_Other"]["p_value"],
    JAMA_GRAY,
    False
))

# Section: Geographic Region (ref = Northeast)
rows.append(("Geographic Region (ref: Northeast)", None, None, None, None, None, True))
rows.append((
    "South",
    est["C(org_state_region,_Treatment('Northeast'))_T_South"]["OR"],
    est["C(org_state_region,_Treatment('Northeast'))_T_South"]["CI_lower"],
    est["C(org_state_region,_Treatment('Northeast'))_T_South"]["CI_upper"],
    est["C(org_state_region,_Treatment('Northeast'))_T_South"]["p_value"],
    JAMA_GRAY,
    False
))
rows.append((
    "Midwest",
    est["C(org_state_region,_Treatment('Northeast'))_T_Midwest"]["OR"],
    est["C(org_state_region,_Treatment('Northeast'))_T_Midwest"]["CI_lower"],
    est["C(org_state_region,_Treatment('Northeast'))_T_Midwest"]["CI_upper"],
    est["C(org_state_region,_Treatment('Northeast'))_T_Midwest"]["p_value"],
    JAMA_GRAY,
    False
))
rows.append((
    "West",
    est["C(org_state_region,_Treatment('Northeast'))_T_West"]["OR"],
    est["C(org_state_region,_Treatment('Northeast'))_T_West"]["CI_lower"],
    est["C(org_state_region,_Treatment('Northeast'))_T_West"]["CI_upper"],
    est["C(org_state_region,_Treatment('Northeast'))_T_West"]["p_value"],
    JAMA_GRAY,
    False
))

# Section: Continuous covariate
rows.append(("Continuous Covariate", None, None, None, None, None, True))
rows.append((
    "Log(Total Award)",
    est["log_total_award"]["OR"],
    est["log_total_award"]["CI_lower"],
    est["log_total_award"]["CI_upper"],
    est["log_total_award"]["p_value"],
    JAMA_GRAY,
    False
))

# ── Layout ─────────────────────────────────────────────────────────────────────
n_rows = len(rows)
fig_height = max(6, n_rows * 0.55 + 1.5)
# Use a more reasonable fixed width to prevent dimension issues
fig_width = 8
fig, ax = plt.subplots(figsize=(fig_width, fig_height))
# Set explicit DPI to prevent rendering issues
matplotlib.rcParams['figure.dpi'] = 100

# Y positions (top to bottom)
y_positions = {}
y = n_rows - 1
data_rows = []
for i, row in enumerate(rows):
    label, OR, lo, hi, pval, color, is_header = row
    y_positions[i] = y
    if not is_header:
        data_rows.append((i, y, label, OR, lo, hi, pval, color))
    y -= 1

# Determine x-axis scale — log scale to handle wide CI
# Clip extreme values for axis display
all_lo = [r[4] for r in data_rows if r[4] is not None and r[4] > 0]
all_hi = [r[5] for r in data_rows if r[5] is not None]
# Exclude "Unknown" region outlier from axis range for readability
# but still plot it clipped
XMIN = 0.05
XMAX = 50.0

ax.set_xscale('log')
ax.set_xlim(XMIN, XMAX)

# Reference line at OR=1 (more prominent)
ax.axvline(x=1.0, color='#666666', linewidth=1.0, linestyle='--', alpha=0.8, zorder=1)
ax.text(1.0, -0.5, 'OR = 1 (No effect)', ha='center', va='top',
        fontsize=8, color='#666666', style='italic', transform=ax.get_yaxis_transform())

# Plot each data row
for idx, y_pos, label, OR, lo, hi, pval, color in data_rows:
    # Clip CI for display purposes
    lo_plot = max(lo, XMIN * 1.01) if lo is not None else OR
    hi_plot = min(hi, XMAX * 0.99) if hi is not None else OR

    # Error bars (thinner, more refined)
    ax.plot([lo_plot, hi_plot], [y_pos, y_pos],
            color=color, linewidth=0.9, zorder=2, solid_capstyle='round')

    # Hollow diamond marker for point estimate (more prominent)
    ax.plot(OR, y_pos, marker='D', markersize=7, color='white',
            markeredgecolor=color, markeredgewidth=1.2, zorder=3)

    # Right-side annotation: OR (95% CI) P
    if pval is not None and pval < 0.001:
        p_str = "<.001"
    elif pval is not None:
        p_str = f".{int(round(pval * 1000)):03d}"[:-1] if pval < 1 else "1.00"
        # Format without leading zero, JAMA style
        p_str = f"{pval:.3f}".lstrip("0") if pval > 0 else "<.001"
    else:
        p_str = ""

    if OR is not None:
        annot = f"{OR:.2f} ({lo:.2f}–{hi:.2f})"
        ax.text(XMAX * 1.02, y_pos, annot, va='center', ha='left', fontsize=8,
                color='#222222', fontfamily='monospace', transform=ax.get_yaxis_transform())
        # Right-align P-values for tabular appearance
        ax.text(XMAX * 1.38, y_pos, p_str, va='center', ha='left', fontsize=8,
                color='#222222', fontfamily='monospace', transform=ax.get_yaxis_transform())

# Y tick labels (labels + section headers)
ytick_positions = []
ytick_labels = []
for i, row in enumerate(rows):
    label, OR, lo, hi, pval, color, is_header = row
    yp = y_positions[i]
    ytick_positions.append(yp)
    if is_header:
        ytick_labels.append(label)
    else:
        ytick_labels.append("  " + label)

ax.set_yticks(ytick_positions)
ax.set_yticklabels(ytick_labels, fontsize=9)

# Bold section headers with separator lines
for i, (text_obj, row) in enumerate(zip(ax.get_yticklabels(), rows)):
    if row[6]:  # is_header
        text_obj.set_fontweight('bold')
        text_obj.set_fontsize(9)
        # Add subtle separator line above header
        yp = y_positions[i] + 0.4
        ax.axhline(y=yp, color='#DDDDDD', linewidth=0.5, linestyle='-', zorder=0)

# Axes labels and title
ax.set_xlabel("Odds Ratio (log scale)", fontsize=11, fontweight='medium')
ax.set_title(
    "Figure 1. Adjusted Odds Ratios for NIH Grant Termination, 2025",
    fontsize=11, loc='left', pad=12, fontweight='bold'
)
# Add subtitle as separate annotation
ax.text(0, 1.02, "N = 5,219; Reference: University-Medical institutions and Northeast region",
        transform=ax.transAxes, fontsize=9, va='bottom', ha='left', color='#555555')

# Column headers at top
top_y = n_rows + 0.4
ax.text(1.0, top_y, "OR (95% CI)", ha='center', va='bottom',
        fontsize=9, fontweight='bold', color='#333333', transform=ax.get_yaxis_transform())
ax.text(XMAX * 1.38, top_y, "P Value", ha='left', va='bottom',
        fontsize=9, fontweight='bold', color='#333333', transform=ax.get_yaxis_transform())

# Legend with subtle frame
primary_patch = mpatches.Patch(color=JAMA_BLUE, label='Primary exposure')
covariate_patch = mpatches.Patch(color=JAMA_GRAY, label='Covariate')
ax.legend(handles=[primary_patch, covariate_patch],
          loc='lower right', fontsize=8, frameon=True,
          edgecolor='#CCCCCC', facecolor='white', fancybox=False)

ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0, width=0.8)
plt.subplots_adjust(left=0.30, right=0.70, top=0.88, bottom=0.10)

# Save
out_png = os.path.join(OUT_DIR, "figure1.png")
out_pdf = os.path.join(OUT_DIR, "figure1.pdf")
# Use explicit DPI without bbox_inches to avoid dimension issues
fig.savefig(out_png, dpi=150, bbox_inches=None, pad_inches=0.1)
fig.savefig(out_pdf, bbox_inches=None, pad_inches=0.1)
plt.close(fig)
print(f"Saved: {out_png}")
print(f"Saved: {out_pdf}")
