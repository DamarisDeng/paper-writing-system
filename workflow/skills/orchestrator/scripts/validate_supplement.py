#!/usr/bin/env python3
"""
Validate that paper.tex contains a fully-populated supplement section.

Usage:
    python workflow/skills/orchestrator/scripts/validate_supplement.py <output_folder>

Exit codes:
    0 — validation passed
    1 — validation failed (reason printed to stdout)
"""
import re
import sys
from pathlib import Path


def validate(output_folder: str) -> tuple[bool, str]:
    paper_tex = Path(output_folder) / "6_paper" / "paper.tex"
    if not paper_tex.exists():
        return False, "paper.tex not found at 6_paper/paper.tex"

    tex_content = paper_tex.read_text(encoding="utf-8")

    # 1. Supplement section must be present
    if not re.search(r'\\section\*\{Supplement', tex_content, re.IGNORECASE):
        return False, "Supplement section (\\section*{Supplement}) missing from paper.tex"

    # 2. Isolate supplement block (from \section*{Supplement to end of file)
    supplement_match = re.search(r'\\section\*\{Supplement.*', tex_content, re.IGNORECASE | re.DOTALL)
    supplement_block = supplement_match.group(0) if supplement_match else ""

    # 3. eAppendix 1 subsection must be present (minimum required content)
    if not re.search(r'\\subsection\*\{eAppendix 1', supplement_block):
        return False, "eAppendix 1 subsection missing — supplement exists but has no model specification content"

    # 4a. Explicit INSERT-style placeholders
    explicit_placeholders = ["[INSERT", "[TODO", "[PLACEHOLDER", "[TBD", "INSERT HERE", "TO BE FILLED"]
    explicit_found = [tok for tok in explicit_placeholders if tok.upper() in supplement_block.upper()]
    if explicit_found:
        return False, f"Explicit placeholder tokens found in supplement: {explicit_found}"

    # 4b. Unfilled template variables from write-paper's template (e.g. [method], [exposure], [outcome])
    template_vars = re.findall(r'\[[a-z][a-zA-Z0-9_ ]*\]', supplement_block)
    if template_vars:
        return False, f"Unfilled template variables found in supplement: {template_vars[:5]}"

    return True, "Supplement section present with eAppendix 1 populated"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_supplement.py <output_folder>")
        sys.exit(1)

    passed, reason = validate(sys.argv[1])
    if passed:
        print(f"[STAGE 8 VALIDATION PASSED] {reason}")
        sys.exit(0)
    else:
        print(f"[STAGE 8 VALIDATION FAILED] {reason}")
        print("[ACTION] Re-run write-paper with instruction: 'Populate eAppendix 1 with model equations from analysis_results.json and eAppendix 2 with model fit statistics. Do not use placeholder text.'")
        sys.exit(1)
