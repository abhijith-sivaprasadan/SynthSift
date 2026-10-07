# Data dictionary

## Pilot benchmark: `data/records/records_*.csv`

The four shards form the 16-record provenance-clean pilot benchmark.

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

## Search-derived corpus: `data/search/openalex_snapshot_2026-10-07/records_*.csv`

The eight shards form a fixed 538-record OpenAlex search snapshot.

| Column | Meaning |
|---|---|
| `candidate_id` | Stable SynthSift identifier for this dated snapshot. |
| `openalex_id` | OpenAlex work identifier. |
| `doi` | Normalized DOI where available. |
| `title` | OpenAlex title. |
| `publication_year` / `publication_date` | OpenAlex publication metadata. |
| `work_type` | OpenAlex work type. |
| `language` | OpenAlex language flag; not an eligibility decision. |
| `abstract` | Abstract reconstructed from OpenAlex's abstract inverted index when available. |
| `abstract_missing` | 1 for title-only records, otherwise 0. |
| `landing_page_url` | Primary OpenAlex landing-page URL. |
| `query_arms` | Search arms that retrieved this work. |
| `best_rank` | Lowest within-arm relevance rank among the retrieving queries. |
| `screening_decision` etc. | Intentionally blank in the raw snapshot to prevent labels leaking into acquisition data. |

## `data/search/openalex_snapshot_2026-10-07/version_clusters.csv`

Normalized-title clusters that flag potential report/preprint/conference/journal versions. These are **not** automatically collapsed. A reviewer must decide whether records are duplicate manifestations of one study.

## `data/provenance_audit.csv`

Records removed from the original 16-record pilot because the original text was derived or the source link was inconsistent. No transformed screening text is distributed.

## `data/extraction_reference.csv`

| Column | Meaning |
|---|---|
| `id` | Links to the pilot screening records. |
| `country` | Study geography represented by the pilot reference. |
| `study_design` | Normalized study-design category. |
| `sample_size` | Participant/sample size when meaningful and visible in screening text. |
| `factor_tags` | Semicolon-separated adoption drivers/barriers used as a future information-extraction target. |
