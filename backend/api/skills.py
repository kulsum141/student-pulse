"""Student-owned skill proficiency persistence endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import require_student_id
from backend.models.schemas import SkillLevelsUpdate
from backend.services import database

router = APIRouter()


@router.get("/{student_id}")
def get_skill_levels(student_id: str, _student: dict = Depends(require_student_id)):
    return database.get_skill_levels(student_id)


@router.put("/{student_id}")
def update_skill_levels(
    student_id: str,
    body: SkillLevelsUpdate,
    _student: dict = Depends(require_student_id),
):
    try:
        return database.save_skill_levels(
            student_id, [skill.model_dump() for skill in body.skills]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to save skill levels") from exc