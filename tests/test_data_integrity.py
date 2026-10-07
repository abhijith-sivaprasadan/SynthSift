from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_records():
    parts = sorted((ROOT / "data" / "records").glob("records_*.csv"))
    assert parts, "benchmark record shards are missing"
    return pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)


def test_benchmark_records_are_unique_and_provenance_clean():
    df = load_records()
    assert len(df) == 16
    assert df["id"].is_unique
    assert set(df["reference_label"].astype(int)) == {0, 1}
    assert set(df["text_provenance"]).issubset({"source_abstract", "source_summary"})
    assert df["screening_text"].fillna("").str.strip().ne("").all()
    assert df["source_url"].fillna("").str.startswith("http").all()


def test_expected_class_counts():
    df = load_records()
    counts = df["reference_label"].astype(int).value_counts().to_dict()
    assert counts == {1: 9, 0: 7}


def test_extraction_reference_links_only_to_included_records():
    df = load_records().set_index("id")
    ref = pd.read_csv(ROOT / "data" / "extraction_reference.csv")
    assert ref["id"].is_unique
    assert set(ref["id"]).issubset(set(df.index))
    assert (df.loc[ref["id"], "reference_label"].astype(int).to_numpy() == 1).all()


def test_unresolved_provenance_is_not_in_benchmark():
    df = load_records()
    audit = pd.read_csv(ROOT / "data" / "provenance_audit.csv")
    assert set(df["id"]).isdisjoint(set(audit["id"]))
    assert {"derived_summary", "source_mismatch"}.issuperset(set(audit["text_provenance"]))
