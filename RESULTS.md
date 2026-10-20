# Results and corpus status

## v0.2 search-derived corpus — 7 October 2026

A frozen OpenAlex acquisition using six title/abstract search arms produced:

- **600 raw retrieved records**;
- **538 exact-deduplicated candidate records**;
- **330 records with abstracts**;
- **208 title-only records**;
- **481 records carrying OpenAlex's English-language flag**;
- **29 normalized-title version clusters covering 66 records**.

Exact deduplication uses DOI where present and OpenAlex ID otherwise. Potential publication/version duplicates are only flagged, not silently merged. Eligibility labels are deliberately absent from the acquisition snapshot; manual screening against `screening_protocol_v1.md` is the next reference-data step.

This corpus is a ranked-search pilot, not an exhaustive systematic-review search.

## Phase-1 AI-assisted triage — 20 October 2026

All 240 records of the prespecified Phase-1 sample have a model-assisted `include` (55), `exclude` (158) or `uncertain` (27) recommendation with a written protocol-grounded reason. This sample contains 93 title-only records and 147 with source abstract text. Review used title/abstract excerpts and full abstracts for selected ambiguous cases; it is **not** an independent human eligibility reference. No study inclusion, model sensitivity/specificity, reviewer agreement or full-corpus prevalence inference is made from these recommendations. See [AI screening methods and limits](data/ai_screening/README.md).

The 96 blinded second-review records remain reserved for independent human assessment; the remaining 298 of the 538 OpenAlex candidates were not part of this Phase-1 AI review.

## v0.1 provenance-clean pilot screening

Primary benchmark: **16 records (9 include / 7 exclude)** with source-authored abstract or summary text verified against the linked public source.

| Model | Precision | Recall | F1 | Confusion matrix `[[TN,FP],[FN,TP]]` |
|---|---:|---:|---:|---|
| word TF-IDF + logistic regression | 0.818 | 1.000 | 0.900 | `[[5,2],[0,9]]` |
| character TF-IDF + logistic regression | 0.900 | 1.000 | 0.947 | `[[6,1],[0,9]]` |

Both model rankings reached all 9 included records after screening 9 of 16 records, an illustrative workload reduction of **43.8% at 100% recall**.

These figures are retained only as a pipeline demonstration. They should not be used as real-world performance estimates.

## Structured extraction pilot

Reference rows: 9 eligible pilot records.

The deterministic baseline exactly matched all currently scored reference fields:

- country: 9/9;
- study design: 9/9;
- sample size: 4/4 records where a participant/sample-size field is meaningful and available in the screening text.

Again, this is a pipeline sanity check rather than a general extraction-accuracy claim.
