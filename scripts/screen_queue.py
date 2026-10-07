#!/usr/bin/env python
"""Minimal resumable terminal screener for SynthSift candidate records."""
from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_queue(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    queue = pd.read_csv(path).fillna("")

    if "screening_text" not in queue.columns:
        if "abstract" in queue.columns:
            queue["screening_text"] = queue["abstract"].astype(str)
        else:
            raise ValueError("Queue needs either screening_text or abstract")

    if "screening_basis" not in queue.columns:
        if "abstract_missing" in queue.columns:
            queue["screening_basis"] = queue["abstract_missing"].astype(str).map(
                {"0": "title+abstract", "1": "title-only", "0.0": "title+abstract", "1.0": "title-only"}
            ).fillna("")
        else:
            queue["screening_basis"] = queue["screening_text"].str.strip().ne("").map(
                {True: "title+abstract", False: "title-only"}
            )

    if "version_cluster_id" not in queue.columns:
        queue["version_cluster_id"] = ""

    return queue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queue",
        type=Path,
        default=ROOT / "data/samples/phase1_screening_sample_240.csv",
        help="CSV screening queue or committed Phase-1 sample",
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "annotations/screening_decisions.csv",
    )
    parser.add_argument("--reviewer", default="reviewer1")
    parser.add_argument(
        "--second-review-only",
        action="store_true",
        help="Screen only rows marked second_review_sample=1",
    )
    args = parser.parse_args()

    queue = load_queue(args.queue)

    if args.second_review_only:
        if "second_review_sample" not in queue.columns:
            raise ValueError("--second-review-only requires a second_review_sample column")
        mask = pd.to_numeric(queue["second_review_sample"], errors="coerce").fillna(0).astype(int) == 1
        queue = queue[mask].copy()

    if args.decisions.exists():
        decisions = pd.read_csv(args.decisions).fillna("")
    else:
        decisions = pd.DataFrame(columns=[
            "candidate_id", "decision", "reason", "reviewer", "adjudication_status"
        ])

    done = set(decisions.loc[decisions["reviewer"] == args.reviewer, "candidate_id"])
    remaining = queue[~queue["candidate_id"].isin(done)]

    print("SynthSift screening protocol: protocols/screening_protocol_v1.md")
    print("Keys: [i]nclude  [e]xclude  [u]ncertain  [s]kip  [q]uit")
    print(f"Reviewer: {args.reviewer} | completed: {len(done & set(queue['candidate_id']))} | remaining: {len(remaining)}")
    if args.second_review_only:
        print("Mode: blinded second-review subset (other reviewers' decisions are not displayed)")

    args.decisions.parent.mkdir(parents=True, exist_ok=True)

    for _, row in remaining.iterrows():
        print("\n" + "=" * 90)
        print(
            f"{row['candidate_id']}  {row['screening_basis']}  "
            f"cluster={row['version_cluster_id'] or '-'}"
        )
        print(row["title"])
        text = row["screening_text"] or "[No abstract available: title-only screening]"
        print("\n" + textwrap.fill(str(text), width=100))

        while True:
            choice = input("\nDecision [i/e/u/s/q]: ").strip().lower()
            if choice in {"i", "e", "u", "s", "q"}:
                break
        if choice == "q":
            break
        if choice == "s":
            continue

        decision = {"i": "include", "e": "exclude", "u": "uncertain"}[choice]
        reason = input("Reason (brief, protocol-grounded): ").strip()
        new = pd.DataFrame([{
            "candidate_id": row["candidate_id"],
            "decision": decision,
            "reason": reason,
            "reviewer": args.reviewer,
            "adjudication_status": "",
        }])
        decisions = pd.concat([decisions, new], ignore_index=True)
        decisions.to_csv(args.decisions, index=False)

    print(f"Saved decisions to {args.decisions}")


if __name__ == "__main__":
    main()
