"""
skill_gap.py
------------
StudentPulse ML — Skill Gap Model + Career Roadmap

Two tightly-related responsibilities:

1. SKILL GAP MODEL
   Given a student's current skills and a target role / opportunity,
   identify which required skills the student is missing and score the gap.

2. CAREER ROADMAP
   Given a student's current profile and career goal, generate an ordered
   learning roadmap: which skills to acquire first, in what sequence, and
   which resources / opportunities bridge each gap.

Architecture position:
    Student Profile
          ↓
    Skill Gap Model  ←──── this module
          ↓
    Career Roadmap   ←──── this module

Public API
----------
SkillGapAnalyzer
    .analyze(student_id, item_id, item_type)     → SkillGapReport
    .analyze_for_career_goal(student_id, goal)   → SkillGapReport
    .analyze_all_for_student(student_id, top_k)  → List[SkillGapReport]

CareerRoadmap
    .generate(student_id)       → RoadmapResult
    .generate_from_goal(skills, goal, cgpa) → RoadmapResult

Standalone helpers
    skill_gap_score(have, need)
    missing_skills(have, need)
    learning_order(missing_skills, difficulty_map)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

log = logging.getLogger(__name__)


# ===========================================================================
# 1.  DATA CLASSES
# ===========================================================================

@dataclass
class SkillGapReport:
    """Result of a skill-gap analysis between a student and one target."""
    student_id: str
    student_name: str
    target_id: str
    target_title: str
    target_type: str                         # "opportunity" | "hackathon" | "career_goal"
    current_skills: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    gap_score: float = 0.0                   # 0 = no gap, 1 = complete gap
    readiness_score: float = 0.0             # 0 = not ready, 1 = fully ready
    priority_skills_to_learn: List[str] = field(default_factory=list)


@dataclass
class RoadmapStep:
    """One step in the career roadmap."""
    step_number: int
    skill: str
    reason: str                              # why this skill at this stage
    resource_type: str                       # "course" | "project" | "internship" | "hackathon" | "paper"
    suggested_resources: List[str] = field(default_factory=list)
    estimated_weeks: int = 4


@dataclass
class RoadmapResult:
    """A personalised career roadmap for a student."""
    student_id: str
    student_name: str
    career_goal: str
    current_skills: List[str] = field(default_factory=list)
    target_skills: List[str] = field(default_factory=list)
    already_have: List[str] = field(default_factory=list)
    steps: List[RoadmapStep] = field(default_factory=list)
    total_estimated_weeks: int = 0
    readiness_percentage: float = 0.0


# ===========================================================================
# 2.  STANDALONE  HELPERS
# ===========================================================================

def skill_gap_score(have: List[str], need: List[str]) -> float:
    """Fraction of required skills the student is MISSING.

    Returns 0.0 if no gap (all skills covered), 1.0 if completely unqualified.
    """
    if not need:
        return 0.0
    have_set = set(s.strip().lower() for s in have)
    need_set = set(s.strip().lower() for s in need)
    missing = need_set - have_set
    return len(missing) / len(need_set)


def readiness_score(have: List[str], need: List[str]) -> float:
    """Fraction of required skills the student ALREADY HAS (complement of gap)."""
    return 1.0 - skill_gap_score(have, need)


def missing_skills(have: List[str], need: List[str]) -> List[str]:
    """Return the sorted list of skills in `need` that are absent in `have`."""
    have_set = set(s.strip().lower() for s in have)
    return sorted(s for s in need if s.strip().lower() not in have_set)


def matched_skills_list(have: List[str], need: List[str]) -> List[str]:
    """Return the sorted list of skills in `need` that the student already has."""
    have_set = set(s.strip().lower() for s in have)
    return sorted(s for s in need if s.strip().lower() in have_set)


# ===========================================================================
# 3.  SKILL GAP  ANALYZER
# ===========================================================================

# Career-goal → required skills mapping (canonical target skill sets)
CAREER_GOAL_SKILLS: Dict[str, List[str]] = {
    "data scientist":          ["python", "machine learning", "sql", "statistics", "deep learning", "data visualization"],
    "ml engineer":             ["python", "machine learning", "tensorflow", "pytorch", "mlops", "docker"],
    "nlp engineer":            ["python", "nlp", "transformers", "bert", "pytorch", "text processing"],
    "computer vision engineer":["python", "opencv", "pytorch", "deep learning", "object detection", "image processing"],
    "data engineer":           ["python", "spark", "sql", "kafka", "airflow", "cloud", "hadoop"],
    "backend engineer":        ["python", "java", "rest apis", "sql", "docker", "microservices", "spring boot"],
    "full stack developer":    ["javascript", "react", "node.js", "sql", "html", "css", "rest apis"],
    "frontend developer":      ["javascript", "react", "html", "css", "typescript", "figma"],
    "devops engineer":         ["docker", "kubernetes", "ci/cd", "linux", "terraform", "cloud", "shell scripting"],
    "rl researcher":           ["python", "pytorch", "reinforcement learning", "mathematics", "gym", "simulation"],
    "blockchain developer":    ["solidity", "python", "javascript", "web3.js", "ethereum", "cryptography"],
    "embedded engineer":       ["c++", "embedded c", "matlab", "rtos", "microcontrollers", "sensors"],
    "vlsi engineer":           ["vlsi", "verilog", "matlab", "cadence", "digital design", "synthesis"],
    "android developer":       ["java", "kotlin", "android", "firebase", "rest apis", "gradle"],
    "ux researcher":           ["user research", "figma", "spss", "survey design", "usability testing", "prototyping"],
    "product manager":         ["market research", "excel", "sql", "figma", "agile", "roadmapping", "communication"],
    "quant analyst":           ["python", "statistics", "sql", "excel", "financial modeling", "r"],
    "bioinformatics researcher":["python", "r", "bioinformatics", "blast", "biopython", "genomics", "statistics"],
    "software engineer":       ["python", "java", "data structures", "algorithms", "system design", "git"],
    "data analyst":            ["python", "sql", "excel", "tableau", "statistics", "power bi"],
}

# Skill → difficulty tier (used to order the learning roadmap)
SKILL_DIFFICULTY: Dict[str, int] = {
    # Tier 1 — Foundations (learn first)
    "python": 1, "java": 1, "javascript": 1, "html": 1, "css": 1,
    "sql": 1, "excel": 1, "git": 1, "linux": 1, "c++": 1, "r": 1,
    # Tier 2 — Intermediate
    "machine learning": 2, "statistics": 2, "rest apis": 2, "react": 2,
    "node.js": 2, "docker": 2, "data visualization": 2, "figma": 2,
    "user research": 2, "market research": 2, "survey design": 2,
    "android": 2, "firebase": 2, "kotlin": 2, "shell scripting": 2,
    "bioinformatics": 2, "blast": 2, "financial modeling": 2,
    "embedded c": 2, "verilog": 2, "vlsi": 2, "matlab": 2,
    "solidity": 2, "web3.js": 2, "agile": 2,
    # Tier 3 — Advanced
    "deep learning": 3, "tensorflow": 3, "pytorch": 3, "nlp": 3,
    "transformers": 3, "bert": 3, "opencv": 3, "spark": 3, "kafka": 3,
    "kubernetes": 3, "microservices": 3, "spring boot": 3,
    "reinforcement learning": 3, "object detection": 3, "mlops": 3,
    "terraform": 3, "ci/cd": 3, "cadence": 3, "synthesis": 3,
    "cryptography": 3, "ethereum": 3, "genomics": 3, "biopython": 3,
    "airflow": 3, "hadoop": 3, "system design": 3, "data structures": 3,
}

# Resource suggestions per skill
SKILL_RESOURCES: Dict[str, List[str]] = {
    "python":             ["Python for Everybody (Coursera)", "Automate the Boring Stuff (Book)", "LeetCode Python"],
    "machine learning":   ["Andrew Ng ML Course (Coursera)", "Hands-On ML (Book)", "Kaggle Learn ML"],
    "deep learning":      ["DeepLearning.AI Specialization", "fast.ai", "d2l.ai"],
    "sql":                ["Mode Analytics SQL Tutorial", "SQLZoo", "LeetCode SQL"],
    "react":              ["React Official Docs", "Full Stack Open (Helsinki)", "Scrimba React"],
    "docker":             ["Docker Getting Started", "Play with Docker", "Docker for Developers (Udemy)"],
    "kubernetes":         ["Kubernetes.io Docs", "CKAD Exam Prep", "KodeKloud"],
    "pytorch":            ["PyTorch Official Tutorials", "Zero to Mastery PyTorch", "fast.ai"],
    "nlp":                ["Hugging Face NLP Course", "Stanford CS224N", "NLP with Transformers (Book)"],
    "spark":              ["Databricks Learning", "Spark: The Definitive Guide (Book)", "Udemy Spark & PySpark"],
    "tensorflow":         ["TensorFlow Developer Certificate", "TensorFlow.org Tutorials", "Coursera TF"],
    "solidity":           ["CryptoZombies", "Solidity Docs", "Buildspace Web3"],
    "bioinformatics":     ["Rosalind.info", "Bioinformatics Algorithms (Coursera)", "Biopython Docs"],
    "vlsi":               ["NPTEL VLSI Design", "Verilog HDL (Book)", "Synopsys University Program"],
    "reinforcement learning": ["Spinning Up in Deep RL (OpenAI)", "RL Specialization (Alberta)", "Sutton & Barto Book"],
    "statistics":         ["Khan Academy Statistics", "Think Stats (Book)", "StatQuest YouTube"],
}

_DEFAULT_RESOURCE = ["Search Coursera / Udemy for this skill", "Read official documentation", "Build a small project"]


class SkillGapAnalyzer:
    """Analyses skill gaps between a student and targets (opportunities, hackathons, goals).

    Usage
    -----
    >>> analyzer = SkillGapAnalyzer(engine)
    >>> report = analyzer.analyze("S001", "O001", "opportunity")
    >>> print(report.missing_skills)
    >>> print(f"Readiness: {report.readiness_score:.0%}")
    """

    def __init__(self, engine=None):
        """
        Parameters
        ----------
        engine : fitted RecommendationEngine (optional).
                 If provided, the analyzer can access all DataFrames directly.
                 If None, pass DataFrames explicitly to the methods.
        """
        self._engine = engine

    def analyze(
        self,
        student_id: str,
        target_id: str,
        item_type: str = "opportunity",
        students_df: Optional[pd.DataFrame] = None,
        items_df: Optional[pd.DataFrame] = None,
    ) -> SkillGapReport:
        """Analyse the skill gap between a student and one specific target.

        Parameters
        ----------
        student_id : str
        target_id  : str (opportunity_id / hackathon_id / paper_id)
        item_type  : "opportunity" | "hackathon" | "paper"
        students_df, items_df : override DataFrames (if engine not set)
        """
        sdf, idf, id_col, skill_col = self._resolve_dfs(item_type, students_df, items_df)

        student_row = sdf[sdf["student_id"] == student_id]
        if student_row.empty:
            raise KeyError(f"Student '{student_id}' not found.")
        student_row = student_row.iloc[0]

        item_row = idf[idf[id_col] == target_id]
        if item_row.empty:
            raise KeyError(f"Item '{target_id}' not found in {item_type}.")
        item_row = item_row.iloc[0]

        have = student_row["skills"] if isinstance(student_row["skills"], list) else []
        need = item_row[skill_col] if isinstance(item_row[skill_col], list) else []

        miss  = missing_skills(have, need)
        match = matched_skills_list(have, need)
        gap   = skill_gap_score(have, need)
        ready = readiness_score(have, need)

        return SkillGapReport(
            student_id=student_id,
            student_name=student_row.get("name", student_id),
            target_id=target_id,
            target_title=item_row.get("title", target_id),
            target_type=item_type,
            current_skills=sorted(have),
            required_skills=sorted(need),
            matched_skills=match,
            missing_skills=miss,
            gap_score=round(gap, 4),
            readiness_score=round(ready, 4),
            priority_skills_to_learn=_prioritise(miss),
        )

    def analyze_for_career_goal(
        self,
        student_id: str,
        goal: Optional[str] = None,
        students_df: Optional[pd.DataFrame] = None,
    ) -> SkillGapReport:
        """Analyse the skill gap between a student and their career goal.

        Parameters
        ----------
        student_id : str
        goal       : career goal string (defaults to student's career_goal field)
        students_df: override DataFrame (if engine not set)
        """
        sdf = students_df if students_df is not None else (
            self._engine._students_df if self._engine else None
        )
        if sdf is None:
            raise RuntimeError("Pass students_df or provide a fitted engine.")

        student_row = sdf[sdf["student_id"] == student_id]
        if student_row.empty:
            raise KeyError(f"Student '{student_id}' not found.")
        student_row = student_row.iloc[0]

        goal = goal or student_row.get("career_goal", "software engineer")
        goal_key = goal.strip().lower()
        need = CAREER_GOAL_SKILLS.get(goal_key, [])

        have = student_row["skills"] if isinstance(student_row["skills"], list) else []

        miss  = missing_skills(have, need)
        match = matched_skills_list(have, need)
        gap   = skill_gap_score(have, need)
        ready = readiness_score(have, need)

        return SkillGapReport(
            student_id=student_id,
            student_name=student_row.get("name", student_id),
            target_id=goal_key,
            target_title=goal,
            target_type="career_goal",
            current_skills=sorted(have),
            required_skills=sorted(need),
            matched_skills=match,
            missing_skills=miss,
            gap_score=round(gap, 4),
            readiness_score=round(ready, 4),
            priority_skills_to_learn=_prioritise(miss),
        )

    def analyze_all_for_student(
        self,
        student_id: str,
        top_k: int = 5,
        item_type: str = "opportunity",
        students_df: Optional[pd.DataFrame] = None,
        items_df: Optional[pd.DataFrame] = None,
    ) -> List[SkillGapReport]:
        """Analyse skill gaps for a student against their top-k recommendations.

        Items are pre-filtered to those closest to the student's skill set
        (highest readiness score) so the student sees achievable targets first.

        Returns
        -------
        List[SkillGapReport] sorted by readiness_score descending
        """
        sdf, idf, id_col, skill_col = self._resolve_dfs(item_type, students_df, items_df)

        student_row = sdf[sdf["student_id"] == student_id]
        if student_row.empty:
            raise KeyError(f"Student '{student_id}' not found.")
        student_row = student_row.iloc[0]
        have = student_row["skills"] if isinstance(student_row["skills"], list) else []

        reports = []
        for _, item_row in idf.iterrows():
            need = item_row[skill_col] if isinstance(item_row[skill_col], list) else []
            if not need:
                continue
            miss  = missing_skills(have, need)
            match = matched_skills_list(have, need)
            gap   = skill_gap_score(have, need)
            ready = readiness_score(have, need)
            reports.append(SkillGapReport(
                student_id=student_id,
                student_name=student_row.get("name", student_id),
                target_id=item_row[id_col],
                target_title=item_row.get("title", item_row[id_col]),
                target_type=item_type,
                current_skills=sorted(have),
                required_skills=sorted(need),
                matched_skills=match,
                missing_skills=miss,
                gap_score=round(gap, 4),
                readiness_score=round(ready, 4),
                priority_skills_to_learn=_prioritise(miss),
            ))

        reports.sort(key=lambda r: r.readiness_score, reverse=True)
        return reports[:top_k]

    # ── private ──────────────────────────────────────────────────────────────

    def _resolve_dfs(self, item_type, students_df, items_df):
        """Resolve DataFrames from engine or explicit arguments."""
        if self._engine is not None:
            sdf = students_df if students_df is not None else self._engine._students_df
            if item_type == "opportunity":
                idf, id_col, skill_col = self._engine._opps_df, "opportunity_id", "required_skills"
            elif item_type == "hackathon":
                idf, id_col, skill_col = self._engine._hackathons_df, "hackathon_id", "required_skills"
            else:
                idf, id_col, skill_col = self._engine._papers_df, "paper_id", "keywords"
            if items_df is not None:
                idf = items_df
        else:
            if students_df is None or items_df is None:
                raise RuntimeError("Pass students_df and items_df, or provide a fitted engine.")
            sdf = students_df
            if item_type == "opportunity":
                id_col, skill_col = "opportunity_id", "required_skills"
            elif item_type == "hackathon":
                id_col, skill_col = "hackathon_id", "required_skills"
            else:
                id_col, skill_col = "paper_id", "keywords"
            idf = items_df
        return sdf, idf, id_col, skill_col


# ===========================================================================
# 4.  CAREER  ROADMAP
# ===========================================================================

class CareerRoadmap:
    """Generates a personalised skill-acquisition roadmap for a student.

    Usage
    -----
    >>> roadmap_gen = CareerRoadmap(engine)
    >>> result = roadmap_gen.generate("S001")
    >>> for step in result.steps:
    ...     print(f"Step {step.step_number}: Learn {step.skill}  (~{step.estimated_weeks} weeks)")
    """

    def __init__(self, engine=None):
        self._engine = engine
        self._analyzer = SkillGapAnalyzer(engine)

    def generate(
        self,
        student_id: str,
        goal: Optional[str] = None,
        students_df: Optional[pd.DataFrame] = None,
    ) -> RoadmapResult:
        """Generate a career roadmap for an existing student.

        Parameters
        ----------
        student_id  : str
        goal        : override career goal (defaults to student's career_goal)
        students_df : override DataFrame
        """
        sdf = students_df if students_df is not None else (
            self._engine._students_df if self._engine else None
        )
        if sdf is None:
            raise RuntimeError("Pass students_df or provide a fitted engine.")

        student_row = sdf[sdf["student_id"] == student_id]
        if student_row.empty:
            raise KeyError(f"Student '{student_id}' not found.")
        student_row = student_row.iloc[0]

        have  = student_row["skills"] if isinstance(student_row["skills"], list) else []
        goal  = goal or student_row.get("career_goal", "software engineer")

        return self.generate_from_goal(
            skills=have,
            goal=goal,
            cgpa=float(student_row.get("cgpa", 0.0)),
            student_id=student_id,
            student_name=student_row.get("name", student_id),
        )

    def generate_from_goal(
        self,
        skills: List[str],
        goal: str,
        cgpa: float = 7.0,
        student_id: str = "NEW",
        student_name: str = "New Student",
    ) -> RoadmapResult:
        """Generate a roadmap given explicit skills and a goal string.

        Parameters
        ----------
        skills       : current skill list
        goal         : career goal (e.g. "Data Scientist")
        cgpa         : student's CGPA (used to adjust resource difficulty)
        student_id   : for labelling
        student_name : for labelling
        """
        goal_key  = goal.strip().lower()
        need      = CAREER_GOAL_SKILLS.get(goal_key, [])
        miss      = missing_skills(skills, need)
        have      = [s.strip().lower() for s in skills]
        already   = matched_skills_list(skills, need)

        if not need:
            log.warning("No skill map found for career goal '%s'. Using generic roadmap.", goal)
            need = ["problem solving", "communication", "project management"]
            miss = need

        ready_pct = 100.0 * (1.0 - skill_gap_score(skills, need))

        # Build ordered steps: tier-1 skills first → tier-3 last
        ordered_miss = _prioritise(miss)

        steps = []
        for i, skill in enumerate(ordered_miss, start=1):
            tier      = SKILL_DIFFICULTY.get(skill.lower(), 2)
            resources = SKILL_RESOURCES.get(skill.lower(), _DEFAULT_RESOURCE)
            reason    = _roadmap_reason(skill, goal, i, len(ordered_miss))
            steps.append(RoadmapStep(
                step_number=i,
                skill=skill,
                reason=reason,
                resource_type=_resource_type_for_skill(skill),
                suggested_resources=resources[:3],
                estimated_weeks=tier * 3,     # tier1=3w, tier2=6w, tier3=9w
            ))

        total_weeks = sum(s.estimated_weeks for s in steps)

        return RoadmapResult(
            student_id=student_id,
            student_name=student_name,
            career_goal=goal,
            current_skills=sorted(have),
            target_skills=sorted(need),
            already_have=sorted(already),
            steps=steps,
            total_estimated_weeks=total_weeks,
            readiness_percentage=round(ready_pct, 1),
        )


# ===========================================================================
# 5.  PRIVATE  HELPERS
# ===========================================================================

def _prioritise(miss: List[str]) -> List[str]:
    """Sort missing skills by tier (foundations first) then alphabetically."""
    return sorted(miss, key=lambda s: (SKILL_DIFFICULTY.get(s.lower(), 2), s))


def _roadmap_reason(skill: str, goal: str, step: int, total: int) -> str:
    """Generate a short human-readable reason for learning this skill now."""
    tier = SKILL_DIFFICULTY.get(skill.lower(), 2)
    if tier == 1:
        return f"Foundation skill required for all {goal} roles. Learn this first."
    elif tier == 2:
        return f"Core intermediate skill for {goal}. Build on your foundations."
    else:
        return f"Advanced specialisation skill — essential for senior {goal} positions."


def _resource_type_for_skill(skill: str) -> str:
    """Map a skill to the most appropriate resource type."""
    skill_l = skill.lower()
    if any(k in skill_l for k in ["project", "system design", "architecture"]):
        return "project"
    if any(k in skill_l for k in ["internship", "work experience"]):
        return "internship"
    if any(k in skill_l for k in ["hackathon", "competition"]):
        return "hackathon"
    return "course"


# ===========================================================================
# 6.  CLI
# ===========================================================================

if __name__ == "__main__":
    from ml.preprocessing import preprocess_all
    from ml.feature_engineering import build_all_features
    from ml.similarity import compute_all_similarities
    from ml.clustering import cluster_students
    from ml.recommendation_engine import RecommendationEngine

    data  = preprocess_all()
    feats = build_all_features(data)
    sims  = compute_all_similarities(feats, data["students"], data["opportunities"],
                                     data["papers"], data["hackathons"])
    model, labels = cluster_students(feats["student_matrix"])
    engine = RecommendationEngine()
    engine.fit(data, feats, sims, model, labels)

    analyzer = SkillGapAnalyzer(engine)
    roadmap  = CareerRoadmap(engine)

    # Gap analysis vs a specific opportunity
    report = analyzer.analyze("S001", "O001", "opportunity")
    print(f"\n{'='*60}")
    print(f"Skill Gap: {report.student_name} → {report.target_title}")
    print(f"  Readiness   : {report.readiness_score:.0%}")
    print(f"  Matched     : {report.matched_skills}")
    print(f"  Missing     : {report.missing_skills}")
    print(f"  Priority    : {report.priority_skills_to_learn}")

    # Career roadmap
    result = roadmap.generate("S001")
    print(f"\n{'='*60}")
    print(f"Career Roadmap: {result.student_name} → {result.career_goal}")
    print(f"  Readiness   : {result.readiness_percentage}%")
    print(f"  Total weeks : {result.total_estimated_weeks}")
    for step in result.steps:
        print(f"  Step {step.step_number}: {step.skill} (~{step.estimated_weeks} weeks)")
        print(f"    └ {step.suggested_resources[0]}")
