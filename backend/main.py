"""
StudentPulse Backend — FastAPI application entry point
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import (
    profile,
    preferences,
    recommendations,
    skill_gap,
    roadmap,
    internships,
    hackathons,
    research,
    assistant,
    auth,
    opportunities,
    saved,
    skills,
)
from backend.services.database import initialize_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(_app):
    initialize_database()
    yield


app = FastAPI(
    title="StudentPulse API",
    description="AI-powered personalised career & research recommendation system",
    version="1.0.0",
    lifespan=lifespan,
)

_default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("STUDENT_PULSE_CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router,              prefix="/api/auth",            tags=["Authentication"])
app.include_router(profile.router,         prefix="/api/profile",         tags=["Profile"])
app.include_router(preferences.router,     prefix="/api/preferences",     tags=["Preferences"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(skill_gap.router,       prefix="/api/skill-gap",       tags=["Skill Gap"])
app.include_router(roadmap.router,         prefix="/api/roadmap",         tags=["Roadmap"])
app.include_router(internships.router,     prefix="/api/internships",     tags=["Internships"])
app.include_router(hackathons.router,      prefix="/api/hackathons",      tags=["Hackathons"])
app.include_router(research.router,        prefix="/api/research",        tags=["Research"])
app.include_router(assistant.router,       prefix="/api/assistant",       tags=["AI Assistant"])
app.include_router(opportunities.router,   prefix="/api/opportunities",   tags=["Application Opportunities"])
app.include_router(saved.router,            prefix="/api/saved",           tags=["Saved Opportunities"])
app.include_router(skills.router,           prefix="/api/skills",          tags=["Student Skills"])


@app.get("/")
def root():
    return {"status": "ok", "service": "StudentPulse API", "version": "1.0.0"}


@app.get("/health")
def health():
    from backend.services.ml_service import get_engine_status
    return {"status": "ok", "ml_engine": get_engine_status()}
