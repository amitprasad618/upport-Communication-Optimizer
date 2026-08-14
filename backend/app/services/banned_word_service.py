import json
from pathlib import Path
from typing import List, Dict, Any

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "banned_words.json"


def load_rules() -> List[Dict[str, Any]]:
    """Load rule objects from the JSON config file.

    Returns a list of rule dicts with keys: term, category, severity, replacement, reason, contextual
    """
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        rules = data.get("rules", [])
        # Normalize and validate minimal shape
        normalized = []
        for r in rules:
            term = r.get("term")
            if not term:
                continue
            normalized.append({
                "term": term,
                "category": r.get("category", "unknown"),
                "severity": r.get("severity", "low"),
                "replacement": r.get("replacement", ""),
                "reason": r.get("reason", ""),
                "contextual": bool(r.get("contextual", False)),
            })
        return normalized
    except Exception:
        return []


def find_matches(text: str) -> List[Dict[str, Any]]:
    """Detect all rule matches in `text`.

    Matching is case-insensitive and returns a list of matches with:
      - term, start, end, category, severity, replacement, reason, contextual

    For contextual rules, we do NOT modify the text here — return metadata only.
    Deterministic rules are safe suggestions for replacement but not applied here.
    """
    if not text:
        return []

    rules = load_rules()
    lowered = text.lower()
    matches: List[Dict[str, Any]] = []

    for rule in rules:
        term = rule["term"]
        term_lower = term.lower()
        start = 0
        while True:
            idx = lowered.find(term_lower, start)
            if idx == -1:
                break
            end = idx + len(term_lower)
            # Preserve original-cased match slice
            original_match = text[idx:end]
            matches.append({
                "term": term,
                "matched_text": original_match,
                "start": idx,
                "end": end,
                "category": rule.get("category"),
                "severity": rule.get("severity"),
                "replacement": rule.get("replacement"),
                "reason": rule.get("reason"),
                "contextual": bool(rule.get("contextual", False)),
            })
            # allow overlapping matches by moving start by 1
            start = idx + 1

    # Sort matches by start index
    matches.sort(key=lambda m: m["start"])
    return matches


__all__ = ["load_rules", "find_matches"]
