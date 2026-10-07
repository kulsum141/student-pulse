"""Internships API — /api/internships"""
from typing import Optional
from fastapi import APIRouter, Query
from backend.services import ml_service

router = APIRouter()


def _normalise(item, rec=None):
    d = {}
    if isinstance(item, dict):
        d = {k: (list(v) if hasattr(v, "tolist") else v) for k, v in item.items()}
    if rec is not None:
        d["score"] = rec.score
        d["skill_overlap"] = rec.skill_overlap
        d["matched_skills"] = rec.matched_skills
    return d


@router.get("/")
def list_internships(
    student_id: Optional[str] = Query(None),
    top_k: int = Query(10, ge=1, le=25),
    type: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
):
    filters = {}
    if type:
        filters["type"] = type
    if remote is not None:
        filters["remote"] = remote

    items = ml_service.get_internships(student_id, top_k=top_k, filters=filters or None)

    if items and hasattr(items[0], "item_id"):
        # ML recommendation objects
        engine = ml_service.get_engine()
        result = []
        for rec in items:
            row = engine._opps_df[engine._opps_df["opportunity_id"] == rec.item_id]
            if not row.empty:
                result.append(_normalise(row.iloc[0].to_dict(), rec))
            else:
                result.append({"opportunity_id": rec.item_id, "title": rec.title,
                               "score": rec.score, "skill_overlap": rec.skill_overlap,
                               "matched_skills": rec.matched_skills})
        return result
    return [_normalise(i) for i in items]
