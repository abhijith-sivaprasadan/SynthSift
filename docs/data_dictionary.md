# Data dictionary

## `data/records/records_*.csv`

The four shards form one 16-record provenance-clean benchmark.

| Column | Meaning |
|---|---|
| `id` | Stable pilot record identifier. |
| `title` | Publication/report title. |
| `screening_text` | Verified source-authored abstract or source summary used for screening. |
| `source_url` | Public source used for provenance checking. |
| `text_provenance` | `source_abstract` or `source_summary`. |
| `publication_year` | Year explicitly identified during source check when available. |
| `doi` | DOI explicitly identified during source check when available. |
| `reference_label` | Protocol decision: 1 include, 0 exclude. |
| `decision_rationale` | Protocol-grounded rationale. |
| `exclude_reason` | Specific exclusion reason for excluded records. |
| `provenance_note` | Audit note about the text/source. |

## `data/provenance_audit.csv`

Records removed from the benchmark because the original pilot text was derived or the source link was inconsistent. No transformed screening text is distributed.

## `data/extraction_reference.csv`

| Column | Meaning |
|---|---|
| `id` | Links to the screening records. |
| `country` | Study geography represented by the pilot reference. |
| `study_design` | Normalized study-design category. |
| `sample_size` | Participant/sample size when meaningful and visible in screening text. |
| `factor_tags` | Semicolon-separated adoption drivers/barriers used as a future information-extraction target. |
