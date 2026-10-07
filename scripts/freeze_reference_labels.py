#!/usr/bin/env python
"""Freeze completed/adjudicated human screening decisions into a versioned reference file."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample",
        type=Path,
        default=ROOT / "data/samples/phase1_screening_sample_240.csv",
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "annotations/screening_decisions.csv",
    )
    parser.add_argument(
        "--adjudicated",
        type=Path,
        help="Optional CSV with candidate_id,final_decision,adjudication_reason",
    )
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()

    sample = pd.read_csv(args.sample).fillna("")
    dec = pd.read_csv(args.decisions).fillna("")
    valid = {"include", "exclude", "uncertain"}

    if not set(dec["decision"]).issubset(valid):
        raise ValueError("Unexpected decision value in annotation file")

    reviewer_counts = dec.groupby("candidate_id")["reviewer"].nunique()
    if args.adjudicated:
        adj = pd.read_csv(args.adjudicated).fillna("")
        final = sample[["candidate_id", "title"]].merge(
            adj, on="candidate_id", how="left", validate="one_to_one"
        )
        if final["final_decision"].eq("").any():
            raise ValueError("Adjudicated file does not cover every sample record")
    else:
        single = dec.sort_values(["candidate_id", "reviewer"]).drop_duplicates(
            "candidate_id", keep="first"
        )
        final = sample[["candidate_id", "title"]].merge(
            single[["candidate_id", "decision", "reason", "reviewer"]],
            on="candidate_id", how="left", validate="one_to_one"
        )
        if final["decision"].eq("").any():
            raise ValueError(
                "Reference set is incomplete. Finish screening or supply an adjudicated file."
            )
        final = final.rename(columns={
            "decision": "final_decision",
            "reason": "adjudication_reason",
        })

    out_dir = ROOT / "data/labels"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"phase1_reference_{args.version}.csv"
    final.to_csv(out_path, index=False)
    print(f"Frozen {len(final)} reference decisions to {out_path}")


if __name__ == "__main__":
    main()
