#!/usr/bin/env python
"""Generate or audit source-based next-stage study-review worklists.

Does not contact journals, resolve DOI URLs, retrieve full text, or write human labels.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from synthsift.full_corpus_review import ROOT, read_csv
from synthsift.review_preparation import OUT, build_review_packs


def blind_reference_packets(destination: Path) -> None:
    """Source-only exports without AI recommendations or internal screening reasons."""
    sample = read_csv(ROOT / "data/samples/phase1_screening_sample_240.csv")
    cols = [
        "candidate_id", "title", "abstract", "abstract_missing", "doi", "openalex_id",
        "publication_year", "work_type", "language", "best_rank",
    ]
    if not all(sample[c].eq("").all() for c in ["decision", "reason", "reviewer"]):
        raise ValueError("Frozen human reference sample unexpectedly contains decisions")
    sample[cols].to_csv(destination / "blind_first_review_240.csv", index=False)
    second = sample.loc[sample["second_review_sample"].eq("1"), cols]
    if len(second) != 96:
        raise ValueError("Frozen second-review subset changed")
    second.to_csv(destination / "blind_second_review_96.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true", help="Compare outputs with committed worklists")
    parser.add_argument(
        "--export-blind", action="store_true",
        help="Create source-only human-review files in the specified output directory",
    )
    args = parser.parse_args()
    packs, stats = build_review_packs()
    if args.check:
        for file, frame in packs.items():
            saved = read_csv(args.out / file)
            pd.testing.assert_frame_equal(
                frame.reset_index(drop=True), saved.reset_index(drop=True),
                check_dtype=False,
            )
        previous = json.loads((args.out / "summary.json").read_text(encoding="utf8"))
        if previous != stats:
            raise ValueError("Published review preparation summary no longer matches sources")
        print("PASS: study-level preflight files reproduce from frozen sources")
    else:
        args.out.mkdir(parents=True, exist_ok=True)
        for file, frame in packs.items():
            frame.to_csv(args.out / file, index=False)
        (args.out / "summary.json").write_text(
            json.dumps(stats, indent=2) + "\n", encoding="utf8"
        )
    if args.export_blind:
        args.out.mkdir(parents=True, exist_ok=True)
        blind_reference_packets(args.out)
        print("Source-only, unlabelled human-review packets exported; AI fields excluded.")
    print(json.dumps(stats, indent=2))
    print("No full texts downloaded. No version family or eligibility adjudicated.")


if __name__ == "__main__":
    main()
