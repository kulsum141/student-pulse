"""Recommendations API — /api/recommendations"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.models.schemas import RecommendationResponse, RecommendationItem, FeedbackRequest
from backend.services import ml_service

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
):
    """Get all recommendations for a student from the ML engine."""
    result = ml_service.recommend_all(student_id, top_k_opps, top_k_papers, top_k_hackathons)
    if result is None:
        raise HTTPException(status_code=503, detail="ML engine not available")
    return RecommendationResponse(
        student_id=result.student_id,
        student_name=result.student_name,
        opportunities=[_rec_to_item(r) for r in result.opportunities],
        papers=[_rec_to_item(r) for r in result.papers],
        hackathons=[_rec_to_item(r) for r in result.hackathons],
    )


@router.post("/feedback", status_code=200)
def record_feedback(body: FeedbackRequest):
    ok = ml_service.record_feedback(
        body.student_id, body.item_id, body.item_type, body.feedback_type
    )
    return {"success": ok}
