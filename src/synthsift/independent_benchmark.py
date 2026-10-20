"""Independent human-reference benchmark for saved, source-fingerprinted LLM screening runs.

No API access, and no implicit conversion of AI-first-pass labels into human truth.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

from synthsift.llm_runner import canonical, digest

BINARY = {"include", "exclude"}


def rows(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: required columns missing: {sorted(required)}")
        return list(reader)


def unique(records: list[dict], field: str, what: str) -> dict[str, dict]:
    found = {}
    for record in records:
        key = (record.get(field) or "").strip()
        if not key or key in found:
            raise ValueError(f"{what}: blank or duplicate {field}: {key!r}")
        found[key] = record
    return found


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(success: int, n: int) -> list[float | None]:
    """Unadjusted 95% Wilson binomial interval; not a population-generalisation CI."""
    if not n:
        return [None, None]
    z = 1.959963984540054
    p = success / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    rad = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, mid - rad), min(1.0, mid + rad)]


def _segment(items: list[dict]) -> dict:
    positives = sum(r["reference"] == "include" for r in items)
    negatives = len(items) - positives
    tp = sum(r["reference"] == "include" and r["prediction"] == "include" for r in items)
    fp = sum(r["reference"] == "exclude" and r["prediction"] == "include" for r in items)
    tn = sum(r["reference"] == "exclude" and r["prediction"] == "exclude" for r in items)
    fn = sum(r["reference"] == "include" and r["prediction"] == "exclude" for r in items)
    review = sum(r["prediction"] in {"uncertain", "error"} for r in items)
    auto = tn + fn
    return {
        "n": len(items), "reference_positive": positives, "reference_negative": negatives,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "model_abstentions_or_errors": review,
        "auto_excluded": auto, "auto_exclusion_fraction": auto / len(items) if items else None,
        "auto_exclusion_false_negative_fraction": fn / auto if auto else None,
        "auto_exclusion_false_negative_wilson95": wilson(fn, auto),
        "eligible_retention_with_human_review": (positives - fn) / positives if positives else None,
        "eligible_retention_wilson95": wilson(positives - fn, positives),
        "model_only_recall_on_determinate_predictions":
            tp / (tp + fn) if tp + fn else None,
        "model_only_precision_on_determinate_predictions":
            tp / (tp + fp) if tp + fp else None,
        "potential_auto_exclusion_only": True,
        "zero_missed_eligible_gate": fn == 0 if positives else None,
    }


def evaluate(sample_path: Path, reference_path: Path, manifest_path: Path,
             ledger_path: Path, config_path: Path) -> dict:
    """Fail closed on provenance, missing IDs, changed texts, and synthetic/replayed outputs."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("kind") != "synthsift_independent_human_reference_v1"
            or manifest.get("blinding_attested") is not True
            or not str(manifest.get("attested_by", "")).strip()
            or manifest.get("all_reference_decisions_binary") is not True
            or manifest.get("double_review_complete") is not True
            or manifest.get("reference_sha256") != sha(reference_path)
            or manifest.get("sample_sha256") != sha(sample_path)):
        raise ValueError("Missing or invalid independent human-reference attestation or file hashes")

    sample = rows(sample_path, {"candidate_id", "title", "abstract", "second_review_sample"})
    reference = rows(reference_path, {"candidate_id", "final_decision", "reviewers_n"})
    s = unique(sample, "candidate_id", "sample")
    r = unique(reference, "candidate_id", "reference")
    if not s or set(r) != set(s):
        raise ValueError("Reference must cover exactly the frozen sample without duplicate IDs")
    if len(s) != manifest.get("reference_count"):
        raise ValueError("Reference count does not match attested manifest")
    for key, ref in r.items():
        if ref["final_decision"] not in BINARY:
            raise ValueError(f"{key}: only resolved binary human decisions can be scored")
        if int(ref["reviewers_n"]) < (2 if s[key]["second_review_sample"] == "1" else 1):
            raise ValueError(f"{key}: required independent human reviews missing")
    if manifest.get("double_review_count") != sum(
        x["second_review_sample"] == "1" for x in sample
    ):
        raise ValueError("Second review subset is not fully accounted for")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not all(k in config for k in ("model", "prompt_sha256", "prompt_version",
                                   "temperature", "input_manifest_sha256")):
        raise ValueError("Run configuration has missing provenance fields")
    input_recs = [
        {"candidate_id": x["candidate_id"], "title": x["title"].strip(),
         "abstract": x["abstract"].strip()} for x in sample
    ]
    if config["input_manifest_sha256"] != digest(canonical(input_recs)):
        raise ValueError("LLM run was not performed on this exact frozen sample and order")
    if config["model"].lower().startswith(("synthetic", "fixture", "demo")):
        raise ValueError("Synthetic screening cannot yield independent model-accuracy claims")

    predictions = []
    with ledger_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                predictions.append(json.loads(line))
    pred = unique(predictions, "candidate_id", "LLM ledger")
    if set(pred) != set(s):
        raise ValueError("Missing or extra LLM predictions; coverage must be complete")

    aligned = []
    for item in sample:
        key = item["candidate_id"]
        p = pred[key]
        source = {"candidate_id": key, "title": item["title"].strip(),
                  "abstract": item["abstract"].strip()}
        if p.get("input_sha256") != digest(canonical(source)):
            raise ValueError(f"{key}: source fingerprint mismatch")
        if p.get("provider") != "openai":
            raise ValueError(f"{key}: fixture/replay/non-live provider is not independently scored")
        if any(p.get(k) != config[k] for k in ("model", "prompt_version", "temperature")):
            raise ValueError(f"{key}: model configuration differs from run_config")
        if p.get("prompt_sha256") != config["prompt_sha256"]:
            raise ValueError(f"{key}: prompt fingerprint differs from run_config")
        if p.get("status") == "ok":
            output = p.get("output")
            if not isinstance(output, dict) or output.get("decision") not in {
                "include", "exclude", "uncertain"
            } or output.get("abstain") is not (output["decision"] == "uncertain"):
                raise ValueError(f"{key}: malformed decision or abstention")
            decision = output["decision"]
        elif p.get("status") == "error" and p.get("output") is None:
            decision = "error"
        else:
            raise ValueError(f"{key}: unrecognised inference status")
        aligned.append({
            "candidate_id": key, "reference": r[key]["final_decision"],
            "prediction": decision, "source_basis": "title_only" if not source["abstract"]
            else "title_abstract",
        })

    result = {
        "kind": "synthsift_independent_human_evaluation_v1",
        "reference_scope": "human-reviewed frozen search sample; not full-text systematic-review truth",
        "run_provenance": {
            "model": config["model"], "prompt_version": config["prompt_version"],
            "sample_sha256": sha(sample_path), "reference_sha256": sha(reference_path),
            "reference_manifest_sha256": sha(manifest_path),
            "llm_ledger_sha256": sha(ledger_path), "run_config_sha256": sha(config_path),
            "attestation": manifest["attested_by"], "provider": "openai",
        },
        "overall": _segment(aligned),
        "by_source_basis": {
            basis: _segment([x for x in aligned if x["source_basis"] == basis])
            for basis in ("title_only", "title_abstract")
        },
        "interpretation": (
            "Auto-exclusion fraction is a potential workload proxy, NOT an achieved workload "
            "saving. Any missed eligible study blocks an unqualified safe-automation claim. "
            "Wilson intervals reflect sampling variability only; this OpenAlex-ranked sample "
            "is not a representative systematic-search corpus. No calibration claim is made."
        ),
        "errors_to_review": [x["candidate_id"] for x in aligned if x["prediction"] == "error"],
        "false_exclusion_ids": [
            x["candidate_id"] for x in aligned
            if x["reference"] == "include" and x["prediction"] == "exclude"
        ],
        "model_abstention_ids": [
            x["candidate_id"] for x in aligned if x["prediction"] == "uncertain"
        ],
    }
    return result
