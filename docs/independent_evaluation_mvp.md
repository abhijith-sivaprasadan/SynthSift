# SynthSift MVP Step 2 — independent evaluation

**Status (20 October 2026): evaluation code implemented, but the empirical benchmark has NOT yet been performed.** The frozen 240/96 human reference is incomplete, and no live-model predictions on that set are recorded. Offline tests use synthetic data and are not evidence of model accuracy.

## Protocol and preregistration

Evaluate the frozen 240-citation search-derived sample using the unchanged residential heat-pump adoption protocol. The 96 records selected for second review need two different human reviewers. Reviewers see only source title/abstract, not existing AI predictions; unresolved disagreements or human uncertain calls need reasoned adjudication. Prior 538 AI-assisted recommendations must NEVER become human reference labels. The sample includes possible version duplicates and is not a representative comprehensive systematic search.

## Step A — complete source-only blinded human screening

```bash
python -m pip install -e '.[dev]'
python scripts/screen_queue.py --reviewer human_reviewer_1
python scripts/screen_queue.py --reviewer human_reviewer_2 --second-review-only
python scripts/screening_status.py
```

Human annotations remain in ignored annotations/screening_decisions.csv. Resolve conflicts or uncertain votes in annotations/adjudicated.csv with candidate_id,final_decision,adjudication_reason. Final labels must be include/exclude; retain original reviewer votes. If you previously saw AI judgments for these exact citations, do not falsely claim AI-blind reviewing: recruit unexposed reviewers or select a new independent evaluation set.

Once the full human sample and second reviews are complete, have the responsible human attest (only if accurate):

```bash
python scripts/freeze_independent_reference.py --adjudicated annotations/adjudicated.csv --attestor 'Human reviewer name' --attest-blind-human-review
```

The freeze validates reviewer completeness, second-review coverage and adjudication, then writes a versioned reference CSV plus a SHA-256-bound manifest. It refuses to overwrite a reference. The manifest captures a human attestation: software alone cannot verify that a reviewer was independent.

## Step B — execute real, consented model inference

```bash
# Set OPENAI_API_KEY through your shell environment, never commit it.
python scripts/run_llm_screening.py --provider openai --model gpt-4o-mini --input data/samples/phase1_screening_sample_240.csv --out results/live_phase1_v1
```

The model ID is an example, not a claim that this model was evaluated. A real external call is billable, and has not been executed here. Run configuration and original decisions are preserved by the existing engine. Reuse --resume for an interrupted exact-request run.

## Step C — evaluate against the independently frozen reference

```bash
python scripts/evaluate_llm_benchmark.py --ledger results/live_phase1_v1/screening.jsonl --out results/phase1_independent_evaluation.json
```

The evaluation fails closed if: independent human attestation or SHA-256 hashes are absent/invalid; reference IDs are missing or duplicated; the reference does not cover the sample; source-level input hashes differ; run model/prompt/input manifest mismatches; or the prediction ledger came from a fixture/replay. No API request occurs during evaluation.

Outputs: full-sample and title-only versus title/abstract contingency counts (TP, FP, TN, FN), abstentions and inference errors; precision/recall restricted to determinate model decisions; eligibility retention once all non-exclusions go to human reviewers; potential auto-exclusion rate, false exclusions, and Wilson binomial 95% intervals. The report supplies exact false-exclusion and abstention IDs for audit.

**Never conflate potential automated exclusion with actual workload savings.** Human-review time and actual error costs remain unmeasured. A false-negative exclusion blocks an unqualified safe-automation claim, while observing zero false negatives would not prove universal safety. The sample is not representative, has possible duplicate study versions, and the labels address title/abstract eligibility only.

## Offline tests, not real measurements

```bash
pytest -q tests/test_independent_benchmark.py
```

Synthetic tests cover an incorrect automated exclusion, reviewer disagreement, second-review incompleteness, missing model rows, source tampering and fixture rejection. Their numerical values are not reportable model performance.

**Appropriate application claim until human evaluation:** Built a provenance-gated benchmark to score reproducible LLM screening against independent human references, with explicit deferral handling, false-exclusion detection and stratified audits. Independent human adjudication and live-model accuracy testing remain outstanding.

Next: complete the 240/96 human screening, carry out a live model run, independently inspect error cases, then proceed to source-grounded extraction (Step 3).
