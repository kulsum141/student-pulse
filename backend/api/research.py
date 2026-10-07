"""Research Papers API — /api/research"""
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
    return d


@router.get("/")
def list_research(
    student_id: Optional[str] = Query(None),
    top_k: int = Query(10, ge=1, le=25),
):
    items = ml_service.get_research(student_id, top_k=top_k)

    if items and hasattr(items[0], "item_id"):
        engine = ml_service.get_engine()
        result = []
        for rec in items:
            row = engine._papers_df[engine._papers_df["paper_id"] == rec.item_id]
            if not row.empty:
                result.append(_normalise(row.iloc[0].to_dict(), rec))
            else:
                result.append({"paper_id": rec.item_id, "title": rec.title, "score": rec.score})
        return result
    return [_normalise(i) for i in items]
