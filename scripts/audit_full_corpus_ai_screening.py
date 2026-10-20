#!/usr/bin/env python
"""Reconstruct complete OpenAlex 538-record AI triage without claiming human labels."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

from synthsift.full_corpus_review import load_full_corpus, summary

ROOT = Path(__file__).resolve().parents[1]


def verify_committed(df: pd.DataFrame, result: dict) -> None:
    base = ROOT / "data/ai_screening"
    ledger = pd.read_csv(base / "full_corpus_ai_assisted_v1.csv", dtype=str, keep_default_na=False)
    priority = pd.read_csv(
        base / "full_corpus_review_priority_v1.csv", dtype=str, keep_default_na=False
    )
    expected_priority = df.loc[df["priority_flags"].ne("")]
    pd.testing.assert_frame_equal(ledger, df, check_dtype=False)
    pd.testing.assert_frame_equal(priority, expected_priority, check_dtype=False)
    published = json.loads((base / "full_corpus_summary_v1.json").read_text(encoding="utf8"))
    if result != published:
        raise ValueError("Committed full-corpus summary no longer matches frozen source/decisions")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail when committed output differs")
    parser.add_argument("--out", type=Path, default=Path("results/full_corpus_ai"))
    args = parser.parse_args()
    df = load_full_corpus()
    report = summary(df)
    if args.check:
        verify_committed(df, report)
        print("Full 538-case AI screen, source provenance, priority file and summary checked.")
    else:
        args.out.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.out / "full_corpus_ai_assisted_v1.csv", index=False)
        df.loc[df["priority_flags"].ne("")].to_csv(
            args.out / "full_corpus_review_priority_v1.csv", index=False
        )
        (args.out / "summary.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf8"
        )
        print(f"Generated auditable output in {args.out}")
    print(json.dumps(report, indent=2))
    print("These are AI recommendations, NOT gold labels or completed human screening.")


if __name__ == "__main__":
    main()
