#!/usr/bin/env python3
"""
Build the Stage 4 download manifest from data_acquisition_requirements
in ranked_questions.json.

Usage:
    python workflow/skills/orchestrator/scripts/build_stage4_manifest.py <output_folder>

Exit codes:
    0 — manifest written (or no downloads needed)
    1 — error reading ranked_questions.json

Prints one of:
    MANIFEST_WRITTEN <path>   — manifest created, caller should run acquire-data
    NO_DOWNLOADS_NEEDED       — data_acquisition_requirements is empty, skip Stage 4
"""
import json
import sys
from pathlib import Path


def build_manifest(output_folder: str) -> None:
    ranked_path = Path(output_folder) / "2_scoring" / "ranked_questions.json"
    if not ranked_path.exists():
        print(f"ERROR: {ranked_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(ranked_path) as f:
        ranked = json.load(f)

    data_reqs = ranked.get("data_acquisition_requirements", [])

    if not data_reqs:
        print("NO_DOWNLOADS_NEEDED")
        sys.exit(0)

    manifest = []
    for req in data_reqs:
        manifest.append({
            "name": req.get("variable", "unknown"),
            "description": req.get("action", "Supplementary data for analysis"),
            "target_dir": req.get("target_dir", req.get("variable", "unknown")),
            "downloads": [
                {
                    "url": req.get("url", ""),
                    "extract": req.get("extract", False)
                }
            ]
        })

    manifest_path = Path(output_folder) / "2_research_question" / "download_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"MANIFEST_WRITTEN {manifest_path}")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: build_stage4_manifest.py <output_folder>")
        sys.exit(1)

    build_manifest(sys.argv[1])
