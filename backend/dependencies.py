"""Shared authentication dependencies for student-scoped API routes."""
import os
from fastapi import Depends, HTTPException, Request

from backend.services import database
from backend.services.security import hash_session_token

SESSION_COOKIE_NAME = "student_pulse_session"


def get_current_student(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Please sign in to continue")
    student = database.get_session_student(hash_session_token(token))
    if student is None:
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again")
    return student


def require_student_id(student_id: str, student: dict = Depends(get_current_student)) -> dict:
    if student_id != student["student_id"]:
        raise HTTPException(status_code=403, detail="You cannot access another student's data")
    return student


def session_cookie_options() -> dict:
    same_site = os.getenv("STUDENT_PULSE_COOKIE_SAMESITE", "lax").lower()
    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"
    secure_default = "true" if same_site == "none" else "false"
    secure = os.getenv("STUDENT_PULSE_COOKIE_SECURE", secure_default).lower() in {"1", "true", "yes"}
    return {
        "key": SESSION_COOKIE_NAME,
        "httponly": True,
        "secure": secure,
        "samesite": same_site,
        "path": "/",
        "max_age": 60 * 60 * 24 * 30,
    }