import logging
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.banned_word_service import find_matches
from app.services import llm_service
from app.services.validation_service import validate_llm_output
from app.services.diff_service import generate_segments

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    original_text = req.text

    # 1. Detect banned words
    detected = find_matches(original_text)

    # 2. Call LLM with original + detected rules
    try:
        llm_resp = llm_service.optimize_response(original_text, detected)
    except llm_service.LLMError as e:
        logger.error(f"LLM optimization failed: {e}", exc_info=True)
        # Pass the actual message so you can debug in Swagger
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal error: {str(e)}")

    # 3. Validate LLM output
    llm_resp_safe = llm_resp if isinstance(llm_resp, dict) else {}
    validation = validate_llm_output(llm_resp_safe, original_text)

    # 4. Generate independent diff
    diff = generate_segments(original_text, llm_resp_safe.get("improved_text", ""))

    response = {
        "original_text": original_text,
        "improved_text": llm_resp_safe.get("improved_text", ""),
        "detected_issues": detected,
        "changes": llm_resp_safe.get("changes", []),
        "diff": diff,
        "tone_before": llm_resp_safe.get("tone_before"),
        "tone_after": llm_resp_safe.get("tone_after"),
        "validation": validation,
    }

    # If validation failed, return controlled response with validation info
    if not validation.get("is_valid", False):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=response)

    return response


@router.get("/health")
def api_health():
    return {"status": "ok"}