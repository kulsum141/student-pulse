"""
feedback.py
-----------
StudentPulse ML — Student Feedback + Future Personalization

Collects explicit and implicit feedback from students on recommendations,
stores it persistently in a JSON/CSV log, and re-weights the recommendation
engine's scoring based on accumulated feedback.

Architecture position:
    AI Assistant
         ↓
    Student Feedback    ←──── this module
         ↓
    Future Personalization ←── this module

Feedback types
--------------
* THUMBS_UP   : student liked / clicked a recommendation
* THUMBS_DOWN : student dismissed / disliked a recommendation
* APPLIED     : student applied to an opportunity / registered for a hackathon
* SAVED       : student bookmarked an item
* IGNORED     : item shown but never interacted with (implicit negative)

Personalization strategy
------------------------
1. Accumulate per-student interaction counts per item.
2. Derive a "preference signal" per item domain/type/skill.
3. When scoring items, multiply the base score by a personalization factor
   derived from past positive/negative interactions.
4. Items in "liked" domains get a boost; "disliked" domains get a penalty.

Public API
----------
FeedbackStore
    .record(student_id, item_id, item_type, feedback_type, context)
    .get_student_feedback(student_id)
    .get_item_stats(item_id)
    .export_csv(path)
    .load_csv(path)

PersonalizationLayer
    .apply(student_id, recommendations)  → re-ranked List[Recommendation]
    .preference_profile(student_id)      → PreferenceProfile
"""

import csv
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

_HERE = Path(__file__).parent
DEFAULT_FEEDBACK_CSV  = _HERE / "data" / "feedback_log.csv"
DEFAULT_FEEDBACK_JSON = _HERE / "data" / "feedback_log.json"


# ===========================================================================
# 1.  FEEDBACK  TYPES
# ===========================================================================

class FeedbackType(str, Enum):
    THUMBS_UP   = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    APPLIED     = "applied"
    SAVED       = "saved"
    IGNORED     = "ignored"

# Numeric weights per feedback type (positive = boost, negative = penalty)
FEEDBACK_WEIGHTS: Dict[str, float] = {
    FeedbackType.APPLIED:     +1.0,
    FeedbackType.SAVED:       +0.6,
    FeedbackType.THUMBS_UP:   +0.4,
    FeedbackType.IGNORED:     -0.1,
    FeedbackType.THUMBS_DOWN: -0.5,
}


# ===========================================================================
# 2.  DATA  CLASSES
# ===========================================================================

@dataclass
class FeedbackRecord:
    """A single feedback event from a student on a recommendation."""
    feedback_id:   str
    student_id:    str
    item_id:       str
    item_type:     str                   # "opportunity" | "hackathon" | "paper"
    feedback_type: str                   # FeedbackType value
    timestamp:     str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    item_title:    str = ""
    item_domain:   str = ""
    item_skills:   str = ""              # comma-separated skills of the item
    score_at_time: float = 0.0           # engine score when shown


@dataclass
class PreferenceProfile:
    """Derived preference profile for one student based on their feedback."""
    student_id: str
    liked_domains:    List[str] = field(default_factory=list)
    disliked_domains: List[str] = field(default_factory=list)
    liked_skills:     List[str] = field(default_factory=list)
    disliked_skills:  List[str] = field(default_factory=list)
    applied_count:    int = 0
    saved_count:      int = 0
    total_feedback:   int = 0
    engagement_rate:  float = 0.0         # positive events / total shown


# ===========================================================================
# 3.  FEEDBACK  STORE
# ===========================================================================

class FeedbackStore:
    """Persistent feedback log for student-recommendation interactions.

    Feedback is stored in-memory and optionally synced to CSV/JSON on disk.

    Usage
    -----
    >>> store = FeedbackStore()
    >>> store.record("S001", "O001", "opportunity", FeedbackType.APPLIED,
    ...              item_title="ML Intern", item_domain="data science")
    >>> store.export_csv("feedback_log.csv")
    """

    def __init__(self, path: Optional[Path] = None):
        """
        Parameters
        ----------
        path : optional path to a CSV file for persistent storage.
               If it exists, records are loaded on init.
        """
        self._records: List[FeedbackRecord] = []
        self._path = Path(path) if path else DEFAULT_FEEDBACK_CSV
        self._counter = 0

        # Auto-load existing log if present
        if self._path.exists():
            self.load_csv(self._path)

    def record(
        self,
        student_id: str,
        item_id:    str,
        item_type:  str,
        feedback_type: FeedbackType,
        item_title:  str = "",
        item_domain: str = "",
        item_skills: str = "",
        score_at_time: float = 0.0,
    ) -> FeedbackRecord:
        """Record one feedback event.

        Parameters
        ----------
        student_id    : student who gave feedback
        item_id       : the recommended item
        item_type     : "opportunity" | "hackathon" | "paper"
        feedback_type : FeedbackType enum value
        item_title    : human-readable title (for logs)
        item_domain   : domain of the item (for preference learning)
        item_skills   : comma-separated skills (for preference learning)
        score_at_time : the engine's score when the item was shown

        Returns
        -------
        FeedbackRecord
        """
        self._counter += 1
        rec = FeedbackRecord(
            feedback_id   = f"FB{self._counter:06d}",
            student_id    = student_id,
            item_id       = item_id,
            item_type     = item_type,
            feedback_type = str(feedback_type),
            item_title    = item_title,
            item_domain   = item_domain,
            item_skills   = item_skills,
            score_at_time = score_at_time,
        )
        self._records.append(rec)
        log.info(
            "Feedback recorded: student=%s  item=%s  type=%s",
            student_id, item_id, feedback_type
        )
        return rec

    def get_student_feedback(self, student_id: str) -> List[FeedbackRecord]:
        """Return all feedback records for a given student."""
        return [r for r in self._records if r.student_id == student_id]

    def get_item_stats(self, item_id: str) -> Dict:
        """Return aggregate stats for an item across all students.

        Returns
        -------
        dict with keys: item_id, total_interactions, by_type (counts)
        """
        recs = [r for r in self._records if r.item_id == item_id]
        by_type: Dict[str, int] = {}
        for r in recs:
            by_type[r.feedback_type] = by_type.get(r.feedback_type, 0) + 1
        return {
            "item_id":            item_id,
            "total_interactions": len(recs),
            "by_type":            by_type,
            "net_score":          sum(
                FEEDBACK_WEIGHTS.get(r.feedback_type, 0) for r in recs
            ),
        }

    def summary(self) -> Dict:
        """Return a summary of all feedback collected."""
        from collections import Counter
        type_counts = Counter(r.feedback_type for r in self._records)
        student_counts = Counter(r.student_id for r in self._records)
        return {
            "total_records": len(self._records),
            "unique_students": len(student_counts),
            "by_feedback_type": dict(type_counts),
            "top_students_by_activity": student_counts.most_common(5),
        }

    # ── persistence ──────────────────────────────────────────────────────

    def export_csv(self, path: Optional[Path] = None) -> Path:
        """Export all feedback records to a CSV file."""
        path = Path(path or self._path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(FeedbackRecord.__dataclass_fields__.keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rec in self._records:
                writer.writerow(asdict(rec))
        log.info("Feedback exported → %s  (%d records)", path, len(self._records))
        return path

    def load_csv(self, path: Path) -> int:
        """Load feedback records from a CSV file.  Returns number loaded."""
        path = Path(path)
        if not path.exists():
            return 0
        loaded = 0
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self._records.append(FeedbackRecord(**{
                    k: (float(row[k]) if k == "score_at_time" else row[k])
                    for k in FeedbackRecord.__dataclass_fields__
                    if k in row
                }))
                loaded += 1
        self._counter = max((int(r.feedback_id.replace("FB", "") or 0) for r in self._records), default=0)
        log.info("Feedback loaded ← %s  (%d records)", path, loaded)
        return loaded

    def export_json(self, path: Optional[Path] = None) -> Path:
        """Export feedback records as JSON (for API consumption)."""
        path = Path(path or DEFAULT_FEEDBACK_JSON)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in self._records], f, indent=2)
        log.info("Feedback JSON exported → %s", path)
        return path


# ===========================================================================
# 4.  PERSONALIZATION  LAYER
# ===========================================================================

class PersonalizationLayer:
    """Re-ranks recommendations using accumulated student feedback.

    Strategy
    --------
    1. Build a preference profile from the student's feedback history.
    2. For each recommendation, compute a personalization multiplier:
       - Items in liked domains  → multiplier > 1.0 (boost)
       - Items in disliked domains → multiplier < 1.0 (penalty)
       - Items with liked skills → small additional boost
    3. Final score = base_score × personalization_multiplier.

    Usage
    -----
    >>> pl = PersonalizationLayer(store)
    >>> reranked = pl.apply("S001", result.opportunities)
    """

    def __init__(self, store: FeedbackStore):
        self._store = store

    def preference_profile(self, student_id: str) -> PreferenceProfile:
        """Derive the student's preference profile from their feedback history.

        Returns
        -------
        PreferenceProfile
        """
        records = self._store.get_student_feedback(student_id)

        liked_domains:    Dict[str, float] = {}
        disliked_domains: Dict[str, float] = {}
        liked_skills:     Dict[str, float] = {}
        disliked_skills:  Dict[str, float] = {}
        applied = saved = 0

        for rec in records:
            weight = FEEDBACK_WEIGHTS.get(rec.feedback_type, 0.0)
            domain = rec.item_domain.strip().lower()
            skills = [s.strip().lower() for s in rec.item_skills.split(",") if s.strip()]

            if rec.feedback_type == FeedbackType.APPLIED:
                applied += 1
            if rec.feedback_type == FeedbackType.SAVED:
                saved += 1

            if weight > 0:
                liked_domains[domain]  = liked_domains.get(domain, 0) + weight
                for sk in skills:
                    liked_skills[sk] = liked_skills.get(sk, 0) + weight
            elif weight < 0:
                disliked_domains[domain]  = disliked_domains.get(domain, 0) + abs(weight)
                for sk in skills:
                    disliked_skills[sk] = disliked_skills.get(sk, 0) + abs(weight)

        total = len(records)
        positive = sum(1 for r in records if FEEDBACK_WEIGHTS.get(r.feedback_type, 0) > 0)
        engagement = positive / total if total > 0 else 0.0

        return PreferenceProfile(
            student_id=student_id,
            liked_domains=sorted(liked_domains, key=liked_domains.get, reverse=True)[:5],
            disliked_domains=sorted(disliked_domains, key=disliked_domains.get, reverse=True)[:5],
            liked_skills=sorted(liked_skills, key=liked_skills.get, reverse=True)[:10],
            disliked_skills=sorted(disliked_skills, key=disliked_skills.get, reverse=True)[:10],
            applied_count=applied,
            saved_count=saved,
            total_feedback=total,
            engagement_rate=round(engagement, 3),
        )

    def apply(self, student_id: str, recommendations: list, engine=None) -> list:
        """Re-rank a list of Recommendation objects using feedback signals.

        Parameters
        ----------
        student_id      : str
        recommendations : List[Recommendation] from the engine
        engine          : optional — used to fetch item domain/skills metadata

        Returns
        -------
        Re-ranked List[Recommendation] (sorted by adjusted score descending)
        """
        if not self._store.get_student_feedback(student_id):
            # No feedback yet — return unchanged
            return recommendations

        profile = self.preference_profile(student_id)
        adjusted = []

        for rec in recommendations:
            multiplier = self._compute_multiplier(rec, profile, engine)
            # Create a copy with adjusted score (don't mutate original)
            from copy import copy
            adj = copy(rec)
            adj.score = round(min(1.0, rec.score * multiplier), 4)
            adj.explanation = (
                rec.explanation + f" | personalization ×{multiplier:.2f}"
            )
            adjusted.append(adj)

        adjusted.sort(key=lambda r: r.score, reverse=True)
        log.info(
            "Personalization applied for student=%s  items=%d",
            student_id, len(adjusted)
        )
        return adjusted

    def _compute_multiplier(self, rec, profile: PreferenceProfile, engine) -> float:
        """Compute a [0.5, 1.5] multiplier for one recommendation."""
        multiplier = 1.0

        # Get item domain from engine metadata if available
        item_domain = ""
        item_skills: List[str] = []
        if engine is not None:
            try:
                if rec.item_type == "opportunity":
                    row = engine._opps_df[engine._opps_df["opportunity_id"] == rec.item_id]
                elif rec.item_type == "hackathon":
                    row = engine._hackathons_df[engine._hackathons_df["hackathon_id"] == rec.item_id]
                else:
                    row = engine._papers_df[engine._papers_df["paper_id"] == rec.item_id]
                if not row.empty:
                    item_domain = str(row.iloc[0].get("domain", "")).lower()
                    skills_val  = row.iloc[0].get("required_skills", [])
                    item_skills = skills_val if isinstance(skills_val, list) else []
            except Exception:
                pass

        # Domain boost / penalty
        if item_domain and item_domain in profile.liked_domains:
            multiplier += 0.25
        if item_domain and item_domain in profile.disliked_domains:
            multiplier -= 0.30

        # Skill signal
        for sk in item_skills:
            if sk in profile.liked_skills:
                multiplier += 0.05
                break   # cap at one boost per item
        for sk in item_skills:
            if sk in profile.disliked_skills:
                multiplier -= 0.05
                break

        return max(0.5, min(1.5, multiplier))


# ===========================================================================
# 5.  FEEDBACK  COLLECTOR  (convenience wrapper for the AI Assistant)
# ===========================================================================

class FeedbackCollector:
    """High-level wrapper used by the AI Assistant to collect feedback inline.

    Usage
    -----
    >>> collector = FeedbackCollector(store)
    >>> collector.thumbs_up("S001", "O001", "opportunity")
    >>> collector.applied("S001", "H004", "hackathon")
    """

    def __init__(self, store: Optional[FeedbackStore] = None):
        self.store = store or FeedbackStore()

    def thumbs_up(self, student_id, item_id, item_type, **kwargs):
        return self.store.record(student_id, item_id, item_type, FeedbackType.THUMBS_UP, **kwargs)

    def thumbs_down(self, student_id, item_id, item_type, **kwargs):
        return self.store.record(student_id, item_id, item_type, FeedbackType.THUMBS_DOWN, **kwargs)

    def applied(self, student_id, item_id, item_type, **kwargs):
        return self.store.record(student_id, item_id, item_type, FeedbackType.APPLIED, **kwargs)

    def saved(self, student_id, item_id, item_type, **kwargs):
        return self.store.record(student_id, item_id, item_type, FeedbackType.SAVED, **kwargs)

    def ignored(self, student_id, item_id, item_type, **kwargs):
        return self.store.record(student_id, item_id, item_type, FeedbackType.IGNORED, **kwargs)

    def save(self, path: Optional[Path] = None):
        """Persist the feedback log to disk."""
        return self.store.export_csv(path)


# ===========================================================================
# 6.  CLI
# ===========================================================================

if __name__ == "__main__":
    # Demo: simulate feedback and re-ranking
    store     = FeedbackStore()
    collector = FeedbackCollector(store)
    layer     = PersonalizationLayer(store)

    # Simulate student S001 interactions
    collector.applied(   "S001", "O001", "opportunity", item_domain="data science",
                         item_skills="python,machine learning,sql", score_at_time=0.82)
    collector.saved(     "S001", "O005", "opportunity", item_domain="ai research",
                         item_skills="python,nlp,machine learning")
    collector.thumbs_down("S001", "O006", "opportunity", item_domain="electronics",
                          item_skills="c++,embedded c,matlab")
    collector.ignored(   "S001", "O008", "opportunity", item_domain="mobile development")
    collector.applied(   "S001", "H001", "hackathon",   item_domain="ai/ml",
                         item_skills="python,machine learning")

    profile = layer.preference_profile("S001")
    print(f"\nPreference Profile for S001:")
    print(f"  Liked domains    : {profile.liked_domains}")
    print(f"  Disliked domains : {profile.disliked_domains}")
    print(f"  Liked skills     : {profile.liked_skills[:5]}")
    print(f"  Engagement rate  : {profile.engagement_rate:.0%}")
    print(f"  Applied          : {profile.applied_count}")

    summary = store.summary()
    print(f"\nFeedback Summary:")
    print(f"  Total records    : {summary['total_records']}")
    print(f"  By type          : {summary['by_feedback_type']}")

    path = store.export_csv()
    print(f"\nFeedback log exported to: {path}")
