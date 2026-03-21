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
