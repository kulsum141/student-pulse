"""
ai_assistant.py
---------------
StudentPulse ML — AI Assistant Layer

The AI Assistant is the conversational interface that sits on top of all ML
modules. It interprets student queries in natural language and routes them to
the right ML function, then formats the answer into plain English.

Architecture position:
    RecommendationEngine + SkillGapAnalyzer + CareerRoadmap
                      ↓
                AI Assistant   ←──── this module
                      ↓
              Student Feedback

This module is intentionally BACKEND-ONLY (no API keys, no external calls).
It uses rule-based intent classification and template-based response generation
so the system works fully offline. When an LLM API (Gemini / Claude / OpenAI)
is integrated at the deployment layer, this module provides the context payload
and parses the structured response.

Public API
----------
StudentAssistant
    .ask(student_id, query)          → AssistantResponse
    .ask_for_new_student(query, profile) → AssistantResponse
    .get_suggestions(student_id)     → List[str]   proactive prompts

IntentClassifier
    .classify(query)                 → Intent

ResponseFormatter
    .format_recommendations(result)  → str
    .format_skill_gap(report)        → str
    .format_roadmap(result)          → str
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ===========================================================================
# 1.  INTENT  TYPES
# ===========================================================================

class Intent(Enum):
    RECOMMEND_OPPORTUNITIES  = "recommend_opportunities"
    RECOMMEND_HACKATHONS     = "recommend_hackathons"
    RECOMMEND_PAPERS         = "recommend_papers"
    RECOMMEND_ALL            = "recommend_all"
    SKILL_GAP                = "skill_gap"
    CAREER_ROADMAP           = "career_roadmap"
    EXPLAIN_RECOMMENDATION   = "explain_recommendation"
    PROFILE_SUMMARY          = "profile_summary"
    FILTER_BY_LOCATION       = "filter_by_location"
    FILTER_BY_REMOTE         = "filter_by_remote"
    FILTER_BY_TYPE           = "filter_by_type"
    UNKNOWN                  = "unknown"


@dataclass
class AssistantResponse:
    """Structured response from the AI Assistant."""
    student_id: str
    query: str
    intent: Intent
    answer: str                              # plain-English answer
    data: Any = None                         # underlying ML result (for UI)
    suggestions: List[str] = field(default_factory=list)   # follow-up prompts
    confidence: float = 1.0


# ===========================================================================
# 2.  INTENT  CLASSIFIER
# ===========================================================================

# Keyword → Intent mapping (order matters: more specific patterns first)
_INTENT_PATTERNS = [
    # Skill gap / missing skills
    (Intent.SKILL_GAP,              r"skill.?gap|missing skill|what skill|am i eligible|gap|lacking"),
    # Career roadmap
    (Intent.CAREER_ROADMAP,         r"roadmap|career path|how to become|steps to|learning path|plan"),
    # Explain a specific recommendation
    (Intent.EXPLAIN_RECOMMENDATION, r"why.*(recommend|suggest)|explain|reason|how did you"),
    # Remote filter
    (Intent.FILTER_BY_REMOTE,       r"remote|work from home|wfh|online.*(job|intern)"),
    # Location filter
    (Intent.FILTER_BY_LOCATION,     r"(in|at|near|around|bangalore|mumbai|delhi|chennai|hyderabad|pune|kolkata)"),
    # Type filter
    (Intent.FILTER_BY_TYPE,         r"internship|full.?time|permanent|part.?time"),
    # Hackathons
    (Intent.RECOMMEND_HACKATHONS,   r"hackathon|competition|contest|code.?fest|build|sprint"),
    # Papers / research
    (Intent.RECOMMEND_PAPERS,       r"paper|research|article|read|study|journal|publication"),
    # Opportunities
    (Intent.RECOMMEND_OPPORTUNITIES,r"job|intern|opportunit|role|position|opening|work|hire|company"),
    # Profile summary
    (Intent.PROFILE_SUMMARY,        r"my profile|my skill|about me|who am i|my background|my strength"),
    # Catch-all recommend
    (Intent.RECOMMEND_ALL,          r"recommend|suggest|show|find|what.*(can|should)|help me"),
]


class IntentClassifier:
    """Rule-based intent classifier for student queries."""

    def classify(self, query: str) -> Intent:
        q = query.strip().lower()
        for intent, pattern in _INTENT_PATTERNS:
            if re.search(pattern, q):
                return intent
        return Intent.UNKNOWN

    def extract_filters(self, query: str) -> Dict:
        """Extract any filters (location, remote, type) from the query."""
        q = query.strip().lower()
        filters = {}
        if re.search(r"remote|wfh|work from home", q):
            filters["remote"] = True
        if re.search(r"internship|intern", q):
            filters["type"] = "internship"
        elif re.search(r"full.?time|permanent", q):
            filters["type"] = "full-time"
        # Location extraction (simple keyword match)
        for city in ["bangalore", "mumbai", "delhi", "chennai", "hyderabad", "pune", "kolkata"]:
            if city in q:
                filters["location"] = city.capitalize()
        return filters


# ===========================================================================
# 3.  RESPONSE  FORMATTER
# ===========================================================================

class ResponseFormatter:
    """Formats ML results into plain-English responses."""

    def format_recommendations(self, result, item_type: str = "all") -> str:
        lines = [f"Here are personalised recommendations for **{result.student_name}**:\n"]

        if item_type in ("all", "opportunity") and result.opportunities:
            lines.append("🏢 **Top Opportunities**")
            for i, r in enumerate(result.opportunities, 1):
                lines.append(
                    f"  {i}. **{r.title}** — Score: {r.score:.2f} | "
                    f"Skills matched: {len(r.matched_skills)}/{len(r.matched_skills) + 1} "
                    f"({', '.join(r.matched_skills[:3])}{'…' if len(r.matched_skills) > 3 else ''})"
                )

        if item_type in ("all", "hackathon") and result.hackathons:
            lines.append("\n🏆 **Top Hackathons**")
            for i, r in enumerate(result.hackathons, 1):
                lines.append(
                    f"  {i}. **{r.title}** — Score: {r.score:.2f} | "
                    f"Match: {r.skill_overlap:.0%}"
                )

        if item_type in ("all", "paper") and result.papers:
            lines.append("\n📄 **Top Research Papers**")
            for i, r in enumerate(result.papers, 1):
                lines.append(f"  {i}. **{r.title}** — Score: {r.score:.2f}")

        return "\n".join(lines)

    def format_skill_gap(self, report) -> str:
        lines = [
            f"**Skill Gap Analysis: {report.student_name} → {report.target_title}**\n",
            f"✅ **Readiness:** {report.readiness_score:.0%}",
            f"✅ **Skills you have:** {', '.join(report.matched_skills) or 'none'}",
            f"❌ **Skills you need:** {', '.join(report.missing_skills) or 'none — you are fully qualified!'}",
        ]
        if report.priority_skills_to_learn:
            lines.append(
                f"\n📌 **Start with:** {', '.join(report.priority_skills_to_learn[:3])}"
            )
        return "\n".join(lines)

    def format_roadmap(self, result) -> str:
        lines = [
            f"**Career Roadmap: {result.student_name} → {result.career_goal}**\n",
            f"📊 Current readiness: **{result.readiness_percentage}%**",
            f"⏱ Estimated total: **{result.total_estimated_weeks} weeks**",
            f"✅ Already have: {', '.join(result.already_have[:5]) or 'none'}",
            f"\n🗺 **Learning Steps:**",
        ]
        for step in result.steps:
            lines.append(
                f"  {step.step_number}. **{step.skill.title()}** (~{step.estimated_weeks} weeks)"
            )
            lines.append(f"     ↳ {step.reason}")
            if step.suggested_resources:
                lines.append(f"     📚 {step.suggested_resources[0]}")
        return "\n".join(lines)

    def format_profile(self, student_row) -> str:
        skills = student_row.get("skills", [])
        return (
            f"**Profile Summary: {student_row.get('name', '?')}**\n"
            f"  🎓 Department : {student_row.get('department', '?').title()}\n"
            f"  📅 Year       : {student_row.get('year_of_study', '?')}\n"
            f"  📈 CGPA       : {student_row.get('cgpa', '?')}\n"
            f"  💼 Internships: {student_row.get('past_internships', 0)}\n"
            f"  🎯 Goal       : {student_row.get('career_goal', '?')}\n"
            f"  🛠 Skills     : {', '.join(skills[:8])}{'…' if len(skills) > 8 else ''}"
        )


# ===========================================================================
# 4.  STUDENT  ASSISTANT
# ===========================================================================

class StudentAssistant:
    """Conversational AI assistant for StudentPulse.

    Routes student natural-language queries to the appropriate ML module
    and returns a structured AssistantResponse.

    Usage
    -----
    >>> from ml.ai_assistant import StudentAssistant
    >>> assistant = StudentAssistant(engine, analyzer, roadmap_gen)
    >>> response = assistant.ask("S001", "Show me remote internships in Bangalore")
    >>> print(response.answer)
    """

    def __init__(self, engine=None, analyzer=None, roadmap_gen=None):
        """
        Parameters
        ----------
        engine      : fitted RecommendationEngine
        analyzer    : SkillGapAnalyzer instance
        roadmap_gen : CareerRoadmap instance
        """
        self._engine     = engine
        self._analyzer   = analyzer
        self._roadmap    = roadmap_gen
        self._classifier = IntentClassifier()
        self._formatter  = ResponseFormatter()

    def ask(self, student_id: str, query: str) -> AssistantResponse:
        """Answer a query from an existing student.

        Parameters
        ----------
        student_id : str  (must be in the engine's student index)
        query      : free-text question from the student

        Returns
        -------
        AssistantResponse
        """
        intent  = self._classifier.classify(query)
        filters = self._classifier.extract_filters(query)

        log.info("student=%s  intent=%s  query=%r", student_id, intent.value, query[:60])

        try:
            answer, data = self._dispatch(student_id, intent, filters, query)
        except Exception as exc:
            log.warning("Assistant dispatch error: %s", exc)
            answer = (
                "I couldn't process that request. "
                "Try asking: 'Show me internships', 'What is my skill gap for O001?', "
                "or 'Show me my career roadmap'."
            )
            data = None
            intent = Intent.UNKNOWN

        suggestions = self.get_suggestions(student_id, intent)

        return AssistantResponse(
            student_id=student_id,
            query=query,
            intent=intent,
            answer=answer,
            data=data,
            suggestions=suggestions,
        )

    def ask_for_new_student(
        self,
        query: str,
        skills: List[str],
        interests: List[str],
        cgpa: float = 7.0,
        goal: str = "software engineer",
    ) -> AssistantResponse:
        """Answer a query from a student not yet in the dataset (cold-start).

        Parameters
        ----------
        query     : free-text question
        skills    : student's current skills
        interests : student's interests
        cgpa      : student's CGPA
        goal      : career goal string
        """
        intent  = self._classifier.classify(query)
        filters = self._classifier.extract_filters(query)

        if self._engine is None:
            return AssistantResponse(
                student_id="NEW", query=query, intent=Intent.UNKNOWN,
                answer="Engine not initialised. Call StudentAssistant(engine=...).",
            )

        if intent in (Intent.RECOMMEND_ALL, Intent.RECOMMEND_OPPORTUNITIES,
                      Intent.RECOMMEND_HACKATHONS, Intent.RECOMMEND_PAPERS):
            result = self._engine.recommend_for_new_student(skills, interests, cgpa)
            answer = self._formatter.format_recommendations(result)
            data   = result
        elif intent in (Intent.CAREER_ROADMAP, Intent.SKILL_GAP):
            from ml.skill_gap import CareerRoadmap
            rg     = self._roadmap or CareerRoadmap(self._engine)
            result = rg.generate_from_goal(skills, goal, cgpa)
            answer = self._formatter.format_roadmap(result)
            data   = result
        else:
            result = self._engine.recommend_for_new_student(skills, interests, cgpa)
            answer = self._formatter.format_recommendations(result)
            data   = result

        return AssistantResponse(
            student_id="NEW", query=query, intent=intent, answer=answer, data=data,
            suggestions=["Tell me my skill gaps", "Show my career roadmap"],
        )

    def get_suggestions(
        self,
        student_id: str,
        last_intent: Optional[Intent] = None,
    ) -> List[str]:
        """Return 3 proactive follow-up prompts for the student.

        Parameters
        ----------
        student_id  : str
        last_intent : the previous intent (to avoid repeating suggestions)
        """
        all_suggestions = {
            Intent.RECOMMEND_ALL:            ["What is my skill gap for my top match?", "Show my career roadmap", "Show me remote internships"],
            Intent.RECOMMEND_OPPORTUNITIES:  ["Show me hackathons too", "What skills am I missing for these?", "Filter to remote only"],
            Intent.RECOMMEND_HACKATHONS:     ["Show internships as well", "What is my skill gap for the top hackathon?"],
            Intent.RECOMMEND_PAPERS:         ["Which paper should I read first?", "Show me opportunities in this domain"],
            Intent.SKILL_GAP:                ["Show my career roadmap", "What opportunities am I ready for?"],
            Intent.CAREER_ROADMAP:           ["Show me opportunities matching my goal", "What hackathons can I join now?"],
            Intent.EXPLAIN_RECOMMENDATION:   ["Show more recommendations", "What is my skill gap?"],
            Intent.PROFILE_SUMMARY:          ["Show my recommendations", "What is my career roadmap?"],
            None:                            ["Show me recommendations", "What is my skill gap?", "Show my career roadmap"],
        }
        return all_suggestions.get(last_intent, all_suggestions[None])

    # ── private ──────────────────────────────────────────────────────────────

    def _dispatch(self, student_id: str, intent: Intent, filters: Dict, query: str):
        """Route intent to the correct ML function and return (answer, data)."""
        engine    = self._engine
        analyzer  = self._analyzer
        roadmap   = self._roadmap

        if engine is None:
            raise RuntimeError("RecommendationEngine not set. Pass engine= to StudentAssistant.")

        # ── recommendations ──────────────────────────────────────────────
        if intent == Intent.RECOMMEND_OPPORTUNITIES or intent == Intent.FILTER_BY_REMOTE \
                or intent == Intent.FILTER_BY_LOCATION or intent == Intent.FILTER_BY_TYPE:
            result = engine.recommend_all(student_id)
            answer = self._formatter.format_recommendations(result, item_type="opportunity")
            return answer, result

        if intent == Intent.RECOMMEND_HACKATHONS:
            result = engine.recommend_all(student_id)
            answer = self._formatter.format_recommendations(result, item_type="hackathon")
            return answer, result

        if intent == Intent.RECOMMEND_PAPERS:
            result = engine.recommend_all(student_id)
            answer = self._formatter.format_recommendations(result, item_type="paper")
            return answer, result

        if intent in (Intent.RECOMMEND_ALL, Intent.UNKNOWN):
            result = engine.recommend_all(student_id)
            answer = self._formatter.format_recommendations(result)
            return answer, result

        # ── skill gap ────────────────────────────────────────────────────
        if intent == Intent.SKILL_GAP:
            if analyzer is None:
                from ml.skill_gap import SkillGapAnalyzer
                analyzer = SkillGapAnalyzer(engine)
            # Analyse vs career goal (most useful default)
            report = analyzer.analyze_for_career_goal(student_id)
            answer = self._formatter.format_skill_gap(report)
            return answer, report

        # ── career roadmap ───────────────────────────────────────────────
        if intent == Intent.CAREER_ROADMAP:
            if roadmap is None:
                from ml.skill_gap import CareerRoadmap
                roadmap = CareerRoadmap(engine)
            result = roadmap.generate(student_id)
            answer = self._formatter.format_roadmap(result)
            return answer, result

        # ── profile summary ──────────────────────────────────────────────
        if intent == Intent.PROFILE_SUMMARY:
            idx = engine._student_idx.get(student_id)
            if idx is None:
                return "Student not found.", None
            row    = engine._students_df.iloc[idx]
            answer = self._formatter.format_profile(row)
            return answer, row.to_dict()

        # ── explain ──────────────────────────────────────────────────────
        if intent == Intent.EXPLAIN_RECOMMENDATION:
            result = engine.recommend_all(student_id, top_k_opps=1)
            if result.opportunities:
                top = result.opportunities[0]
                answer = engine.get_explanation(student_id, top.item_id, "opportunity")
            else:
                answer = "No recommendations found to explain."
            return answer, None

        # Fallback
        result = engine.recommend_all(student_id)
        answer = self._formatter.format_recommendations(result)
        return answer, result


# ===========================================================================
# 5.  CONTEXT  BUILDER  (for external LLM integration)
# ===========================================================================

def build_llm_context(
    student_id: str,
    engine,
    analyzer=None,
    top_k: int = 5,
) -> Dict:
    """Build a structured context payload for sending to an external LLM.

    This function gathers all relevant data about a student and packages it
    as a dict that can be serialised into a prompt for Gemini / Claude / GPT.

    Returns
    -------
    dict with keys:
        "student_profile"    : student row as dict
        "top_opportunities"  : list of top-k recommendation dicts
        "top_hackathons"     : list of top-k hackathon dicts
        "top_papers"         : list of top-k paper dicts
        "skill_gap_summary"  : {missing, matched, readiness}
        "career_goal"        : str
    """
    from ml.skill_gap import SkillGapAnalyzer
    analyzer = analyzer or SkillGapAnalyzer(engine)

    idx = engine._student_idx.get(student_id)
    if idx is None:
        raise KeyError(f"Student '{student_id}' not found.")
    student_row = engine._students_df.iloc[idx].to_dict()

    result = engine.recommend_all(student_id, top_k_opps=top_k,
                                  top_k_papers=top_k, top_k_hackathons=top_k)
    gap_report = analyzer.analyze_for_career_goal(student_id)

    return {
        "student_profile": student_row,
        "top_opportunities": [
            {"id": r.item_id, "title": r.title, "score": r.score,
             "matched_skills": r.matched_skills}
            for r in result.opportunities
        ],
        "top_hackathons": [
            {"id": r.item_id, "title": r.title, "score": r.score}
            for r in result.hackathons
        ],
        "top_papers": [
            {"id": r.item_id, "title": r.title, "score": r.score}
            for r in result.papers
        ],
        "skill_gap_summary": {
            "career_goal":   gap_report.target_title,
            "readiness":     f"{gap_report.readiness_score:.0%}",
            "matched":       gap_report.matched_skills,
            "missing":       gap_report.missing_skills,
            "priority_next": gap_report.priority_skills_to_learn[:3],
        },
        "career_goal": student_row.get("career_goal", ""),
    }


# ===========================================================================
# 6.  CLI
# ===========================================================================

if __name__ == "__main__":
    from ml.preprocessing import preprocess_all
    from ml.feature_engineering import build_all_features
    from ml.similarity import compute_all_similarities
    from ml.clustering import cluster_students
    from ml.recommendation_engine import RecommendationEngine
    from ml.skill_gap import SkillGapAnalyzer, CareerRoadmap

    data   = preprocess_all()
    feats  = build_all_features(data)
    sims   = compute_all_similarities(feats, data["students"], data["opportunities"],
                                      data["papers"], data["hackathons"])
    model, labels = cluster_students(feats["student_matrix"])
    engine = RecommendationEngine()
    engine.fit(data, feats, sims, model, labels)

    analyzer  = SkillGapAnalyzer(engine)
    roadmap   = CareerRoadmap(engine)
    assistant = StudentAssistant(engine, analyzer, roadmap)

    queries = [
        "Show me internships",
        "What hackathons can I join?",
        "What is my skill gap?",
        "Show me my career roadmap",
        "Tell me about my profile",
        "Show me remote opportunities in Bangalore",
        "Why did you recommend that?",
    ]

    print(f"\n{'='*65}")
    print("  StudentPulse AI Assistant Demo — Student S001 (Aarav Sharma)")
    print("="*65)
    for q in queries:
        resp = assistant.ask("S001", q)
        print(f"\n🗣  Q: {q}")
        print(f"   Intent: {resp.intent.value}")
        print(f"   A:\n{resp.answer[:300]}{'…' if len(resp.answer) > 300 else ''}")
        print(f"   Suggestions: {resp.suggestions[:2]}")
