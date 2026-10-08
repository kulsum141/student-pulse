"""AI Assistant API — /api/assistant"""
from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_current_student
from backend.models.schemas import AssistantRequest, AssistantResponse
from backend.services import database, ml_service

router = APIRouter()


@router.post("/ask", response_model=AssistantResponse)
def ask_assistant(body: AssistantRequest, student: dict = Depends(get_current_student)):
    """Send a natural-language query to the AI assistant."""
    if body.student_id != student["student_id"]:
        raise HTTPException(status_code=403, detail="You cannot ask on behalf of another student")
    profile = database.get_student(student["student_id"])
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    try:
        response = ml_service.ask_assistant_for_profile(profile, body.query)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="AI Assistant is unavailable") from exc
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
