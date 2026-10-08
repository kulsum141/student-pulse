"""CRUD endpoints for application-managed opportunity records."""
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from backend.dependencies import get_current_student
from backend.models.schemas import OpportunityCreate, OpportunityUpdate
from backend.services import database

router = APIRouter()


@router.get("/")
def list_opportunities(
    category: Optional[Literal["internship", "hackathon", "research", "job"]] = Query(None),
    search: Optional[str] = Query(None, max_length=160),
    _student: dict = Depends(get_current_student),
):
    return database.list_opportunities(category, search)


@router.post("/", status_code=201)
def create_opportunity(body: OpportunityCreate, student: dict = Depends(get_current_student)):
    try:
        return database.create_opportunity(
            student["student_id"], uuid.uuid4().hex, body.model_dump()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to save this opportunity") from exc


@router.put("/{opportunity_id}")
def update_opportunity(
    opportunity_id: str,
    body: OpportunityUpdate,
    student: dict = Depends(get_current_student),
):
    try:
        item = database.update_opportunity(
            student["student_id"], opportunity_id, body.model_dump(exclude_unset=True)
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to update this opportunity") from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return item


@router.delete("/{opportunity_id}", status_code=204)
def delete_opportunity(opportunity_id: str, student: dict = Depends(get_current_student)):
    if not database.delete_opportunity(student["student_id"], opportunity_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return Response(status_code=204)