#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

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
        "--disagreements",
        type=Path,
        default=ROOT / "results/screening_disagreements.csv",
    )
    args = parser.parse_args()

    sample = pd.read_csv(args.sample).fillna("")
    total_ids = set(sample["candidate_id"])

    if not args.decisions.exists():
        print(json.dumps({
            "sample_n": len(sample),
            "reviewers": 0,
            "completed_decisions": 0,
            "message": "No annotation file exists yet.",
        }, indent=2))
        return

    dec = pd.read_csv(args.decisions).fillna("")
    dec = dec[dec["candidate_id"].isin(total_ids)].copy()
    reviewers = sorted(x for x in dec["reviewer"].unique() if x)

    status = {
        "sample_n": int(len(sample)),
        "reviewers": reviewers,
        "by_reviewer": {},
    }
    for reviewer in reviewers:
        sub = dec[dec["reviewer"] == reviewer]
        counts = sub["decision"].value_counts().to_dict()
        status["by_reviewer"][reviewer] = {
            "completed": int(sub["candidate_id"].nunique()),
            "remaining": int(len(sample) - sub["candidate_id"].nunique()),
            "include": int(counts.get("include", 0)),
            "exclude": int(counts.get("exclude", 0)),
            "uncertain": int(counts.get("uncertain", 0)),
        }

    if len(reviewers) >= 2:
        a = dec[dec["reviewer"] == reviewers[0]][["candidate_id", "decision"]].rename(
            columns={"decision": "decision_a"}
        )
        b = dec[dec["reviewer"] == reviewers[1]][["candidate_id", "decision"]].rename(
            columns={"decision": "decision_b"}
        )
        pair = a.merge(b, on="candidate_id", how="inner", validate="one_to_one")
        if len(pair):
            pair["agree"] = pair["decision_a"] == pair["decision_b"]
            status["pairwise"] = {
                "reviewer_a": reviewers[0],
                "reviewer_b": reviewers[1],
                "overlap_n": int(len(pair)),
                "agreement": float(pair["agree"].mean()),
                "cohen_kappa": float(
                    cohen_kappa_score(pair["decision_a"], pair["decision_b"])
                ),
                "disagreements": int((~pair["agree"]).sum()),
            }
            disagreements = pair[~pair["agree"]].merge(
                sample[["candidate_id", "title"]], on="candidate_id", how="left"
            )
            args.disagreements.parent.mkdir(parents=True, exist_ok=True)
            disagreements.to_csv(args.disagreements, index=False)

    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
