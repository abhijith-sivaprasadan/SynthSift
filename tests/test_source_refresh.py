"""Verify that OpenAlex metadata rechecks are never presented as human/full-text evidence."""
import pandas as pd

from synthsift.source_refresh import describe_response


def test_metadata_refresh_only_reports_presence_without_copying_abstract():
    row = pd.Series({
        "candidate_id": "OA0001", "openalex_id": "https://openalex.org/W3129081719"
    })
    data = {
        "id": "https://openalex.org/W3129081719",
        "abstract_inverted_index": {"hello": [0, 1], "world": [2]},
        "best_oa_location": {"landing_page_url": "https://example.org/preprint"},
        "title": "Example paper",
    }
    out = describe_response(row, data, "2026-10-20T18:00:00+00:00")
    assert out["status"] == "metadata_returned"
    assert out["has_abstract_now"] == "yes"
    assert out["abstract_index_terms"] == "2"
    assert out["oa_landing_url"] == "https://example.org/preprint"
    assert "hello" not in str(out)
    assert "full_text" not in str(out).lower()


def test_mismatched_openalex_identity_is_rejected_without_inference():
    row = pd.Series({"candidate_id": "OA0001", "openalex_id": "https://openalex.org/W3129081719"})
    result = describe_response(
        row, {"id": "https://openalex.org/W99999", "abstract_inverted_index": {"x": [0]}},
        "2026-10-20T18:00:00+00:00"
    )
    assert result["status"] == "id_mismatch"
    assert result["has_abstract_now"] == "unknown"



def test_committed_live_metadata_followup_does_not_claim_full_text():
    from synthsift.full_corpus_review import read_csv
    from pathlib import Path
    import json
    root = Path(__file__).resolve().parents[1]
    base = root / "data/review_preparation/openalex_title_only_metadata_20261020"
    frame = read_csv(base.with_suffix(".csv"))
    summary = json.loads(base.with_suffix(".json").read_text())
    assert len(frame) == frame["candidate_id"].nunique() == 87
    assert summary["records_attempted"] == 87
    assert summary["metadata_returned"] == 82
    assert summary["abstract_metadata_now_present"] == 0
    assert summary["checks_not_successful"] == 5
    assert summary["full_text_read_or_verified"] == 0
    assert set(frame["status"]).issubset({"metadata_returned", "http_404"})
    assert set(frame.loc[frame["status"] == "http_404", "candidate_id"]) == {
        "OA0150", "OA0282", "OA0381", "OA0458", "OA0467"
    }
