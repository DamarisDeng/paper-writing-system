"""
Figure 2: Bar chart of NIH grant termination rates by institutional type.
JAMA Network Open style with Wilson score confidence intervals.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import os
import sys
import math

# Load JAMA style
sys.path.insert(0, os.path.dirname(__file__))
import jama_style
from jama_style import JAMA_BLUE, JAMA_ORANGE, JAMA_GREEN, JAMA_RED, JAMA_GRAY, PHI_RATIO

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = "/Users/damarisdeng/projects/paper-writing-system/exam_folder/exam_paper"
DATA_PATH = os.path.join(BASE, "3_analysis", "analytic_dataset.csv")
OUT_DIR = os.path.join(BASE, "4_figures", "figures")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
print(f"Loaded dataset: {len(df)} rows, columns: {list(df.columns)}")

# Identify relevant columns
org_col = "org_type_grouped"
term_col = "terminated_binary"

# ── Compute termination rates and Wilson CIs ──────────────────────────────────
def wilson_ci(successes, n, z=1.96):
    """Wilson score interval for a proportion."""
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    center = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    margin = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / (1 + z**2 / n)
    return max(0, center - margin), min(1, center + margin)

groups = df.groupby(org_col)[term_col].agg(['sum', 'count']).reset_index()
groups.columns = [org_col, 'n_terminated', 'n_total']
groups['rate'] = groups['n_terminated'] / groups['n_total'] * 100

# Wilson CI
ci_lo, ci_hi = [], []
for _, row in groups.iterrows():
    lo, hi = wilson_ci(row['n_terminated'], row['n_total'])
    ci_lo.append(lo * 100)
    ci_hi.append(hi * 100)
groups['ci_lo'] = ci_lo
groups['ci_hi'] = ci_hi
groups['ci_lo_err'] = groups['rate'] - groups['ci_lo']
groups['ci_hi_err'] = groups['ci_hi'] - groups['rate']

# Sort descending by rate
groups = groups.sort_values('rate', ascending=False).reset_index(drop=True)

# Overall mean
overall_mean = df[term_col].mean() * 100

print(groups.to_string())
print(f"Overall termination rate: {overall_mean:.1f}%")

# ── Color assignment ───────────────────────────────────────────────────────────
def assign_color(rate):
    if rate > 30:
        return JAMA_RED
    elif rate >= 20:
        return JAMA_ORANGE
    else:
        return JAMA_BLUE

colors = [assign_color(r) for r in groups['rate']]

# ── Plot ───────────────────────────────────────────────────────────────────────
fig_width = 8
fig_height = fig_width / PHI_RATIO
fig, ax = plt.subplots(figsize=(fig_width, fig_height))

x = np.arange(len(groups))
bars = ax.bar(x, groups['rate'], color=colors, width=0.55, zorder=2,
              edgecolor='none', linewidth=0)

# Error bars (thinner, more refined)
ax.errorbar(
    x, groups['rate'],
    yerr=[groups['ci_lo_err'].values, groups['ci_hi_err'].values],
    fmt='none', ecolor='#444444', elinewidth=1.0, capsize=3, capthick=1.0, zorder=3
)

# Reference line: overall mean (more refined)
ax.axhline(overall_mean, color='#555555', linewidth=0.9, linestyle='--', zorder=1,
           label=f'Overall mean: {overall_mean:.1f}%', alpha=0.8)

# Bar labels: N and rate (smaller, better positioned)
for i, (bar, row) in enumerate(zip(bars, groups.itertuples())):
    label_text = f"n={row.n_total:,}\n{row.rate:.1f}%"
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + groups['ci_hi_err'].iloc[i] + 0.8,
        label_text,
        ha='center', va='bottom', fontsize=7.5, color='#333333', fontweight='medium'
    )

# X tick labels with better styling
ax.set_xticks(x)
ax.set_xticklabels(groups[org_col], fontsize=9, rotation=15, ha='right', fontweight='medium')
ax.tick_params(axis='x', width=0.8, length=4)

# Y axis with better styling
ax.set_ylabel("Termination Rate (%)", fontsize=11, fontweight='medium')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.tick_params(axis='y', width=0.8, length=4)
y_max = groups['ci_hi'].max() + 7
ax.set_ylim(0, y_max)
ax.set_xlim(-0.5, len(groups) - 0.5)

# Legend for colors (positioned better, with frame)
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=JAMA_RED, label='>30% termination'),
    Patch(facecolor=JAMA_ORANGE, label='20–30% termination'),
    Patch(facecolor=JAMA_BLUE, label='<20% termination'),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=8, frameon=True,
          edgecolor='#CCCCCC', facecolor='white', fancybox=False)

# Title / caption with better styling
ax.set_title(
    "Figure 2. NIH Grant Termination Rates by Institutional Type, 2025",
    fontsize=11, loc='left', pad=12, fontweight='bold'
)
# Add subtitle as separate annotation
ax.text(0, 1.02, "Error bars: 95% CI (Wilson score). Dashed line: overall mean termination rate.",
        transform=ax.transAxes, fontsize=9, va='bottom', ha='left', color='#555555')

# Subtle horizontal grid only
ax.grid(axis='y', alpha=0.15, linewidth=0.5, linestyle='-', zorder=0)
ax.spines['left'].set_linewidth(0.9)
ax.spines['bottom'].set_linewidth(0.9)
plt.tight_layout()

# Save
out_png = os.path.join(OUT_DIR, "figure2.png")
out_pdf = os.path.join(OUT_DIR, "figure2.pdf")
fig.savefig(out_png, dpi=300, bbox_inches='tight')
fig.savefig(out_pdf, bbox_inches='tight')
plt.close(fig)
print(f"Saved: {out_png}")
print(f"Saved: {out_pdf}")
