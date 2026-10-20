"""Integrity tests for the 538-candidate *AI-only* title/abstract triage."""
import json
from pathlib import Path

import pandas as pd

from synthsift.full_corpus_review import load_full_corpus, summary

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/ai_screening"


def test_covers_every_openalex_candidate_exactly_once():
    df = load_full_corpus()
    report = summary(df)
    assert len(df) == 538 and df["candidate_id"].is_unique
    assert report["candidate_total"] == 538
    assert (report["phase1_original"], report["additional_2026_10_20"]) == (240, 298)
    assert report["counts"] == {"include": 144, "exclude": 341, "uncertain": 53}
    assert report["title_only"] == 208 and report["abstract_available"] == 330
    assert report["priority_unique"] == 150
    assert report["potential_version_records"] == 66
    assert report["title_only_includes"] == 51


def test_original_240_decisions_are_preserved_verbatim():
    old = pd.read_csv(DATA / "phase1_ai_assisted_v1.csv", dtype=str, keep_default_na=False)
    df = load_full_corpus().set_index("candidate_id")
    for field in ("decision", "reason", "reviewer"):
        assert df.loc[old["candidate_id"], field].tolist() == old[field].tolist()


def test_new_machine_reviewer_attribution_and_no_gold_labels():
    df = load_full_corpus()
    assert set(df["reviewer"]) == {
        "ai_assistant_gpt6_20261020", "ai_assistant_gpt6_20261020_full_corpus"
    }
    assert df["reason"].str.strip().str.len().min() >= 24
    assert df["decision"].isin({"include", "exclude", "uncertain"}).all()
    assert not summary(df)["human_reference_complete"]
    assert not summary(df)["human_second_review_complete"]
    assert not summary(df)["model_accuracy_estimates_valid"]


def test_reproducibility_of_committed_outputs():
    df = load_full_corpus()
    ledger = pd.read_csv(DATA / "full_corpus_ai_assisted_v1.csv", dtype=str, keep_default_na=False)
    priority = pd.read_csv(
        DATA / "full_corpus_review_priority_v1.csv", dtype=str, keep_default_na=False
    )
    pd.testing.assert_frame_equal(df, ledger, check_dtype=False)
    pd.testing.assert_frame_equal(
        df.loc[df["priority_flags"].ne("")], priority, check_dtype=False
    )
    assert json.loads((DATA / "full_corpus_summary_v1.json").read_text()) == summary(df)


def test_priority_rechecks_do_not_silently_discard_uncertainty():
    df = load_full_corpus()
    assert df.loc[df["decision"].eq("uncertain"), "priority_flags"].str.contains(
        "uncertain", regex=False
    ).all()
    assert df.loc[df["potential_version_clusters"].ne(""), "priority_flags"].str.contains(
        "potential_version", regex=False
    ).all()
    title_includes = df["screening_basis"].eq("title-only") & df["decision"].eq("include")
    assert df.loc[title_includes, "priority_flags"].str.contains(
        "title_only_include", regex=False
    ).all()
