from __future__ import annotations

from collections import defaultdict
from math import floor
from typing import Iterable

import pandas as pd


def fnv1a32(text: str) -> int:
    """Deterministic 32-bit FNV-1a hash used to avoid RNG/version drift."""
    value = 0x811C9DC5
    for char in text:
        value ^= ord(char)
        value = (value * 0x01000193) & 0xFFFFFFFF
    return value


def sampling_stratum(row: pd.Series) -> str:
    abstract = str(row.get("abstract", "") or "").strip()
    basis = "abstract" if abstract else "title_only"
    rank = int(row["best_rank"])
    band = "01_20" if rank <= 20 else "21_50" if rank <= 50 else "51_100"
    return f"{basis}__{band}"


def proportional_quotas(sizes: dict[str, int], total: int) -> dict[str, int]:
    population = sum(sizes.values())
    if total > population:
        raise ValueError("sample size cannot exceed population")
    details = []
    for key, size in sizes.items():
        exact = total * size / population
        base = floor(exact)
        details.append([key, size, base, exact - base])
    remaining = total - sum(item[2] for item in details)
    details.sort(key=lambda item: (-item[3], item[0]))
    for idx in range(remaining):
        details[idx][2] += 1
    return {key: base for key, _, base, _ in details}


def deterministic_stratified_sample(
    frame: pd.DataFrame,
    total: int,
    seed: str,
) -> tuple[pd.DataFrame, dict[str, int]]:
    df = frame.copy()
    df["sampling_stratum"] = df.apply(sampling_stratum, axis=1)
    grouped = {key: part.copy() for key, part in df.groupby("sampling_stratum", sort=False)}
    quotas = proportional_quotas({key: len(part) for key, part in grouped.items()}, total)

    selected = []
    for key, part in grouped.items():
        part["_sample_hash"] = part["candidate_id"].map(
            lambda value: fnv1a32(f"{seed}|{value}")
        )
        part = part.sort_values(["_sample_hash", "candidate_id"])
        selected.append(part.head(quotas[key]))

    out = pd.concat(selected, ignore_index=True)
    out = out.drop(columns=["_sample_hash"]).sort_values(
        ["best_rank", "candidate_id"]
    ).reset_index(drop=True)
    return out, quotas
