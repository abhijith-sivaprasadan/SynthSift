# Search protocol v1.0

**Frozen:** 7 October 2026  
**Source:** OpenAlex  
**Purpose:** create a real search-derived candidate corpus for SynthSift title/abstract screening experiments.

This protocol is deliberately broader than the original 16-record hand-curated pilot. Its purpose is to generate a realistic mixture of eligible studies, irrelevant records and difficult near-misses. It is **not** presented as an exhaustive systematic-review search.

## Query arms

Each query is applied to OpenAlex's `title_and_abstract.search` field and retrieves the top 100 records in OpenAlex relevance order:

1. `heat pump adoption`
2. `heat pump uptake`
3. `heat pump household`
4. `heat pump consumer`
5. `heat pump willingness`
6. `heat pump barrier`

The exact machine-readable configuration is in `config/search_v1.json`.

## Retrieval and preservation

For each record, preserve:

- OpenAlex work ID;
- DOI where available;
- title;
- publication year/date;
- work type;
- OpenAlex language flag;
- abstract reconstructed from OpenAlex's abstract inverted index;
- primary landing-page URL;
- query arm(s) that retrieved the record;
- best within-arm relevance rank.

Records without an OpenAlex abstract are retained as title-only screening records rather than silently removed.

## Deduplication

Exact deduplication is performed using:

1. normalized DOI when present;
2. otherwise OpenAlex work ID.

Different DOIs are **not** automatically merged even when titles match, because report, preprint, conference and journal versions may represent different bibliographic records. Instead, a second-pass normalized-title clustering step flags potential publication/version duplicates for human adjudication.

## Language

No language filter is applied at acquisition. This keeps the acquisition layer separate from any later eligibility restriction and exposes the effect of language metadata on screening.

## Relationship to screening protocol

Eligibility decisions use `protocols/screening_protocol_v1.md`. Acquisition terms are not eligibility criteria. A record retrieved through an adoption-related query can still be excluded after screening, and a title-only record can be marked uncertain pending additional information.

## Scope limitation

Because OpenAlex relevance-ranking can change as its index changes, this repository commits a dated snapshot. Re-running the same code later reproduces the **process**, not necessarily the exact 2026-10-07 rank order. The committed snapshot is the fixed benchmark candidate set.
