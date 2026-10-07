from pathlib import Path

import pandas as pd

from synthsift.sampling import deterministic_stratified_sample, fnv1a32

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/search/openalex_snapshot_2026-10-07"


def load_snapshot():
    return pd.concat(
        [pd.read_csv(p).fillna("") for p in sorted(SNAPSHOT.glob("records_*.csv"))],
        ignore_index=True,
    )


def test_hash_is_stable():
    assert fnv1a32("20261007-phase1|OA0001") == 2482150883


def test_phase1_sample_shape_and_strata():
    df = load_snapshot()
    sample, quotas = deterministic_stratified_sample(df, 240, "20261007-phase1")
    assert len(sample) == 240
    assert sample["candidate_id"].is_unique
    assert quotas == {
        "abstract__01_20": 29,
        "title_only__01_20": 22,
        "abstract__21_50": 42,
        "abstract__51_100": 76,
        "title_only__51_100": 43,
        "title_only__21_50": 28,
    }


def test_committed_phase1_ids_match_generator():
    df = load_snapshot()
    generated, _ = deterministic_stratified_sample(df, 240, "20261007-phase1")
    committed = pd.read_csv(ROOT / "data/samples/phase1_screening_sample_240.csv")
    assert generated["candidate_id"].tolist() == committed["candidate_id"].tolist()
