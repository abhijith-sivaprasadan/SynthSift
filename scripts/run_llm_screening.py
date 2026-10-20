#!/usr/bin/env python
"""Run a versioned eligibility-screening pipeline (fixture, live OpenAI, or offline replay)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from synthsift.llm_runner import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["fixture", "openai", "replay"], default="fixture")
    parser.add_argument("--input", type=Path, default=ROOT / "data/llm_demo/citations_v1.csv")
    parser.add_argument("--config", type=Path, default=ROOT / "config/llm_screening_v1.json")
    parser.add_argument("--fixture", type=Path, default=ROOT / "data/llm_demo/fixture_responses_v1.json")
    parser.add_argument("--cache", type=Path, help="Prior successful screening.jsonl for --provider replay")
    parser.add_argument("--model", help="Override the provider model ID; replay must match recorded model")
    parser.add_argument("--out", type=Path, default=ROOT / "results/llm_demo")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        summary = run(input_file=args.input, out=args.out, cfg_file=args.config, provider=args.provider,
                      fixture_file=args.fixture, replay_file=args.cache, model_override=args.model,
                      resume=args.resume)
    except (ValueError, OSError) as exc:
        print("Screening setup failed: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    if summary["errors"]:
        print("Provider/validation errors: decisions were NOT accepted. See review_queue.csv", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
