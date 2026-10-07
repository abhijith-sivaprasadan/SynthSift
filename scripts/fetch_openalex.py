#!/usr/bin/env python
"""Retrieve a dated OpenAlex candidate corpus using SynthSift search protocol v1.

This script reproduces the acquisition *process*. The committed dated snapshot is
the fixed benchmark because OpenAlex relevance rankings can change over time.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from synthsift.openalex import deduplicate, flatten_openalex_work, title_clusters

FIELDS = [
    "candidate_id", "openalex_id", "doi", "title", "publication_year",
    "publication_date", "work_type", "language", "abstract", "abstract_missing",
    "landing_page_url", "query_arms", "best_rank", "screening_decision",
    "screening_reason", "reviewer", "adjudication_status",
]


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_arm(session: requests.Session, config: dict, arm: str, mailto: str | None) -> dict:
    params = {
        "filter": f"title_and_abstract.search:{config['query_prefix']} {arm}",
        "per-page": int(config["per_page"]),
        "select": ",".join(config["select"]),
    }
    if mailto:
        params["mailto"] = mailto
    response = session.get(config["base_url"], params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **{k: row.get(k, "") for k in FIELDS},
                "abstract_missing": 0 if row.get("abstract") else 1,
                "query_arms": ";".join(sorted(row.get("query_arms") or [])),
                "screening_decision": "",
                "screening_reason": "",
                "reviewer": "",
                "adjudication_status": "",
            })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config/search_v1.json")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--mailto", help="Optional contact email for OpenAlex polite-pool usage")
    parser.add_argument("--shard-size", type=int, default=75)
    args = parser.parse_args()

    config = load_config(args.config)
    output = args.output_dir or ROOT / "data/search" / f"openalex_snapshot_{config['snapshot_date']}"

    session = requests.Session()
    session.headers.update({"User-Agent": "SynthSift/0.2 (research-methods pilot)"})

    raw = []
    arm_meta = []
    for arm in config["query_arms"]:
        payload = fetch_arm(session, config, arm, args.mailto)
        results = payload.get("results", [])
        arm_meta.append({
            "term": arm,
            "query": f"{config['query_prefix']} {arm}",
            "openalex_total_count": payload.get("meta", {}).get("count"),
            "retrieved": len(results),
        })
        for rank, work in enumerate(results, start=1):
            raw.append(flatten_openalex_work(work, arm, rank))

    records = deduplicate(raw)
    output.mkdir(parents=True, exist_ok=True)

    for old in output.glob("records_*.csv"):
        old.unlink()
    for start in range(0, len(records), args.shard_size):
        write_csv(output / f"records_{start // args.shard_size + 1:03d}.csv", records[start:start + args.shard_size])

    clusters = title_clusters(records)
    with (output / "version_clusters.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "cluster_id", "normalized_title", "candidate_ids", "dois",
            "publication_years", "titles",
        ])
        writer.writeheader()
        for idx, cluster in enumerate(clusters, start=1):
            members = cluster["members"]
            writer.writerow({
                "cluster_id": f"VC{idx:03d}",
                "normalized_title": cluster["normalized_title"],
                "candidate_ids": ";".join(str(x["candidate_id"]) for x in members),
                "dois": ";".join(str(x.get("doi") or "") for x in members if x.get("doi")),
                "publication_years": ";".join(str(x.get("publication_year") or "") for x in members if x.get("publication_year")),
                "titles": " | ".join(str(x.get("title") or "") for x in members),
            })

    years = [int(r["publication_year"]) for r in records if str(r.get("publication_year", "")).isdigit() and int(r["publication_year"]) > 0]
    manifest = {
        "snapshot_date": config["snapshot_date"],
        "source": "OpenAlex",
        "query_arms": arm_meta,
        "raw_records": len(raw),
        "deduplicated_records": len(records),
        "records_with_abstract": sum(bool(r.get("abstract")) for r in records),
        "records_without_abstract": sum(not bool(r.get("abstract")) for r in records),
        "english_language_flag": sum(r.get("language") == "en" for r in records),
        "publication_year_min": min(years) if years else None,
        "publication_year_max": max(years) if years else None,
        "duplicate_title_clusters": len(clusters),
        "records_in_duplicate_title_clusters": sum(len(c["members"]) for c in clusters),
        "deduplication": "normalized DOI when present; otherwise OpenAlex work ID",
        "note": "Ranked top-N records per query arm; candidate corpus, not exhaustive systematic search.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
