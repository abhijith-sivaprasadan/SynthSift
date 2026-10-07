# Human screening workflow

The v0.2 acquisition snapshot deliberately contains **no reference labels**. Human decisions are kept separate from acquisition and model outputs so that later evaluation remains interpretable.

## Phase 1 — 240-record reference sample

The committed Phase-1 sample contains **240 records** selected from the 538-record OpenAlex snapshot without using any classifier or LLM prediction.

Sampling is proportional across:

- abstract available vs. title-only;
- OpenAlex best-rank bands 1–20, 21–50 and 51–100.

Selection within each stratum is deterministic using a fixed hash seed, so the exact sample is reproducible across machines.

The committed sample is:

`data/samples/phase1_screening_sample_240.csv`

Rebuild it with:

```bash
python scripts/create_screening_samples.py
```

## Reviewer 1

Read `protocols/screening_protocol_v1.md`, then run:

```bash
python scripts/screen_queue.py --reviewer abhijith
```

The default queue is the 240-record Phase-1 sample.

For every candidate, choose:

- `include` — clearly meets the frozen protocol;
- `exclude` — clearly fails the protocol;
- `uncertain` — title/abstract information is insufficient;
- skip — defer without recording a decision.

Give a brief protocol-grounded reason. The tool saves after every decision and resumes automatically.

In-progress decisions are written to:

`annotations/screening_decisions.csv`

That file is ignored by Git until a reference version is deliberately frozen.

## Independent second review — 96 records

A prespecified **96-record subset** is embedded in the Phase-1 sample. It was selected using the same non-model stratification principle.

A second reviewer runs:

```bash
python scripts/screen_queue.py --reviewer reviewer2 --second-review-only
```

The terminal interface never displays reviewer 1's decisions, preserving independent review.

## Progress and agreement

At any time:

```bash
python scripts/screening_status.py
```

With one reviewer, it reports completion and include/exclude/uncertain counts. Once two reviewers overlap, it additionally reports:

- raw agreement;
- Cohen's kappa;
- disagreement count;
- a CSV of records requiring adjudication.

## Adjudication

Do not overwrite either reviewer's original decision.

Resolve disagreements in a separate adjudication table with:

```text
candidate_id,final_decision,adjudication_reason
```

Uncertain records should also be resolved before a binary model benchmark unless the benchmark explicitly models an uncertain class.

## Freeze the reference set

Only after Phase 1 is complete:

```bash
python scripts/freeze_reference_labels.py --version v1
```

If dual-review disagreements require adjudication:

```bash
python scripts/freeze_reference_labels.py \
  --adjudicated annotations/adjudicated.csv \
  --version v1
```

The frozen label file is written under `data/labels/`. That version—not the mutable annotation workspace—should be used for model development and evaluation.

## Why this separation matters

Model predictions must not influence the human reference decisions they are later evaluated against. The Phase-1 sample therefore contains no ML/LLM score, predicted label or active-learning priority. Acquisition, human screening, adjudication and model evaluation remain separate stages.
