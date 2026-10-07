"""
Pydantic response/request models for StudentPulse API
"""
from typing import Any, List, Optional
from pydantic import BaseModel


# ── Student Profile ───────────────────────────────────────────────────────────

class StudentProfile(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    cgpa: Optional[float] = None
    skills: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    preferred_location: Optional[str] = None
    open_to_remote: Optional[bool] = None
    past_internships: Optional[int] = 0
    courses_completed: Optional[List[str]] = []
    language_known: Optional[List[str]] = []
    career_goal: Optional[str] = None


# ── Preferences ───────────────────────────────────────────────────────────────

class StudentPreferences(BaseModel):
    student_id: str
    career_goal: Optional[str] = None
    interests: Optional[List[str]] = []
    skill_level: Optional[str] = None          # beginner | intermediate | advanced
    preferred_opportunity_type: Optional[str] = None  # internship | full-time | research | hackathon
    work_mode: Optional[str] = None            # remote | onsite | hybrid
    location: Optional[str] = None
    learning_style: Optional[str] = None       # visual | hands-on | reading | video


# ── Recommendation ────────────────────────────────────────────────────────────

class RecommendationItem(BaseModel):
    item_id: str
    title: str
    item_type: str
    score: float
    cosine_score: float
    skill_overlap: float
    cgpa_factor: float
    matched_skills: List[str] = []
    explanation: str = ""


class RecommendationResponse(BaseModel):
    student_id: str
    student_name: str
    opportunities: List[RecommendationItem] = []
    papers: List[RecommendationItem] = []
    hackathons: List[RecommendationItem] = []


# ── Skill Gap ─────────────────────────────────────────────────────────────────

class SkillGapResponse(BaseModel):
    student_id: str
    student_name: str
    target_id: str
    target_title: str
    target_type: str
    current_skills: List[str] = []
    required_skills: List[str] = []
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    gap_score: float
    readiness_score: float
    priority_skills_to_learn: List[str] = []


# ── Roadmap ───────────────────────────────────────────────────────────────────

class RoadmapStep(BaseModel):
    step_number: int
    skill: str
    reason: str
    resource_type: str
    suggested_resources: List[str] = []
    estimated_weeks: int


class RoadmapResponse(BaseModel):
    student_id: str
    student_name: str
    career_goal: str
    current_skills: List[str] = []
    target_skills: List[str] = []
    already_have: List[str] = []
    steps: List[RoadmapStep] = []
    total_estimated_weeks: int
    readiness_percentage: float


# ── Internship / Hackathon / Research raw rows ────────────────────────────────

class OpportunityItem(BaseModel):
    opportunity_id: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[Any] = None
    required_skills: Optional[Any] = None
    min_cgpa: Optional[float] = None
    stipend_per_month: Optional[Any] = None
    duration_months: Optional[Any] = None
    score: Optional[float] = None
    skill_overlap: Optional[float] = None
    matched_skills: Optional[List[str]] = []


class HackathonItem(BaseModel):
    hackathon_id: Optional[str] = None
    title: Optional[str] = None
    organizer: Optional[str] = None
    mode: Optional[str] = None
    difficulty_level: Optional[str] = None
    required_skills: Optional[Any] = None
    prize_pool: Optional[Any] = None
    duration_days: Optional[Any] = None
    score: Optional[float] = None
    skill_overlap: Optional[float] = None
    matched_skills: Optional[List[str]] = []


class ResearchItem(BaseModel):
    paper_id: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[Any] = None
    domain: Optional[str] = None
    keywords: Optional[Any] = None
    journal: Optional[str] = None
    year: Optional[Any] = None
    citations: Optional[Any] = None
    score: Optional[float] = None
    skill_overlap: Optional[float] = None


# ── AI Assistant ──────────────────────────────────────────────────────────────

class AssistantRequest(BaseModel):
    student_id: str
    query: str


class AssistantResponse(BaseModel):
    student_id: str
    query: str
    intent: str
    answer: str
    suggestions: List[str] = []
    confidence: float = 1.0


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    student_id: str
    item_id: str
    item_type: str   # opportunity | hackathon | paper
    feedback_type: str  # thumbs_up | thumbs_down | saved | applied
