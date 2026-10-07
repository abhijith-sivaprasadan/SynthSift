from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstruct an OpenAlex abstract from its inverted index."""
    if not inverted_index:
        return ""
    max_pos = max((p for positions in inverted_index.values() for p in positions), default=-1)
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    text = " ".join(words).strip()
    text = re.sub(r"\s+([,.;:!?%\)\]])", r"\1", text)
    text = re.sub(r"([\(\[])\s+", r"\1", text)
    return text


def normalize_doi(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", str(value), flags=re.I).strip().lower()


def normalize_title(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value)).lower()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def flatten_openalex_work(work: dict[str, Any], query_arm: str, rank: int) -> dict[str, Any]:
    primary = work.get("primary_location") or {}
    year = work.get("publication_year")
    if not isinstance(year, int) or year <= 0:
        year = ""
    return {
        "openalex_id": work.get("id") or "",
        "doi": normalize_doi(work.get("doi")),
        "title": work.get("title") or "",
        "publication_year": year,
        "publication_date": work.get("publication_date") or "",
        "work_type": work.get("type") or "",
        "language": work.get("language") or "",
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "landing_page_url": primary.get("landing_page_url") or "",
        "query_arms": {query_arm},
        "best_rank": int(rank),
    }


def deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Exact deduplication by DOI, falling back to OpenAlex ID."""
    merged: dict[str, dict[str, Any]] = {}
    for record in records:
        doi = normalize_doi(record.get("doi"))
        key = f"doi:{doi}" if doi else str(record.get("openalex_id") or "")
        if not key:
            continue
        if key not in merged:
            copy = dict(record)
            copy["doi"] = doi
            copy["query_arms"] = set(record.get("query_arms") or [])
            merged[key] = copy
            continue
        current = merged[key]
        current["query_arms"].update(record.get("query_arms") or [])
        current["best_rank"] = min(int(current["best_rank"]), int(record["best_rank"]))
        if not current.get("abstract") and record.get("abstract"):
            current["abstract"] = record["abstract"]
        if not current.get("landing_page_url") and record.get("landing_page_url"):
            current["landing_page_url"] = record["landing_page_url"]
    out = list(merged.values())
    out.sort(key=lambda r: (int(r["best_rank"]), str(r.get("title") or "").lower()))
    for idx, record in enumerate(out, start=1):
        record["candidate_id"] = f"OA{idx:04d}"
    return out


def title_clusters(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = normalize_title(record.get("title"))
        if key:
            grouped[key].append(record)
    clusters = []
    for normalized_title, members in grouped.items():
        if len(members) < 2:
            continue
        clusters.append({"normalized_title": normalized_title, "members": members})
    clusters.sort(key=lambda x: (-len(x["members"]), x["normalized_title"]))
    return clusters
