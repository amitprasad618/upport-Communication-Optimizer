from fastapi import APIRouter
import importlib
import os

router = APIRouter()


@router.get("/diagnose")
def diagnose():
    """Return a safe diagnostic about local LLM configuration.

    Does NOT expose secrets. Helps debug common causes of 502 LLM errors:
    - whether a compatible GenAI SDK is importable
    - whether GEMINI_API_KEY is present in the process environment
    - current ALLOWED_ORIGINS value
    """
    sdk_candidates = [
        "google.generativeai",
        "google.genai",
        "google_genai",
    ]
    sdk_available = False
    available_name = None
    for name in sdk_candidates:
        try:
            importlib.import_module(name)
            sdk_available = True
            available_name = name
            break
        except Exception:
            continue

    return {
        "sdk_available": sdk_available,
        "sdk_name": available_name,
        "gemini_api_key_present": bool(os.getenv("GEMINI_API_KEY")),
        "allowed_origins": os.getenv("ALLOWED_ORIGINS", ""),
    }
