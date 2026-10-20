"""No external API: verify human reference gates and offline scoring arithmetic only.

All cases are synthetic; no measured SynthSift model accuracy is asserted by these tests.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from freeze_independent_reference import freeze
from synthsift.independent_benchmark import evaluate, sha
from synthsift.llm_runner import canonical, digest


def csv_file(path, fields, records):
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=fields)
        w.writeheader()
        w.writerows(records)


def dataset(tmp):
    sample = tmp / "sample.csv"
    recs = [
        {"candidate_id": "T01", "title": "Household adoption grants", "abstract": "Surveys measure willingness to buy residential heat pumps.", "second_review_sample": "0"},
        {"candidate_id": "T02", "title": "Industrial refrigeration compressors", "abstract": "Experimental tests of compressors for factories.", "second_review_sample": "1"},
        {"candidate_id": "T03", "title": "Residential investment choices", "abstract": "Costs influence homeowners adopting heat pumps.", "second_review_sample": "1"},
        {"candidate_id": "T04", "title": "Post-installation heat pump control", "abstract": "", "second_review_sample": "0"},
    ]
    csv_file(sample, list(recs[0]), recs)
    decisions = tmp / "reviews.csv"
    review = [
        ("T01", "review1", "include"),
        ("T02", "review1", "exclude"),
        ("T02", "review2", "exclude"),
        ("T03", "review1", "include"),
        ("T03", "review2", "uncertain"),
        ("T04", "review1", "exclude"),
    ]
    csv_file(decisions, ["candidate_id", "reviewer", "decision", "reason"], [
        {"candidate_id": k, "reviewer": person, "decision": vote,
         "reason": "Source-based human protocol decision"} for k, person, vote in review
    ])
    adj = tmp / "adjudicated.csv"
    csv_file(adj, ["candidate_id", "final_decision", "adjudication_reason"], [
        {"candidate_id": "T03", "final_decision": "include",
         "adjudication_reason": "Adjudicated from citation"}
    ])
    protocol = tmp / "protocol.md"
    protocol.write_text("Frozen protocol (synthetic test only)", encoding="utf-8")
    ref = tmp / "reference.csv"
    return sample, recs, decisions, adj, protocol, ref


def fake_run(tmp, recs, decisions=("include", "exclude", "exclude", "uncertain"), provider="openai"):
    out = tmp / "run"
    out.mkdir(exist_ok=True)
    model = "test-live-model"  # synthetic records and fabricated test responses, NOT real inference
    prompt_sha = "demo-sha"
    config = {
        "model": model, "temperature": 0.0, "prompt_version": "test-v1",
        "prompt_sha256": prompt_sha,
        "input_manifest_sha256": digest(canonical([
            {"candidate_id": r["candidate_id"], "title": r["title"], "abstract": r["abstract"]}
            for r in recs
        ])),
    }
    (out / "run_config.json").write_text(json.dumps(config), encoding="utf-8")
    payload = []
    for r, decision in zip(recs, decisions):
        payload.append({
            "candidate_id": r["candidate_id"], "provider": provider,
            "status": "ok", "input_sha256": digest(canonical({
                "candidate_id": r["candidate_id"], "title": r["title"], "abstract": r["abstract"]
            })), "model": model, "temperature": 0.0, "prompt_version": "test-v1",
            "prompt_sha256": prompt_sha,
            "output": {"decision": decision, "abstain": decision == "uncertain"}
        })
    (out / "screening.jsonl").write_text(
        "\n".join(canonical(r) for r in payload) + "\n", encoding="utf-8"
    )
    return out


def test_freeze_and_evaluate_offline_synthetic(tmp_path):
    sample, recs, decisions, adj, protocol, ref = dataset(tmp_path)
    info = freeze(sample, decisions, adj, protocol, ref, "Human Test Attestor")
    assert info["records"] == 4 and info["second_reviewed"] == 2
    manifest = ref.with_suffix(".manifest.json")
    meta = json.loads(manifest.read_text())
    assert meta["source_ai_predictions_used_as_reference"] is False
    assert meta["reference_sha256"] == sha(ref)
    out = fake_run(tmp_path, recs)
    scored = evaluate(sample, ref, manifest, out / "screening.jsonl", out / "run_config.json")
    v = scored["overall"]
    assert (v["tp"], v["tn"], v["fn"], v["fp"]) == (1, 1, 1, 0)
    assert v["model_abstentions_or_errors"] == 1
    assert v["auto_excluded"] == 2
    assert v["auto_exclusion_fraction"] == 0.5
    assert v["eligible_retention_with_human_review"] == 0.5
    assert v["zero_missed_eligible_gate"] is False
    assert scored["false_exclusion_ids"] == ["T03"]
    assert scored["model_abstention_ids"] == ["T04"]
    assert scored["by_source_basis"]["title_only"]["n"] == 1


def test_does_not_freeze_unresolved_or_incomplete_review(tmp_path):
    sample, recs, decisions, adj, protocol, ref = dataset(tmp_path)
    with pytest.raises(ValueError, match="ambiguous"):
        freeze(sample, decisions, None, protocol, ref, "Human Test Attestor")
    lines = list(csv.DictReader(decisions.open()))
    csv_file(decisions, list(lines[0]), [x for x in lines if not
             (x["candidate_id"] == "T02" and x["reviewer"] == "review2")])
    with pytest.raises(ValueError, match="incomplete second"):
        freeze(sample, decisions, adj, protocol, ref, "Human Test Attestor")
    assert not ref.exists()


def test_evaluation_rejects_fixtures_hash_tampering_and_missing_rows(tmp_path):
    sample, recs, decisions, adj, protocol, ref = dataset(tmp_path)
    freeze(sample, decisions, adj, protocol, ref, "Test Attestor")
    manifest = ref.with_suffix(".manifest.json")
    out = fake_run(tmp_path, recs, provider="fixture")
    with pytest.raises(ValueError, match="provider"):
        evaluate(sample, ref, manifest, out / "screening.jsonl", out / "run_config.json")
    # Reject stale evidence even when candidate IDs still match.
    txt = (out / "screening.jsonl").read_text().replace('"provider":"fixture"', '"provider":"openai"')
    txt = txt.replace('"input_sha256":"', '"input_sha256":"bad-')
    (out / "screening.jsonl").write_text(txt)
    with pytest.raises(ValueError, match="fingerprint"):
        evaluate(sample, ref, manifest, out / "screening.jsonl", out / "run_config.json")
    (out / "screening.jsonl").write_text("\n".join(txt.splitlines()[:-1]) + "\n")
    with pytest.raises(ValueError, match="coverage"):
        evaluate(sample, ref, manifest, out / "screening.jsonl", out / "run_config.json")


def test_reference_manifest_cannot_silently_follow_label_edits(tmp_path):
    sample, recs, decisions, adj, protocol, ref = dataset(tmp_path)
    freeze(sample, decisions, adj, protocol, ref, "Test Attestor")
    out = fake_run(tmp_path, recs)
    ref.write_text(ref.read_text() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="attestation"):
        evaluate(sample, ref, ref.with_suffix(".manifest.json"),
                 out / "screening.jsonl", out / "run_config.json")
