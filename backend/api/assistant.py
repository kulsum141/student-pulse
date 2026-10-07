"""AI Assistant API — /api/assistant"""
from fastapi import APIRouter, HTTPException
from backend.models.schemas import AssistantRequest, AssistantResponse
from backend.services import ml_service

router = APIRouter()


@router.post("/ask", response_model=AssistantResponse)
def ask_assistant(body: AssistantRequest):
    """Send a natural-language query to the AI assistant."""
    response = ml_service.ask_assistant(body.student_id, body.query)
    if response is None:
        raise HTTPException(status_code=503, detail="ML engine not available")
    return AssistantResponse(
        student_id=response.student_id,
        query=response.query,
        intent=response.intent.value,
        answer=response.answer,
        suggestions=response.suggestions,
        confidence=response.confidence,
    )
