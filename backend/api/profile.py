"""Profile API — /api/profile"""
import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_current_student, require_student_id
from backend.models.schemas import ProfileUpdate, StudentProfile
from backend.services import database

router = APIRouter()


@router.get("/", response_model=List[StudentProfile])
def list_profiles(student: dict = Depends(get_current_student)):
    """Return only the authenticated student's profile."""
    return [StudentProfile(**student)]


@router.get("/me", response_model=StudentProfile)
def get_my_profile(student: dict = Depends(get_current_student)):
    return StudentProfile(**student)


@router.put("/me", response_model=StudentProfile)
def update_my_profile(body: ProfileUpdate, student: dict = Depends(get_current_student)):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        return StudentProfile(**student)
    try:
        profile = database.update_student(student["student_id"], fields)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="That email is already in use") from exc
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return StudentProfile(**profile)


@router.get("/{student_id}", response_model=StudentProfile)
def get_profile(student_id: str, _student: dict = Depends(require_student_id)):
    """Return the authenticated student's profile."""
    profile = database.get_student(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found")
    return StudentProfile(**profile)
