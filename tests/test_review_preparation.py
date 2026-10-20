"""Review-preparation integrity and scientific boundary tests."""
from pathlib import Path

import pandas as pd

from synthsift.full_corpus_review import ROOT, read_csv
from synthsift.review_preparation import OUT, build_review_packs
from scripts.prepare_review_evidence import blind_reference_packets


def test_all_candidates_covered_without_pretending_full_text_access():
    packs, summary = build_review_packs()
    inv = packs["source_inventory.csv"]
    assert len(inv) == inv["candidate_id"].nunique() == 538
    assert (inv["external_full_text_verified"] == "no").all()
    assert (inv["study_identity_adjudicated"] == "no").all()
    assert (inv["independent_human_review_done"] == "no").all()
    assert summary["candidate_records_needing_source_recheck"] == 87
    assert summary["full_text_verified"] == 0


def test_version_family_queue_flags_disagreement_but_never_deduplicates():
    packs, summary = build_review_packs()
    v = packs["version_family_review.csv"]
    assert len(v) == 29
    assert summary["clustered_candidate_records"] == 66
    assert summary["clusters_with_discordant_AI_recommendations"] == 1
    assert v.loc[v["ai_decision_disagreement"] == "yes", "cluster_id"].tolist() == ["VC006"]
    assert (v["study_identity_resolution"] == "unresolved").all()
    assert (v["canonical_record_id"] == "").all()


def test_extraction_queue_is_empty_and_not_reference_ground_truth():
    packs, summary = build_review_packs()
    x = packs["provisional_evidence_extraction_queue.csv"]
    assert len(x) == 197
    assert (x["extraction_status"] == "not_started").all()
    assert x["population_extracted"].eq("").all()
    assert x["effect_estimate_extracted"].eq("").all()
    assert summary["ai_includes"] == 144 and summary["ai_uncertain"] == 53
    assert summary["independent_human_reference_review_complete"] is False


def test_all_machine_exclusions_retained_for_false_negative_audit():
    packs, _ = build_review_packs()
    x = packs["excluded_record_audit_queue.csv"]
    assert len(x) == 341
    assert (x["decision"] == "exclude").all()
    assert (x["independent_false_negative_audit"] == "not_performed").all()
    assert set(x["audit_priority"]) <= {"high", "standard"}


def test_unlabeled_human_review_packets_do_not_leak_ai_decisions(tmp_path: Path):
    blind_reference_packets(tmp_path)
    a = read_csv(tmp_path / "blind_first_review_240.csv")
    b = read_csv(tmp_path / "blind_second_review_96.csv")
    assert len(a) == 240 and len(b) == 96
    assert set(b["candidate_id"]).issubset(set(a["candidate_id"]))
    for frame in [a, b]:
        assert not set(frame.columns) & {
            "decision", "reason", "reviewer", "ai_decision", "priority_flags",
            "ai_reviewer", "candidate_label", "screening_recommendation",
        }


def test_committed_review_outputs_match_sources():
    packs, _ = build_review_packs()
    for filename, frame in packs.items():
        committed = read_csv(OUT / filename)
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True), committed.reset_index(drop=True),
            check_dtype=False,
        )


def test_targeted_false_negative_recheck_preserves_frozen_ai_provenance():
    path = OUT / "targeted_exclusion_recheck_20261020.csv"
    audit = read_csv(path)
    original = build_review_packs()[0]["excluded_record_audit_queue.csv"]
    top = original.loc[original["audit_priority"].eq("high"), "candidate_id"]
    assert len(audit) == len(top) == 8
    assert audit["candidate_id"].tolist() == top.tolist()
    assert (audit["frozen_ai_decision"] == "exclude").all()
    suggested = audit.loc[audit["changes_recommendation"].eq("yes")]
    assert len(suggested) == 1
    assert suggested["candidate_id"].iat[0] == "OA0443"
    assert suggested["second_ai_recommendation"].iat[0] == "include"
    assert "sciencedirect.com" in suggested["external_source_url"].iat[0]
