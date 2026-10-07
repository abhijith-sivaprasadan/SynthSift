#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=ROOT / "data/search/openalex_snapshot_2026-10-07",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "results/openalex_screening_queue.csv")
    args = parser.parse_args()

    shards = sorted(args.snapshot_dir.glob("records_*.csv"))
    if not shards:
        raise FileNotFoundError(f"No record shards found under {args.snapshot_dir}")

    df = pd.concat([pd.read_csv(path) for path in shards], ignore_index=True)
    clusters_path = args.snapshot_dir / "version_clusters.csv"
    cluster_for = {}
    if clusters_path.exists():
        clusters = pd.read_csv(clusters_path).fillna("")
        for _, row in clusters.iterrows():
            for candidate_id in str(row["candidate_ids"]).split(";"):
                if candidate_id:
                    cluster_for[candidate_id] = row["cluster_id"]

    df["version_cluster_id"] = df["candidate_id"].map(cluster_for).fillna("")
    df["screening_text"] = df["abstract"].fillna("")
    df["screening_basis"] = df["screening_text"].str.strip().ne("").map(
        {True: "title+abstract", False: "title-only"}
    )
    df["decision"] = ""
    df["reason"] = ""
    df["reviewer"] = ""
    df["adjudication_status"] = ""

    columns = [
        "candidate_id", "version_cluster_id", "title", "screening_text",
        "screening_basis", "doi", "openalex_id", "publication_year",
        "work_type", "language", "query_arms", "best_rank",
        "landing_page_url", "decision", "reason", "reviewer",
        "adjudication_status",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df[columns].to_csv(args.output, index=False)

    summary = {
        "records": int(len(df)),
        "title_abstract": int((df["screening_basis"] == "title+abstract").sum()),
        "title_only": int((df["screening_basis"] == "title-only").sum()),
        "version_clustered_records": int(df["version_cluster_id"].ne("").sum()),
        "english_flag": int((df["language"] == "en").sum()),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
