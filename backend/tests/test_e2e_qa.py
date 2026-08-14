from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _post(client, text):
    return client.post("/api/analyze", json={"text": text})


def test_empty_input(client):
    # Pydantic should reject empty string (min_length enforced)
    resp = _post(client, "")
    assert resp.status_code == 422


def test_very_long_input(client):
    long_text = "x" * 6000
    resp = _post(client, long_text)
    assert resp.status_code == 422


def test_gemini_api_failure(monkeypatch, client):
    from app.services.llm_service import LLMError

    def fail_opt(original, detected):
        raise LLMError("simulated")

    monkeypatch.setattr("app.services.llm_service.optimize_response", fail_opt)
    resp = _post(client, "Some text for LLM")
    assert resp.status_code == 502


def test_invalid_gemini_response(monkeypatch, client):
    # LLM returns non-dict
    def bad_opt(original, detected):
        return "not a dict"

    monkeypatch.setattr("app.services.llm_service.optimize_response", bad_opt)
    resp = _post(client, "Hello with URL https://example.com and ID CASE-1")
    # validation should fail and return 422
    assert resp.status_code == 422


def test_remaining_banned_term_after_optimization(monkeypatch, client):
    # Return improved text that still contains a high severity banned term
    def opt(original, detected):
        return {"improved_text": original, "tone_before": "", "tone_after": "", "changes": []}

    monkeypatch.setattr("app.services.llm_service.optimize_response", opt)
    resp = _post(client, "Please contact the AdSpam team.")
    assert resp.status_code == 422


def test_preserve_urls_numbers_products(monkeypatch, client):
    original = "See https://example.com and ref CASE-123. ProductX needs 3 retries."

    def opt(original_text, detected_rules):
        return {
            "improved_text": "Please see https://example.com for CASE-123. ProductX requires 3 retries.",
            "tone_before": "casual",
            "tone_after": "professional_constructive",
            "changes": []
        }

    monkeypatch.setattr("app.services.llm_service.optimize_response", opt)
    resp = _post(client, original)
    assert resp.status_code == 200
    body = resp.json()
    assert body["validation"]["is_valid"] is True
