"""Optional live OpenAlex metadata follow-up.

Never copy abstracts into repository or infer full-text access from an OpenAlex location.
"""
from __future__ import annotations
from datetime import datetime, timezone
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests

from synthsift.review_preparation import build_review_packs

OPENALEX = "https://api.openalex.org/works/"


def describe_response(source: pd.Series, data: dict, checked_utc: str) -> dict:
    expected = str(source["openalex_id"]).rsplit("/", 1)[-1]
    received = str(data.get("id") or "").rsplit("/", 1)[-1]
    if received != expected:
        return {
            "candidate_id": source["candidate_id"], "source_openalex_id": source["openalex_id"],
            "checked_utc": checked_utc, "status": "id_mismatch",
            "has_abstract_now": "unknown", "oa_landing_url": "",
            "abstract_index_terms": "", "note": "Returned work ID does not match frozen source",
        }
    abstract = data.get("abstract_inverted_index")
    oa = data.get("best_oa_location")
    link = oa.get("landing_page_url") if isinstance(oa, dict) else ""
    return {
        "candidate_id": source["candidate_id"], "source_openalex_id": source["openalex_id"],
        "checked_utc": checked_utc, "status": "metadata_returned",
        "has_abstract_now": "yes" if isinstance(abstract, dict) and abstract else "no",
        "oa_landing_url": link or "",
        "abstract_index_terms": str(len(abstract)) if isinstance(abstract, dict) else "0",
        "note": "Metadata-only check. No article/full-text or abstract copied; OA location not verified.",
    }


def refresh_title_only_priority(
    limit: int | None = None, sleep_seconds: float = 0.2
) -> tuple[pd.DataFrame, dict]:
    packs, _ = build_review_packs()
    sources = packs["source_inventory.csv"]
    target = sources[sources["requires_source_recheck"].eq("yes")].copy()
    if limit is not None:
        target = target.head(limit)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "SynthSift/0.2 (research metadata audit; https://github.com/abhijith-sivaprasadan/SynthSift)",
        "Accept": "application/json",
    })
    rows: list[dict] = []
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    key = os.environ.get("OPENALEX_API_KEY", "")
    for _, item in target.iterrows():
        value = str(item["openalex_id"]).rsplit("/", 1)[-1]
        row = {
            "candidate_id": item["candidate_id"], "source_openalex_id": item["openalex_id"],
            "checked_utc": stamp, "status": "", "has_abstract_now": "unknown",
            "oa_landing_url": "", "abstract_index_terms": "",
            "note": "",
        }
        if not re.fullmatch(r"W\d+", value):
            row["status"] = "invalid_source_id"
            row["note"] = "Frozen OpenAlex ID does not match expected work-ID structure"
        else:
            params = {"api_key": key} if key else {}
            for attempt in range(3):
                try:
                    response = session.get(OPENALEX + value, params=params, timeout=14)
                    if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    if response.status_code == 200:
                        row = describe_response(item, response.json(), stamp)
                    else:
                        row["status"] = f"http_{response.status_code}"
                        row["note"] = "OpenAlex API did not return verifiable metadata"
                    break
                except (requests.RequestException, ValueError) as exc:
                    row["status"] = "request_failed"
                    row["note"] = type(exc).__name__
                    if attempt < 2:
                        time.sleep(2 ** (attempt + 1))
        rows.append(row)
        time.sleep(sleep_seconds)
    result = pd.DataFrame(rows)
    stats = {
        "source": "Live OpenAlex metadata-only lookups (not publisher/full-text retrieval)",
        "checked_utc": stamp,
        "records_attempted": len(result),
        "metadata_returned": int(result["status"].eq("metadata_returned").sum()),
        "abstract_metadata_now_present": int(result["has_abstract_now"].eq("yes").sum()),
        "checks_not_successful": int(result["status"].ne("metadata_returned").sum()),
        "full_text_read_or_verified": 0,
        "machine_eligibility_reclassification_performed": 0,
    }
    return result, stats
