#!/usr/bin/env python
"""Evaluate a real LLM run against a frozen, independently human-reviewed sample."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from synthsift.independent_benchmark import evaluate


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample", type=Path, default=ROOT / "data/samples/phase1_screening_sample_240.csv")
    p.add_argument("--reference", type=Path, default=ROOT / "data/labels/phase1_independent_v1.csv")
    p.add_argument("--manifest", type=Path, help="Reference attestation manifest; defaults to reference .manifest.json")
    p.add_argument("--ledger", type=Path, required=True, help="screening.jsonl from a live run")
    p.add_argument("--run-config", type=Path, help="run_config.json; defaults to alongside --ledger")
    p.add_argument("--out", type=Path, default=ROOT / "results/independent_benchmark.json")
    args = p.parse_args()
    manifest = args.manifest or args.reference.with_suffix(".manifest.json")
    config = args.run_config or args.ledger.parent / "run_config.json"
    try:
        report = evaluate(args.sample, args.reference, manifest, args.ledger, config)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("Independent benchmark unavailable: " + str(exc), file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Wrote " + str(args.out), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
