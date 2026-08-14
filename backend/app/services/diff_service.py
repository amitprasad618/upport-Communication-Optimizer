
from difflib import SequenceMatcher
import re
from typing import List, Dict, Any


def _tokenize_with_spaces(text: str) -> List[str]:
    """Split text into a list of tokens where whitespace is preserved as separate tokens.

    This preserves spacing and punctuation when reconstructing segments.
    """
    if text is None:
        return []
    # Split into runs of whitespace or non-whitespace
    return re.findall(r"\s+|[^\s]+", text)


def generate_segments(original: str, revised: str) -> List[Dict[str, Any]]:
    """Generate structured diff segments between original and revised texts.

    Each segment is a dict with a `type` key: one of `unchanged`, `added`,
    `removed`, or `replaced`.

    - `unchanged`: {"type": "unchanged", "text": "..."}
    - `removed`: {"type": "removed", "text": "..."}
    - `added`: {"type": "added", "text": "..."}
    - `replaced`: {"type": "replaced", "original": "...", "text": "..."}

    The function uses a word/whitespace tokenization and difflib.SequenceMatcher
    to produce stable, human-friendly segments the frontend can render.
    """
    a = _tokenize_with_spaces(original or "")
    b = _tokenize_with_spaces(revised or "")

    sm = SequenceMatcher(None, a, b)
    segments: List[Dict[str, Any]] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        left = ''.join(a[i1:i2])
        right = ''.join(b[j1:j2])
        if tag == 'equal':
            segments.append({"type": "unchanged", "text": left})
        elif tag == 'delete':
            segments.append({"type": "removed", "text": left})
        elif tag == 'insert':
            segments.append({"type": "added", "text": right})
        elif tag == 'replace':
            # Represent replace as a single segment with original and new text
            segments.append({"type": "replaced", "original": left, "text": right})

    return segments


__all__ = ["generate_segments"]
