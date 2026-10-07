# Pilot results

Generated from the provenance-clean subset on 7 October 2026.

## Screening

Primary benchmark: **16 records (9 include / 7 exclude)** with source-authored abstract or summary text verified against the linked public source.

| Model | Precision | Recall | F1 | Confusion matrix `[[TN,FP],[FN,TP]]` |
|---|---:|---:|---:|---|
| word TF-IDF + logistic regression | 0.818 | 1.000 | 0.900 | `[[5,2],[0,9]]` |
| character TF-IDF + logistic regression | 0.900 | 1.000 | 0.947 | `[[6,1],[0,9]]` |

Both model rankings reached all 9 included records after screening 9 of 16 records, an illustrative workload reduction of **43.8% at 100% recall**.

### Bootstrap intervals

Conditional non-parametric bootstrap intervals on the fixed out-of-fold predictions:

- word TF-IDF: precision 0.556–1.000; recall 1.000–1.000; F1 0.714–1.000;
- character TF-IDF: precision 0.667–1.000; recall 1.000–1.000; F1 0.800–1.000.

These intervals should not be read as evidence of production performance. With only 16 records, resampling a set with zero observed false negatives necessarily produces an uninformative recall interval. They also do not include uncertainty from data collection, label adjudication, model choice or hyperparameter selection.

## Structured extraction

Reference rows: 9 eligible records.

The deterministic baseline exactly matched all currently scored reference fields:

- country: 9/9;
- study design: 9/9;
- sample size: 4/4 records where a participant/sample-size field is meaningful and available in the screening text.

This is a pipeline sanity check, not a claim of general extraction accuracy. The rules were developed on the pilot records and require evaluation on a larger held-out corpus before any performance interpretation.

## What changed after the provenance audit

The first prototype was not suitable for a research-facing portfolio because some fields described as abstracts were AI-rewritten summaries. The revised benchmark distributes only provenance-verified source-authored screening text. Seven unresolved legacy records remain listed in a provenance-audit manifest without their transformed text. One inconsistent inclusion decision (a post-adoption user-satisfaction report) was also corrected under the frozen protocol, while a heating-choice study that directly analyses heat-pump ownership remains eligible.
