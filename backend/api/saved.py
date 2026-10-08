"""Saved opportunity endpoints scoped to the authenticated student."""
from fastapi import APIRouter, Depends, HTTPException, Response

from backend.dependencies import get_current_student
from backend.services import database

router = APIRouter()


@router.get("/")
def list_saved_opportunities(student: dict = Depends(get_current_student)):
    return database.list_saved_opportunities(student["student_id"])


@router.delete("/{opportunity_id}", status_code=204)
def remove_saved_opportunity(opportunity_id: str, student: dict = Depends(get_current_student)):
    if not database.delete_saved_opportunity(student["student_id"], opportunity_id):
        raise HTTPException(status_code=404, detail="Saved opportunity not found")
    return Response(status_code=204)