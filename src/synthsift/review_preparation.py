"""Prepare bibliographic evidence and review packs. Never adjudicate study identity or eligibility.

All provisional AI labels stay isolated from human-reference screening.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import pandas as pd

from synthsift.full_corpus_review import ROOT, SNAPSHOT, load_full_corpus, read_csv

OUT = ROOT / "data/review_preparation"
CUE_UPTAKE = ("adopt", "uptake", "diffus", "accept", "willing", "choic", "prefer", "barrier")
CUE_HOUSEHOLD = ("household", "residential", "domestic", "homeowner", "homes", "home heating")


def source_link(row: pd.Series) -> tuple[str, str]:
    """Return a *locator*, not a verified accessible/full-text document."""
    doi = str(row["doi"]).strip()
    if doi:
        return "https://doi.org/" + quote(doi, safe="/:.()-_"), "doi_resolver_unchecked"
    site = str(row["source_url"]).strip()
    if site.startswith(("https://", "http://")):
        return site, "source_landing_unchecked"
    openalex = str(row["openalex_id"]).strip()
    if openalex.startswith(("https://", "http://")):
        return openalex, "openalex_record_unchecked"
    return "", "no_source_locator"


def build_review_packs() -> tuple[dict[str, pd.DataFrame], dict]:
    original = load_full_corpus()
    df = original.copy()
    locators = df.apply(source_link, axis=1)
    df["lookup_url"] = [item[0] for item in locators]
    df["lookup_kind"] = [item[1] for item in locators]
    df["external_full_text_verified"] = "no"
    df["independent_human_review_done"] = "no"
    df["study_identity_adjudicated"] = "no"
    df["requires_source_recheck"] = (
        df["screening_basis"].eq("title-only")
        & df["decision"].isin(["include", "uncertain"])
    ).map({True: "yes", False: "no"})
    source_columns = [
        "candidate_id", "title", "publication_year", "work_type", "language",
        "doi", "openalex_id", "source_url", "lookup_url", "lookup_kind",
        "screening_basis", "decision", "reason", "reviewer",
        "potential_version_clusters", "priority_flags", "phase1_sample",
        "second_review_sample", "requires_source_recheck",
        "external_full_text_verified", "study_identity_adjudicated",
        "independent_human_review_done",
    ]
    inventory = df[source_columns].copy()

    cluster_data = read_csv(SNAPSHOT / "version_clusters.csv")
    if cluster_data["cluster_id"].duplicated().any():
        raise ValueError("Duplicate version cluster IDs in frozen source")
    source_by_id = {row["candidate_id"]: row for _, row in df.iterrows()}
    cluster_rows = []
    members = set()
    for _, group in cluster_data.iterrows():
        ids = group["candidate_ids"].split(";")
        if len(ids) < 2 or any(i not in source_by_id for i in ids):
            raise ValueError("Cluster has missing source candidate or fewer than two entries")
        if members.intersection(ids):
            raise ValueError("Candidate appears in two distinct version clusters")
        members.update(ids)
        matched = [source_by_id[i] for i in ids]
        decisions = [str(item["decision"]) for item in matched]
        cluster_rows.append({
            "cluster_id": group["cluster_id"],
            "normalized_title": group["normalized_title"],
            "candidate_ids": group["candidate_ids"],
            "doi_values": ";".join(str(item["doi"]) for item in matched),
            "publication_years": ";".join(str(item["publication_year"]) for item in matched),
            "ai_decision_sequence": ";".join(decisions),
            "ai_decision_disagreement": "yes" if len(set(decisions)) > 1 else "no",
            "title_only_records": str(sum(item["screening_basis"] == "title-only" for item in matched)),
            "source_locators": " | ".join(source_link(item)[0] for item in matched),
            "study_identity_resolution": "unresolved",
            "canonical_record_id": "",
            "independent_adjudication": "not_performed",
            "note": "Normalized-title match is a candidate version family, NOT a confirmed same-study finding.",
        })
    families = pd.DataFrame(cluster_rows)
    if set(members) != set(
        df.loc[df["potential_version_clusters"].ne(""), "candidate_id"]
    ):
        raise ValueError("Cluster membership disagrees with screened ledger")

    # This is an extraction *staging* list, not extracted evidence.
    staging = df.loc[df["decision"].isin(["include", "uncertain"]), [
        "candidate_id", "title", "decision", "screening_basis", "lookup_url",
        "lookup_kind", "potential_version_clusters", "priority_flags",
    ]].reset_index(drop=True)
    staging["full_text_acquired"] = "no"
    staging["study_inclusion_adjudicated"] = "no"
    staging["population_extracted"] = ""
    staging["design_extracted"] = ""
    staging["adoption_determinant_extracted"] = ""
    staging["effect_estimate_extracted"] = ""
    staging["risk_of_bias_assessed"] = "no"
    staging["extraction_status"] = "not_started"

    # Never use these weak keyword cues as eligibility criteria or automatic correction.
    def audit_flags(row: pd.Series) -> str:
        title = str(row["title"]).lower()
        flags = []
        if any(word in title for word in CUE_UPTAKE):
            flags.append("adoption_word_in_excluded_title")
        if any(word in title for word in CUE_HOUSEHOLD):
            flags.append("household_word_in_excluded_title")
        if row["screening_basis"] == "title-only":
            flags.append("excluded_on_title_only")
        return ";".join(flags)

    excluded = df.loc[df["decision"].eq("exclude"), [
        "candidate_id", "title", "decision", "reason", "screening_basis",
        "lookup_url", "lookup_kind", "potential_version_clusters",
    ]].copy()
    excluded["audit_flags"] = excluded.apply(audit_flags, axis=1)
    excluded["audit_priority"] = excluded["audit_flags"].map(
        lambda v: "high" if (
            "adoption_word_in_excluded_title" in v
            and "household_word_in_excluded_title" in v
        ) else "standard"
    )
    excluded["independent_false_negative_audit"] = "not_performed"
    excluded = excluded.reset_index(drop=True)

    stats = {
        "source": "frozen OpenAlex 2026-10-07; AI first pass 2026-10-20",
        "status": "review preparation, not human adjudication or full-text acquisition",
        "source_inventory": len(inventory),
        "potential_version_clusters": len(families),
        "clustered_candidate_records": len(members),
        "clusters_with_discordant_AI_recommendations": int(
            families["ai_decision_disagreement"].eq("yes").sum()
        ),
        "candidate_records_pending_evidence_extraction": len(staging),
        "ai_includes": int(staging["decision"].eq("include").sum()),
        "ai_uncertain": int(staging["decision"].eq("uncertain").sum()),
        "candidate_records_needing_source_recheck": int(
            inventory["requires_source_recheck"].eq("yes").sum()
        ),
        "ai_exclusions_awaiting_independent_false_negative_audit": len(excluded),
        "ai_exclusions_with_both_adoption_and_household_title_cues": int(
            excluded["audit_priority"].eq("high").sum()
        ),
        "full_text_verified": 0,
        "study_level_deduplications_adjudicated": 0,
        "independent_human_reference_review_complete": False,
        "independent_second_review_complete": False,
    }
    return {
        "source_inventory.csv": inventory,
        "version_family_review.csv": families,
        "provisional_evidence_extraction_queue.csv": staging,
        "excluded_record_audit_queue.csv": excluded,
    }, stats
