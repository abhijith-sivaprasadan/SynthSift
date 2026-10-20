"""Rebuild AI-only 538-record title/abstract screening from frozen source and decision batches.

These are *not* independent human reference labels or final systematic-review inclusions.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data/search/openalex_snapshot_2026-10-07"
SCREEN_DIR = ROOT / "data/ai_screening"
OLD_REVIEWER = "ai_assistant_gpt6_20261020"
NEW_REVIEWER = "ai_assistant_gpt6_20261020_full_corpus"
LABELS = {"include", "exclude", "uncertain"}
OUTPUT_COLUMNS = [
    "candidate_id", "title", "decision", "reason", "reviewer", "screening_basis",
    "potential_version_clusters", "priority_flags", "phase1_sample",
    "second_review_sample", "doi", "openalex_id", "source_url",
    "publication_year", "work_type", "language", "query_arms", "best_rank",
]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def load_full_corpus() -> pd.DataFrame:
    shards = sorted(SNAPSHOT.glob("records_*.csv"))
    if len(shards) != 8:
        raise ValueError("Expected eight frozen OpenAlex snapshot CSV shards")
    source = pd.concat([read_csv(p) for p in shards], ignore_index=True)
    old = read_csv(SCREEN_DIR / "phase1_ai_assisted_v1.csv")
    new_files = sorted(SCREEN_DIR.glob("full_corpus_batch_[0-9][0-9].csv"))
    if len(new_files) != 6:
        raise ValueError("Expected exactly six reviewed-new-record batch files")
    newer = pd.concat([read_csv(f) for f in new_files], ignore_index=True)
    sample = read_csv(ROOT / "data/samples/phase1_screening_sample_240.csv")
    if (len(source), len(old), len(newer), len(sample)) != (538, 240, 298, 240):
        raise ValueError("Frozen source, AI batch, or sample record counts changed")
    for name, frame in [("source", source), ("old AI", old), ("new AI", newer), ("sample", sample)]:
        if frame["candidate_id"].duplicated().any():
            raise ValueError(f"{name} contains duplicate candidate IDs")
    if not old["reviewer"].eq(OLD_REVIEWER).all():
        raise ValueError("Existing Phase-1 AI decisions must preserve original attribution")
    if not newer["reviewer"].eq(NEW_REVIEWER).all():
        raise ValueError("New full-corpus decisions must carry explicit AI attribution")
    if set(old["candidate_id"]) != set(sample["candidate_id"]):
        raise ValueError("Original 240 AI decisions no longer match frozen Phase-1 sample")
    if set(newer["candidate_id"]) & set(sample["candidate_id"]):
        raise ValueError("The 298-record extension overlaps the original 240")
    decisions = pd.concat(
        [old[["candidate_id", "decision", "reason", "reviewer"]],
         newer[["candidate_id", "decision", "reason", "reviewer"]]],
        ignore_index=True,
    )
    if set(decisions["candidate_id"]) != set(source["candidate_id"]):
        raise ValueError("Incomplete or extraneous AI decisions for 538 source candidates")
    if not decisions["decision"].isin(LABELS).all():
        raise ValueError("Unexpected AI screening label")
    if decisions["reason"].str.strip().str.len().lt(24).any():
        raise ValueError("Every record needs an individual protocol-grounded explanation")

    metadata = source.drop(columns=["screening_decision", "screening_reason", "reviewer", "adjudication_status"], errors="ignore").merge(decisions, on="candidate_id", how="left", validate="one_to_one")
    metadata["screening_basis"] = metadata["abstract"].str.strip().eq("").map(
        {True: "title-only", False: "title+abstract"}
    )
    if (
        metadata["screening_basis"].eq("title-only").sum() != 208
        or metadata["screening_basis"].eq("title+abstract").sum() != 330
    ):
        raise ValueError("Frozen abstract-availability distribution changed")

    sample_meta = sample[["candidate_id", "second_review_sample"]].copy()
    metadata = metadata.merge(sample_meta, on="candidate_id", how="left", validate="one_to_one")
    metadata["phase1_sample"] = metadata["candidate_id"].isin(sample["candidate_id"]).map(
        {True: "1", False: "0"}
    )
    metadata["second_review_sample"] = metadata["second_review_sample"].fillna("0").replace("", "0")
    clusters = read_csv(SNAPSHOT / "version_clusters.csv")
    per_id: dict[str, list[str]] = {}
    for _, cluster in clusters.iterrows():
        for id_ in cluster["candidate_ids"].split(";"):
            if id_:
                if id_ not in set(source["candidate_id"]):
                    raise ValueError("Version cluster references nonexisting source candidate")
                per_id.setdefault(id_, []).append(cluster["cluster_id"])
    metadata["potential_version_clusters"] = metadata["candidate_id"].map(
        lambda id_: ";".join(per_id.get(id_, []))
    )
    def priority(row):
        flags = []
        if row["decision"] == "uncertain":
            flags.append("uncertain")
        if row["potential_version_clusters"]:
            flags.append("potential_version")
        if row["screening_basis"] == "title-only" and row["decision"] == "include":
            flags.append("title_only_include")
        return ";".join(flags)
    metadata["priority_flags"] = metadata.apply(priority, axis=1)
    metadata["source_url"] = metadata["landing_page_url"]
    return metadata[OUTPUT_COLUMNS].fillna("")


def summary(df: pd.DataFrame) -> dict:
    return {
        "status": "AI-assisted title/available-abstract first-pass; not human-adjudicated",
        "protocol": "protocols/screening_protocol_v1.md",
        "source_snapshot": "data/search/openalex_snapshot_2026-10-07",
        "candidate_total": int(len(df)),
        "phase1_original": int(df["phase1_sample"].eq("1").sum()),
        "additional_2026_10_20": int(df["phase1_sample"].eq("0").sum()),
        "counts": {
            label: int(df["decision"].eq(label).sum())
            for label in ["include", "exclude", "uncertain"]
        },
        "title_only": int(df["screening_basis"].eq("title-only").sum()),
        "abstract_available": int(df["screening_basis"].eq("title+abstract").sum()),
        "priority_unique": int(df["priority_flags"].ne("").sum()),
        "potential_version_records": int(df["potential_version_clusters"].ne("").sum()),
        "uncertain_count": int(df["decision"].eq("uncertain").sum()),
        "title_only_includes": int(
            (df["screening_basis"].eq("title-only") & df["decision"].eq("include")).sum()
        ),
        "human_reference_complete": False,
        "human_second_review_complete": False,
        "model_accuracy_estimates_valid": False,
    }
