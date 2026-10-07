"""Preferences API — /api/preferences"""
from fastapi import APIRouter, HTTPException
from backend.models.schemas import StudentPreferences
from backend.services import ml_service

router = APIRouter()


@router.get("/{student_id}", response_model=StudentPreferences)
def get_preferences(student_id: str):
    prefs = ml_service.load_preferences(student_id)
    return StudentPreferences(student_id=student_id, **prefs)


@router.post("/{student_id}", response_model=StudentPreferences)
def save_preferences(student_id: str, body: StudentPreferences):
    data = body.model_dump(exclude={"student_id"}, exclude_none=True)
    ml_service.save_preferences(student_id, data)
    return body
