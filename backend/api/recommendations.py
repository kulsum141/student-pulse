"""Recommendations API — /api/recommendations"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.dependencies import require_student_id, get_current_student
from backend.models.schemas import RecommendationResponse, RecommendationItem, FeedbackRequest
from backend.services import database, ml_service

router = APIRouter()


def _rec_to_item(r) -> RecommendationItem:
    return RecommendationItem(
        item_id=r.item_id,
        title=r.title,
        item_type=r.item_type,
        score=r.score,
        cosine_score=r.cosine_score,
        skill_overlap=r.skill_overlap,
        cgpa_factor=r.cgpa_factor,
        matched_skills=r.matched_skills,
        explanation=r.explanation,
    )


@router.get("/{student_id}", response_model=RecommendationResponse)
def get_recommendations(
    student_id: str,
    top_k_opps: int = Query(5, ge=1, le=25),
    top_k_papers: int = Query(5, ge=1, le=25),
    top_k_hackathons: int = Query(5, ge=1, le=25),
    _student: dict = Depends(require_student_id),
):
    """Get all recommendations for a student from the ML engine."""
    profile = database.get_student(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    try:
        result = ml_service.recommend_for_profile(profile, top_k_opps, top_k_papers, top_k_hackathons)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Recommendation engine is unavailable for this profile") from exc
    if result is None:
        raise HTTPException(status_code=503, detail="Recommendation engine is unavailable")
    return RecommendationResponse(
        student_id=result.student_id,
        student_name=result.student_name,
        opportunities=[_rec_to_item(r) for r in result.opportunities],
        papers=[_rec_to_item(r) for r in result.papers],
        hackathons=[_rec_to_item(r) for r in result.hackathons],
    )


@router.post("/feedback", status_code=200)
def record_feedback(body: FeedbackRequest, student: dict = Depends(get_current_student)):
    if body.student_id != student["student_id"]:
        raise HTTPException(status_code=403, detail="You cannot submit feedback for another student")
    ok = ml_service.record_feedback(
        body.student_id, body.item_id, body.item_type, body.feedback_type
    )
    if not ok:
        raise HTTPException(status_code=503, detail="Feedback could not be recorded")
    if body.feedback_type == "saved":
        database.save_opportunity(student["student_id"], {
            "opportunity_id": body.item_id,
            "item_type": body.item_type,
            "title": body.title,
            "organization": body.organization,
            "description": body.description,
            "skills": body.skills,
            "location": body.location,
            "deadline": body.deadline,
            "url": body.url,
        })
    elif body.feedback_type == "applied":
        database.delete_saved_opportunity(student["student_id"], body.item_id)
    return {"success": True}
