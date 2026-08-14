from app.services.diff_service import generate_segments


def _flatten_text(segments):
    out = []
    for s in segments:
        if s["type"] == "replaced":
            out.append(s["original"])
            out.append(s["text"])
        else:
            out.append(s.get("text", ""))
    return "".join(out)


def test_word_replacement():
    orig = "Please fix the setting."
    rev = "Please correct the setting."
    segs = generate_segments(orig, rev)
    # ensure a replaced segment exists
    assert any(s["type"] == "replaced" for s in segs)


def test_phrase_replacement():
    orig = "I will get back to you shortly."
    rev = "I will respond to you shortly."
    segs = generate_segments(orig, rev)
    assert any(s["type"] == "replaced" for s in segs)


def test_deletion():
    orig = "This is unnecessary text."
    rev = ""
    segs = generate_segments(orig, rev)
    assert any(s["type"] == "removed" for s in segs)


def test_addition():
    orig = "Please check."
    rev = "Please check. Thank you."
    segs = generate_segments(orig, rev)
    assert any(s["type"] == "added" for s in segs)


def test_unchanged_text():
    orig = "No changes here."
    rev = "No changes here."
    segs = generate_segments(orig, rev)
    assert len(segs) == 1 and segs[0]["type"] == "unchanged"


def test_punctuation_changes():
    orig = "Check this, please."
    rev = "Check this please!"
    segs = generate_segments(orig, rev)
    # allow either replaced or combination
    assert any(s["type"] in ("replaced", "removed", "added") for s in segs)
