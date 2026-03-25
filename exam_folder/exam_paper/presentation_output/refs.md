# References — NIH Grant Termination Study

## Primary Citation

Deng J, Luxu S, Ding N, Claude. Institutional Type and Geographic Region, Not Funding Category, Drive NIH Grant Termination in 2025: A Cross-Sectional Analysis. *JAMA Network Open*. 2026. doi:10.1001/jamanetworkopen.2026.XXXXXXX

---

## Data Sources

1. **NIH Grant Witness Dataset**
   - Publicly available registry of NIH awards affected by 2025 federal funding actions
   - https://grantwitness.com
   - Accessed: March 2026
   - 5,419 unique award records (5,219 in final analytic sample)

2. **NIH RePORTER**
   - Official NIH grant tracking system
   - https://reporter.nih.gov
   - Source of award details, institutional information, activity codes

3. **USAspending.gov**
   - Federal spending database
   - Source of award amounts and financial data

---

## Key Background Literature

### NIH Funding Context

1. **NIH Budget and Portfolio**
   - NIH supports >$48 billion annually in extramural research
   - ~50,000 active grants spanning basic science, clinical investigation, workforce development
   - Training grants represent primary pipeline for next-generation investigators

2. **2025 Federal Funding Actions**
   - February-March 2025: >5,000 NIH grants terminated, frozen, or disrupted
   - Estimated $17.2 billion in committed research funding affected
   - Unprecedented scope in NIH history

### Related Studies

3. **Mastej et al. (2025)**
   - Documented profound disruption to scientific training programs
   - Highlighted concerns for early-career researchers
   - Noted potential impact on scientific workforce diversity

4. **Miller et al. (2026) — JAMA Pediatrics**
   - Documented selective termination of grants in areas inconsistent with federal policy priorities
   - Found disproportionate impact on gender-affirming care research
   - Demonstrated content-based targeting in specific domains

5. **Jalali et al. (2025)**
   - Analyzed institutional capacity to respond to funding disruptions
   - Noted differential impacts on community-based research settings

6. **Gonsalves et al. (2025)**
   - Documented court challenges to grant terminations
   - Harvard lawsuit secured reinstatements for Massachusetts institutions
   - Geographic variation in legal outcomes

### Methodological References

7. **STROBE Guidelines**
   - Von Elm et al. (2007). Strengthening the Reporting of Observational Studies in Epidemiology
   - Study followed STROBE reporting guidelines

8. **Statistical Methods**
   - Python 3.11 with statsmodels 0.14, pandas 2.0, scipy 1.11
   - Multivariable logistic regression with maximum likelihood estimation
   - Profile likelihood confidence intervals, Wald tests

---

## Key Statistics from Study

| Statistic | Value |
|-----------|-------|
| Total grants analyzed | 5,219 |
| Training grants | 1,558 (29.9%) |
| R&D grants | 3,661 (70.1%) |
| Overall termination rate | 20.4% |
| Training grant termination (unadjusted) | 30.1% |
| R&D grant termination (unadjusted) | 16.2% |
| Training grant OR (adjusted) | 1.11 (95% CI: 0.90-1.36, P=.33) |
| South vs Northeast OR | 25.23 (95% CI: 19.96-31.89, P<.001) |
| Hospital/NP vs Medical School OR | 10.52 (95% CI: 7.69-14.38, P<.001) |
| Log(award) OR | 0.66 (95% CI: 0.62-0.71, P<.001) |
| McFadden pseudo-R² | 0.295 |

---

## Institutional Classification

| Category | Examples |
|----------|----------|
| **University-Medical** | Schools of medicine, public health, dentistry, nursing, veterinary medicine, pharmacy |
| **University-Other** | Schools of arts and sciences, engineering, other academic departments |
| **Hospital/Non-Profit** | Independent hospitals, non-profit research institutes, community-based organizations |
| **Other** | Government agencies, for-profit entities |

---

## Grant Mechanisms Analyzed

### Research Training & Career Development (Exposure)
- **F-series**: F31, F32, F30 pre- and postdoctoral fellowships
- **T-series**: T32 institutional training grants
- **K-series**: K01, K08, K23, K99/R00 career development awards

### Research & Development (Reference)
- **R-series**: R01, R21, R03, R56 investigator-initiated research grants

### Excluded Categories
- Small Business Innovation Research (SBIR/STTR)
- Other Transactions Authority
- Construction and Modernization

---

## Geographic Classification

US Census Bureau four-region classification:
- **Northeast**: CT, ME, MA, NH, RI, VT, NJ, NY, PA
- **Midwest**: IL, IN, IA, KS, MI, MN, MO, NE, ND, OH, SD, WI
- **South**: AL, AR, DE, DC, FL, GA, KY, LA, MD, MS, NC, OK, SC, TN, TX, VA, WV
- **West**: AK, AZ, CA, CO, HI, ID, MT, NM, NV, OR, UT, WA, WY

---

## Presentation Metadata

| Field | Value |
|-------|-------|
| Title | Institutional Type and Geographic Region, Not Funding Category, Drive NIH Grant Termination in 2025 |
| Authors | Junyang Deng, Shupeng Luxu, Nuo Ding, Claude |
| Journal | JAMA Network Open |
| Publication Date | March 2026 |
| DOI | 10.1001/jamanetworkopen.2026.XXXXXXX |
| Study Design | Cross-sectional analysis |
| Sample Size | 5,219 NIH grants |
| Funding Source | None |
| Conflicts of Interest | None reported |

---

## Notes for Further Reading

This study contributes to the emerging literature on the 2025 NIH funding disruptions by:

1. Providing the first multivariable analysis of grant termination predictors
2. Documenting the role of geographic and institutional confounding
3. Identifying structural inequities in termination patterns
4. Informing equity-focused policy responses

For questions about data access or analysis code, contact the corresponding author.
