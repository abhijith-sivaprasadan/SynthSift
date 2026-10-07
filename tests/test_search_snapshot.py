from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/search/openalex_snapshot_2026-10-07"


def load_snapshot():
    shards = sorted(SNAPSHOT.glob("records_*.csv"))
    assert shards
    return pd.concat([pd.read_csv(p) for p in shards], ignore_index=True)


def test_snapshot_shape_and_exact_deduplication():
    df = load_snapshot()
    assert len(df) == 538
    assert df["candidate_id"].is_unique
    assert df["openalex_id"].is_unique

    dois = df["doi"].dropna().astype(str).str.strip()
    dois = dois[dois != ""].str.lower()
    assert dois.is_unique


def test_screening_fields_are_blank_in_raw_snapshot():
    df = load_snapshot().fillna("")
    for column in ["screening_decision", "screening_reason", "reviewer", "adjudication_status"]:
        assert (df[column] == "").all()


def test_abstract_counts_and_title_only_are_preserved():
    df = load_snapshot().fillna("")
    has_abstract = df["abstract"].str.strip().ne("")
    assert int(has_abstract.sum()) == 330
    assert int((~has_abstract).sum()) == 208


def test_version_clusters_are_audit_flags_not_exact_deduplication():
    clusters = pd.read_csv(SNAPSHOT / "version_clusters.csv").fillna("")
    assert len(clusters) == 29
    candidate_ids = []
    for value in clusters["candidate_ids"]:
        candidate_ids.extend(x for x in str(value).split(";") if x)
    assert len(candidate_ids) == 66
