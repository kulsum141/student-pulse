"""
ml_service.py
-------------
Adapter / singleton that wraps the existing ML RecommendationEngine.
All API routes call this service rather than importing ML code directly.
The engine is loaded ONCE at startup from the pre-trained artefact.
"""
import logging
import pickle
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_ENGINE = None
_ENGINE_STATUS = "not_loaded"

_ARTEFACT_PATH = Path(__file__).parent.parent.parent / "ml" / "data" / "artefacts" / "engine.pkl"


def _load_engine():
    global _ENGINE, _ENGINE_STATUS
    try:
        if not _ARTEFACT_PATH.exists():
            log.warning("No engine.pkl found at %s. Running training pipeline…", _ARTEFACT_PATH)
            from ml.train import train
            _ENGINE = train()
            _ENGINE_STATUS = "trained_fresh"
        else:
            with open(_ARTEFACT_PATH, "rb") as f:
                _ENGINE = pickle.load(f)
            # Re-attach auxiliary modules if missing (older pickle)
            if _ENGINE._skill_gap_analyzer is None:
                from ml.skill_gap import SkillGapAnalyzer, CareerRoadmap
                from ml.ai_assistant import StudentAssistant
                from ml.feedback import FeedbackStore, PersonalizationLayer
                analyzer = SkillGapAnalyzer(_ENGINE)
                roadmap  = CareerRoadmap(_ENGINE)
                store    = FeedbackStore()
                pl       = PersonalizationLayer(store)
                assistant = StudentAssistant(_ENGINE, analyzer, roadmap)
                _ENGINE._skill_gap_analyzer = analyzer
                _ENGINE._career_roadmap     = roadmap
                _ENGINE._feedback_store     = store
                _ENGINE._personalization    = pl
                _ENGINE._assistant          = assistant
            _ENGINE_STATUS = "loaded"
            log.info("ML engine loaded from %s", _ARTEFACT_PATH)
    except Exception as exc:
        log.error("Failed to load ML engine: %s", exc)
        _ENGINE_STATUS = f"error: {exc}"
        _ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _load_engine()
    return _ENGINE


def get_engine_status() -> str:
    return _ENGINE_STATUS


# ── Convenience wrappers ──────────────────────────────────────────────────────

def get_all_students() -> list:
    engine = get_engine()
    if engine is None:
        return []
    return engine._students_df.to_dict(orient="records")


def get_student(student_id: str) -> Optional[dict]:
    engine = get_engine()
    if engine is None:
        return None
    df = engine._students_df
    row = df[df["student_id"] == student_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def recommend_all(student_id: str, top_k_opps=5, top_k_papers=5, top_k_hackathons=5):
    engine = get_engine()
    if engine is None:
        return None
    return engine.recommend_all(student_id, top_k_opps, top_k_papers, top_k_hackathons)


def recommend_for_new(skills, interests, cgpa=7.0, top_k=5):
    engine = get_engine()
    if engine is None:
        return None
    return engine.recommend_for_new_student(skills, interests, cgpa, top_k)


def get_skill_gap(student_id: str, target_id: Optional[str] = None, item_type: str = "opportunity"):
    engine = get_engine()
    if engine is None:
        return None
    analyzer = engine._skill_gap_analyzer
    if analyzer is None:
        from ml.skill_gap import SkillGapAnalyzer
        analyzer = SkillGapAnalyzer(engine)
    if target_id:
        return analyzer.analyze(student_id, target_id, item_type)
    return analyzer.analyze_for_career_goal(student_id)


def get_skill_gap_all(student_id: str, top_k: int = 5, item_type: str = "opportunity"):
    engine = get_engine()
    if engine is None:
        return []
    analyzer = engine._skill_gap_analyzer
    if analyzer is None:
        from ml.skill_gap import SkillGapAnalyzer
        analyzer = SkillGapAnalyzer(engine)
    return analyzer.analyze_all_for_student(student_id, top_k=top_k, item_type=item_type)


def get_roadmap(student_id: str, goal: Optional[str] = None):
    engine = get_engine()
    if engine is None:
        return None
    roadmap = engine._career_roadmap
    if roadmap is None:
        from ml.skill_gap import CareerRoadmap
        roadmap = CareerRoadmap(engine)
    return roadmap.generate(student_id, goal=goal)


def ask_assistant(student_id: str, query: str):
    engine = get_engine()
    if engine is None:
        return None
    assistant = engine._assistant
    if assistant is None:
        from ml.ai_assistant import StudentAssistant
        from ml.skill_gap import SkillGapAnalyzer, CareerRoadmap
        assistant = StudentAssistant(engine, SkillGapAnalyzer(engine), CareerRoadmap(engine))
    return assistant.ask(student_id, query)


def get_internships(student_id: Optional[str] = None, top_k: int = 10, filters: Optional[dict] = None):
    engine = get_engine()
    if engine is None:
        return []
    if student_id:
        recs = engine.recommend_opportunities(student_id, top_k=top_k, filters=filters)
        return recs
    # Return raw dataframe rows for browse mode
    df = engine._opps_df
    if filters:
        for col, val in filters.items():
            if col in df.columns:
                df = df[df[col].astype(str).str.lower() == str(val).lower()]
    return df.head(top_k).to_dict(orient="records")


def get_hackathons(student_id: Optional[str] = None, top_k: int = 10, filters: Optional[dict] = None):
    engine = get_engine()
    if engine is None:
        return []
    if student_id:
        recs = engine.recommend_hackathons(student_id, top_k=top_k, filters=filters)
        return recs
    df = engine._hackathons_df
    if filters:
        for col, val in filters.items():
            if col in df.columns:
                df = df[df[col].astype(str).str.lower() == str(val).lower()]
    return df.head(top_k).to_dict(orient="records")


def get_research(student_id: Optional[str] = None, top_k: int = 10, filters: Optional[dict] = None):
    engine = get_engine()
    if engine is None:
        return []
    if student_id:
        recs = engine.recommend_papers(student_id, top_k=top_k, filters=filters)
        return recs
    df = engine._papers_df
    return df.head(top_k).to_dict(orient="records")


def record_feedback(student_id: str, item_id: str, item_type: str, feedback_type: str):
    engine = get_engine()
    if engine is None or engine._feedback_store is None:
        return False
    try:
        engine._feedback_store.record(student_id, item_id, item_type, feedback_type)
        return True
    except Exception:
        return False


def save_preferences(student_id: str, prefs: dict):
    """Store preferences in a simple JSON sidecar file."""
    import json
    prefs_dir = Path(__file__).parent.parent.parent / "ml" / "data"
    prefs_file = prefs_dir / "user_preferences.json"
    all_prefs = {}
    if prefs_file.exists():
        with open(prefs_file) as f:
            all_prefs = json.load(f)
    all_prefs[student_id] = prefs
    with open(prefs_file, "w") as f:
        json.dump(all_prefs, f, indent=2)
    return True


def load_preferences(student_id: str) -> dict:
    import json
    prefs_dir = Path(__file__).parent.parent.parent / "ml" / "data"
    prefs_file = prefs_dir / "user_preferences.json"
    if not prefs_file.exists():
        return {}
    with open(prefs_file) as f:
        all_prefs = json.load(f)
    return all_prefs.get(student_id, {})
