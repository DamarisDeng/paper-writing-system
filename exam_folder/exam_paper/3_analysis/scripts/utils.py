"""
utils.py — Shared utilities used across all analysis modules.

Provides p-value formatting, JSON sanitization, and common constants.
"""

import json
import os
from typing import Optional

import numpy as np


def safe_pval(p) -> Optional[float]:
    """Format p-value: never exactly 0, report as < 0.001 threshold."""
    if p is None:
        return None
    p = float(p)
    if np.isnan(p):
        return None
    if p < 0.001:
        return 0.001  # Downstream should display as "< 0.001"
    return round(p, 4)


def sanitize_pvalues(obj):
    """Recursively find and sanitize p-values in a nested dict/list."""
    if isinstance(obj, dict):
        return {k: sanitize_pvalues(v) if k != "p_value" else safe_pval(v)
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_pvalues(item) for item in obj]
    return obj


def save_json(data: dict, path: str):
    """Write a dict to JSON with default=str for non-serializable types."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Saved: {path}")


def update_json_section(section_name: str, data: dict, path: str):
    """Load an existing JSON file, update one top-level key, and re-save."""
    existing = {}
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)
    existing[section_name] = data
    save_json(existing, path)


def save_model_summary(summary_text: str, path: str):
    """Save a plain-text model summary."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(summary_text)
    print(f"  Saved model summary: {path}")


# ── JAMA display formatting ──────────────────────────────────────────────────

JAMA_BLUE   = "#1f4e79"
JAMA_ORANGE = "#c05000"


def jama_p(p: float) -> str:
    """JAMA p-value string. No leading zero; '< .001' threshold."""
    if p < 0.001:
        return "< .001"
    elif p < 0.01:
        return f"{p:.3f}".lstrip("0")   # ".003"
    else:
        return f"{p:.2f}".lstrip("0")   # ".03"


def jama_ci(lo: float, hi: float) -> str:
    """95% CI string in JAMA format: '95% CI, 1.22-1.72'."""
    return f"95% CI, {lo:.2f}-{hi:.2f}"


def jama_effect(estimate: float, ci_lo: float, ci_hi: float,
                p: float, metric: str = "OR") -> str:
    """Full JAMA effect-size sentence, e.g. 'OR = 1.45 (95% CI, 1.22-1.72; P < .001)'."""
    p_str = jama_p(p)
    p_part = f"P {p_str}" if p_str.startswith("<") else f"P = {p_str}"
    return f"{metric} = {estimate:.2f} (95% CI, {ci_lo:.2f}-{ci_hi:.2f}; {p_part})"


def jama_fig(nrows: int = 1, ncols: int = 1):
    """Return (fig, ax) configured with JAMA-style defaults (no top/right spines, light grid)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(nrows, ncols, figsize=(7, 4.5), facecolor="white")
    axes = [ax] if nrows * ncols == 1 else list(ax.flat)
    for a in axes:
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.yaxis.grid(True, color="#e0e0e0", linewidth=0.7, zorder=0)
        a.set_axisbelow(True)
    return fig, ax
    # Save: fig.savefig("path.png", dpi=300, bbox_inches="tight")
