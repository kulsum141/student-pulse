"""Registration and cookie-session authentication endpoints."""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from backend.dependencies import SESSION_COOKIE_NAME, get_current_student, session_cookie_options
from backend.models.schemas import AuthResponse, LoginRequest, StudentProfile, StudentRegistration
from backend.services import database, ml_service
from backend.services.security import create_session_token, hash_password, hash_session_token, verify_password

log = logging.getLogger(__name__)
router = APIRouter()


def _csv_values(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _linked_engine_profile(email: str) -> dict | None:
    try:
        return next(
            (row for row in ml_service.get_all_students() if str(row.get("email", "")).lower() == email),
            None,
        )
    except Exception as exc:
        log.warning("Unable to match registration with an existing engine profile: %s", exc)
        return None


def _create_login_session(response: Response, student: dict) -> AuthResponse:
    token = create_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    database.create_session(
        hash_session_token(token),
        student["student_id"],
        expires_at.isoformat(),
    )
    cookie_options = session_cookie_options()
    response.set_cookie(value=token, **cookie_options)
    return AuthResponse(student=StudentProfile(**student))


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: StudentRegistration, response: Response):
    existing, _ = database.get_student_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    profile = body.model_dump(exclude={"password"})
    engine_profile = _linked_engine_profile(body.email)
    if engine_profile:
        profile["skills"] = body.skills or _csv_values(engine_profile.get("skills"))
        profile["interests"] = body.interests or _csv_values(engine_profile.get("interests"))
        profile["career_goal"] = body.career_goal or engine_profile.get("career_goal")
        profile["gpa"] = body.gpa if body.gpa is not None else engine_profile.get("cgpa")
        profile["preferred_location"] = body.preferred_location or engine_profile.get("preferred_location")
        profile["open_to_remote"] = body.open_to_remote if body.open_to_remote is not None else bool(engine_profile.get("open_to_remote", True))
        student_id = str(engine_profile.get("student_id") or uuid.uuid4().hex)
    else:
        student_id = uuid.uuid4().hex

    try:
        student = database.create_student(student_id, profile, hash_password(body.password))
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
        log.exception("Student registration failed")
        raise HTTPException(status_code=500, detail="Unable to create your account") from exc
    return _create_login_session(response, student)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, response: Response):
    student, password_hash = database.get_student_by_email(body.email)
    if student is None or password_hash is None or not verify_password(body.password, password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return _create_login_session(response, student)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        database.delete_session(hash_session_token(token))
    options = session_cookie_options()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path=options["path"],
        httponly=options["httponly"],
        secure=options["secure"],
        samesite=options["samesite"],
    )
    response.status_code = 204
    return response


@router.get("/me", response_model=StudentProfile)
def me(student: dict = Depends(get_current_student)):
    return StudentProfile(**student)