from typing import List


def validate_no_disallowed_terms(text: str, disallowed: List[str]) -> List[str]:
    """Return list of matched disallowed terms found in the text."""
    found = []
    lowered = text.lower()
    for term in disallowed:
        if term.lower() in lowered:
            found.append(term)
    return found
