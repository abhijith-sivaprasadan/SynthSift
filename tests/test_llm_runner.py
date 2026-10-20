"""Acceptance tests: deterministic local demo, replay, provenance and provider error handling."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from synthsift.llm_runner import (
    OpenAIChatProvider, ProviderError, digest, canonical, fingerprint,
    load_config, messages, prompt_bundle, read_citations, run, validate_response,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/llm_screening_v1.json"
INPUT = ROOT / "data/llm_demo/citations_v1.csv"
FIXTURE = ROOT / "data/llm_demo/fixture_responses_v1.json"


def run_fixture(path: Path, **kw):
    return run(input_file=INPUT, out=path, cfg_file=CONFIG, provider="fixture", fixture_file=FIXTURE, **kw)


def test_offline_fixture_complete_and_repeatable(tmp_path):
    a = run_fixture(tmp_path / "demo")
    assert (a["records"], a["successful"], a["errors"], a["abstained"]) == (5, 5, 0, 1)
    assert a["counts"] == {"exclude": 2, "include": 2, "uncertain": 1}
    assert a["historical_538_labels_used"] is False
    assert a["fixture_is_real_model_inference"] is False
    ledger = tmp_path / "demo/screening.jsonl"
    before = ledger.read_bytes()
    assert len([json.loads(line) for line in before.decode().splitlines()]) == 5
    assert run_fixture(tmp_path / "demo", resume=True) == a
    assert ledger.read_bytes() == before
    queue = list(csv.DictReader((tmp_path / "demo/review_queue.csv").open()))
    assert [x["candidate_id"] for x in queue] == ["DEMO03"]
    assert queue[0]["status"] == "ok"


def test_offline_replay_verifies_exact_request_hash(tmp_path):
    run_fixture(tmp_path / "original")
    old = tmp_path / "original/screening.jsonl"
    out = run(input_file=INPUT, out=tmp_path / "replay", cfg_file=CONFIG, provider="replay",
              replay_file=old, model_override="synthetic-fixture-v1")
    assert out["successful"] == 5 and out["errors"] == 0
    rows = [json.loads(x) for x in (tmp_path / "replay/screening.jsonl").read_text().splitlines()]
    assert all(x["provider"] == "replay" and x["status"] == "ok" for x in rows)


def test_source_edit_invalidates_fixture_and_prevents_resume(tmp_path):
    run_fixture(tmp_path / "demo")
    text = INPUT.read_text().replace("grant awareness", "contractor training")
    altered = tmp_path / "edited.csv"
    altered.write_text(text)
    with pytest.raises(ValueError, match="different configuration"):
        run(input_file=altered, out=tmp_path / "demo", cfg_file=CONFIG, provider="fixture",
            fixture_file=FIXTURE, resume=True)
    other = run(input_file=altered, out=tmp_path / "new", cfg_file=CONFIG, provider="fixture", fixture_file=FIXTURE)
    assert other["errors"] == 1
    assert other["successful"] == 4


def test_untrusted_evidence_requires_literal_quote_and_fail_closed():
    rec = read_citations(INPUT)[0]
    row = {
        "decision": "exclude", "reason_category": "non_residential",
        "reason": "This is a synthetic unsupported assertion about an industrial setting.",
        "evidence_span": "no such phrase in the citation", "abstain": False,
    }
    with pytest.raises(ValueError, match="literal span"):
        validate_response(row, rec)
    row["evidence_span"] = "grant awareness"
    row["decision"] = "uncertain"
    with pytest.raises(ValueError, match="Abstain"):
        validate_response(row, rec)


def test_reject_duplicate_citations_and_injected_extra_columns(tmp_path):
    duplicate = tmp_path / "dup.csv"
    duplicate.write_text("candidate_id,title,abstract\nX,a,b\nX,c,d\n")
    with pytest.raises(ValueError, match="duplicate"):
        read_citations(duplicate)
    # Reference labels exist but cannot reach prompt construction.
    record = read_citations(INPUT)[0] | {"reference_label": "1", "user_secret": "do not send"}
    m = messages(record, prompt_bundle(load_config(CONFIG)))
    assert "reference_label" not in m[1]["content"]
    assert "do not send" not in m[1]["content"]


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self.payload = status, payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, replies):
        self.replies, self.calls = iter(replies), []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return next(self.replies)


def test_live_provider_retry_and_strict_structured_outputs():
    rec = read_citations(INPUT)[0]
    cfg = load_config(CONFIG)
    prompt = prompt_bundle(cfg)
    reply = json.loads(FIXTURE.read_text())["replies"][fingerprint(rec, "synthetic-fixture-v1", 0.0, prompt)["request_sha256"]]
    fake = FakeSession([
        FakeResponse(429, {}), FakeResponse(503, {}),
        FakeResponse(200, {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(reply)}}]}),
    ])
    delays = []
    provider = OpenAIChatProvider("test-key", session=fake, sleep=lambda x: delays.append(x))
    assert provider.screen(rec, prompt, "gpt-4o-mini", 0, 400) == reply
    assert delays == [1, 2]
    assert len(fake.calls) == 3
    _, request = fake.calls[0]
    assert request["json"]["response_format"]["json_schema"]["strict"] is True
    assert request["json"]["store"] is False
    assert request["json"]["temperature"] == 0


def test_non_retryable_error_is_not_an_exclusion():
    fake = FakeSession([FakeResponse(400, {"error": "bad input"})])
    p = OpenAIChatProvider("test-key", session=fake, sleep=lambda _: None)
    with pytest.raises(ProviderError, match="Nonretryable"):
        p.screen(read_citations(INPUT)[0], prompt_bundle(load_config(CONFIG)), "gpt-4o-mini", 0, 400)


def test_live_mode_requires_api_key_before_emitting_records(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        run(input_file=INPUT, out=tmp_path / "live", cfg_file=CONFIG, provider="openai")
    assert not (tmp_path / "live").exists()
