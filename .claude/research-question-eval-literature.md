**Changes to `generate-research-questions` SKILL.md:**

The module currently selects one primary question and 1–2 secondary questions, then commits. The change is to make it a **candidate generator, not a decision-maker**. Specifically:

- Step 4 (Rank and Select) stops choosing a single primary. Instead it outputs **all 2–3 candidate PICO questions** from Step 3, each with their feasibility and variable role assignments. The ranking by data feasibility, significance, novelty, and rigor still happens here, but as preliminary scores — not a final selection.
- The output contract changes: `research_questions.json` replaces the `primary_question` field with a `candidate_questions` list, where each entry has the full PICO structure, variable roles, feasibility assessment, and the preliminary score. No question is labeled "primary" yet.
- Secondary questions still exist but are now attached per-candidate (each candidate can have its own subgroup/sensitivity analyses).
- Step 5 (variable role assignment) needs to handle the fact that different candidates may have different variable roles — each candidate carries its own role mapping.

**Changes to the Orchestrator SKILL.md:**

- **New stage inserted** between Stage 2 and the current Stage 3: literature-informed scoring. It reads `candidate_questions` from `research_questions.json`, scores each against the literature, applies feasibility filtering, and produces `ranked_questions.json` with the top entry as the primary analysis target. This stage calls `score_and_rank()`.
- **Stage 4 (analysis) gains a feedback check**: after analysis completes, the orchestrator calls `build_feedback_signal()`. If structural issues are found and cycle count < 2, it returns to the scoring stage with the feedback signal for re-ranking. The inter-stage data flow diagram gets a backward arrow.
- **Cycle counting and hard limit of 2** become part of the orchestrator's stage execution logic, not a separate orchestrator.
- **New artifact**: `decision_log.json` records the full question selection and feedback path. It's added to the inter-stage data flow as an input to Stage 7 (write paper) so the methods section describes the selection process.
- **Time budget reallocation**: the new scoring stage needs ~5 minutes, and up to 2 feedback cycles means analysis time could double in the worst case. The budget table needs adjustment.
- **Validation check** for the new stage: `ranked_questions.json` exists with at least one scored candidate.