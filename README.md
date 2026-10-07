# SynthSift

**Reproducible human-in-the-loop screening and structured extraction for environmental evidence synthesis.**

SynthSift is a small research-methods pilot that tests how automated text workflows can support — rather than replace — evidence-synthesis decisions. The demonstration task asks:

> **What drives or limits household/residential adoption, uptake or diffusion of heat pumps?**

The repository focuses on the parts that matter when automation is used in research: a frozen eligibility protocol, auditable reference decisions, source-text provenance, held-out evaluation, false-negative inspection, uncertainty, workload/recall trade-offs, and structured data extraction.

It is intentionally **not** presented as a systematic review or as evidence that the reported model performance will generalise to a real database search.

## What is in the repository

- `protocols/screening_protocol_v1.md` — frozen title/abstract eligibility protocol.
- `data/records/` — 16 provenance-verified pilot records with source URL, screening text and protocol decisions.
- `data/extraction_reference.csv` — structured reference fields for eligible studies.
- `src/synthsift/` — reusable screening and extraction utilities.
- `scripts/run_screening_benchmark.py` — repeated out-of-fold screening evaluation.
- `scripts/run_extraction_benchmark.py` — structured-extraction baseline and field-level evaluation.
- `scripts/evaluate_predictions.py` — model-agnostic evaluator for external/LLM screening scores.
- `docs/llm_prompt_v1.md` — versioned conservative LLM screening prompt; no LLM result is claimed unless an actual run is committed.
- `docs/methodology.md` — design choices and limitations.
- `docs/ai_disclosure.md` — AI-assistance disclosure.
- `tests/` + GitHub Actions — reproducibility checks.

## Data provenance audit

The original prototype contained several AI-rewritten summaries in a column labelled as abstracts. That is unacceptable for an evidence-synthesis benchmark because transformed text can change both screening difficulty and model behaviour.

SynthSift therefore separates provenance explicitly:

- `source_abstract` — author/publisher abstract verified against the linked public source;
- `source_summary` — source-authored summary or executive-summary text when no conventional abstract was available;
- `derived_summary` / `source_mismatch` — unresolved legacy provenance states recorded only in `data/provenance_audit.csv`; transformed screening text is not distributed.

The benchmark dataset therefore contains only the 16 records with verified source-authored screening text. Seven unresolved legacy records remain visible in the audit manifest without their transformed text.

## Reference decisions

The current labels are protocol-based pilot decisions. They are **not dual-independent-human ground truth**. The protocol was tightened before evaluation so that, for example:

- cross-technology heating-choice studies remain eligible when heat-pump choice is analysed directly;
- post-adoption satisfaction alone is not treated as an adoption study;
- engineering optimisation, refrigerant/LCA and industrial/district-heat studies are excluded unless they contain an adoption-decision dimension.

Every exclusion has a reason in the committed record shards.

## Screening benchmark

Two lightweight, locally reproducible baselines are included:

1. word TF-IDF (1–2 grams) + class-balanced logistic regression;
2. character TF-IDF (3–5 grams) + class-balanced logistic regression.

The script uses **repeated stratified out-of-fold predictions**. Each record is held out once per repeat, and its held-out probabilities are averaged across repeats before evaluation. This reduces dependence on one arbitrary split and avoids in-sample scoring.

Run:

```bash
python -m pip install -e .
python scripts/run_screening_benchmark.py
```

Current provenance-clean pilot (`N=16`, 9 include / 7 exclude; 10 repeats):

| Model | Precision | Recall | F1 | False negatives |
|---|---:|---:|---:|---:|
| word TF-IDF + logistic regression | 0.818 | 1.000 | 0.900 | 0 |
| character TF-IDF + logistic regression | 0.900 | 1.000 | 0.947 | 0 |

Both ranking baselines place all nine eligible records within the first nine screened records, corresponding to an **illustrative 43.8% workload reduction at 100% recall on this tiny curated set**.

That number should **not** be interpreted as expected real-world savings. The corpus is deliberately small, prevalence is much higher than in many real systematic searches, and the negatives are not a representative sample of difficult near-misses. `docs/methodology.md` records these limitations explicitly.

## Structured extraction benchmark

For nine eligible records, the repository also stores small reference fields:

- country;
- study design;
- sample size where that quantity is meaningful;
- factor tags describing reported adoption drivers/barriers.

A transparent deterministic extractor provides the first benchmark. It is deliberately simple: the important artifact is the **evaluation harness**, which can later compare rule-based, NLP and LLM extraction outputs against the same reference table.

```bash
python scripts/run_extraction_benchmark.py
```

On the current reference subset, the deterministic baseline exactly matches the available country, study-design and participant/sample-size fields. The corpus is too small for those percentages to be scientifically interesting; the point is to make extraction errors measurable and auditable rather than judge generated outputs impressionistically.

## Evaluating an LLM without coupling the project to an API

SynthSift does not claim an LLM experiment that was never run. Any model can instead produce:

```csv
id,score
R01,0.94
R02,0.81
...
```

and be evaluated through the same harness:

```bash
python scripts/evaluate_predictions.py predictions.csv
```

`docs/llm_prompt_v1.md` contains a conservative JSON screening prompt with an explicit `uncertain` state. A future model run should record provider/model identifier, date, prompt version, decoding settings, raw outputs and any human adjudication.

## Reproducibility

```bash
python -m pip install -e '.[dev]'
pytest -q
python scripts/run_screening_benchmark.py --repeats 10
python scripts/run_extraction_benchmark.py
```

CI runs tests plus reduced-repeat screening and extraction checks on every push and pull request.

## Limitations

This repository is a methodological demonstration, not a completed evidence synthesis. The main limitations are:

- the provenance-clean benchmark contains only 16 records;
- candidate records were curated rather than taken from a documented database-search result set, so class prevalence and screening difficulty are unrealistic;
- reference decisions have not undergone dual independent screening and adjudication;
- bootstrap intervals are descriptive for this fixed pilot sample and do not capture model-development uncertainty;
- no LLM screening/extraction result is reported yet;
- factor-tag extraction is stored as reference data but is not yet scored by the deterministic baseline.

The next meaningful research step is not to chase a higher F1 on these 16 records. It is to run a documented bibliographic search, preserve the full candidate pool, obtain independently screened reference decisions, then compare classical, embedding and LLM-assisted methods under the same recall-first evaluation design.

## AI-assistance disclosure

AI tools were used for code assistance, public-source retrieval, provenance checking and methodological critique. See [`docs/ai_disclosure.md`](docs/ai_disclosure.md). The repository does not describe AI-assisted pilot labels as dual-human ground truth and does not report model experiments that were not actually executed.

## License

MIT for code. Bibliographic/source text remains attributable to the linked original sources and should be used subject to the source's terms.
