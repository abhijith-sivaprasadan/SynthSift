# AI-assisted Phase-1 screening — frozen OpenAlex sample

**Performed:** 20 October 2026  
**Protocol:** [screening protocol v1.0](../../protocols/screening_protocol_v1.md), frozen on 7 October 2026  
**Reviewer ID:** `ai_assistant_gpt6_20261020` (**AI, not a human reviewer**)  
**Record universe:** the already-frozen `data/samples/phase1_screening_sample_240.csv`, not all 538 search candidates.

This is a **complete AI-assisted first pass of the 240 sampled titles and available abstracts**, not a completed human-reference study. Every record has exactly one include, exclude or uncertain recommendation and a specific reason in the eight append-only-origin screening batches (`batch_01.csv` through `batch_08.csv`). No decision has been written to `annotations/screening_decisions.csv` or `data/labels/`.

## Screening result (sample only)

| Recommendation | Records |
|---|---:|
| Include | 55 |
| Exclude | 158 |
| Uncertain — requires more source evidence / human review | 27 |
| Total AI-assessed Phase-1 sample | 240 |

The frozen sample contains 93 title-only and 147 title-and-abstract records. The initial pass examined source titles and available abstract **excerpts**, followed by inspection of complete abstracts for selected borderline cases. Consequently these recommendations should be checked against the full source abstracts before they are treated as human eligibility decisions. Lack of an abstract is not itself exclusion evidence. A record outside this sample has **not** been evaluated by this screening pass.

## Decision boundaries

- **Include:** clear economic, behavioural, social, policy, infrastructure, building-stock, installer/workforce or market determinant of *residential* heat-pump uptake. A review or system-level bottleneck may qualify.
- **Exclude:** technical thermodynamics, refrigerants, industrial/district-process heating, installed equipment control/demand response, grid impacts given *assumed* adoption, or household appliances unrelated to household heating.
- **Uncertain:** source text is ambiguous about a separate heat-pump choice, sector, or adoption determinant. Do not silently collapse this category into exclude.
- If title-normalisation suggests multiple bibliographic versions, flag them rather than deduplicating eligibility decisions on title alone.

## Reproduce the audit and review queue

```bash
python -m pip install -e '.[dev]'
python scripts/audit_ai_screening.py --out results/ai_first_pass
pytest -q tests/test_ai_screening.py
```

Convenience copies are also committed: [`phase1_ai_assisted_v1.csv`](phase1_ai_assisted_v1.csv), a source-linked 240-record ledger; [`priority_rechecks_v1.csv`](priority_rechecks_v1.csv), the 51 records marked uncertain and/or potential bibliographic duplicates; and [`summary_v1.json`](summary_v1.json), a machine-readable status statement.

Output:
- `ai_decisions_240.csv` — annotated sample, source IDs and reasons.
- `human_review_priority.csv` — uncertain cases and potential version duplicates; may contain both types of flags.
- `summary.json` — method, AI decision totals and flags indicating **no independent human review**.

The scripts reject missing or duplicate IDs, invalid decisions, blank reasons and human-style reviewer attribution.

## What is *not* complete

1. **Independent human screening:** The prespecified 96-record blinded second-review set has *not* been completed. User `abhijith` has not performed the Phase-1 human reference screening; AI decisions must not be copied into that user's name.
2. **Human adjudication:** No disagreements have been independently adjudicated; the 27 uncertain recommendations and 29 potential publication/version clusters across the *full snapshot* need further evidence as applicable.
3. **Full-text eligibility and extraction:** Not performed for this sample. Do not treat these records as final included studies or write a literature-synthesis conclusion.
4. **Model evaluation:** Screening-model recall, precision, kappa, false-negative rate and workload reduction **cannot** be inferred from the machine's own first-pass recommendations. The separate 16-record pilot is only a software sanity check.
5. **All 538 candidates:** The remaining 298 records in the frozen OpenAlex corpus have not received this AI first-pass review. No claim of complete-corpus screening is made.

This experiment is best treated as an **auditable AI-assisted triage result**, available for later blinded human assessment and structured disagreement analysis.
