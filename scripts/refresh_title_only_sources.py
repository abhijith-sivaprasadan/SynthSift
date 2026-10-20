#!/usr/bin/env python
"""Optional live bibliographic follow-up for high-risk title-only AI decisions.

Uses OpenAlex only. The resulting metadata is NOT full-text retrieval or eligibility review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from synthsift.source_refresh import refresh_title_only_priority


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("results/openalex_refresh_20261020.csv"))
    p.add_argument("--limit", type=int, default=87)
    p.add_argument("--allow-live", action="store_true", required=True)
    args = p.parse_args()
    if not 1 <= args.limit <= 87:
        raise SystemExit("--limit must be 1..87")
    df, stats = refresh_title_only_priority(limit=args.limit)
    if df.empty or len(df) != args.limit or df["candidate_id"].duplicated().any():
        raise ValueError("Incomplete/malformed live metadata check")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    args.out.with_suffix(".json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf8"
    )
    print(json.dumps(stats, indent=2))
    print("CAUTION: metadata location and abstract flags do not prove publisher access/full-text or adoption eligibility.")


if __name__ == "__main__":
    main()
