import re
from typing import Dict, Any, List

from app.services.banned_word_service import find_matches


def _extract_urls(text: str) -> List[str]:
    # simple URL regex
    url_re = re.compile(r"https?://[\w\-\.\?\,\'/\+&%\$#=~:;:@!()]+")
    return url_re.findall(text or "")


def _extract_numbers(text: str) -> List[str]:
    # integers and floats (keep punctuation like commas/dots)
    num_re = re.compile(r"\b\d[\d,\.]*\b")
    return num_re.findall(text or "")


def _extract_ids(text: str) -> List[str]:
    # heuristic: tokens with letters+digits or long digit sequences
    tokens = re.findall(r"\b[\w\-]{4,}\b", text or "")
    ids = [t for t in tokens if re.search(r"\d", t) and len(t) >= 4]
    return ids


def _extract_product_like_tokens(text: str) -> List[str]:
    # heuristic: words with an uppercase letter inside (e.g., ProductName)
    tokens = re.findall(r"\b[A-Za-z0-9\-\._]{3,}\b", text or "")
    products = [t for t in tokens if re.search(r"[A-Z]", t)]
    # dedupe preserving order
    seen = set()
    out = []
    for p in products:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def validate_llm_output(llm_output: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    """Validate LLM output against practical safeguards.

    Returns a dict with keys:
      - is_valid: bool
      - remaining_banned_terms: list
      - warnings: list
      - validation_errors: list
    """
    result = {
        "is_valid": True,
        "remaining_banned_terms": [],
        "warnings": [],
        "validation_errors": [],
    }

    # Basic structure validation
    if not isinstance(llm_output, dict):
        result["is_valid"] = False
        result["validation_errors"].append("LLM output is not a JSON object")
        return result

    # Required keys
    required_keys = ["improved_text", "tone_before", "tone_after", "changes"]
    missing = [k for k in required_keys if k not in llm_output]
    if missing:
        result["is_valid"] = False
        result["validation_errors"].append(f"LLM output is missing keys: {missing}")
        return result

    improved = llm_output.get("improved_text") or ""
    if not isinstance(improved, str) or not improved.strip():
        result["is_valid"] = False
        result["validation_errors"].append("improved_text is empty or not a string")
        return result

    # 1) Check banned terms still exist in improved_text
    matches = find_matches(improved)
    result["remaining_banned_terms"] = matches

    # 2) High-severity banned terminology remains
    high = [m for m in matches if (m.get("severity") or "").lower() == "high"]
    if high:
        result["is_valid"] = False
        result["validation_errors"].append("High-severity banned terms remain in improved_text")

    # 3) Important original information appears to have been removed
    # URLs
    orig_urls = _extract_urls(original_text)
    missing_urls = [u for u in orig_urls if u not in improved]
    if missing_urls:
        result["is_valid"] = False
        result["validation_errors"].append(f"URLs missing from improved_text: {missing_urls}")

    # Numbers
    orig_numbers = _extract_numbers(original_text)
    # filter out common small numbers like years? Keep all for now
    missing_numbers = [n for n in orig_numbers if n not in improved]
    if missing_numbers:
        result["is_valid"] = False
        result["validation_errors"].append(f"Numeric values missing from improved_text: {missing_numbers}")

    # IDs
    orig_ids = _extract_ids(original_text)
    missing_ids = [i for i in orig_ids if i not in improved]
    if missing_ids:
        result["is_valid"] = False
        result["validation_errors"].append(f"IDs missing from improved_text: {missing_ids}")

    # Product-like tokens
    prod_tokens = _extract_product_like_tokens(original_text)
    missing_prods = [p for p in prod_tokens if p not in improved]
    if missing_prods:
        result["warnings"].append(f"Product-like tokens missing from improved_text: {missing_prods}")

    # 4) Detect obvious unsupported additions (claims of fix/resolution)
    unsupported_patterns = [r"\b(issue (is )?fixed)\b", r"\b(we (have )?fixed)\b", r"\b(resolved|has been resolved)\b", r"\b(root cause)\b"]
    added_unsupported = []
    lowered_orig = (original_text or "").lower()
    lowered_improved = improved.lower()
    for pat in unsupported_patterns:
        if re.search(pat, lowered_improved) and not re.search(pat, lowered_orig):
            added_unsupported.append(pat)
    if added_unsupported:
        result["is_valid"] = False
        result["validation_errors"].append("Improved text contains unsupported claims or fixes: " + ", ".join(added_unsupported))

    # 5) improved_text not empty already validated

    # 6) Validate that LLM returned expected structure types
    if not isinstance(llm_output.get("changes"), list):
        result["is_valid"] = False
        result["validation_errors"].append("'changes' must be a list")

    return result


__all__ = ["validate_llm_output"]
