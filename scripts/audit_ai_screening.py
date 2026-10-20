#!/usr/bin/env python
"""Audit machine-generated title/abstract decisions separately from human labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from synthsift.ai_review import load_ai_screening, summary_for


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results/ai_first_pass"))
    args = parser.parse_args()
    df = load_ai_screening()
    summary = summary_for(df)
    args.out.mkdir(parents=True, exist_ok=True)
    # Preserve the frozen sample order, original source text, and annotation reasons.
    cols = [
        "candidate_id", "title", "abstract_missing", "decision", "reason", "reviewer",
        "potential_version_clusters", "review_priority", "second_review_sample",
        "doi", "openalex_id", "publication_year", "language",
    ]
    df[cols].to_csv(args.out / "ai_decisions_240.csv", index=False)
    df.loc[df["review_priority"].ne(""), cols].to_csv(
        args.out / "human_review_priority.csv", index=False
    )
    with (args.out / "summary.json").open("w", encoding="utf8") as stream:
        json.dump(summary, stream, indent=2)
        stream.write("\n")
    print(json.dumps(summary, indent=2))
    print(f"Results: {args.out}")
    print("IMPORTANT: machine labels have NOT been frozen into data/labels or human reference files.")


if __name__ == "__main__":
    main()
