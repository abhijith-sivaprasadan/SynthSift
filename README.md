# SynthSift

**Reproducible human-in-the-loop screening and structured extraction for environmental evidence synthesis.**

SynthSift is a research-methods project for evaluating where automation can safely reduce evidence-synthesis workload without obscuring errors, uncertainty or human judgement. The demonstration domain is residential heat-pump adoption.

> **Review question:** What drives or limits household/residential adoption, uptake or diffusion of heat pumps?

The project now has two layers:

1. a small, provenance-audited pilot benchmark used to validate the evaluation machinery; and
2. a fixed **search-derived OpenAlex corpus** for the next, more realistic screening benchmark.

It is intentionally not presented as a completed systematic review.

## v0.2: search-derived candidate corpus

On 7 October 2026, six OpenAlex title/abstract query arms retrieved the top 100 relevance-ranked records for:

- `heat pump adoption`
- `heat pump uptake`
- `heat pump household`
- `heat pump consumer`
- `heat pump willingness`
- `heat pump barrier`

The frozen snapshot contains:

| Stage | Records |
|---|---:|
| Raw retrievals | 600 |
| Exact-deduplicated candidates | **538** |
| With OpenAlex abstract | 330 |
| Title-only | 208 |
| OpenAlex English-language flag | 481 |
| Potential publication/version clusters | 29 clusters / 66 records |

Exact deduplication uses normalized DOI when present and OpenAlex ID otherwise. Different report, preprint, conference and journal records are not silently collapsed: normalized-title clustering flags them for human adjudication.

The search protocol is frozen in [`protocols/search_protocol_v1.md`](protocols/search_protocol_v1.md), the machine-readable configuration is in [`config/search_v1.json`](config/search_v1.json), and the dated snapshot is under [`data/search/openalex_snapshot_2026-10-07/`](data/search/openalex_snapshot_2026-10-07/).

This is a ranked-search **candidate corpus**, not an exhaustive systematic-search strategy.

## Manual screening workflow

The raw search snapshot contains no eligibility labels. Build a screening queue with:

```bash
python -m pip install -e '.[dev]'
python scripts/build_screening_queue.py
```

Then screen against the frozen eligibility protocol:

```bash
python scripts/screen_queue.py --reviewer abhijith
```

The screener supports `include`, `exclude`, `uncertain`, skip and resume. Partial decisions are written under `annotations/` and ignored by Git so unfinished labels cannot leak into the benchmark. See [`docs/screening_workflow.md`](docs/screening_workflow.md).

A second reviewer should independently screen a prespecified subset before model development if the project is used for a stronger human-agreement benchmark.

## Reproducible acquisition

The committed snapshot is fixed because OpenAlex relevance ranking can change as its index changes. The acquisition process itself can be rerun with:

```bash
python scripts/fetch_openalex.py
```

The script preserves DOI, OpenAlex ID, title, publication date/year, work type, language flag, abstract when available, landing-page URL, query-arm provenance and best within-arm rank.

## Pilot benchmark

The original 16-record pilot remains as a provenance-clean methods check. It uses only source-authored screening text after removing transformed summaries from the first prototype.

Current repeated out-of-fold screening results:

| Model | Precision | Recall | F1 |
|---|---:|---:|---:|
| word TF-IDF + logistic regression | 0.818 | 1.000 | 0.900 |
| character TF-IDF + logistic regression | 0.900 | 1.000 | 0.947 |

Both ranked all nine eligible pilot records within the first nine screened records, an illustrative 43.8% workload reduction at 100% recall. These numbers are retained as pipeline checks only and should not be interpreted as real-world performance estimates.

## Structured extraction pilot

For nine eligible pilot studies, SynthSift stores reference fields for:

- country;
- study design;
- sample size where meaningful;
- adoption-driver/barrier factor tags.

A deterministic baseline provides a transparent first extraction benchmark. The important artifact is the evaluation harness: later NLP or LLM extraction outputs can be compared field by field rather than judged impressionistically.

## Evaluating external or LLM screening predictions

SynthSift is model-provider agnostic. A model can produce:

```csv
id,score
R01,0.94
R02,0.81
```

and be evaluated with:

```bash
python scripts/evaluate_predictions.py predictions.csv
```

[`docs/llm_prompt_v1.md`](docs/llm_prompt_v1.md) contains a conservative `include / exclude / uncertain` screening prompt, but the repository does not claim an LLM experiment unless an actual run and its configuration are committed.

## Repository map

- `config/search_v1.json` — machine-readable OpenAlex acquisition configuration.
- `protocols/search_protocol_v1.md` — frozen search protocol.
- `protocols/screening_protocol_v1.md` — frozen eligibility protocol.
- `data/search/openalex_snapshot_2026-10-07/` — 538-record fixed search snapshot.
- `data/records/` — 16-record provenance-clean pilot benchmark.
- `data/extraction_reference.csv` — pilot structured-extraction reference.
- `src/synthsift/` — reusable screening, extraction and OpenAlex helpers.
- `scripts/fetch_openalex.py` — live acquisition pipeline.
- `scripts/build_screening_queue.py` — fixed-snapshot queue builder.
- `scripts/screen_queue.py` — resumable manual title/abstract screener.
- `scripts/run_screening_benchmark.py` — repeated out-of-fold pilot benchmark.
- `scripts/run_extraction_benchmark.py` — structured-extraction pilot.
- `tests/` — unit, provenance and corpus-integrity tests.
- `.github/workflows/ci.yml` — install, compile, tests and benchmark smoke checks.

## Reproducibility

```bash
python -m pip install -e '.[dev]'
pytest -q
python scripts/build_screening_queue.py
python scripts/run_screening_benchmark.py --repeats 10
python scripts/run_extraction_benchmark.py
```

CI runs the full offline integrity path on each push and pull request. The live OpenAlex fetch is deliberately not part of CI because the committed dated snapshot—not a changing external API—is the benchmark input.

## Methodological guardrails

SynthSift keeps several boundaries explicit:

- search acquisition is separate from eligibility decisions;
- unfinished human annotations are separate from frozen reference labels;
- potential publication/version duplicates are flagged, not silently merged;
- title-only records are retained rather than discarded;
- LLM outputs are not called human ground truth;
- no model result is reported unless the underlying run exists;
- workload-reduction figures are always tied to the evaluated corpus and recall level.

## Current limitations

The search-derived corpus still needs reference screening. It is OpenAlex-only and relevance-ranked rather than an exhaustive multi-database systematic search. The current reference labels in the pilot have not undergone dual independent screening and adjudication. No real LLM comparison is reported yet.

Those are now explicit next research steps rather than hidden weaknesses.

## AI-assistance disclosure

AI tools were used for code assistance, public-source retrieval, provenance checking and methodological critique. See [`docs/ai_disclosure.md`](docs/ai_disclosure.md).

## License

MIT for project code. Bibliographic metadata comes from OpenAlex; source-linked publication content remains attributable to its original sources and should be used subject to applicable terms.
