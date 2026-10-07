"""Profile API — /api/profile"""
from typing import List
from fastapi import APIRouter, HTTPException
from backend.models.schemas import StudentProfile
from backend.services import ml_service

router = APIRouter()


def _to_list(val):
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return [s.strip() for s in val.split(",") if s.strip()]
    return []


def _row_to_profile(row: dict) -> StudentProfile:
    return StudentProfile(
        student_id=row.get("student_id", ""),
        name=row.get("name", ""),
        email=row.get("email"),
        department=row.get("department"),
        year_of_study=int(row.get("year_of_study", 1)) if row.get("year_of_study") else None,
        cgpa=float(row.get("cgpa", 0)) if row.get("cgpa") else None,
        skills=_to_list(row.get("skills", [])),
        interests=_to_list(row.get("interests", [])),
        preferred_location=row.get("preferred_location"),
        open_to_remote=bool(row.get("open_to_remote", False)),
        past_internships=int(row.get("past_internships", 0)) if row.get("past_internships") else 0,
        courses_completed=_to_list(row.get("courses_completed", [])),
        language_known=_to_list(row.get("language_known", [])),
        career_goal=str(row.get("career_goal", "")) if row.get("career_goal") else None,
    )


@router.get("/", response_model=List[StudentProfile])
def list_profiles():
    """Return all student profiles."""
    rows = ml_service.get_all_students()
    return [_row_to_profile(r) for r in rows]


@router.get("/{student_id}", response_model=StudentProfile)
def get_profile(student_id: str):
    """Return a single student profile."""
    row = ml_service.get_student(student_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found")
    return _row_to_profile(row)
