# Reference: Load and Profile

## Table of Contents

1. [Variable Type Rules](#variable-type-rules)
2. [Data Context Structure](#data-context-structure)

---

## Variable Type Rules

When fixing misclassified variable types in `variable_types.json`:

### Common Reclassifications

| Detected As | Should Be | Example |
|-------------|-----------|---------|
| `numeric` | `categorical` or `identifier` | Zip codes, FIPS codes, phone numbers |
| `numeric` | `datetime` | Date strings that failed parsing |
| `numeric` | `binary` | Yes/No encoded as 0/1 |
| `text` | `categorical` | Short categorical codes |

### Type Definitions

- `numeric` — Continuous numeric data (measurements, counts)
- `categorical` — Finite set of categories (not ordered)
- `binary` — Two categories (yes/no, 0/1)
- `ordinal` — Ordered categories (low/medium/high)
- `datetime` — Dates or timestamps
- `text` — Long-form text (notes, descriptions)
- `identifier` — IDs, keys, codes (not used for analysis)

### Data Quality Flags

Flag and document:
- Columns with >50% missing values
- Unexpected value ranges
- Datasets that may need filtering (e.g., metadata rows)

---

## Data Context Structure

Add a `data_context` field to the top level of `profile.json`:

```json
{
  "data_context": {
    "summary": "Brief description of what this data collection is about",
    "dataset_relationships": "How the datasets relate to each other (e.g., linkable by state, joinable on date)",
    "research_directions": ["Potential research question 1", "Potential research question 2"],
    "data_quality_notes": ["Any issues found: missing data patterns, suspicious values, etc."]
  },
  "datasets": { ... }
}
```

### Summary

Provide a concise 1-2 sentence description of what data collection represents.

### Dataset Relationships

Explain how multiple datasets relate:
- Linkable by common key (state FIPS, patient ID)
- Temporal relationship (same time period, different years)
- Hierarchical (individual vs. aggregate)

### Research Directions

List 2-3 potential research questions the data could support, based on your understanding of the variables and their relationships.

### Data Quality Notes

Document any issues found:
- Missing data patterns
- Suspicious or outlier values
- Encoding issues
- Structural problems (metadata rows, multi-header tables)
