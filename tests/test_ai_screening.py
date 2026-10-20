"""Regression checks for the independently identifiable AI first-pass output."""
from pathlib import Path
import shutil

import pytest

from synthsift.ai_review import load_ai_screening, summary_for, REVIEWER

ROOT = Path(__file__).resolve().parents[1]


def test_full_frozen_sample_is_screened_without_human_labels():
    df = load_ai_screening()
    x = summary_for(df)
    assert x["sample_n"] == 240
    assert x["completed_ai_first_pass"] == 240
    assert x["include"] + x["exclude"] + x["uncertain"] == 240
    assert x["uncertain"] > 0
    assert x["title_only_n"] == 93
    assert df["candidate_id"].is_unique
    assert set(df["reviewer"]) == {REVIEWER}
    assert not x["second_human_review_completed"]
    assert not x["use_for_model_accuracy_claims"]


def test_uncertain_and_versions_remain_flagged():
    df = load_ai_screening()
    assert df.loc[df["decision"] == "uncertain", "review_priority"].str.contains(
        "uncertain", regex=False
    ).all()
    assert df["potential_version_clusters"].ne("").any()
    assert df.loc[df["potential_version_clusters"].ne(""), "review_priority"].str.contains(
        "possible_version_duplicate", regex=False
    ).all()


def test_missing_batch_record_fails_closed(tmp_path: Path):
    source = ROOT / "data/ai_screening"
    for file in source.glob("batch_[0-9][0-9].csv"):
        shutil.copy(file, tmp_path / file.name)
    file = tmp_path / "batch_08.csv"
    data = file.read_text(encoding="utf8").splitlines()
    file.write_text("\n".join(data[:-1]) + "\n", encoding="utf8")
    with pytest.raises(ValueError, match="coverage mismatch"):
        load_ai_screening(batch_dir=tmp_path)


def test_forged_human_reviewer_fails_closed(tmp_path: Path):
    source = ROOT / "data/ai_screening"
    for file in source.glob("batch_[0-9][0-9].csv"):
        shutil.copy(file, tmp_path / file.name)
    file = tmp_path / "batch_01.csv"
    file.write_text(file.read_text(encoding="utf8").replace(REVIEWER, "abhijith", 1))
    with pytest.raises(ValueError, match="machine reviewer"):
        load_ai_screening(batch_dir=tmp_path)


def test_committed_ledgers_match_batch_records():
    import pandas as pd

    df = load_ai_screening()
    all_decisions = pd.read_csv(ROOT / "data/ai_screening/phase1_ai_assisted_v1.csv").fillna("")
    priority = pd.read_csv(ROOT / "data/ai_screening/priority_rechecks_v1.csv").fillna("")
    assert len(all_decisions) == len(df) == 240
    assert all_decisions["candidate_id"].tolist() == df["candidate_id"].tolist()
    assert all_decisions["decision"].tolist() == df["decision"].tolist()
    assert all_decisions["reason"].tolist() == df["reason"].tolist()
    assert all_decisions["reviewer"].eq(REVIEWER).all()
    assert priority["candidate_id"].tolist() == df.loc[
        df["review_priority"].ne(""), "candidate_id"
    ].tolist()
    assert len(priority) == 51


def test_committed_summary_prohibits_human_ground_truth_claim():
    import json

    x = json.loads((ROOT / "data/ai_screening/summary_v1.json").read_text())
    assert x["records"] == 240
    assert (x["include"], x["exclude"], x["uncertain"]) == (55, 158, 27)
    assert x["flagged_for_human_review"] == 51
    assert x["independent_second_human_review"] is False
    assert x["reference_labels_frozen"] is False
