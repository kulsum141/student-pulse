"""Roadmap API — /api/roadmap"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.models.schemas import RoadmapResponse, RoadmapStep
from backend.services import ml_service

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


@router.get("/{student_id}", response_model=RoadmapResponse)
def get_roadmap(student_id: str, goal: Optional[str] = Query(None)):
    """Generate a personalised career roadmap for a student."""
    result = ml_service.get_roadmap(student_id, goal=goal)
    if result is None:
        raise HTTPException(status_code=503, detail="ML engine not available")
    return _roadmap_to_schema(result)
