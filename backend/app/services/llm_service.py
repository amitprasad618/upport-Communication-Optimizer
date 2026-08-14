import os
import json
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMError(Exception):
    pass

def _extract_and_parse_json(text: str) -> Dict[str, Any]:
    if not text:
        raise LLMError("Empty response from LLM")

    s = text.strip()
    # Strip markdown code blocks if the model adds them
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    s = s.strip()

    try:
        return json.loads(s)
    except Exception:
        # Fallback substring search
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end+1])
            except Exception:
                pass
        raise LLMError("LLM response did not contain valid JSON")

def optimize_response(
    original_text: str,
    detected_rules: List[Dict[str, Any]],
    *,
    model: str = "gemini-3.5-flash",
    timeout: int = 30
) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not configured in .env")

    system_instructions = (
        "You are a Support Communication Optimization Assistant.\n"
        "Improve customer/publisher-facing support responses.\n"
        "MUST preserve technical meaning, factual information, product names, metrics, dates, IDs, URLs, and troubleshooting steps.\n"
        "MUST NOT invent facts, troubleshooting steps, or resolutions.\n"
        "Improve grammar, clarity, professionalism, and constructiveness.\n"
        "For contextual banned words, decide based on context whether to remove or rewrite.\n"
        "For deterministic banned terms, apply the provided replacement.\n"
        "Return valid JSON only with keys: improved_text, tone_before, tone_after, changes.\n"
        "Do not include any explanatory text outside the JSON."
    )

    user_prompt = (
        f"Original message:\n{original_text}\n\n"
        f"Detected rules (JSON):\n{json.dumps(detected_rules, ensure_ascii=False, indent=2)}\n\n"
        "Instructions: Return ONLY valid JSON matching the schema with keys: "
        "'improved_text', 'tone_before', 'tone_after', and 'changes'."
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instructions,
                temperature=0.2,
                response_mime_type="application/json",
            )
        )

        if not response.text:
            raise LLMError("Empty response received from Gemini API")

        return _extract_and_parse_json(response.text)

    except ImportError:
        logger.exception("google-genai SDK not installed")
        raise LLMError("Missing dependency: Run `pip install google-genai`")
    except Exception as e:
        logger.exception("Gemini API request failed: %s", str(e))
        raise LLMError(f"LLM processing error: {str(e)}")

__all__ = ["optimize_response", "LLMError"]