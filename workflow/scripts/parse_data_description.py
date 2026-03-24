#!/usr/bin/env python3
"""
Parse Data_Description.md and identify required datasets.

This script reads the Data_Description.md file and:
1. Extracts dataset names and download instructions
2. Checks what's already available on disk
3. Generates a download manifest for missing datasets

Usage:
    python parse_data_description.py <data_folder> <output_folder>
"""

import json
import os
import re
import sys
from pathlib import Path

# JSON schema for manifest validation
MANIFEST_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name", "target_dir"],
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "target_dir": {"type": "string"},
            "downloads": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {"type": "string", "format": "uri"},
                        "extract": {"type": "boolean"}
                    }
                }
            },
            "verify_patterns": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
}


def parse_data_description(data_desc_path: Path) -> list[dict]:
    """Parse Data_Description.md and extract dataset information.

    Returns a list of datasets with their download requirements.
    """
    if not data_desc_path.exists():
        print(f"Warning: {data_desc_path} not found")
        return []

    with open(data_desc_path) as f:
        content = f.read()

    datasets = []

    # Parse each dataset section (marked by ## headers)
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip first section (title)
        if not section.strip():
            continue

        lines = section.strip().split('\n')
        dataset_name = lines[0].strip()

        dataset_info = {
            "name": dataset_name,
            "description": "",
            "target_dir": "",
            "downloads": [],
            "verify_patterns": [],
            "file_patterns": []  # Files that should exist if dataset is present
        }

        # Extract description
        desc_match = re.search(r'- \*\*What it contains\*\*:\s*(.+)', section)
        if desc_match:
            dataset_info["description"] = desc_match.group(1).strip()

        # Extract download script/instructions
        download_block = re.search(r'```bash\n(.*?)```', section, re.DOTALL)
        if download_block:
            script = download_block.group(1)
            dataset_info["download_script"] = script

            # Extract URLs from script (handles wget and curl patterns)
            url_pattern = r'(?:wget|curl).*?\s+([\'"]?)(https?://[^\s\'" ]+)\1'
            for match in re.finditer(url_pattern, script):
                url = match.group(2)
                dataset_info["downloads"].append({
                    "url": url,
                    "extract": url.endswith('.zip')
                })

        # Extract dataset filename (if mentioned)
        name_match = re.search(r'- \*\*Dataset name\*\*:\s*`?([^`\n]+)`?', section)
        if name_match:
            filename = name_match.group(1).strip()
            dataset_info["file_patterns"].append(filename)

        # Extract verify patterns from "Files included" or similar
        files_match = re.search(r'Files included.*?:\s*(.+)', section, re.IGNORECASE)
        if files_match:
            files_text = files_match.group(1)
            # Look for patterns like *.csv, pulse2021_puf_*.csv, etc.
            patterns = re.findall(r'[\w.*]+\.?\w*', files_text)
            dataset_info["verify_patterns"] = [p for p in patterns if '*' in p or '.' in p]

        # Extract target_dir from markdown (data-driven approach)
        # Look for patterns like "to the folder `data/HPS_PUF`" or "in the folder `HPS_PUF`"
        target_dir_match = re.search(
            r'(?:to|in)\s+the\s+folder\s+[`\'"]?data/([^\s\'"`]+)[`\'"]?',
            section,
            re.IGNORECASE
        )
        if target_dir_match:
            dataset_info["target_dir"] = target_dir_match.group(1)
        else:
            # Also check for "in the folder `FOLDER_NAME`" pattern (without data/ prefix)
            target_dir_match = re.search(
                r'in\s+the\s+folder\s+[`\'"]?([^/`\s\'"]+)[`\'"]?',
                section,
                re.IGNORECASE
            )
            if target_dir_match:
                dataset_info["target_dir"] = target_dir_match.group(1)
            else:
                # Default: use sanitized name as target_dir
                safe_name = re.sub(r'[^\w\s-]', '', dataset_name).strip().replace(' ', '_')
                dataset_info["target_dir"] = safe_name

        # Extract verify patterns from specific patterns mentioned in text
        # This captures patterns like "pulse2021_puf_*.csv" that may appear in the description
        verify_pattern_match = re.search(r'([a-zA-Z0-9_]+_\*\\\.[a-z]{3})', section)
        if verify_pattern_match:
            pattern = verify_pattern_match.group(1).replace('\\.', '.')
            if pattern not in dataset_info["verify_patterns"]:
                dataset_info["verify_patterns"].append(pattern)

        if dataset_info["downloads"] or dataset_info["file_patterns"]:
            datasets.append(dataset_info)

    return datasets


def validate_manifest(manifest: list[dict]) -> bool:
    """Validate manifest against JSON schema.

    Returns True if valid, False if invalid (or jsonschema not available).
    """
    try:
        import jsonschema
    except ImportError:
        print("Warning: jsonschema not installed. Skipping manifest validation.")
        print("  Install with: pip install jsonschema")
        return True  # Allow proceeding without validation

    try:
        jsonschema.validate(instance=manifest, schema=MANIFEST_SCHEMA)
        print("Manifest validation: PASSED")
        return True
    except jsonschema.ValidationError as e:
        print(f"Manifest validation FAILED: {e.message}")
        print(f"  Path: {'.'.join(str(p) for p in e.path)}")
        return False


def check_availability(datasets: list[dict], data_folder: Path) -> tuple[list[dict], list[dict]]:
    """Check which datasets are already available.

    Returns:
        (available_datasets, missing_datasets)
    """
    available = []
    missing = []

    for dataset in datasets:
        is_available = False

        # Check if any expected files exist
        for pattern in dataset.get("file_patterns", []):
            # Handle glob patterns
            if '*' in pattern:
                matches = list(data_folder.glob(pattern))
                if matches:
                    is_available = True
                    break
            else:
                # Exact filename match
                if (data_folder / pattern).exists():
                    is_available = True
                    break

        # Also check target_dir if specified
        if dataset.get("target_dir"):
            target_dir = data_folder / dataset["target_dir"]
            if target_dir.exists():
                # Check for verify_patterns
                for pattern in dataset.get("verify_patterns", []):
                    matches = list(target_dir.glob(pattern))
                    if matches:
                        is_available = True
                        break

        dataset["status"] = "available" if is_available else "missing"

        if is_available:
            available.append(dataset)
        else:
            missing.append(dataset)

    return available, missing


def main():
    if len(sys.argv) != 3:
        print("Usage: python parse_data_description.py <data_folder> <output_folder>")
        sys.exit(1)

    data_folder = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])

    data_desc_path = data_folder / "Data_Description.md"

    # Parse the data description
    datasets = parse_data_description(data_desc_path)

    if not datasets:
        print("No datasets found in Data_Description.md")
        # Create empty manifest
        manifest = []
    else:
        # Check availability
        available, missing = check_availability(datasets, data_folder)

        print(f"\n=== Data Availability Check ===")
        print(f"Total datasets documented: {len(datasets)}")
        print(f"Already available: {len(available)}")
        print(f"Missing: {len(missing)}")

        if available:
            print("\nAvailable datasets:")
            for ds in available:
                print(f"  ✓ {ds['name']}")

        if missing:
            print("\nMissing datasets:")
            for ds in missing:
                print(f"  ✗ {ds['name']}: {ds.get('description', 'No description')}")

        # Build manifest for missing datasets
        manifest = []
        for ds in missing:
            entry = {
                "name": ds["name"],
                "description": ds.get("description", ""),
                "target_dir": ds.get("target_dir", ds["name"].replace(' ', '_')),
            }
            if ds.get("downloads"):
                entry["downloads"] = ds["downloads"]
            if ds.get("verify_patterns"):
                entry["verify_patterns"] = ds["verify_patterns"]
            manifest.append(entry)

        # Validate manifest before writing
        if manifest and not validate_manifest(manifest):
            print("ERROR: Manifest validation failed. Aborting.")
            sys.exit(2)

    # Write manifest
    manifest_path = output_folder / "0_data_acquisition" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nWrote manifest to: {manifest_path}")

    # Write availability report
    report = {
        "total_datasets": len(datasets),
        "available_count": len([d for d in datasets if d.get("status") == "available"]),
        "missing_count": len([d for d in datasets if d.get("status") == "missing"]),
        "datasets": [
            {
                "name": ds["name"],
                "status": ds.get("status", "unknown"),
                "description": ds.get("description", ""),
                "target_dir": ds.get("target_dir", "")
            }
            for ds in datasets
        ]
    }

    report_path = output_folder / "0_data_acquisition" / "availability_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Exit with error if datasets are missing (signals orchestrator to run acquire-data)
    if manifest:
        print(f"\n{len(manifest)} dataset(s) need to be downloaded.")
        sys.exit(1)  # Non-zero exit = needs download
    else:
        print("\nAll documented datasets are available.")
        sys.exit(0)  # Zero exit = all available


if __name__ == "__main__":
    main()
