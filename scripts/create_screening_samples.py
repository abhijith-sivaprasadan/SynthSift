#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from synthsift.sampling import deterministic_stratified_sample


def load_snapshot(snapshot_dir: Path) -> pd.DataFrame:
    shards = sorted(snapshot_dir.glob("records_*.csv"))
    if not shards:
        raise FileNotFoundError(f"No search snapshot shards found in {snapshot_dir}")
    return pd.concat([pd.read_csv(p).fillna("") for p in shards], ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=ROOT / "data/search/openalex_snapshot_2026-10-07",
    )
    parser.add_argument("--phase1-n", type=int, default=240)
    parser.add_argument("--second-review-n", type=int, default=96)
    parser.add_argument("--phase1-seed", default="20261007-phase1")
    parser.add_argument("--second-review-seed", default="20261007-second-review")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/samples")
    args = parser.parse_args()

    df = load_snapshot(args.snapshot_dir)
    phase1, q1 = deterministic_stratified_sample(df, args.phase1_n, args.phase1_seed)
    second, q2 = deterministic_stratified_sample(
        phase1, args.second_review_n, args.second_review_seed
    )
    second_ids = set(second["candidate_id"])
    phase1["second_review_sample"] = phase1["candidate_id"].isin(second_ids).astype(int)

    for col in ["decision", "reason", "reviewer", "adjudication_status"]:
        phase1[col] = ""

    args.output_dir.mkdir(parents=True, exist_ok=True)
    phase_path = args.output_dir / f"phase1_screening_sample_{args.phase1_n}.csv"
    second_path = args.output_dir / f"second_review_sample_{args.second_review_n}.csv"

    phase_columns = [
        "candidate_id", "title", "abstract", "abstract_missing", "doi",
        "openalex_id", "publication_year", "work_type", "language", "query_arms",
        "best_rank", "sampling_stratum", "second_review_sample", "decision",
        "reason", "reviewer", "adjudication_status",
    ]
    phase1[phase_columns].to_csv(phase_path, index=False)
    second[["candidate_id", "sampling_stratum", "title", "abstract_missing", "best_rank"]].to_csv(
        second_path, index=False
    )

    manifest = {
        "source_snapshot": str(args.snapshot_dir.relative_to(ROOT)),
        "phase1_n": args.phase1_n,
        "second_review_n": args.second_review_n,
        "phase1_seed": args.phase1_seed,
        "second_review_seed": args.second_review_seed,
        "sampling_method": (
            "proportional allocation across abstract-availability x OpenAlex "
            "best-rank bands; deterministic FNV-1a ordering within strata"
        ),
        "rank_bands": ["1-20", "21-50", "51-100"],
        "phase1_quotas": q1,
        "second_review_quotas": q2,
        "note": "No model score or predicted eligibility label was used in sampling.",
    }
    (args.output_dir / "sampling_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
