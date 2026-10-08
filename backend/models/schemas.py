"""
Pydantic response/request models for StudentPulse API
"""
import re
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Student Profile ───────────────────────────────────────────────────────────

class StudentProfile(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    academic_year: Optional[int] = None
    semester: Optional[int] = None
    cgpa: Optional[float] = None
    gpa: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    preferred_opportunity_types: List[str] = Field(default_factory=list)
    preferred_location: Optional[str] = None
    open_to_remote: Optional[bool] = None
    past_internships: Optional[int] = 0
    courses_completed: List[str] = Field(default_factory=list)
    language_known: List[str] = Field(default_factory=list)
    career_goal: Optional[str] = None


class StudentRegistration(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)
    college: str = Field(min_length=2, max_length=160)
    branch: str = Field(min_length=2, max_length=120)
    academic_year: int = Field(ge=1, le=8)
    semester: int = Field(ge=1, le=16)
    gpa: Optional[float] = Field(default=None, ge=0, le=10)
    career_goal: Optional[str] = Field(default=None, max_length=120)
    skills: List[str] = Field(default_factory=list, max_length=60)
    interests: List[str] = Field(default_factory=list, max_length=60)
    preferred_opportunity_types: List[str] = Field(default_factory=list, max_length=10)
    open_to_remote: bool = True
    preferred_location: Optional[str] = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address")
        return normalized

    @field_validator("skills", "interests", "preferred_opportunity_types")
    @classmethod
    def clean_string_lists(cls, values: List[str]) -> List[str]:
        cleaned = [item.strip() for item in values if item.strip()]
        if any(len(item) > 80 for item in cleaned):
            raise ValueError("List items must be 80 characters or fewer")
        return list(dict.fromkeys(cleaned))


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[str] = Field(default=None, min_length=5, max_length=254)
    college: Optional[str] = Field(default=None, min_length=2, max_length=160)
    branch: Optional[str] = Field(default=None, min_length=2, max_length=120)
    academic_year: Optional[int] = Field(default=None, ge=1, le=8)
    semester: Optional[int] = Field(default=None, ge=1, le=16)
    gpa: Optional[float] = Field(default=None, ge=0, le=10)
    career_goal: Optional[str] = Field(default=None, max_length=120)
    skills: Optional[List[str]] = Field(default=None, max_length=60)
    interests: Optional[List[str]] = Field(default=None, max_length=60)
    preferred_opportunity_types: Optional[List[str]] = Field(default=None, max_length=10)
    open_to_remote: Optional[bool] = None
    preferred_location: Optional[str] = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address")
        return normalized


class AuthResponse(BaseModel):
    student: StudentProfile


# ── Preferences ───────────────────────────────────────────────────────────────

class StudentPreferences(BaseModel):
    student_id: str
    career_goal: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
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
    opportunities: List[RecommendationItem] = Field(default_factory=list)
    papers: List[RecommendationItem] = Field(default_factory=list)
    hackathons: List[RecommendationItem] = Field(default_factory=list)


# ── Skill Gap ─────────────────────────────────────────────────────────────────

class SkillGapResponse(BaseModel):
    student_id: str
    student_name: str
    target_id: str
    target_title: str
    target_type: str
    current_skills: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    gap_score: float
    readiness_score: float
    priority_skills_to_learn: List[str] = Field(default_factory=list)


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
    current_skills: List[str] = Field(default_factory=list)
    target_skills: List[str] = Field(default_factory=list)
    already_have: List[str] = Field(default_factory=list)
    steps: List[RoadmapStep] = Field(default_factory=list)
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
    suggestions: List[str] = Field(default_factory=list)
    confidence: float = 1.0


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    student_id: str
    item_id: str
    item_type: Literal["opportunity", "hackathon", "paper"]
    feedback_type: Literal["thumbs_up", "thumbs_down", "saved", "applied"]
    title: Optional[str] = Field(default=None, max_length=240)
    organization: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    skills: List[str] = Field(default_factory=list, max_length=60)
    location: Optional[str] = Field(default=None, max_length=160)
    deadline: Optional[str] = Field(default=None, max_length=80)
    url: Optional[str] = Field(default=None, max_length=1000)


class OpportunityCreate(BaseModel):
    category: Literal["internship", "hackathon", "research", "job"]
    title: str = Field(min_length=2, max_length=240)
    organization: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=4000)
    skills: List[str] = Field(default_factory=list, max_length=60)
    location: Optional[str] = Field(default=None, max_length=160)
    deadline: Optional[str] = Field(default=None, max_length=80)
    url: Optional[str] = Field(default=None, max_length=1000)
    status: Literal["active", "closed"] = "active"


class OpportunityUpdate(BaseModel):
    category: Optional[Literal["internship", "hackathon", "research", "job"]] = None
    title: Optional[str] = Field(default=None, min_length=2, max_length=240)
    organization: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    skills: Optional[List[str]] = Field(default=None, max_length=60)
    location: Optional[str] = Field(default=None, max_length=160)
    deadline: Optional[str] = Field(default=None, max_length=80)
    url: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[Literal["active", "closed"]] = None


class RoadmapProgressUpdate(BaseModel):
    career_goal: str = Field(min_length=1, max_length=120)
    step_number: int = Field(ge=1, le=200)
    skill: str = Field(min_length=1, max_length=120)
    completed: bool


class SkillLevelItem(BaseModel):
    skill: str = Field(min_length=1, max_length=120)
    current_level: int = Field(ge=0, le=100)
    target_level: int = Field(ge=0, le=100)


class SkillLevelsUpdate(BaseModel):
    skills: List[SkillLevelItem] = Field(max_length=100)
