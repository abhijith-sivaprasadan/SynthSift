# Empirical validation pilot — 80 citations / 32 dual reviews

**Protocol status:** prespecified selection code; no measured LLM accuracy or independent human labels have yet been generated. This pilot is a *subset of the frozen 240-source sample*, not a replacement for the full 240/96 benchmark.

## Frozen, source-only selection

Run from the repository root in Windows PowerShell:

```powershell
python -m pip install -e '.[dev]'
python scripts/create_validation_pilot.py
python scripts/create_validation_pilot.py --check
```

This creates `data/samples/validation_pilot_80_v1.csv` and an adjacent manifest. The generator selects **48 originally single-review + 32 originally dual-review records** from the frozen 240, with proportional allocation within the existing sampling strata and a prespecified SHA-256 seeded rank. It cannot use model predictions or human decisions and refuses to overwrite a differing sample. Commit or archive the CSV + manifest before starting reference review or inspecting any new model outputs; the generator's selection rules are versioned in Git.

## Independent human screening

Recruit human reviewers who have not read the AI-assisted verdicts for these records. Existing 538 AI recommendations and any prior screening assistant output **cannot** be used for adjudication or gold truth. A reviewer who already read AI decisions should not claim blinding.

Give reviewer A the frozen eligibility protocol and the citation-only queue. Give reviewer B the same citation text for the flagged 32 records, without revealing reviewer A's votes.

```powershell
python scripts/screen_queue.py --queue data/samples/validation_pilot_80_v1.csv --decisions annotations/pilot80_reviews.csv --reviewer reviewer_a
python scripts/screen_queue.py --queue data/samples/validation_pilot_80_v1.csv --decisions annotations/pilot80_reviews.csv --reviewer reviewer_b --second-review-only
python scripts/screening_status.py --sample data/samples/validation_pilot_80_v1.csv --decisions annotations/pilot80_reviews.csv --disagreements results/pilot80_disagreements.csv
```

Each reviewer must record a reason for include, exclude or uncertain. Resolve all disagreements and uncertain annotations independently of model predictions into a binary final decision (`include`/`exclude`). Record actual adjudicator and source-grounded rationale. Format `annotations/pilot80_adjudicated.csv` with the columns `candidate_id,final_decision,adjudication_reason` (only entries requiring adjudication are needed). Full-text unknowns should not be assigned unsupported binary answers; resolve via further independent source review and explicitly mark that this is a different evaluation basis, or exclude those records from the binary endpoint in a separately specified study. The present fail-closed evaluator needs all pilot records resolved.

After all votes are complete, only a human genuinely able to make the blindness attestation should run:

```powershell
python scripts/freeze_independent_reference.py --sample data/samples/validation_pilot_80_v1.csv --decisions annotations/pilot80_reviews.csv --adjudicated annotations/pilot80_adjudicated.csv --out data/labels/pilot80_independent_v1.csv --attestor 'HUMAN REVIEW ATTESTOR' --attest-blind-human-review
```

If no disagreements and no uncertain votes occurred, omit `--adjudicated`. Never forge a reviewer identity or mark AI-assisted labels as human.

## Live, billable LLM predictions

The existing engine requires an external **OpenAI API key**, with API usage billed separately from a ChatGPT subscription. Select a model supporting Chat Completions structured `json_schema` responses and temperature 0. Test on a small real subset at your own cost before submitting 80 calls. To enter an API key in PowerShell without putting it in command history:

```powershell
$secret = Read-Host 'OpenAI API key' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
python scripts/run_llm_screening.py --provider openai --model gpt-4o-mini --input data/samples/validation_pilot_80_v1.csv --out results/pilot80_live_v1
```

Replace the example model ID if the API no longer supports it. The live run requires account billing to be set up. Do not upload your API key or checked-in raw review files. To resume the same model/prompt/input configuration:

```powershell
python scripts/run_llm_screening.py --provider openai --model gpt-4o-mini --input data/samples/validation_pilot_80_v1.csv --out results/pilot80_live_v1 --resume
```

## Independently score

```powershell
python scripts/evaluate_llm_benchmark.py --sample data/samples/validation_pilot_80_v1.csv --reference data/labels/pilot80_independent_v1.csv --ledger results/pilot80_live_v1/screening.jsonl --out results/pilot80_independent_evaluation.json
```

Inspect `results/pilot80_independent_evaluation.json`: `overall` TP/FP/TN/FN, `false_exclusion_ids`, `model_abstention_ids`, model errors and title-only/abstract strata. **Do not interpret selective model recall as full-coverage recall**; for a human-in-the-loop policy, the key metrics are number of eligible records *automatically excluded*, eligible retention after escalating all other items to human reviewers, and what fraction of records were potentially auto-excluded. That last fraction is not measured reviewer time saved.

Publish a short results paragraph with sample size, gold-label protocol, number of included citations, model/temperature/date, citation types, abstentions/error count, observed false exclusions and Wilson intervals, plus notable failure examples. Even a zero-false-exclusion pilot does not establish deployment safety; the small relevance-ranked OpenAlex sample may contain duplicate study versions and the findings are title/abstract-level only.

## After the pilot

Complete the original **240/96** study with independent reviewers using the existing `docs/independent_evaluation_mvp.md` workflow. Never silently promote preliminary pilot estimates to a validated full-corpus result. Source-grounded extraction (MVP Step 3) remains a distinct evaluation question.
