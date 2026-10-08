"""Preferences API — /api/preferences"""
from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import require_student_id
from backend.models.schemas import StudentPreferences
from backend.services import database

router = APIRouter()


@router.get("/{student_id}", response_model=StudentPreferences)
def get_preferences(student_id: str, _student: dict = Depends(require_student_id)):
    try:
        return StudentPreferences(**database.get_preferences(student_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student profile not found") from exc


@router.post("/{student_id}", response_model=StudentPreferences)
def save_preferences(student_id: str, body: StudentPreferences, _student: dict = Depends(require_student_id)):
    data = body.model_dump(exclude={"student_id"}, exclude_none=True)
    try:
        return StudentPreferences(**database.save_preferences(student_id, data))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student profile not found") from exc
