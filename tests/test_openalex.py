from synthsift.openalex import reconstruct_abstract, normalize_doi, normalize_title, deduplicate


def test_reconstruct_abstract():
    inv = {"Heat": [0], "pumps": [1], "matter": [2], ".": [3]}
    assert reconstruct_abstract(inv) == "Heat pumps matter."


def test_normalizers():
    assert normalize_doi("https://doi.org/10.1234/ABC") == "10.1234/abc"
    assert normalize_title("The Economic Determinants of Heat-Pump Adoption!") == (
        "the economic determinants of heat pump adoption"
    )


def test_deduplicate_merges_query_arms():
    rows = [
        {"doi": "10.1/x", "openalex_id": "A", "title": "x", "query_arms": {"adoption"}, "best_rank": 4, "abstract": "", "landing_page_url": ""},
        {"doi": "https://doi.org/10.1/X", "openalex_id": "A", "title": "x", "query_arms": {"barrier"}, "best_rank": 2, "abstract": "text", "landing_page_url": "url"},
    ]
    out = deduplicate(rows)
    assert len(out) == 1
    assert out[0]["query_arms"] == {"adoption", "barrier"}
    assert out[0]["best_rank"] == 2
    assert out[0]["abstract"] == "text"
