# NIH Grant Termination Study — Presentation Output

## Contents

| File | Description |
|------|-------------|
| `slides.md` | Main slide deck in Marp Markdown format |
| `notes.md` | Detailed speaker notes (~60 seconds per slide) |
| `refs.md` | References and key statistics |
| `figure1.png` | Forest plot of adjusted odds ratios |
| `figure2.png` | Termination rates by institutional type |

---

## Quick Start

### Option 1: View in VS Code

1. Install the **Marp for VS Code** extension
2. Open `slides.md`
3. Click "Preview" to view slides
4. Export to PDF/PPTX via the command palette (Cmd+Shift+P → "Marp: Export")

### Option 2: Export to PDF (Command Line)

```bash
# Install Marp CLI (if not already installed)
npm install -g @marp-team/marp-cli

# Export to PDF
marp slides.md --pdf --output presentation.pdf

# Export to PPTX
marp slides.md --pptx --output presentation.pptx
```

### Option 3: One-Click Export (Online)

1. Visit https://marp.app/
2. Drag and drop `slides.md` onto the page
3. Click "Export" to download as PDF or PPTX

---

## Presentation Overview

**Title:** Institutional Type and Geographic Region, Not Funding Category, Drive NIH Grant Termination in 2025

**Duration:** 15-18 minutes (13 slides)

**Target Audience:** Academic researchers, public health professionals, policy makers

**Key Message:** After adjustment, training grants were NOT significantly more likely to be terminated—geographic region and institutional type were the primary drivers.

---

## Slide Structure

| Slide | Title | Key Point |
|-------|-------|-----------|
| 1 | Title | Study identification |
| 2 | Research Question | Were training grants disproportionately targeted? |
| 3 | Study Overview | Design, setting, sample |
| 4 | Unadjusted Findings | 30.1% vs 16.2% crude disparity |
| 5 | Adjusted Analysis | OR 1.11, P=.33 — not significant |
| 6 | Geographic Region | South: 25x higher odds |
| 7 | Institutional Type | Hospital/NP: 10.5x higher odds |
| 8 | Award Size | Larger grants protective (OR 0.66) |
| 9 | Sensitivity Analyses | Confounds geographic confounding |
| 10 | Summary of Findings | Three key takeaways |
| 11 | Policy Implications | Target underresourced institutions |
| 12 | Conclusions | Geography and institution, not grant type |
| 13 | Q&A | Discussion |

---

## Self-Evaluation (Rubric)

| Item | Score (0-10) | Notes |
|------|--------------|-------|
| Goal Clarity | 10 | Audience (academic), objective (introduce paper), CTA (understand findings) all clear |
| Story Structure | 9 | Pyramid principle: conclusion first (geography/institution matter), then evidence |
| Slide Assertions | 10 | All headings are testable assertions; evidence supports each claim |
| Evidence Quality | 9 | Includes ORs, CIs, P-values, sample sizes; figures from paper included |
| Chart Fit | 9 | Forest plot and bar chart appropriately selected; complete with labels |
| Visual & Accessibility | 8 | Good contrast, readable fonts; some could use visual hierarchy improvements |
| Coherence & Transitions | 9 | Logical flow from question to methods to results to implications |
| Speakability | 9 | Speaker notes provide 45-60 second scripts; natural language |
| Deliverables Complete | 10 | slides.md, notes.md, refs.md, figures all included |
| Robustness | 8 | Limitations noted in discussion; data sources documented |

**Total Score: 91/100** — Above delivery threshold of 75.

---

## Key Statistics for Quick Reference

- **Sample:** 5,219 NIH grants
- **Overall termination:** 20.4%
- **Training grant OR (adjusted):** 1.11 (95% CI: 0.90-1.36, P=.33)
- **South vs Northeast OR:** 25.23 (95% CI: 19.96-31.89, P<.001)
- **Hospital/NP vs Medical School OR:** 10.52 (95% CI: 7.69-14.38, P<.001)
- **Log(award) OR:** 0.66 (95% CI: 0.62-0.71, P<.001)

---

## Customization Guide

### To Change Colors

Edit the `style` section in `slides.md`:

```yaml
strong {
  color: #AF1E37;  /* Change to your accent color */
}
```

### To Add Institution Logo

Add to the title slide:

```markdown
<img src="logo.png" style="height: 60px; position: absolute; bottom: 40px; right: 40px;">
```

### To Adjust Slide Count

- Remove Slides 11 (Policy Implications) for a shorter 12-slide deck
- Add backup slides with additional sensitivity analyses if needed

### To Replace Figures

1. Place new PNG files in the presentation folder
2. Update references in `slides.md`:
   ```markdown
   <img src="your_figure.png" alt="Description" style="max-width: 100%;">
   ```

---

## Presentation Checklist

Before presenting:

- [ ] Practice timing — aim for 15-18 minutes
- [ ] Verify figures display correctly
- [ ] Memorize key statistics (ORs, CIs, P-values)
- [ ] Prepare answers to anticipated questions
- [ ] Test projector/audio if presenting in person
- [ ] Have backup PDF in case of technical issues
- [ ] Bring printed notes.md if needed for reference

---

## Anticipated Questions

**Q: Why were Southern states so heavily affected?**
A: Likely due to differential political environments, institutional capacity to mount legal challenges, and concentration of court-ordered reinstatements in Northeastern states.

**Q: Does this mean training grants weren't affected at all?**
A: No — 30% of training grants were terminated versus 16% of R&D grants. But after accounting for where they were located and what institutions hosted them, the grant mechanism itself wasn't the independent driver.

**Q: What should be done differently in policy responses?**
A: Remediation should target underresourced institutions (hospitals, non-profits) and regions (South) rather than focusing on specific grant mechanisms.

---

## Citation

If you use these slides, please cite the original paper:

> Deng J, Luxu S, Ding N, Claude. Institutional Type and Geographic Region, Not Funding Category, Drive NIH Grant Termination in 2025: A Cross-Sectional Analysis. *JAMA Network Open*. 2026. doi:10.1001/jamanetworkopen.2026.XXXXXXX
