from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_analyze_success(monkeypatch, client):
    original = "Please contact the AdSpam team about CASE-123."

    def fake_optimize(original_text, detected_rules):
        return {
            "improved_text": "Please contact the Trust & Safety team about CASE-123.",
            "tone_before": "casual",
            "tone_after": "professional_constructive",
            "changes": [
                {"original": "AdSpam team", "replacement": "Trust & Safety team", "reason": "terminology", "category": "terminology"}
            ]
        }

    monkeypatch.setattr("app.services.llm_service.optimize_response", fake_optimize)

    resp = client.post("/api/analyze", json={"text": original})
    assert resp.status_code == 200
    body = resp.json()
    assert body["original_text"] == original
    assert "Trust & Safety team" in body["improved_text"]
    assert isinstance(body["diff"], list)


def test_analyze_llm_error(monkeypatch, client):
    original = "Some text here"

    def fake_optimize(original_text, detected_rules):
        from app.services.llm_service import LLMError

        raise LLMError("simulated")

    monkeypatch.setattr("app.services.llm_service.optimize_response", fake_optimize)

    resp = client.post("/api/analyze", json={"text": original})
    assert resp.status_code == 502
    data = resp.json()
    assert data.get("detail") == "LLM service error"


def test_analyze_validation_failure(monkeypatch, client):
    original = "Please contact the AdSpam team."  # high severity term

    def fake_optimize(original_text, detected_rules):
        # Return a response that still contains the high-severity term
        return {
            "improved_text": "Please contact the AdSpam team.",
            "tone_before": "",
            "tone_after": "",
            "changes": []
        }

    monkeypatch.setattr("app.services.llm_service.optimize_response", fake_optimize)

    resp = client.post("/api/analyze", json={"text": original})
    assert resp.status_code == 422
    data = resp.json()
    # detail should be the safe response dict we constructed
    assert isinstance(data.get("detail"), dict)
    assert data["detail"]["validation"]["is_valid"] is False
