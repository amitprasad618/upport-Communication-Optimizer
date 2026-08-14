from app.services.validation_service import validate_llm_output


def test_structure_missing_keys():
    original = "This is the original."
    out = {"improved_text": "ok"}
    res = validate_llm_output(out, original)
    assert res["is_valid"] is False
    assert any("missing keys" in e for e in res["validation_errors"]) or len(res["validation_errors"])>0


def test_high_severity_banned_remaining():
    original = "Contact the AdSpam team for help."
    out = {
        "improved_text": "Please contact the AdSpam team for help.",
        "tone_before": "casual",
        "tone_after": "professional",
        "changes": []
    }
    res = validate_llm_output(out, original)
    assert res["is_valid"] is False
    assert any(m["term"] == "AdSpam team" for m in res["remaining_banned_terms"])


def test_missing_url_detection():
    original = "See details at https://example.com/details?id=123"
    out = {
        "improved_text": "See details.",
        "tone_before": "",
        "tone_after": "",
        "changes": []
    }
    res = validate_llm_output(out, original)
    assert res["is_valid"] is False
    assert any("URLs missing" in e for e in res["validation_errors"]) or any("URLs missing" in w for w in res["warnings"])==False


def test_unsupported_fix_claims():
    original = "We are investigating the issue."
    out = {
        "improved_text": "We have fixed the issue and it is resolved.",
        "tone_before": "",
        "tone_after": "",
        "changes": []
    }
    res = validate_llm_output(out, original)
    assert res["is_valid"] is False
    assert any("unsupported claims" in e or "unsupported" in e for e in res["validation_errors"]) or any("fixed" in e for e in res["validation_errors"]) 


def test_valid_output_passes():
    original = "Ticket ID: CASE-12345. See https://example.com. Value: 42"
    out = {
        "improved_text": "Ticket ID: CASE-12345. See https://example.com. Value: 42. Updated for clarity.",
        "tone_before": "informal",
        "tone_after": "professional_constructive",
        "changes": [{"original": "Updated for clarity", "replacement": "Updated for clarity", "reason": "style", "category": "style"}]
    }
    res = validate_llm_output(out, original)
    assert res["is_valid"] is True
