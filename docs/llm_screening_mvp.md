# Reproducible LLM screening engine — MVP step 1

**Purpose.** Turn an input CSV of citation titles and source abstracts into versioned machine screening recommendations. This module is **not** a systematic review, human reviewer, or validated screening model. It is independent of the historic 538-record AI suggestion ledger.

## Clean offline demonstration (no API key, no API charges)

```bash
python -m pip install -e '.[dev]'
python scripts/run_llm_screening.py --provider fixture --out results/llm_demo
python scripts/run_llm_screening.py --provider fixture --out results/llm_demo --resume
python scripts/run_llm_screening.py --provider replay --model synthetic-fixture-v1 --cache results/llm_demo/screening.jsonl --out results/replayed_demo
pytest -q tests/test_llm_runner.py
```

The demo uses **five entirely synthetic, hand-authored citations and canned, hand-authored responses**, not actual model inference and not independent reference labels. It intentionally includes an ambiguous title and an abstention. The structured schema, hashing, output, retry logic and code paths are exercised; this demo cannot estimate classification accuracy. CI does not send documents to an external API.

Expected fixture outcome: **five successful outputs**; two provisional `include`, two `exclude`, one `uncertain` with `abstain=true`. The event contents are not scientific research findings.

## Live model calls (explicit opt-in; billable)

```bash
# In your local shell; DO NOT commit or print the API key
export OPENAI_API_KEY='...'
python scripts/run_llm_screening.py \
  --provider openai --model gpt-4o-mini \
  --input data/llm_demo/citations_v1.csv \
  --out results/llm_live_demo
```

On Windows PowerShell, use `$env:OPENAI_API_KEY='...'` to set the key. The model ID is configurable, and the selected model must support Chat Completions structured `json_schema` responses and the requested `temperature` (some reasoning-model settings do not). No API key is required for fixture or replay. **A real live-model run has not been executed or recorded by this project.** Replacing a synthetic demo citation with a real source-authored CSV produces new prompt/input hashes and distinct outputs.

To retry interrupted/failed live calls without re-sending successfully completed records:

```bash
python scripts/run_llm_screening.py --provider openai --model gpt-4o-mini \
  --input data/llm_demo/citations_v1.csv --out results/llm_live_demo --resume
```

To replay a previously successful real run, without API access:

```bash
python scripts/run_llm_screening.py --provider replay --model gpt-4o-mini \
  --input data/llm_demo/citations_v1.csv \
  --cache results/llm_live_demo/screening.jsonl --out results/replayed_live
```

Replay must match the exact input ID/title/abstract, prompt files, schema, model and temperature; otherwise the stored response is rejected. **Replay reconstructs a recorded inference; it is not an independent repeat inference or proof of deterministic LLM behaviour.** `temperature=0` reduces randomness where supported but is not a guarantee of equal outputs across live API invocations.

## Output contract

- `run_config.json`: model, temperature, prompt/schema SHA-256, prompt version and whole-input manifest hash.
- `entries/<candidate_id>.json`: atomic per-citation checkpoint, original input SHA-256, request SHA-256, API/fixture/replay provenance, output/status/errors. No keys are persisted.
- `screening.jsonl`: one complete normalized JSON row per submitted record, in deterministic input order.
- `review_queue.csv`: abstentions and failed inference records for human attention.
- `summary.json`: totals by provisional AI decision and counts of processing errors and abstentions; fields state that no historic 538 AI decision or human reference label was used.

Prompt: [`docs/llm_screening_system_v1.txt`](llm_screening_system_v1.txt). Frozen underlying protocol: [`protocols/screening_protocol_v1.md`](../protocols/screening_protocol_v1.md). Config: [`config/llm_screening_v1.json`](../config/llm_screening_v1.json). All changes to their content change the request fingerprint. Only title and abstract are included in provider prompts; extra input CSV columns, including reference labels, are excluded by design.

### Fail-closed and integrity rules

Decisions are one of `include`, `exclude`, `uncertain`. Each successful result records `reason_category`, explanatory `reason`, a *literal citation evidence_span* (required for include/exclude), and boolean `abstain`. `uncertain` must set `abstain=true` and `reason_category=insufficient_evidence`. A network timeout/429/5xx retries with bounded exponential backoff; schema errors, refusals, malformed JSON, invalid evidence spans or missing fixtures produce an explicit **error** checkpoint, not a fabricated exclusion. CLI exits nonzero if any processing errors remain. Inference failure is never counted as an eligible or ineligible study.

The output directory is protected by a whole-input manifest fingerprint and refuses a different configuration. `--resume` uses only successful exact-request matches. Raw API responses are not published by default. The CI fixtures are independent hand-authored examples, deliberately distinct from any original paper-level `reference_label` or the earlier 538 AI suggestion files.

**Next MVP stage (#2):** a genuinely independent labelled evaluation set. This engine does not currently provide independent precision, recall, workload reduction, calibration, fairness or deployment-reliability estimates.
