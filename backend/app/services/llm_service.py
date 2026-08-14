import os
import json
import time
import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class ChangeItemModel(BaseModel):
    original: str = Field(description="The original text or phrase that was modified or removed")
    replacement: str = Field(description="The replacement text or phrase")
    reason: str = Field(description="Reason for making this change")
    category: str = Field(description="Category of the change: grammar, tone, banned_word, or clarity")


class OptimizationResponseModel(BaseModel):
    improved_text: str = Field(description="The complete rewritten and optimized message")
    tone_before: str = Field(description="Assessment of the initial tone")
    tone_after: str = Field(description="Assessment of the improved tone")
    changes: List[ChangeItemModel] = Field(description="List of all specific changes made")


# Fallback list of models available in your account
FALLBACK_MODELS = [
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]


def optimize_response(
    original_text: str,
    detected_rules: List[Dict[str, Any]],
    *,
    model: str = None,
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
        "Always return valid JSON matching the schema."
    )

    user_prompt = (
        f"Original message:\n{original_text}\n\n"
        f"Detected rules (JSON):\n{json.dumps(detected_rules, ensure_ascii=False, indent=2)}\n\n"
        "Optimize the original message according to the rules and schema."
    )

    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import ServerError, APIError

        client = genai.Client(api_key=api_key)
        
        # Build candidate models to try in sequence
        candidate_models = [model] if model else []
        for m in FALLBACK_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        last_exception = None

        for candidate in candidate_models:
            for attempt in range(2):  # Try each model up to 2 times
                try:
                    logger.info(f"Attempting LLM call with model: {candidate} (attempt {attempt + 1})")
                    response = client.models.generate_content(
                        model=candidate,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instructions,
                            temperature=0.2,
                            response_mime_type="application/json",
                            response_schema=OptimizationResponseModel,
                        )
                    )

                    # 1. Use SDK parsed Pydantic object
                    if getattr(response, "parsed", None) is not None:
                        return response.parsed.model_dump()

                    # 2. Fallback parse
                    if response.text:
                        text = response.text.strip()
                        if text.startswith("```json"):
                            text = text[7:]
                        elif text.startswith("```"):
                            text = text[3:]
                        if text.endswith("```"):
                            text = text[:-3]
                        return json.loads(text.strip())

                except ServerError as se:
                    last_exception = se
                    logger.warning(f"Model {candidate} returned 503/server error: {se}. Retrying/falling back...")
                    time.sleep(1)  # Brief pause before retry or fallback
                except APIError as ae:
                    last_exception = ae
                    logger.warning(f"Model {candidate} API error: {ae}. Trying next fallback model...")
                    break  # Move to next model immediately for non-server errors

        # If all retries and fallback models failed
        raise LLMError(f"All candidate models failed. Last error: {str(last_exception)}")

    except ImportError:
        logger.exception("google-genai SDK not installed")
        raise LLMError("Missing dependency: Run `pip install google-genai`")
    except Exception as e:
        logger.exception("Gemini API processing failed: %s", str(e))
        raise LLMError(f"LLM processing error: {str(e)}")


__all__ = ["optimize_response", "LLMError"]