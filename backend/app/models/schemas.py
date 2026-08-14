from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    # Limit input size to a reasonable maximum to reduce abuse and resource usage
    text: str = Field(..., min_length=1, max_length=5000)


class ChangeItem(BaseModel):
    original: Optional[str]
    replacement: Optional[str]
    reason: Optional[str]
    category: Optional[str]


class ValidationResult(BaseModel):
    is_valid: bool
    remaining_banned_terms: List[dict] = []
    warnings: List[str] = []
    validation_errors: List[str] = []


class AnalyzeResponse(BaseModel):
    original_text: str
    improved_text: str
    detected_issues: List[dict] = []
    changes: List[ChangeItem] = []
    diff: List[dict] = []
    tone_before: Optional[str] = None
    tone_after: Optional[str] = None
    validation: ValidationResult
