"""Explicitly AI-assisted first-pass eligibility decisions, never human reference labels."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REVIEWER = "ai_assistant_gpt6_20261020"
DECISIONS = {"include", "exclude", "uncertain"}
COLUMNS = ["candidate_id", "decision", "reason", "reviewer"]


def load_ai_screening(
    sample_path: Path | None = None,
    batch_dir: Path | None = None,
    clusters_path: Path | None = None,
) -> pd.DataFrame:
    """Join checked AI decisions to the frozen Phase-1 sample without altering human files."""
    sample_path = sample_path or ROOT / "data/samples/phase1_screening_sample_240.csv"
    batch_dir = batch_dir or ROOT / "data/ai_screening"
    clusters_path = (
        clusters_path or ROOT / "data/search/openalex_snapshot_2026-10-07/version_clusters.csv"
    )
    sample = pd.read_csv(sample_path, dtype=str).fillna("")
    if sample["candidate_id"].duplicated().any():
        raise ValueError("Frozen sample has duplicate IDs")
    paths = sorted(batch_dir.glob("batch_[0-9][0-9].csv"))
    if not paths:
        raise ValueError("No AI-screening batch files")
    frames = [pd.read_csv(path, dtype=str).fillna("") for path in paths]
    for path, frame in zip(paths, frames):
        if frame.columns.tolist() != COLUMNS:
            raise ValueError(f"{path.name}: unexpected column schema")
    dec = pd.concat(frames, ignore_index=True)
    if dec["candidate_id"].duplicated().any():
        raise ValueError("AI-screening decisions duplicate candidate IDs")
    if set(dec["candidate_id"]) != set(sample["candidate_id"]):
        raise ValueError(
            f"AI-screening coverage mismatch: missing={len(set(sample.candidate_id)-set(dec.candidate_id))}, "
            f"unexpected={len(set(dec.candidate_id)-set(sample.candidate_id))}"
        )
    if not set(dec["decision"]).issubset(DECISIONS):
        raise ValueError("Unsupported AI-screening label")
    if not dec["reviewer"].eq(REVIEWER).all():
        raise ValueError("AI decisions must identify their machine reviewer (not a human reviewer)")
    if dec["reason"].str.strip().str.len().lt(24).any():
        raise ValueError("Every AI-assisted decision requires a substantive reason")
    annotated = sample.drop(
        columns=["decision", "reason", "reviewer", "adjudication_status"],
        errors="ignore",
    ).merge(dec, on="candidate_id", how="left", validate="one_to_one", sort=False)
    # Source snapshot's version clusters are *potential* duplicates, not verified same studies.
    clusters = pd.read_csv(clusters_path, dtype=str).fillna("")
    ids_to_clusters: dict[str, list[str]] = {}
    for _, item in clusters.iterrows():
        for candidate_id in item["candidate_ids"].split(";"):
            if candidate_id:
                ids_to_clusters.setdefault(candidate_id, []).append(item["cluster_id"])
    annotated["potential_version_clusters"] = annotated["candidate_id"].map(
        lambda key: ";".join(ids_to_clusters.get(key, []))
    )
    annotated["review_priority"] = annotated.apply(
        lambda row: (
            "uncertain+possible_version_duplicate"
            if row["decision"] == "uncertain" and row["potential_version_clusters"]
            else "uncertain"
            if row["decision"] == "uncertain"
            else "possible_version_duplicate"
            if row["potential_version_clusters"]
            else ""
        ),
        axis=1,
    )
    return annotated


def summary_for(annotated: pd.DataFrame) -> dict:
    counts = annotated["decision"].value_counts().to_dict()
    return {
        "review_method": "AI-assisted title and available abstract screening; not human reference",
        "frozen_protocol": "protocols/screening_protocol_v1.md",
        "candidate_source": "frozen 2026-10-07 OpenAlex ranked-search sample",
        "sample_n": int(len(annotated)),
        "completed_ai_first_pass": int(annotated["decision"].isin(DECISIONS).sum()),
        "include": int(counts.get("include", 0)),
        "exclude": int(counts.get("exclude", 0)),
        "uncertain": int(counts.get("uncertain", 0)),
        "title_only_n": int(annotated["abstract_missing"].eq("1").sum()),
        "flagged_potential_version_n": int(
            annotated["potential_version_clusters"].ne("").sum()
        ),
        "second_human_review_completed": False,
        "human_adjudication_completed": False,
        "use_for_model_accuracy_claims": False,
    }
