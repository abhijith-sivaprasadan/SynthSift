# Data dictionary

## `data/records.csv`

| Column | Meaning |
|---|---|
| `id` | Stable pilot record identifier. |
| `title` | Publication/report title. |
| `screening_text` | Text available to the title/abstract screening task. |
| `source_url` | Public source used for provenance checking. |
| `text_provenance` | `source_abstract`, `source_summary`, `derived_summary`, or `source_mismatch`. |
| `publication_year` | Year explicitly identified during source check when available. |
| `doi` | DOI explicitly identified during source check when available. |
| `reference_label` | Protocol decision: 1 include, 0 exclude. |
| `decision_rationale` | Protocol-grounded rationale. |
| `exclude_reason` | Specific exclusion reason for excluded records. |
| `primary_benchmark` | 1 when source-authored screening text was verified and can enter the primary benchmark. |
| `provenance_note` | Audit note about the text/source. |

## `data/extraction_reference.csv`

| Column | Meaning |
|---|---|
| `id` | Links to `records.csv`. |
| `country` | Study geography represented by the pilot reference. |
| `study_design` | Normalized study-design category. |
| `sample_size` | Participant/sample size when meaningful and visible in screening text. |
| `factor_tags` | Semicolon-separated adoption drivers/barriers used as a future information-extraction target. |
