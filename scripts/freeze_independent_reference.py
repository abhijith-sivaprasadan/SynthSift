#!/usr/bin/env python
"""Freeze independently reviewed 240/96 sample; never derive labels from AI-ledger files."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from synthsift.independent_benchmark import rows, unique, sha, BINARY

VALID = BINARY | {"uncertain"}


def freeze(sample_path: Path, decisions_path: Path, adjudicated_path: Path | None,
           protocol_path: Path, reference_path: Path, attested_by: str) -> dict:
    sample = rows(sample_path, {"candidate_id", "title", "second_review_sample"})
    s = unique(sample, "candidate_id", "sample")
    if not s:
        raise ValueError("Frozen sample is empty")
    if not any(x["second_review_sample"] == "1" for x in sample):
        raise ValueError("Frozen sample lacks an independent second-review subset")
    decisions = rows(decisions_path, {"candidate_id", "decision", "reason", "reviewer"})
    by_id = defaultdict(dict)
    for d in decisions:
        key, reviewer = d["candidate_id"].strip(), d["reviewer"].strip()
        if key not in s or not reviewer or d["decision"] not in VALID or not d["reason"].strip():
            raise ValueError("Human review contains missing reason, invalid reviewer/decision, or unknown ID")
        if any(token in reviewer.lower() for token in ("gpt", "llm", "assistant", "fixture")):
            raise ValueError("AI-attributed decisions cannot be frozen as human reference")
        if reviewer in by_id[key]:
            raise ValueError(f"{key}: multiple decisions from reviewer {reviewer}")
        by_id[key][reviewer] = d["decision"]
    adjudicated = {}
    if adjudicated_path:
        adj = rows(adjudicated_path, {"candidate_id", "final_decision", "adjudication_reason"})
        adjudicated = unique(adj, "candidate_id", "adjudications")
        if not set(adjudicated).issubset(s):
            raise ValueError("Adjudications contain an unknown candidate")
        for key, a in adjudicated.items():
            if a["final_decision"] not in BINARY or not a["adjudication_reason"].strip():
                raise ValueError(f"{key}: adjudication must be binary and include a reason")
    out = []
    need_adjudication = []
    second_n = 0
    for item in sample:
        key = item["candidate_id"]
        reviews = by_id[key]
        second = item["second_review_sample"] == "1"
        if second:
            second_n += 1
        if len(reviews) < (2 if second else 1):
            raise ValueError(f"{key}: incomplete {'second' if second else 'first'} human review")
        distinct = set(reviews.values())
        ambiguous = len(distinct) > 1 or "uncertain" in distinct
        if ambiguous and key not in adjudicated:
            need_adjudication.append(key)
            continue
        final = adjudicated[key]["final_decision"] if key in adjudicated else next(iter(distinct))
        if final not in BINARY:
            raise ValueError(f"{key}: unresolved reference class")
        out.append({
            "candidate_id": key, "final_decision": final,
            "reviewers_n": len(reviews),
            "review_resolution": "adjudicated" if key in adjudicated else "agreement",
        })
    if need_adjudication:
        raise ValueError(
            f"{len(need_adjudication)} ambiguous records require independent adjudication: "
            + ", ".join(need_adjudication[:12])
        )
    if not attested_by.strip():
        raise ValueError("A named human attestor is required")
    if not protocol_path.is_file():
        raise ValueError("Frozen screening protocol file missing")
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = reference_path.with_suffix(".manifest.json")
    if reference_path.exists() or manifest_path.exists():
        raise ValueError("Reference or manifest already exists; choose a new version, do not overwrite")
    with reference_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "candidate_id", "final_decision", "reviewers_n", "review_resolution"
        ])
        writer.writeheader()
        writer.writerows(out)
    manifest = {
        "kind": "synthsift_independent_human_reference_v1",
        "reference_count": len(out), "double_review_count": second_n,
        "all_reference_decisions_binary": True, "double_review_complete": True,
        "blinding_attested": True, "attested_by": attested_by.strip(),
        "attestation_scope": (
            "Attestor confirms decisions were made by named human reviewers using source "
            "titles/abstracts and frozen protocol, without consulting AI-generated screening "
            "recommendations for these records. Independent second review performed where flagged."
        ),
        "sample_sha256": sha(sample_path), "reference_sha256": sha(reference_path),
        "protocol_sha256": sha(protocol_path), "human_annotation_sha256": sha(decisions_path),
        "adjudication_sha256": sha(adjudicated_path) if adjudicated_path else None,
        "source_ai_predictions_used_as_reference": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"reference": str(reference_path), "manifest": str(manifest_path),
            "records": len(out), "second_reviewed": second_n}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample", type=Path, default=ROOT / "data/samples/phase1_screening_sample_240.csv")
    p.add_argument("--decisions", type=Path, default=ROOT / "annotations/screening_decisions.csv")
    p.add_argument("--adjudicated", type=Path)
    p.add_argument("--protocol", type=Path, default=ROOT / "protocols/screening_protocol_v1.md")
    p.add_argument("--out", type=Path, default=ROOT / "data/labels/phase1_independent_v1.csv")
    p.add_argument("--attestor", required=True, help="Human reviewer attesting to AI-blind protocol review")
    p.add_argument("--attest-blind-human-review", action="store_true", required=True,
                   help="Confirm decisions were made by humans independently of AI first-pass labels")
    args = p.parse_args()
    try:
        result = freeze(args.sample, args.decisions, args.adjudicated, args.protocol,
                        args.out, args.attestor)
    except (OSError, ValueError) as exc:
        print(f"Cannot freeze independent reference: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
