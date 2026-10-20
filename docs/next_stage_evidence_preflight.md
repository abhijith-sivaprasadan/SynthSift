# Post-screening study-level evidence preflight — 20 October 2026

The initial AI-assisted title/abstract pass was completed for **538 frozen OpenAlex records**. This work prepares the next research stage without falsely claiming independent human review, confirmed bibliographic deduplication or full-text screening.

## What is now prepared and reproducible

| Audit / output | Count | Evidence level |
|---|---:|---|
| [Bibliographic/source locator inventory](../data/review_preparation/source_inventory.csv) | 538 | Frozen record identifiers and DOI/landing URLs only — external document availability not automatically verified |
| [Potential publication-version families](../data/review_preparation/version_family_review.csv) | 29 clusters, covering 66 records | Title-normalised candidate groups, **not** deduplicated or independently adjudicated studies |
| [Provisional full-text/extraction preparation queue](../data/review_preparation/provisional_evidence_extraction_queue.csv) | 197 | Union of 144 AI-includes and 53 AI-uncertain records; **no full-text eligibility or effects extracted** |
| [Title-only source follow-up candidates](../data/review_preparation/source_inventory.csv) | 87 | 51 AI-includes and 36 AI-uncertain records lacking a frozen abstract |
| [Excluded-record false-negative audit queue](../data/review_preparation/excluded_record_audit_queue.csv) | 341 | All provisional machine exclusions, none counted as independently audited |
| [High-cue exclusion recheck](../data/review_preparation/targeted_exclusion_recheck_20261020.csv) | 8 | Explicit separate AI second pass using supplied abstract evidence and two externally checked publisher abstracts |

The eight records with both adoption-related and household-related words in the *excluded* title were inspected. **OA0443 requires a change in the next provisional AI screening version**: the 2020 paper *The stranger in the German energy system? How energy system requirements misalign with household preferences for flexible heat pumps* was originally excluded from title-only evidence, but the publisher abstract reports a survey of **985 potential flexible-heat-pump adopters** and tests market shares/consumer preferences. This fits the frozen protocol's household adoption determinant criterion. [Publisher abstract](https://www.sciencedirect.com/science/article/abs/pii/S2214629620301791). We logged a **separate AI second-pass recommendation of `include`**, rather than altering the historical 538-record v1 ledger or misrepresenting this as human adjudication.

The other seven high-cue records retain their first AI recommendations; those with title-only sources still warrant independent source confirmation. This audit is *targeted*, not a statistically valid false-negative sample of all 341 exclusions. Do not infer the overall screening false-negative rate from it.

### Potential version-family problem (VC006)

Of the 29 frozen normalised-title families, **28 have uniform provisional AI recommendations and one does not**. VC006 contains OA0293 (AI `include`) and OA0356/OA0416 (AI `uncertain`); these are bibliographic versions of a German household heating choice paper, but study identity and final inclusion remain to be independently adjudicated. The generator retains **all** candidate IDs and leaves the canonical ID intentionally blank.

## Reproduce the offline audit

```bash
python -m pip install -e '.[dev]'
python scripts/prepare_review_evidence.py --check
python -m pytest -q tests/test_review_preparation.py tests/test_source_refresh.py
```

To produce a separate **source-only, model-output-free** set of reviewer files without contaminating human reference labels:

```bash
python scripts/prepare_review_evidence.py --out results/reviewer_pack --export-blind
```

The two unlabelled files then contain the prespecified 240 first-review records and 96 second-review records. The original programme requires two genuinely independent human reviewers. No ChatGPT/AI pass counts as either human reviewer, even if it examines the same record twice.

For title-only source-location follow-up, an **optional** OpenAlex API metadata check is implemented:

```bash
python scripts/refresh_title_only_sources.py --allow-live --limit 87 --out results/openalex_title_only_metadata_20261020.csv
```

It does not copy abstracts, fetch articles, follow or test publisher PDF links, or reclassify studies. The metadata flag `has_abstract_now=yes` means only that a current OpenAlex inverted-index abstract is available. Any API failures must be reported, not misinterpreted as missing abstracts or inaccessible articles. Source documentation: [OpenAlex API authentication](https://help.openalex.org/api/authentication/) and [Works endpoint reference](https://help.openalex.org/api/endpoints/).

## Next research work still required

1. **Independent human title/abstract reference screening and 96-record blind second review**. Current machine first-pass coverage is not ground truth.
2. **Study-level bibliographic/version adjudication**, including the 29 potential title clusters and all 66 candidate records they cover. Do not simply collapse versions by title.
3. **Independent false-negative audit of machine exclusions**. Start with the eight conspicuous title-cue cases and a separately prespecified random sample; one candidate issue (OA0443) is already documented.
4. **Source/full-text retrieval for provisional inclusions and uncertainties**, then eligibility adjudication and independent extraction.
5. **Reference-grounded ML benchmarking** only once the previous steps support defensible labels. Do not calculate precision/recall against an AI's own recommendations.

**Accurate external summary:** “Prepared reproducible study-level bibliographic review packs for the 538-candidate heat-pump adoption corpus, flagged 29 possible version families and 87 title-only source gaps, and identified a likely false-negative screening case through a targeted publisher-abstract recheck. Human confirmation and full-text research remain outstanding.”
