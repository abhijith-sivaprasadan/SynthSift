# Manual screening workflow

The v0.2 acquisition snapshot deliberately contains **no reference labels**. That separation prevents search/acquisition code from leaking labels into later model experiments.

## 1. Build the queue

```bash
python scripts/build_screening_queue.py
```

The command produces `results/openalex_screening_queue.csv` from the committed OpenAlex snapshot and attaches any potential publication/version cluster ID.

## 2. Screen against the frozen protocol

Read `protocols/screening_protocol_v1.md`, then run:

```bash
python scripts/screen_queue.py --reviewer abhijith
```

For every candidate, choose:

- `include` — clearly meets the protocol;
- `exclude` — clearly fails the protocol;
- `uncertain` — title/abstract information is insufficient;
- skip — defer without recording a decision.

Give a brief protocol-grounded reason. The tool saves after every decision and resumes automatically from `annotations/screening_decisions.csv`.

## 3. Handle version clusters

When a record has a `version_cluster_id`, inspect the other cluster members before final analysis. Do not automatically delete them merely because their normalized titles match; they may represent report, preprint, conference and journal versions.

## 4. Second-review subset

For stronger reference data, have a second reviewer independently screen a prespecified random subset before seeing reviewer 1's decisions. A useful portfolio target is at least 75–100 records. Agreement and adjudication should then be recorded separately rather than overwriting either reviewer's original decisions.

## 5. Freeze labels before model benchmarking

Do not tune an LLM prompt, classifier threshold or embedding model against records whose reference decision is still being changed. Once the first reference set is frozen, tag/version it and evaluate every method against the same decisions.
