"""
write_paper.py — Helper utilities for Stage 8: Write Paper.

Provides functions for loading upstream outputs, copying assets,
generating a LaTeX paper skeleton, and validating the final paper.tex.

Usage in SKILL.md:
    import sys; sys.path.insert(0, "workflow/skills/write-paper")
    from write_paper import (
        load_all_inputs, copy_assets, generate_paper_skeleton,
        validate_paper_tex, format_stat
    )
"""

import json
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# ── Input Loading ──────────────────────────────────────────────────────────

def load_all_inputs(output_folder: str) -> Dict[str, Any]:
    """
    Load all upstream outputs needed for paper writing.

    Returns a dict with keys:
        research_questions, analysis_results, manifest,
        bib_path, bib_keys, profile, decision_log, analysis_plan,
        results_summary
    Missing files are recorded in the 'missing' key.
    """
    inputs: Dict[str, Any] = {"missing": []}

    file_map = {
        "research_questions": [
            os.path.join(output_folder, "2_scoring", "ranked_questions.json"),
            os.path.join(output_folder, "2_research_question", "research_questions.json"),
        ],
        "analysis_results": [
            os.path.join(output_folder, "3_analysis", "analysis_results.json"),
        ],
        "manifest": [
            os.path.join(output_folder, "4_figures", "manifest.json"),
        ],
        "profile": [
            os.path.join(output_folder, "1_data_profile", "profile.json"),
        ],
        "decision_log": [
            os.path.join(output_folder, "decision_log.json"),
        ],
        "analysis_plan": [
            os.path.join(output_folder, "3_analysis", "analysis_plan.json"),
        ],
        "results_summary": [
            os.path.join(output_folder, "3_analysis", "results_summary.md"),
        ],
    }

    for key, candidates in file_map.items():
        loaded = False
        for path in candidates:
            if os.path.exists(path):
                try:
                    if path.endswith(".json"):
                        with open(path, "r", encoding="utf-8") as f:
                            inputs[key] = json.load(f)
                    else:
                        with open(path, "r", encoding="utf-8") as f:
                            inputs[key] = f.read()
                    inputs[f"{key}_path"] = path
                    loaded = True
                    break
                except (json.JSONDecodeError, IOError) as e:
                    inputs["missing"].append(f"{path} (parse error: {e})")
        if not loaded:
            inputs["missing"].append(key)

    bib_path = os.path.join(output_folder, "5_references", "references.bib")
    if os.path.exists(bib_path):
        inputs["bib_path"] = bib_path
        inputs["bib_keys"] = extract_bib_keys(bib_path)
    else:
        inputs["bib_path"] = None
        inputs["bib_keys"] = []
        inputs["missing"].append("references.bib")

    required = ["research_questions", "analysis_results", "manifest"]
    missing_required = [k for k in required if k in inputs.get("missing", [])]
    inputs["ready"] = len(missing_required) == 0
    inputs["missing_required"] = missing_required

    print(f"[write_paper] Loaded {len(file_map) - len(inputs['missing'])} / {len(file_map) + 1} inputs")
    if inputs["missing"]:
        print(f"[write_paper] Missing: {inputs['missing']}")

    return inputs


def extract_bib_keys(bib_path: str) -> List[str]:
    """Extract all citation keys from a BibTeX file."""
    keys = []
    pattern = re.compile(r"@\w+\{([^,]+),")
    try:
        with open(bib_path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    keys.append(match.group(1).strip())
    except IOError:
        pass
    return keys


# ── Asset Copying ──────────────────────────────────────────────────────────

def copy_assets(output_folder: str) -> Dict[str, List[str]]:
    """
    Copy figures, tables, and references to <output_folder>/6_paper/.

    Returns a dict with lists of copied files by category.
    """
    paper_dir = os.path.join(output_folder, "6_paper")
    fig_src = os.path.join(output_folder, "4_figures", "figures")
    tab_src = os.path.join(output_folder, "4_figures", "tables")
    bib_src = os.path.join(output_folder, "5_references", "references.bib")

    fig_dst = os.path.join(paper_dir, "figures")
    tab_dst = os.path.join(paper_dir, "tables")

    os.makedirs(fig_dst, exist_ok=True)
    os.makedirs(tab_dst, exist_ok=True)

    copied: Dict[str, List[str]] = {"figures": [], "tables": [], "references": []}

    if os.path.isdir(fig_src):
        for f in os.listdir(fig_src):
            if f.lower().endswith((".png", ".pdf", ".jpg", ".jpeg", ".eps")):
                src = os.path.join(fig_src, f)
                dst = os.path.join(fig_dst, f)
                shutil.copy2(src, dst)
                copied["figures"].append(f)

    if os.path.isdir(tab_src):
        for f in os.listdir(tab_src):
            if f.lower().endswith(".tex"):
                src = os.path.join(tab_src, f)
                dst = os.path.join(tab_dst, f)
                shutil.copy2(src, dst)
                copied["tables"].append(f)

    if os.path.isfile(bib_src):
        shutil.copy2(bib_src, os.path.join(paper_dir, "references.bib"))
        copied["references"].append("references.bib")

    print(f"[write_paper] Copied: {len(copied['figures'])} figures, "
          f"{len(copied['tables'])} tables, {len(copied['references'])} bib files")
    return copied


# ── Statistical Formatting ────────────────────────────────────────────────

def format_stat(
    estimate: float,
    ci_lower: float,
    ci_upper: float,
    p_value: Any,
    measure: str = "coefficient",
    decimals: int = 1,
) -> str:
    """
    Format a statistical result in JAMA style.

    Examples:
        "OR, 1.45 (95% CI, 1.22-1.72; P < .001)"
        "-23.4 (95% CI, -35.2 to -11.5; P < .001)"
    """
    est_str = f"{estimate:.{decimals}f}"
    ci_lo_str = f"{ci_lower:.{decimals}f}"
    ci_hi_str = f"{ci_upper:.{decimals}f}"

    p_str = _format_p_value(p_value)

    measure_labels = {
        "or": "OR",
        "hr": "HR",
        "rr": "RR",
        "aor": "aOR",
        "ahr": "aHR",
        "coefficient": "",
        "difference": "",
        "beta": r"$\beta$",
    }

    label = measure_labels.get(measure.lower(), "")

    if label:
        return f"{label}, {est_str} (95\\% CI, {ci_lo_str} to {ci_hi_str}; {p_str})"
    else:
        return f"{est_str} (95\\% CI, {ci_lo_str} to {ci_hi_str}; {p_str})"


def format_descriptive(mean: float, sd: float, decimals: int = 1) -> str:
    """Format a descriptive statistic as 'mean (SD, sd)'."""
    return f"{mean:.{decimals}f} (SD, {sd:.{decimals}f})"


def format_count_pct(n: int, pct: float, decimals: int = 1) -> str:
    """Format a categorical count as 'n (pct%)'."""
    n_str = f"{n:,}".replace(",", "\\,")
    return f"{n_str} ({pct:.{decimals}f}\\%)"


def _format_p_value(p_value: Any) -> str:
    """Format P value per JAMA style (no leading zero)."""
    if isinstance(p_value, str):
        p_lower = p_value.strip().lower()
        if "<" in p_lower:
            num_part = p_lower.replace("<", "").replace("p", "").replace("=", "").strip()
            try:
                val = float(num_part)
                return f"P < {_strip_leading_zero(val)}"
            except ValueError:
                return f"P {p_value.strip()}"
        try:
            val = float(p_lower)
            p_value = val
        except ValueError:
            return f"P = {p_value}"

    if isinstance(p_value, (int, float)):
        if p_value < 0.001:
            return "P < .001"
        elif p_value < 0.01:
            return f"P = {_strip_leading_zero(round(p_value, 3))}"
        else:
            return f"P = {_strip_leading_zero(round(p_value, 2))}"

    return f"P = {p_value}"


def _strip_leading_zero(val: float) -> str:
    """Remove leading zero from a decimal number (JAMA style: .05 not 0.05)."""
    s = f"{val}"
    if s.startswith("0."):
        return s[1:]
    if s.startswith("-0."):
        return "-" + s[2:]
    return s


# ── LaTeX Skeleton Generation ─────────────────────────────────────────────

def generate_paper_skeleton(
    output_folder: str,
    template_path: str,
    inputs: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a paper.tex skeleton with boilerplate pre-filled from upstream
    data. The skeleton contains the full LaTeX preamble and section structure
    with placeholder markers (%%FILL: ...) where Claude must write content.

    Args:
        output_folder: Base output directory
        template_path: Path to the JAMA template.tex
        inputs: Loaded upstream inputs (from load_all_inputs); loaded if None

    Returns:
        The generated LaTeX source as a string. Also writes to
        <output_folder>/6_paper/paper.tex.
    """
    if inputs is None:
        inputs = load_all_inputs(output_folder)

    rq = inputs.get("research_questions", {})
    analysis = inputs.get("analysis_results", {})
    manifest = inputs.get("manifest", {})
    profile = inputs.get("profile", {})

    primary_q = rq.get("primary_question", rq)
    question_text = primary_q.get("question", "Research Question")
    population = primary_q.get("population", "")
    exposure = primary_q.get("exposure_or_intervention", "")
    outcome = primary_q.get("outcome", "")
    study_design = primary_q.get("study_design", "")

    title = _derive_title(primary_q)
    short_title = title[:60] + "..." if len(title) > 63 else title
    subject = _derive_subject(primary_q)

    analytic = analysis.get("analytic_sample", {})
    total_n = analytic.get("total_n", "N")
    primary = analysis.get("primary_analysis", {})
    method = primary.get("method", "Statistical Analysis")

    figures = manifest.get("figures", [])
    tables = manifest.get("tables", [])

    bib_keys = inputs.get("bib_keys", [])

    fig_includes = _build_figure_includes(figures)
    tab_includes = _build_table_includes(tables)
    primary_results = _extract_primary_results(analysis)
    sensitivity_results = _extract_sensitivity_results(analysis)
    descriptive_summary = _extract_descriptive_summary(analysis)
    limitations = _extract_limitations(rq)

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    preamble = _extract_preamble(template)

    skeleton = _assemble_paper(
        preamble=preamble,
        title=title,
        short_title=short_title,
        subject=subject,
        question_text=question_text,
        population=population,
        exposure=exposure,
        outcome=outcome,
        study_design=study_design,
        total_n=total_n,
        method=method,
        primary_results=primary_results,
        sensitivity_results=sensitivity_results,
        descriptive_summary=descriptive_summary,
        fig_includes=fig_includes,
        tab_includes=tab_includes,
        limitations=limitations,
        bib_keys=bib_keys,
    )

    paper_path = os.path.join(output_folder, "6_paper", "paper.tex")
    os.makedirs(os.path.dirname(paper_path), exist_ok=True)
    with open(paper_path, "w", encoding="utf-8") as f:
        f.write(skeleton)

    print(f"[write_paper] Paper skeleton written to {paper_path} ({len(skeleton)} bytes)")
    return skeleton


def _derive_title(primary_q: Dict) -> str:
    """Derive a paper title from the research question."""
    exposure = primary_q.get("exposure_or_intervention", "Exposure")
    outcome = primary_q.get("outcome", "Outcome")
    design = primary_q.get("study_design", "")

    exposure_short = exposure.split(",")[0].split(";")[0].strip()
    outcome_short = outcome.split(",")[0].split(";")[0].strip()

    if len(exposure_short) > 50:
        exposure_short = exposure_short[:50].rsplit(" ", 1)[0]
    if len(outcome_short) > 50:
        outcome_short = outcome_short[:50].rsplit(" ", 1)[0]

    design_suffix = ""
    design_lower = design.lower()
    if "cross-sectional" in design_lower:
        design_suffix = "A Cross-Sectional Study"
    elif "cohort" in design_lower:
        design_suffix = "A Cohort Study"
    elif "ecological" in design_lower:
        design_suffix = "An Ecological Study"
    elif "difference" in design_lower:
        design_suffix = "A Difference-in-Differences Analysis"
    elif "case-control" in design_lower:
        design_suffix = "A Case-Control Study"

    title = f"Association Between {exposure_short} and {outcome_short}"
    if design_suffix:
        title = f"{title}: {design_suffix}"

    return title


def _derive_subject(primary_q: Dict) -> str:
    """Derive the JAMA subject area from the research question."""
    text = json.dumps(primary_q).lower()
    if any(kw in text for kw in ["public health", "population", "vaccine", "mandate",
                                   "mortality", "covid", "pandemic", "epidemiol"]):
        return "Public Health"
    if any(kw in text for kw in ["cardio", "heart", "stroke", "hypertension"]):
        return "Cardiology"
    if any(kw in text for kw in ["cancer", "oncol", "tumor", "neoplasm"]):
        return "Oncology"
    if any(kw in text for kw in ["diabetes", "endocrin", "metabol"]):
        return "Endocrinology and Diabetes"
    if any(kw in text for kw in ["pediatr", "child", "infant", "neonat"]):
        return "Pediatrics"
    return "Public Health"


def _extract_preamble(template: str) -> str:
    """Extract the LaTeX preamble (everything before \\begin{document})."""
    idx = template.find(r"\begin{document}")
    if idx == -1:
        return template
    return template[:idx]


def _build_figure_includes(figures: List[Dict]) -> str:
    """Build LaTeX \\includegraphics blocks for all figures."""
    lines = []
    for i, fig in enumerate(figures, 1):
        files = fig.get("files", {})
        pdf_path = files.get("pdf", f"figures/figure{i}.pdf")
        png_path = files.get("png", f"figures/figure{i}.png")
        title = fig.get("title", f"Figure {i}")

        fig_path = pdf_path if pdf_path else png_path

        lines.append(f"\\begin{{figure}}[H]")
        lines.append(f"\\centering")
        lines.append(f"\\includegraphics[width=\\textwidth]{{{fig_path}}}")
        lines.append(f"\\caption{{{_escape_latex(title)}}}")
        lines.append(f"\\label{{fig:figure{i}}}")
        lines.append(f"\\end{{figure}}")
        lines.append("")
    return "\n".join(lines)


def _build_table_includes(tables: List[Dict]) -> str:
    """Build LaTeX \\input blocks for all tables."""
    lines = []
    for tab in tables:
        file_path = tab.get("file", "")
        if file_path:
            lines.append(f"\\input{{{file_path}}}")
            lines.append("")
    return "\n".join(lines)


def _extract_primary_results(analysis: Dict) -> Dict[str, Any]:
    """Extract primary analysis results for paper content."""
    primary = analysis.get("primary_analysis", {})
    models = primary.get("models", [])

    result = {
        "method": primary.get("method", ""),
        "outcome": primary.get("outcome", ""),
        "exposure": primary.get("exposure", ""),
        "models": [],
    }

    for model in models:
        model_info = {
            "name": model.get("model_name", ""),
            "n": model.get("n", 0),
            "r_squared": model.get("r_squared", None),
            "adj_r_squared": model.get("adj_r_squared", None),
            "coefficients": [],
        }
        for coef in model.get("coefficients", []):
            model_info["coefficients"].append({
                "variable": coef.get("variable", ""),
                "estimate": coef.get("estimate", 0),
                "ci_lower": coef.get("ci_lower", 0),
                "ci_upper": coef.get("ci_upper", 0),
                "p_value": coef.get("p_value", ""),
                "formatted": format_stat(
                    coef.get("estimate", 0),
                    coef.get("ci_lower", 0),
                    coef.get("ci_upper", 0),
                    coef.get("p_value", ""),
                ),
            })
        result["models"].append(model_info)

    return result


def _extract_sensitivity_results(analysis: Dict) -> List[Dict]:
    """Extract sensitivity analysis results."""
    sensitivities = analysis.get("sensitivity_analyses", [])
    results = []
    for sa in sensitivities:
        info = {
            "name": sa.get("name", ""),
            "description": sa.get("description", ""),
        }
        sa_results = sa.get("results", {})
        coefficients = sa_results.get("coefficients", [])
        exposure_coefs = [c for c in coefficients if c.get("variable") != "intercept"]
        if exposure_coefs:
            c = exposure_coefs[0]
            info["formatted"] = format_stat(
                c.get("estimate", 0),
                c.get("ci_lower", 0),
                c.get("ci_upper", 0),
                c.get("p_value", ""),
            )
        results.append(info)
    return results


def _extract_descriptive_summary(analysis: Dict) -> Dict[str, Any]:
    """Extract descriptive statistics summary for sample description."""
    desc = analysis.get("descriptive_statistics", {})
    sample = analysis.get("analytic_sample", {})

    return {
        "total_n": sample.get("total_n", 0),
        "exposure_groups": sample.get("exposure_groups", {}),
        "variables": desc.get("variables", {}),
    }


def _extract_limitations(rq: Dict) -> List[str]:
    """Extract limitations from the research question feasibility assessment."""
    feasibility = rq.get("feasibility_assessment") or {}
    limitations = list(feasibility.get("limitations", []))
    if not limitations:
        primary = rq.get("primary_question", rq)
        if isinstance(primary, dict):
            feasibility = primary.get("feasibility_assessment", {}) or {}
            limitations = list(feasibility.get("limitations", []))
    return [lim for lim in limitations if isinstance(lim, str)]


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in text content."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def _assemble_paper(
    preamble: str,
    title: str,
    short_title: str,
    subject: str,
    question_text: str,
    population: str,
    exposure: str,
    outcome: str,
    study_design: str,
    total_n: Any,
    method: str,
    primary_results: Dict,
    sensitivity_results: List[Dict],
    descriptive_summary: Dict,
    fig_includes: str,
    tab_includes: str,
    limitations: List[str],
    bib_keys: List[str],
) -> str:
    """Assemble the full paper.tex from components."""

    models = primary_results.get("models", [])
    fully_adjusted = models[-1] if models else {}
    exposure_coefs = [
        c for c in fully_adjusted.get("coefficients", [])
        if c.get("variable") not in ("intercept",)
        and not c["variable"].startswith("log")
        and c["variable"].lower() not in ("northeast", "south", "west", "midwest")
    ]
    main_finding_formatted = exposure_coefs[0]["formatted"] if exposure_coefs else "%%FILL: main finding"
    r_squared = fully_adjusted.get("r_squared")
    r2_str = f"{r_squared:.2f}" if r_squared else ""

    exposure_groups = descriptive_summary.get("exposure_groups", {})
    group_names = list(exposure_groups.keys())
    group_info = []
    for gn in group_names:
        gdata = exposure_groups[gn]
        group_info.append(f"{gn.replace('_', ' ')} (n={gdata.get('n', '?')})")
    groups_str = "; ".join(group_info) if group_info else "%%FILL: group sizes"

    lim_text = ""
    for i, lim in enumerate(limitations, 1):
        clean = lim.split(":", 1)[-1].strip() if ":" in lim else lim
        ordinal = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth"][min(i - 1, 5)]
        lim_text += f"{ordinal}, {clean.lower()}\n\n"

    preamble_patched = preamble
    preamble_patched = re.sub(
        r"\\newcommand\{\\jamashorttitle\}\{[^}]*\}",
        f"\\\\newcommand{{\\\\jamashorttitle}}{{{_escape_latex(short_title)}}}",
        preamble_patched,
    )
    preamble_patched = re.sub(
        r"\\newcommand\{\\jamasubject\}\{[^}]*\}",
        f"\\\\newcommand{{\\\\jamasubject}}{{{subject}}}",
        preamble_patched,
    )

    paper = f"""{preamble_patched}
\\begin{{document}}
\\thispagestyle{{firstpage}}
\\sloppy


%% --- Article Type + Subject --------------------------------------------------
{{\\sffamily\\bfseries\\fontsize{{9}}{{11}}\\selectfont
  \\textcolor{{jamacrimson}}{{Original Investigation}}%
  \\textcolor{{jamadarkgray}}{{\\enspace|\\enspace {subject}}}%
}}

\\vspace{{8pt}}

%% --- Title -------------------------------------------------------------------
{{\\sffamily\\bfseries\\fontsize{{18}}{{21}}\\selectfont\\color{{jamadarkgray}}
{_escape_latex(title)}\\par}}

\\vspace{{8pt}}

%% --- Authors -----------------------------------------------------------------
{{\\fontsize{{9.5}}{{11.5}}\\selectfont\\color{{jamadarkgray}}
AI-Generated Research Paper; Claude, Anthropic\\par}}

\\vspace{{12pt}}

%% =============================================================================
%%  ABSTRACT  +  KEY POINTS  (side-by-side layout)
%% =============================================================================

\\noindent{{\\color{{jamalightgray}}\\rule{{\\textwidth}}{{0.5pt}}}}
\\vspace{{6pt}}

\\noindent
\\begin{{minipage}}[t]{{0.62\\textwidth}}
%% --- Abstract (left column, ~62% width) --------------------------------------
{{\\sffamily\\bfseries\\fontsize{{11}}{{13}}\\selectfont\\color{{jamacrimson}} Abstract\\par}}
\\vspace{{4pt}}

\\abslabel{{IMPORTANCE}}
{{\\fontsize{{9}}{{11.5}}\\selectfont
%%FILL: 1-2 sentences on why this study matters — gap in knowledge.
\\par}}

\\absrule

\\abslabel{{OBJECTIVE}}
{{\\fontsize{{9}}{{11.5}}\\selectfont
%%FILL: Begin with "To determine..." or "To evaluate..."
\\par}}

\\absrule

\\abslabel{{DESIGN, SETTING, AND PARTICIPANTS}}
{{\\fontsize{{9}}{{11.5}}\\selectfont
%%FILL: {study_design}. {population}. N = {total_n}.
\\par}}

\\absrule

\\abslabel{{EXPOSURE}}
{{\\fontsize{{9}}{{11.5}}\\selectfont
%%FILL: {_escape_latex(exposure[:200])}
\\par}}

\\absrule

\\abslabel{{MAIN OUTCOMES AND MEASURES}}
{{\\fontsize{{9}}{{11.5}}\\selectfont
%%FILL: {_escape_latex(outcome[:200])}. {method}.
\\par}}

\\absrule

\\abslabel{{RESULTS}}
{{\\fontsize{{9}}{{11.5}}\\selectfont
%%FILL: Key demographics (N={total_n}, {groups_str}), then main findings: {main_finding_formatted}.
\\par}}

\\absrule

\\abslabel{{CONCLUSIONS AND RELEVANCE}}
{{\\fontsize{{9}}{{11.5}}\\selectfont
%%FILL: Interpretation and implications in 1-2 sentences.
\\par}}

\\vspace{{4pt}}
\\noindent{{\\color{{jamalightgray}}\\rule{{0.62\\textwidth}}{{0.4pt}}}}


\\end{{minipage}}%
\\hfill
%% --- Key Points (right column, ~33% width) -----------------------------------
\\begin{{minipage}}[t]{{0.33\\textwidth}}
\\begin{{mdframed}}[style=keypointsbox]
{{\\sffamily\\bfseries\\fontsize{{10}}{{12}}\\selectfont\\color{{jamacrimson}}
Key Points\\par}}
\\vspace{{4pt}}

{{\\sffamily\\bfseries\\fontsize{{8.5}}{{10.5}}\\selectfont Question\\enspace}}%
{{\\fontsize{{8.5}}{{10.5}}\\selectfont
%%FILL: One-sentence research question.
\\par}}

\\vspace{{6pt}}

{{\\sffamily\\bfseries\\fontsize{{8.5}}{{10.5}}\\selectfont Findings\\enspace}}%
{{\\fontsize{{8.5}}{{10.5}}\\selectfont
%%FILL: Main quantitative result: {main_finding_formatted}.
\\par}}

\\vspace{{6pt}}

{{\\sffamily\\bfseries\\fontsize{{8.5}}{{10.5}}\\selectfont Meaning\\enspace}}%
{{\\fontsize{{8.5}}{{10.5}}\\selectfont
%%FILL: Clinical/policy implication in one sentence.
\\par}}
\\end{{mdframed}}



\\end{{minipage}}

\\newpage

%% =============================================================================
%%  INTRODUCTION
%% =============================================================================
\\section*{{Introduction}}

%%FILL: Paragraph 1 — Broad context: burden of disease, prevalence, public health significance.

%%FILL: Paragraph 2 — Background: What is known — cite references.

%%FILL: Paragraph 3 — Gap: What is not known.

%%FILL: Paragraph 4 — Objective: Clear statement of study aim.


%% =============================================================================
%%  METHODS
%% =============================================================================
\\section*{{Methods}}

\\subsection*{{Data}}
%%FILL: Data source, time period, population, sample selection.
This study used publicly available, deidentified data and was exempt from institutional review board approval.

\\subsection*{{Outcome Measures}}
%%FILL: Define primary outcome: {_escape_latex(outcome[:200])}.

\\subsection*{{Exposure}}
%%FILL: Define exposure: {_escape_latex(exposure[:200])}.

\\subsection*{{Covariates}}
%%FILL: List all adjustment variables with justification.

\\subsection*{{Statistical Analysis}}
%%FILL: Describe methods ({method}). N = {total_n}.
Analyses were performed using Python version 3.x with statsmodels and pandas. Statistical significance was set at 2-sided P < .05.


%% =============================================================================
%%  RESULTS
%% =============================================================================
\\section*{{Results}}

%%FILL: Sample description — reference Table 1. Report total N={total_n}, {groups_str}.

%%FILL: Primary analysis — main finding: {main_finding_formatted}. R² = {r2_str}.

%%FILL: Sensitivity analyses.

{tab_includes}

{fig_includes}


%% =============================================================================
%%  DISCUSSION
%% =============================================================================
\\section*{{Discussion}}

%%FILL: Paragraph 1 — Summary: Restate main finding in context.

%%FILL: Paragraph 2 — Comparison: How results compare to prior studies.

%%FILL: Paragraph 3 — Mechanisms: Possible explanations.

%%FILL: Paragraph 4 — Implications: Clinical, policy, or public health significance.

\\subsection*{{Limitations}}
{lim_text if lim_text else "%%FILL: Limitations of this study."}

%%FILL: Future directions — 1-2 sentences.


%% =============================================================================
%%  CONCLUSIONS
%% =============================================================================
\\section*{{Conclusions}}

%%FILL: 2-3 sentences. Main finding and primary implication.


%% =============================================================================
%%  ARTICLE INFORMATION
%% =============================================================================
\\vspace{{6pt}}
\\noindent{{\\color{{jamalightgray}}\\rule{{\\textwidth}}{{0.4pt}}}}
\\vspace{{4pt}}


%% =============================================================================
%%  REFERENCES
%% =============================================================================

{{\\fontsize{{8.5}}{{10.5}}\\selectfont
\\bibliographystyle{{vancouver}}
\\bibliography{{references}}
}}


%% =============================================================================
%%  SUPPLEMENT (optional, starts on new page)
%% =============================================================================
\\clearpage
\\section*{{Supplement 1}}

\\subsection*{{eAppendix 1. Statistical Models and Methods Details}}
%%FILL: Detailed model specifications, equations, assumption checks.

\\subsection*{{eTable 1. Supplementary Table Title}}
%%FILL: Additional table from analysis.

\\subsection*{{eFigure 1. Supplementary Figure Title}}
%%FILL: Additional figure from analysis.


\\end{{document}}"""

    return paper


# ── Validation ─────────────────────────────────────────────────────────────

def validate_paper_tex(output_folder: str) -> Dict[str, Any]:
    """
    Validate the generated paper.tex for completeness and correctness.

    Returns a dict with:
        passed (bool), errors (list), warnings (list), checks (dict)
    """
    paper_path = os.path.join(output_folder, "6_paper", "paper.tex")
    bib_path = os.path.join(output_folder, "6_paper", "references.bib")
    fig_dir = os.path.join(output_folder, "6_paper", "figures")
    tab_dir = os.path.join(output_folder, "6_paper", "tables")

    result: Dict[str, Any] = {
        "passed": True,
        "errors": [],
        "warnings": [],
        "checks": {},
    }

    if not os.path.exists(paper_path):
        result["passed"] = False
        result["errors"].append("paper.tex does not exist")
        return result

    with open(paper_path, "r", encoding="utf-8") as f:
        content = f.read()

    size_kb = len(content.encode("utf-8")) / 1024
    result["checks"]["file_size_kb"] = round(size_kb, 1)
    if size_kb < 5:
        result["errors"].append(f"paper.tex is too small ({size_kb:.1f} KB, expected >5 KB)")
        result["passed"] = False

    result["checks"]["balanced_braces"] = _check_balanced_braces(content)
    if not result["checks"]["balanced_braces"]:
        result["errors"].append("Unbalanced braces detected in paper.tex")
        result["passed"] = False

    envs = _check_balanced_environments(content)
    result["checks"]["balanced_environments"] = envs["balanced"]
    if not envs["balanced"]:
        result["errors"].append(f"Unbalanced environments: {envs['unmatched']}")
        result["passed"] = False

    required_sections = [
        (r"\\abslabel\{IMPORTANCE\}", "Abstract: IMPORTANCE"),
        (r"\\abslabel\{OBJECTIVE\}", "Abstract: OBJECTIVE"),
        (r"\\abslabel\{DESIGN, SETTING, AND PARTICIPANTS\}", "Abstract: DESIGN"),
        (r"\\abslabel\{EXPOSURE\}", "Abstract: EXPOSURE"),
        (r"\\abslabel\{MAIN OUTCOMES AND MEASURES\}", "Abstract: MAIN OUTCOMES"),
        (r"\\abslabel\{RESULTS\}", "Abstract: RESULTS"),
        (r"\\abslabel\{CONCLUSIONS AND RELEVANCE\}", "Abstract: CONCLUSIONS"),
        (r"Key Points", "Key Points box"),
        (r"\\section\*\{Introduction\}", "Introduction"),
        (r"\\section\*\{Methods\}", "Methods"),
        (r"\\section\*\{Results\}", "Results"),
        (r"\\section\*\{Discussion\}", "Discussion"),
        (r"\\subsection\*\{Limitations\}", "Limitations"),
        (r"\\section\*\{Conclusions\}", "Conclusions"),
        (r"\\bibliography\{references\}", "References"),
    ]

    missing_sections = []
    for pattern, name in required_sections:
        if not re.search(pattern, content):
            missing_sections.append(name)
    result["checks"]["sections_present"] = len(required_sections) - len(missing_sections)
    result["checks"]["sections_total"] = len(required_sections)
    if missing_sections:
        result["errors"].append(f"Missing sections: {missing_sections}")
        result["passed"] = False

    placeholders = re.findall(r"%%FILL:|TODO|XXX|PLACEHOLDER", content, re.IGNORECASE)
    result["checks"]["placeholders_remaining"] = len(placeholders)
    if placeholders:
        result["warnings"].append(
            f"{len(placeholders)} placeholder(s) remaining in paper.tex"
        )

    cite_keys_used = set(re.findall(r"\\cite\{([^}]+)\}", content))
    expanded_keys = set()
    for key_group in cite_keys_used:
        for key in key_group.split(","):
            expanded_keys.add(key.strip())
    result["checks"]["citations_used"] = len(expanded_keys)

    if os.path.exists(bib_path):
        bib_keys = set(extract_bib_keys(bib_path))
        missing_keys = expanded_keys - bib_keys
        if missing_keys:
            result["warnings"].append(f"Citations not in references.bib: {missing_keys}")
        result["checks"]["citations_resolved"] = len(expanded_keys - missing_keys)
    else:
        result["warnings"].append("references.bib not found in 6_paper/")

    fig_refs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", content)
    missing_figs = []
    for fig_ref in fig_refs:
        full_path = os.path.join(output_folder, "6_paper", fig_ref)
        if not os.path.exists(full_path):
            missing_figs.append(fig_ref)
    result["checks"]["figures_referenced"] = len(fig_refs)
    result["checks"]["figures_missing"] = len(missing_figs)
    if missing_figs:
        result["errors"].append(f"Missing figure files: {missing_figs}")
        result["passed"] = False

    tab_refs = re.findall(r"\\input\{([^}]+)\}", content)
    missing_tabs = []
    for tab_ref in tab_refs:
        full_path = os.path.join(output_folder, "6_paper", tab_ref)
        if not os.path.exists(full_path):
            missing_tabs.append(tab_ref)
    result["checks"]["tables_referenced"] = len(tab_refs)
    result["checks"]["tables_missing"] = len(missing_tabs)
    if missing_tabs:
        result["errors"].append(f"Missing table files: {missing_tabs}")
        result["passed"] = False

    if not result["errors"]:
        result["passed"] = True

    status = "PASS" if result["passed"] else "FAIL"
    print(f"[write_paper] Validation: {status} "
          f"({len(result['errors'])} errors, {len(result['warnings'])} warnings)")

    return result


def _check_balanced_braces(content: str) -> bool:
    """Check that all curly braces in the LaTeX source are balanced.

    Counts { and } on non-comment portions of each line. Escaped braces
    (\\{ and \\}) are treated as balanced pairs in practice so we include
    them in the raw count for simplicity.
    """
    depth = 0
    for line in content.split("\n"):
        code_part = line
        idx = 0
        while idx < len(code_part):
            if code_part[idx] == "%" and (idx == 0 or code_part[idx - 1] != "\\"):
                code_part = code_part[:idx]
                break
            idx += 1
        depth += code_part.count("{") - code_part.count("}")
        if depth < 0:
            return False
    return depth == 0


def _check_balanced_environments(content: str) -> Dict[str, Any]:
    """Check that all LaTeX environments are properly opened and closed."""
    begins = re.findall(r"\\begin\{(\w+)\}", content)
    ends = re.findall(r"\\end\{(\w+)\}", content)

    begin_counts: Dict[str, int] = {}
    end_counts: Dict[str, int] = {}
    for env in begins:
        begin_counts[env] = begin_counts.get(env, 0) + 1
    for env in ends:
        end_counts[env] = end_counts.get(env, 0) + 1

    unmatched = []
    all_envs = set(list(begin_counts.keys()) + list(end_counts.keys()))
    for env in all_envs:
        b = begin_counts.get(env, 0)
        e = end_counts.get(env, 0)
        if b != e:
            unmatched.append(f"{env}: {b} begin vs {e} end")

    return {"balanced": len(unmatched) == 0, "unmatched": unmatched}


# ── Main (for standalone testing) ──────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python write_paper.py <output_folder> [template_path]")
        print("")
        print("Commands:")
        print("  python write_paper.py <output_folder>                  — validate paper.tex")
        print("  python write_paper.py <output_folder> <template_path>  — generate skeleton")
        print("  python write_paper.py <output_folder> --copy-assets    — copy assets only")
        sys.exit(1)

    output_folder = sys.argv[1]

    if len(sys.argv) >= 3 and sys.argv[2] == "--copy-assets":
        result = copy_assets(output_folder)
        print(json.dumps(result, indent=2))
    elif len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
        template_path = sys.argv[2]
        inputs = load_all_inputs(output_folder)
        if inputs["ready"]:
            skeleton = generate_paper_skeleton(output_folder, template_path, inputs)
            print(f"Skeleton generated: {len(skeleton)} bytes")
        else:
            print(f"Cannot generate skeleton — missing required inputs: {inputs['missing_required']}")
            sys.exit(1)
    else:
        result = validate_paper_tex(output_folder)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["passed"] else 1)
