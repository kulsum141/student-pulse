"""Roadmap API — /api/roadmap"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.dependencies import require_student_id
from backend.models.schemas import RoadmapProgressUpdate, RoadmapResponse, RoadmapStep
from backend.services import database, ml_service

router = APIRouter()


def _roadmap_to_schema(result) -> RoadmapResponse:
    return RoadmapResponse(
        student_id=result.student_id,
        student_name=result.student_name,
        career_goal=result.career_goal,
        current_skills=result.current_skills,
        target_skills=result.target_skills,
        already_have=result.already_have,
        steps=[
            RoadmapStep(
                step_number=s.step_number,
                skill=s.skill,
                reason=s.reason,
                resource_type=s.resource_type,
                suggested_resources=s.suggested_resources,
                estimated_weeks=s.estimated_weeks,
            )
            for s in result.steps
        ],
        total_estimated_weeks=result.total_estimated_weeks,
        readiness_percentage=result.readiness_percentage,
    )


@router.get("/{student_id}/progress")
def get_progress(student_id: str, career_goal: str = Query(..., max_length=120), _student: dict = Depends(require_student_id)):
    return database.get_roadmap_progress(student_id, career_goal)


@router.put("/{student_id}/progress")
def save_progress(student_id: str, body: RoadmapProgressUpdate, _student: dict = Depends(require_student_id)):
    return database.set_roadmap_step(
        student_id, body.career_goal, body.step_number, body.skill, body.completed
    )


@router.get("/{student_id}", response_model=RoadmapResponse)
def get_roadmap(student_id: str, goal: Optional[str] = Query(None), _student: dict = Depends(require_student_id)):
    """Generate a personalised career roadmap for a student."""
    profile = database.get_student(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    try:
        result = ml_service.get_roadmap_for_profile(profile, goal=goal)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Roadmap generation is unavailable") from exc
    if result is None:
        raise HTTPException(status_code=503, detail="ML engine not available")
    return _roadmap_to_schema(result)
