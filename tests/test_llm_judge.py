"""B06/B12/B13: LLM output validation, deterministic options, and explicit fallback reporting (LLM is mocked)."""
import json

import pytest
import requests

from backend import config
from backend.llm.judge import LLMOutputError, evaluate_hallucination, parse_llm_output

CTX = "[telephone.txt]: Bell received a patent for the telephone in 1876."


@pytest.mark.parametrize("raw, expected", [
    ('{"verdict": "Supported", "confidence": 0.9, "reason": "Matches context."}', "Supported"),
    ('{"verdict": " hallucinated ", "confidence": 0.7, "reason": "x"}', "Hallucinated"),
    ('{"verdict": "insufficient_evidence", "confidence": 0.4, "reason": "x"}', "Insufficient Evidence"),
    ('Sure! Here it is: {"verdict": "Supported", "confidence": 1, "reason": "y"} Hope that helps.', "Supported"),
    ('```json\n{"verdict": "Hallucinated", "confidence": 0.8, "reason": "z"}\n```', "Hallucinated"),
])
def test_valid_outputs_are_parsed_and_normalised(raw, expected):
    assert parse_llm_output(raw)["verdict"] == expected


@pytest.mark.parametrize("raw", [
    "",                                                                   # empty
    "   ",                                                                # whitespace
    "I think it is supported.",                                           # no JSON
    '{"verdict": "Supported", "confidence": 0.9',                         # truncated JSON
    "[1, 2, 3]",                                                          # not an object
    "{}",                                                                 # missing fields
    '{"verdict": null, "confidence": 0.5, "reason": "r"}',                # null
    '{"verdict": "Partially supported", "confidence": 0.5, "reason": "r"}',  # unexpected label
    '{"verdict": "Supported", "confidence": 85, "reason": "r"}',          # out of range
    '{"verdict": "Supported", "confidence": 0.8, "reason": ""}',          # empty reason
    '{"verdict": "Supported", "confidence": "high", "reason": "r"}',      # wrong type
])
def test_invalid_outputs_raise(raw):
    with pytest.raises(LLMOutputError):
        parse_llm_output(raw)


def test_valid_llm_answer_reports_llm_engine(fake_ollama):
    fake_ollama(json.dumps({"verdict": "Hallucinated", "confidence": 0.93, "reason": "Year differs."}))
    out = evaluate_hallucination("q", "Bell patented it in 1877.", CTX)
    assert out["verdict"] == "Hallucinated"
    assert out["engine"] == "llm"
    assert out["model"] == f"ollama:{config.OLLAMA_MODEL}"
    assert out["fallback_reason"] is None


def test_request_uses_configured_url_and_deterministic_options(fake_ollama, monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_URL", "http://ollama.internal:11434")
    calls = fake_ollama(json.dumps({"verdict": "Supported", "confidence": 0.9, "reason": "ok"}))
    evaluate_hallucination("q", "r", CTX)
    call = calls[0]
    assert call["url"] == "http://ollama.internal:11434/api/generate"
    assert call["json"]["format"] == "json"
    assert call["json"]["stream"] is False
    assert call["json"]["options"]["temperature"] == 0.0
    assert call["json"]["options"]["seed"] == config.LLM_SEED
    assert call["timeout"] == config.OLLAMA_TIMEOUT_SECONDS


@pytest.mark.parametrize("behaviour, reason", [
    (requests.ConnectionError("refused"), "llm_unavailable"),
    (requests.Timeout("slow"), "llm_unavailable"),
    (404, "llm_unavailable"),          # e.g. model not pulled
    (500, "llm_unavailable"),
    ("not json at all", "llm_invalid_output"),
    ('{"verdict": "Maybe", "confidence": 0.5, "reason": "r"}', "llm_invalid_output"),
    ("{}", "llm_invalid_output"),
])
def test_failures_fall_back_to_rules_and_say_why(fake_ollama, behaviour, reason):
    fake_ollama(behaviour)
    out = evaluate_hallucination("q", "Bell patented the telephone in 1876.", CTX)
    assert out["engine"] == "heuristic"
    assert out["model"] == config.HEURISTIC_ENGINE_NAME
    assert out["fallback_reason"] == reason
    assert out["verdict"] == "Supported"  # decided by the rules, not invented


@pytest.mark.parametrize("body", [["not", "an", "object"], {"response": {"verdict": "Supported"}}])
def test_unexpected_ollama_body_falls_back_instead_of_crashing(monkeypatch, body):
    import backend.llm.judge as judge_mod
    from conftest import FakeResponse
    monkeypatch.setattr(judge_mod.requests, "post", lambda *a, **k: FakeResponse(payload=body))
    monkeypatch.setattr(config, "USE_LLM", True)
    out = evaluate_hallucination("q", "Bell patented the telephone in 1876.", CTX)
    assert (out["engine"], out["fallback_reason"]) == ("heuristic", "llm_invalid_output")


def test_llm_disabled_is_reported(monkeypatch):
    monkeypatch.setattr(config, "USE_LLM", False)
    out = evaluate_hallucination("q", "Bell patented the telephone in 1876.", CTX)
    assert (out["engine"], out["fallback_reason"]) == ("heuristic", "llm_disabled")
