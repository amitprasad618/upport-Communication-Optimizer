import pytest

from app.services.banned_word_service import load_rules, find_matches


def test_load_rules_basic():
    rules = load_rules()
    assert isinstance(rules, list)
    assert any(r["term"] == "I'll surely" for r in rules)


def test_find_matches_simple():
    text = "I'll surely take care of this. The AdSpam team reviewed it. Actually, it's fine. I affirm the result."
    matches = find_matches(text)
    terms = [m["term"] for m in matches]
    assert "I'll surely" in terms
    assert "AdSpam team" in terms
    assert "Actually" in terms
    assert "I affirm" in terms

    # Ensure start/end indices correspond to slices
    for m in matches:
        s = m["start"]
        e = m["end"]
        assert text[s:e].lower() == m["matched_text"].lower()


def test_contextual_flag():
    text = "Actually, please ignore."
    matches = find_matches(text)
    assert any(m["term"] == "Actually" and m["contextual"] for m in matches)
