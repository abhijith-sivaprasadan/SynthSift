#!/usr/bin/env python
"""Minimal resumable terminal screener for SynthSift candidate records."""
from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=ROOT / "results/openalex_screening_queue.csv")
    parser.add_argument("--decisions", type=Path, default=ROOT / "annotations/screening_decisions.csv")
    parser.add_argument("--reviewer", default="reviewer1")
    args = parser.parse_args()

    if not args.queue.exists():
        raise FileNotFoundError(
            f"{args.queue} not found. Run scripts/build_screening_queue.py first."
        )

    queue = pd.read_csv(args.queue).fillna("")
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
    print(f"Reviewer: {args.reviewer} | completed: {len(done)} | remaining: {len(remaining)}")

    args.decisions.parent.mkdir(parents=True, exist_ok=True)

    for _, row in remaining.iterrows():
        print("\n" + "=" * 90)
        print(f"{row['candidate_id']}  {row['screening_basis']}  cluster={row['version_cluster_id'] or '-'}")
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
