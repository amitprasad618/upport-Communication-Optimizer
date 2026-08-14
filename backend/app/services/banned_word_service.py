import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "banned_words.json"


def load_banned_words():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(w.lower() for w in data.get("banned_words", []))
    except Exception:
        return set()
