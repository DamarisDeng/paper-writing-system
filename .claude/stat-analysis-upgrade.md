# Implementation Plan: Closing the Gaps for JAMA-Level Reproducibility

## Context

Analysis of 7 JAMA Network Open papers revealed that the pipeline can reproduce most methods, but there are specific gaps that prevent full reproducibility. This plan details the implementation steps to close these gaps.

---

## Gap Summary

| Gap | Papers Affected | Priority | Complexity |
|-----|-----------------|----------|------------|
| Age-as-time-scale for Cox PH | 1, 2, 3 | HIGH | Low |
| Fine-Gray competing risks | 1, 3, 4 | HIGH | Medium |
| Survey weights | 7 | MEDIUM | Medium |
| Time-varying covariates | 5 (optional) | LOW | High |

---

## Critical Files to Modify

```
workflow/skills/statistical-analysis/
├── SKILL.md                              # Update method documentation
├── scripts/
│   ├── regression.py                     # Add age_time_scale, Fine-Gray
│   ├── utils.py                          # Helper functions
│   ├── validation.py                     # Add Fine-Gray assumption checks
│   └── descriptive.py                    # Add survey weight support
└── references/
    └── methods.md                         # Document new methods
```

---

## Implementation Tasks

### Task 1: Add Age-as-Time-Scale Option to Cox PH Models

**File**: `workflow/skills/statistical-analysis/scripts/regression.py`

**Current State**: The `_fit_cox()` function uses `duration_col` directly from the data. It does not support using age as the time scale (where time = age_at_event - age_at_entry).

**Implementation**:

```python
def _fit_cox(df, outcome, exposure, covars, time_scale: str = "time") -> dict:
    """Fit Cox PH model with optional age-as-time-scale.

    Args:
        time_scale: "time" for standard time-to-event, "age" for age-as-time-scale

    For age-as-time-scale:
        - Entry time is df[entry_col] (e.g., age_at_diagnosis)
        - Exit time is df[outcome] (e.g., age_at_event)
        - Model uses (exit - entry) as duration with left-truncation
    """
    from lifelines import CoxPHFitter

    # ... existing event column detection ...

    if time_scale == "age":
        # Need entry column (e.g., age_at_entry)
        entry_col = None
        for name in ("age_entry", "entry_age", "baseline_age", "age_start"):
            if name in df.columns:
                entry_col = name
                break
        if entry_col is None:
            return {"error": "Age-as-time-scale requires an entry age column."}

        # Create CoxPHFitter with left-truncation
        cdf = df[[entry_col, outcome, event_col, exposure] + covars].dropna().copy()
        cph = CoxPHFitter()
        cph.fit(
            cdf,
            duration_col=outcome,
            event_col=event_col,
            entry_col=entry_col,  # Left-truncation
            strata=[],
            show_progress=False
        )
    else:
        # Standard time-to-event (existing code)
        cph.fit(cdf, duration_col=outcome, event_col=event_col)
```

**Changes to `fit_regression()` signature**:
```python
def fit_regression(
    df, outcome, exposure, covariates,
    method: str = "ols",
    cluster_col: Optional[str] = None,
    time_scale: str = "time",  # NEW
) -> dict:
```

**Testing**:
- Create synthetic dataset with age_entry, age_event, event columns
- Verify HR estimates match manual calculation
- Test with and without left-truncation

**SKILL.md updates**:
- Add `time_scale` parameter to Track D documentation
- Example: `fit_regression(..., method="cox", time_scale="age")`

---

### Task 2: Implement Fine-Gray Competing Risks Models

**File**: `workflow/skills/statistical-analysis/scripts/regression.py`

**Current State**: Fine-Gray is mentioned in SKILL.md Track D but not implemented.

**Implementation**: Add new function using `lifelines.CumulativeIncidenceFitter`:

```python
def _fit_fine_gray(df, outcome, exposure, covars, event_of_interest=1) -> dict:
    """Fine-Gray subdistribution hazard model for competing risks.

    Requires:
        - outcome: time-to-event column
        - event_col: event indicator with 0=censored, 1=event_of_interest, 2=competing_event
    """
    from lifelines import CumulativeIncidenceFitter

    # Detect competing event column
    event_col = None
    for name in ("event", "status", "cause", "event_type"):
        if name in df.columns:
            event_col = name
            break

    cols = [outcome, event_col, exposure] + [c for c in covars if c in df.columns]
    cdf = df[cols].dropna().copy()

    # Encode: 0=censored, 1=event_of_interest, 2=competing
    cif = CumulativeIncidenceFitter()
    cif.fit(
        cdf,
        durations=outcome,
        event_col=event_col,
        event_of_interest=event_of_interest
    )

    # Extract subdistribution hazard ratio via regression
    # lifelines doesn't have direct Fine-Gray regression, use alternative:
    from statsmodels import discrete competing risks model
    # OR use R's cmprsk via rpy2

    # For now, return cumulative incidence at time points
    return {
        "method": "Fine-Gray competing risks",
        "cumulative_incidence": cif.cumulative_incidence_.to_dict(),
        "summary": cif.summary.to_dict(),
        # Add SHR after implementing regression
    }
```

**Alternative approach** (more reliable): Use `statsmodels` or implement via cause-specific hazards:

```python
def _fit_fine_gray_cox(df, outcome, exposure, covars, competing_event_col) -> dict:
    """Fine-Gray via cause-specific Cox models."""
    from lifelines import CoxPHFitter

    # Fit cause-specific model for event of interest
    df_eoi = df[df[competing_event_col] != 2].copy()  # Exclude competing events
    df_eoi['event'] = (df_eoi[competing_event_col] == 1).astype(int)

    cph_eoi = CoxPHFitter()
    cph_eoi.fit(df_eoi, duration_col=outcome, event_col='event')

    # Fit cause-specific model for competing event
    df_comp = df[df[competing_event_col] != 1].copy()
    df_comp['event'] = (df_comp[competing_event_col] == 2).astype(int)

    cph_comp = CoxPHFitter()
    cph_comp.fit(df_comp, duration_col=outcome, event_col='event')

    # Return both
    return {
        "method": "Cause-specific Cox (competing risks)",
        "event_of_interest": _extract_cox_results(cph_eoi, exposure),
        "competing_event": _extract_cox_results(cph_comp, exposure),
    }
```

**validation.py updates**:
```python
def _fine_gray_checks(result, df, outcome, event_col) -> dict:
    """Assumption checks for Fine-Gray models."""
    checks = {}

    # Proportionality assumption for subdistribution hazard
    # (requires specialized test, for now document)

    # Check sufficient number of competing events
    n_competing = (df[event_col] == 2).sum()
    n_eoi = (df[event_col] == 1).sum()

    checks["sufficient_competing_events"] = {
        "passed": n_competing >= 10,
        "details": f"n_comp={n_competing}, n_eoi={n_eoi}"
    }

    return checks
```

---

### Task 3: Add Survey Weight Support

**File**: `workflow/skills/statistical-analysis/scripts/regression.py`

**Current State**: No survey weight support. Paper 7 (Medicaid) used survey-weighted analyses.

**Implementation**:

```python
def fit_regression(
    df, outcome, exposure, covariates,
    method: str = "ols",
    cluster_col: Optional[str] = None,
    time_scale: str = "time",
    weights_col: Optional[str] = None,  # NEW
) -> dict:
    """Fit regression with optional survey weights."""
    # ... existing code ...

    if weights_col and weights_col in df.columns:
        weights = df[weights_col].astype(float)
        # Use statsmodels' frequency weights or sampling weights
        if method in ("ols", "linear"):
            result = sm.WLS(y, X, weights=weights[mask]).fit()
        elif method == "logit":
            # For survey-weighted logistic, use sample_weight in sklearn
            # or use statsmodels with frequency weights
            from sklearn.linear_model import LogisticRegression
            lr = LogisticRegression(max_iter=5000)
            lr.fit(X[mask], y[mask], sample_weight=weights[mask])
            # Convert to statsmodels-like result object
            result = _sklearn_to_statsmodels(lr, X[mask], y[mask])
        # ... handle other methods ...
```

**Alternative for complex survey designs**: Use `statsmodels` survey capabilities or `survey` package:

```python
def fit_survey_regression(
    df, outcome, exposure, covariates,
    weights_col: str,
    cluster_col: Optional[str] = None,
    strata_col: Optional[str] = None,
    method: str = "logit",
) -> dict:
    """Fit regression for complex survey data.

    Uses Taylor series linearization for variance estimation.
    """
    import statsmodels.api as sm
    from statsmodels.stats.weightstats import DescrStatsW

    covars = [c for c in covariates if c in df.columns]
    X = pd.get_dummies(df[[exposure] + covars], drop_first=True, dtype=float)
    X = sm.add_constant(X)
    y = df[outcome].astype(float)
    weights = df[weights_col].astype(float)

    mask = X.notna().all(axis=1) & y.notna() & weights.notna()
    X, y, w = X[mask], y[mask], weights[mask]

    # Design-based estimation
    if method == "logit":
        # Use weighted likelihood
        result = sm.Logit(y, X).fit(maxiter=5000, disp=0)
        # Adjust SEs for design effect
        if cluster_col:
            # Cluster-robust SEs
            result = result.get_robustcov_results(cov_type='cluster',
                                                  groups=df[mask][cluster_col])

    return _extract_results(result, method, exposure, X.columns.tolist())
```

**descriptive.py updates** for weighted Table 1:

```python
def generate_table1(
    df, group_col, continuous_vars, categorical_vars,
    weights_col: Optional[str] = None,  # NEW
) -> dict:
    """Generate Table 1 with optional survey weights."""
    if weights_col:
        # Use weighted statistics
        from statsmodels.stats.weightstats import DescrStatsW
        for var in continuous_vars:
            weighted_stats = DescrStatsW(df[var].dropna(),
                                         weights=df[weights_col].dropna())
            mean = weighted_stats.mean
            sd = weighted_stats.std
            # ... weighted tests ...
```

---

### Task 4: Document Variable Schema for Competing Risks

**File**: `workflow/skills/generate-research-questions/SKILL.md`

Add to the variable_roles section:

```markdown
**Competing risks outcomes:**
For survival analyses with competing risks, the outcome variable should be coded as:
- `0` = censored
- `1` = event of interest
- `2` = competing event

Specify the competing event in `outcome_variables` with:
```json
"outcome_variables": ["mortality_event"],
"competing_risks": {
  "outcome_col": "mortality_event",
  "event_of_interest": 1,  // e.g., cardiovascular death
  "competing_event": 2     // e.g., non-cardiovascular death
}
```
```

---

### Task 5: (Optional) Time-Varying Covariates for Cox Models

**Priority**: LOW - None of the 7 papers strictly required this, but it's mentioned in the Cox PH assumption checks.

**Implementation**: Extend `_fit_cox()` to handle time-varying covariates using `lifelines` time-varying format:

```python
def _fit_cox_time_varying(df, outcome, exposure, covars, time_varying_cols=[]) -> dict:
    """Cox PH with time-varying covariates.

    Requires data in long format (multiple rows per subject).
    """
    from lifelines import CoxTimeVaryingFitter

    ctv = CoxTimeVaryingFitter()
    ctv.fit(
        df,
        id_col="subject_id",  # Required for time-varying
        event_col=event_col,
        start_col="start_time",
        stop_col=outcome,  # stop_time
    )
    # ... extract results ...
```

---

## Implementation Order

1. **Task 1: Age-as-time-scale** (30 min) - Highest impact, lowest complexity
2. **Task 4: Documentation** (15 min) - Can be done in parallel with Task 1
3. **Task 2: Fine-Gray** (2 hours) - Medium complexity, high impact
4. **Task 3: Survey weights** (2 hours) - Medium complexity, medium impact
5. **Task 5: Time-varying covariates** (3 hours) - Optional, low priority

**Total estimated time**: ~5 hours for core enhancements (Tasks 1-4)

---

## Validation Plan

After each implementation:

1. **Unit test**: Create synthetic dataset with known ground truth
2. **Compare against published results**: Use one of the 7 papers as reference
3. **Update SKILL.md**: Document new parameters with examples
4. **Update methods.md**: Add implementation guidance and pitfalls

### Example Test for Age-as-Time-Scale:

```python
# Create synthetic data
n = 1000
df = pd.DataFrame({
    "age_entry": np.random.uniform(40, 60, n),
    "age_event": np.random.uniform(50, 80, n),
    "event": np.random.binomial(1, 0.3, n),
    "exposure": np.random.binomial(1, 0.5, n),
    "covariate": np.random.normal(0, 1, n),
})
df["time"] = df["age_event"] - df["age_entry"]

# Standard Cox
result_standard = fit_regression(df, "time", "exposure", ["covariate"], method="cox")

# Age-as-time-scale Cox
result_age = fit_regression(df, "age_event", "exposure", ["covariate"],
                           method="cox", time_scale="age")

# Results should differ (age scale accounts for left-truncation)
```

---

## Files to Create/Modify Summary

| File | Change | Lines Added |
|------|--------|-------------|
| `regression.py` | Add `time_scale`, `weights_col` parameters; implement Fine-Gray | ~150 |
| `validation.py` | Add Fine-Gray assumption checks | ~40 |
| `descriptive.py` | Add weighted statistics option | ~60 |
| `SKILL.md` | Document new parameters and methods | ~80 |
| `methods.md` | Add Fine-Gray, age-time-scale, survey weights sections | ~120 |
| `utils.py` | Helper for weighted calculations | ~30 |

**Total**: ~480 lines of new/modified code
