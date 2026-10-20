# Full-corpus OpenAlex AI screening — v1

**Date:** 20 October 2026  
**Scope:** 538 frozen bibliographic *candidate records* retrieved using six relevance-ranked OpenAlex query arms on 7 October 2026.  
**Protocol:** [Screening v1.0](../../protocols/screening_protocol_v1.md) (frozen before the AI pass)  
**Study question:** What drives or limits household/residential adoption, uptake or diffusion of heat pumps?

This document describes an **AI-assisted title/available-abstract first-pass triage**, not an independently screened systematic review. Full-text study retrieval and human adjudication have not happened. Some abstracts were screened from excerpts; selected borderline records were reconsidered against their complete available abstract. A source record having an abstract does not mean a full-text publication was reviewed.

## Full candidate corpus status

| AI-recommended disposition | Candidate records |
|---|---:|
| Include for follow-up | 144 |
| Exclude at title/available-abstract stage | 341 |
| Uncertain; retain for manual clarification | 53 |
| **Total accounted for** | **538** |

The first 240 recommendations and original reviewer strings were **preserved verbatim** from [the original Phase-1 AI ledger](phase1_ai_assisted_v1.csv). The remaining 298 were screened in [six explicitly machine-attributed batches](full_corpus_batch_01.csv), `full_corpus_batch_01.csv` through `full_corpus_batch_06.csv`. The [complete 538-record ledger](full_corpus_ai_assisted_v1.csv) combines the two sets, adding OpenAlex URL/DOI, protocol-grounded decision reason, original title, abstract-availability flag and provenance. All 538 frozen candidate IDs appear exactly once.

Among these 538 source records, 330 have an OpenAlex abstract and 208 are title-only. These numbers refer to acquired records, not independent publications, and should **not** be interpreted as eligible-study prevalence. The original 29 normalized-title potential-version clusters cover 66 records. They remain separate candidates pending human study-level deduplication; the 144 AI includes may include multiple bibliographic versions of the same study.

## Review-priority list — 150 distinct records

The [priority table](full_corpus_review_priority_v1.csv) is the **union** of three overlapping flags:

- 53 `uncertain` AI decisions;
- 66 records flagged as potential versions within normalized-title clusters;
- 51 title-only records provisionally marked `include`, for which no abstract supported the interpretation.

This yields 150 **unique candidate records**, not 53 + 66 + 51 independent cases. Priorities are for later reviewer attention only; they are not independent adjudication. Records with clear machine `exclude` recommendations must still undergo a justified human audit before using the ledger to benchmark false negatives.

## Inclusion and exclusion judgments

- Include when source title/abstract identifies financial, behavioural, social, market, policy, building, installation/workforce or infrastructure determinants of residential heat-pump adoption; distinguish heat-pump choice in cross-technology studies.
- Exclude where the substantive work is thermodynamic performance, experimental refrigerants/materials, non-residential industrial/district heating, grid load consequences conditional on uptake, or operation/comfort/flexibility *after* installation without adoption determinants.
- Return uncertain when a title-only record or broad technology review does not establish whether distinct residential heat-pump adoption factors were studied. Do not silently turn missing abstracts into excludes.

The screening protocol itself was **not** rewritten to accommodate any result. Decisions are explicitly attributed to `ai_assistant_gpt6_20261020` (original 240) or `ai_assistant_gpt6_20261020_full_corpus` (298 added records).

## Reproduction and integrity

```bash
python -m pip install -e '.[dev]'
python scripts/audit_full_corpus_ai_screening.py --check
python -m pytest -q tests/test_full_corpus_ai_screening.py
```

These commands reconstruct the ledger and priority flags from eight original dated OpenAlex CSV shards, the old 240 ledger, the six added AI batches, the preserved Phase-1 sample and version-cluster manifest. They fail on missing/duplicated IDs, changed decision sources, missing individual reasons, reviewer impersonation or mismatched published CSV/JSON.

Run `python scripts/audit_full_corpus_ai_screening.py --out results/full_corpus_ai` to regenerate working copies in a local ignored results folder.

## What has NOT been completed

1. This is **not** a systematic-search strategy, an independent human eligibility assessment, or full-text inclusion/exclusion of 538 studies. OpenAlex title/abstract relevance ranking and version duplication limit representativeness.
2. The existing 240-record human reference plan and blinded independent 96-record second review are **still uncompleted**. The AI decision ledger is **not** copied into `annotations/` or `data/labels/`, nor passed off as human review.
3. No investigator independently adjudicated the 53 uncertain items, the 66 potentially duplicate bibliographic records, or false negatives among the 341 proposed exclusions.
4. **No model precision, recall, human inter-rater kappa, or automated workload-reduction claims** can be derived by scoring AI predictions against their own AI recommendations.
5. There is **no thematic synthesis, risk-of-bias evaluation or verified paper-level metadata extraction** for the whole corpus.

**Appropriate claim for external use:** “Implemented and released a source-linked, reproducible AI-assisted first-pass screening workflow covering 538 OpenAlex candidate records, with explicit protocol decisions, conservative uncertainty handling, version-duplicate flags and integrity tests. Independent human reference review remains outstanding.”
