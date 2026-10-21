#!/usr/bin/env python
"""Freeze a prespecified AI-blind, stratified 80/32 pilot from the 240/96 reference plan.

Deterministic source-only selection, not a scientific accuracy result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from synthsift.independent_benchmark import sha

SEED = "20261021-synthsift-sei-empirical-pilot-v1"
TARGETS = {0: 48, 1: 32}
SOURCE = ROOT / "data/samples/phase1_screening_sample_240.csv"
DEFAULT_OUT = ROOT / "data/samples/validation_pilot_80_v1.csv"


def rank_id(candidate_id: str) -> str:
    return hashlib.sha256((SEED + "|" + candidate_id).encode("utf-8")).hexdigest()


def select(source: pd.DataFrame) -> pd.DataFrame:
    needed = {"candidate_id", "title", "abstract", "sampling_stratum", "second_review_sample"}
    if not needed.issubset(source.columns):
        raise ValueError(f"Source lacks required columns: {sorted(needed - set(source.columns))}")
    if source["candidate_id"].isna().any() or source["candidate_id"].duplicated().any():
        raise ValueError("Blank or duplicate source candidate IDs")
    if any(x not in (0, 1) for x in source["second_review_sample"]):
        raise ValueError("Second-review sample flag must be 0 or 1")
    if any(not str(s).strip() for s in source["sampling_stratum"]):
        raise ValueError("Missing source-defined sampling stratum")
    if len(source) != 240 or int(source["second_review_sample"].sum()) != 96:
        raise ValueError("Source is not the frozen 240/96 reference plan")
    for col in ("decision", "reviewer", "reason", "adjudication_status"):
        if col in source and source[col].fillna("").astype(str).str.strip().ne("").any():
            raise ValueError("Refuse to draw pilot from a sample containing existing judgments")
    chosen = set()
    for flag, target in TARGETS.items():
        block = source.loc[source["second_review_sample"] == flag]
        n = len(block)
        groups = {stratum: sorted(group["candidate_id"].tolist(), key=lambda k: (rank_id(k), k))
                  for stratum, group in block.groupby("sampling_stratum")}
        quotas = {}
        fractional = []
        for stratum, ids in groups.items():
            exact = target * len(ids) / n
            base = int(exact)
            quotas[stratum] = base
            fractional.append((exact - base, stratum))
        remaining = target - sum(quotas.values())
        for _, stratum in sorted(fractional, key=lambda x: (-x[0], x[1]))[:remaining]:
            quotas[stratum] += 1
        for stratum, ids in groups.items():
            chosen.update(ids[:quotas[stratum]])
    pilot = source.loc[source["candidate_id"].isin(chosen)].copy()
    if len(pilot) != 80 or int(pilot["second_review_sample"].sum()) != 32:
        raise AssertionError("Pilot membership or second-review count is incorrect")
    return pilot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true", help="Check frozen CSV and manifest without writing")
    args = parser.parse_args()
    try:
        source = pd.read_csv(args.source, dtype={"candidate_id": str}).fillna("")
        source["second_review_sample"] = source["second_review_sample"].astype(int)
        pilot = select(source)
        raw_csv = pilot.to_csv(index=False, lineterminator="\n").encode("utf-8")
        manifest = {
            "kind": "synthsift_prespecified_ai_blind_empirical_pilot_v1",
            "source_sample_sha256": sha(args.source),
            "pilot_sha256": hashlib.sha256(raw_csv).hexdigest(),
            "seed": SEED, "selection": "largest remainder by original sampling_stratum "
                "within independent original second-review strata; SHA-256 source-only ranking",
            "n": 80, "double_review_n": 32,
            "second_review_original_flag_reused": True,
            "used_ai_labels_predictions_scores": False,
            "frozen_reference_source": "data/samples/phase1_screening_sample_240.csv",
            "scientific_limit": "small exploratory pilot; no claims until independent human review "
                "and real-model inference",
        }
        manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
        metadata = args.out.with_suffix(".manifest.json")
        for path, content in ((args.out, raw_csv), (metadata, manifest_bytes)):
            if args.check:
                if not path.is_file() or path.read_bytes() != content:
                    raise ValueError(f"Frozen pilot differs from recomputed source: {path}")
            else:
                if path.exists() and path.read_bytes() != content:
                    raise ValueError(f"Refusing to overwrite different frozen pilot: {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        print(json.dumps({"status": "verified" if args.check else "frozen",
                          "path": str(args.out), "records": 80,
                          "second_review_records": 32, "sha256": manifest["pilot_sha256"]}, indent=2))
        return 0
    except (OSError, ValueError, AssertionError) as exc:
        print(f"Pilot preparation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
