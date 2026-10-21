"""AI-blind pilot selection tests; these are not empirical screening-performance tests."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from create_validation_pilot import select, TARGETS


def source_sample():
    return pd.read_csv(ROOT / "data/samples/phase1_screening_sample_240.csv").fillna("")


def test_pilot_membership_and_review_quota():
    source = source_sample()
    pilot = select(source)
    assert len(source) == 240 and len(pilot) == 80
    assert len(set(pilot.candidate_id)) == 80
    assert pilot.second_review_sample.sum() == 32
    assert pilot.second_review_sample.eq(0).sum() == 48
    assert set(pilot.candidate_id).issubset(set(source.candidate_id))
    assert all(pilot[c].astype(str).str.strip().eq("").all()
               for c in ("decision", "reason", "reviewer", "adjudication_status"))
    assert set(pilot.sampling_stratum).issubset(set(source.sampling_stratum))


def test_selection_is_independent_of_source_order_and_model_predictions():
    source = source_sample()
    first = select(source)
    reverse = select(source.iloc[::-1].reset_index(drop=True))
    assert set(first.candidate_id) == set(reverse.candidate_id)
    assert TARGETS == {0: 48, 1: 32}
    with_predictions = source.copy()
    with_predictions["ai_first_pass"] = "exclude"
    assert set(first.candidate_id) == set(select(with_predictions).candidate_id)


def test_fail_closed_if_review_judgments_or_duplicate_ids_enter_source():
    source = source_sample()
    tainted = source.copy()
    tainted.loc[0, "decision"] = "include"
    with pytest.raises(ValueError, match="existing judgments"):
        select(tainted)
    duplicate = source.copy()
    duplicate.loc[1, "candidate_id"] = duplicate.loc[0, "candidate_id"]
    with pytest.raises(ValueError, match="duplicate"):
        select(duplicate)
