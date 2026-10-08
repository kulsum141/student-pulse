"""Skill Gap API — /api/skill-gap"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.dependencies import require_student_id
from backend.models.schemas import SkillGapResponse
from backend.services import database, ml_service

router = APIRouter()


def _gap_to_schema(report) -> SkillGapResponse:
    return SkillGapResponse(
        student_id=report.student_id,
        student_name=report.student_name,
        target_id=report.target_id,
        target_title=report.target_title,
        target_type=report.target_type,
        current_skills=report.current_skills,
        required_skills=report.required_skills,
        matched_skills=report.matched_skills,
        missing_skills=report.missing_skills,
        gap_score=report.gap_score,
        readiness_score=report.readiness_score,
        priority_skills_to_learn=report.priority_skills_to_learn,
    )


@router.get("/{student_id}/career-goal", response_model=SkillGapResponse)
def skill_gap_career_goal(student_id: str, goal: Optional[str] = Query(None), _student: dict = Depends(require_student_id)):
    """Skill gap analysis vs the student's (or supplied) career goal."""
    profile = database.get_student(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    try:
        report = ml_service.get_skill_gap_for_profile(profile, goal=goal)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Skill-gap analysis is unavailable") from exc
    if report is None:
        raise HTTPException(status_code=503, detail="ML engine not available")
    return _gap_to_schema(report)


@router.get("/{student_id}/opportunity/{target_id}", response_model=SkillGapResponse)
def skill_gap_opportunity(student_id: str, target_id: str, _student: dict = Depends(require_student_id)):
    """Skill gap vs a specific opportunity."""
    try:
        profile = database.get_student(student_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Student profile not found")
        report = ml_service.get_skill_gap_for_profile(profile, target_id=target_id, item_type="opportunity")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Skill-gap analysis is unavailable") from exc
    if report is None:
        raise HTTPException(status_code=503, detail="ML engine not available")
    return _gap_to_schema(report)


@router.get("/{student_id}/all", response_model=List[SkillGapResponse])
def skill_gap_all(
    student_id: str,
    top_k: int = Query(5, ge=1, le=20),
    item_type: str = Query("opportunity"),
    _student: dict = Depends(require_student_id),
):
    """Skill gaps vs top-k items sorted by readiness (achievable first)."""
    profile = database.get_student(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    try:
        reports = ml_service.get_skill_gap_all_for_profile(profile, top_k=top_k, item_type=item_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Skill-gap analysis is unavailable") from exc
    if reports is None:
        raise HTTPException(status_code=503, detail="Skill-gap analysis is unavailable")
    return [_gap_to_schema(r) for r in reports]
