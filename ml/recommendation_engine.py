"""
recommendation_engine.py
------------------------
StudentPulse ML — Content-Based Recommendation Engine

Orchestrates the full recommendation pipeline:
    Student Profile
        ↓ feature_engineering
    Student Feature Vector
        ↓ similarity  (cosine + skill overlap + CGPA gate)
    Ranked Opportunity / Paper List
        ↓ diversity reranking (cluster-level)
    Personalised Recommendations

Public API
----------
RecommendationEngine          — main class
    .fit(data, features, sims, cluster_model, labels)
    .recommend_opportunities(student_id, top_k, filters)
    .recommend_papers(student_id, top_k, filters)
    .recommend_all(student_id, top_k_opps, top_k_papers)
    .recommend_for_new_student(skills, interests, cgpa, top_k)
    .get_explanation(student_id, item_id, item_type)

recommend_all_students(engine, top_k)    — batch helper
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from ml.skill_gap import SkillGapAnalyzer, CareerRoadmap
    from ml.ai_assistant import StudentAssistant
    from ml.feedback import FeedbackStore, PersonalizationLayer

import numpy as np
import pandas as pd

from ml.similarity import (
    cosine_similarity_vector,
    skill_overlap_score,
    cgpa_gate,
    weighted_similarity,
    rank_items,
)
from ml.clustering import get_cluster_label

log = logging.getLogger(__name__)


# ===========================================================================
# 1.  DATA CLASSES
# ===========================================================================

@dataclass
class Recommendation:
    """A single recommendation result."""
    item_id: str
    title: str
    item_type: str          # "opportunity" | "paper" | "hackathon"
    score: float
    cosine_score: float
    skill_overlap: float
    cgpa_factor: float
    matched_skills: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class RecommendationResult:
    """Full recommendation output for one student."""
    student_id: str
    student_name: str
    opportunities: List[Recommendation] = field(default_factory=list)
    papers: List[Recommendation] = field(default_factory=list)
    hackathons: List[Recommendation] = field(default_factory=list)


# ===========================================================================
# 2.  ENGINE
# ===========================================================================

class RecommendationEngine:
    """Content-based recommendation engine for StudentPulse.

    Usage
    -----
    >>> from ml.preprocessing import preprocess_all
    >>> from ml.feature_engineering import build_all_features
    >>> from ml.similarity import compute_all_similarities
    >>> from ml.clustering import cluster_students
    >>> from ml.recommendation_engine import RecommendationEngine
    >>>
    >>> data    = preprocess_all()
    >>> feats   = build_all_features(data)
    >>> sims    = compute_all_similarities(feats, data["students"],
    ...                                    data["opportunities"], data["papers"])
    >>> model, labels = cluster_students(feats["student_matrix"])
    >>>
    >>> engine  = RecommendationEngine()
    >>> engine.fit(data, feats, sims, model, labels)
    >>>
    >>> result  = engine.recommend_all("S001")
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Parameters
        ----------
        weights : scoring weights  {cosine, overlap, cgpa}
                  defaults: cosine=0.55, overlap=0.35, cgpa=0.10
        """
        self.weights = weights or {"cosine": 0.55, "overlap": 0.35, "cgpa": 0.10}
        self._fitted = False

        # Auxiliary modules — attached after training (see train.py)
        self._skill_gap_analyzer: Optional["SkillGapAnalyzer"] = None
        self._career_roadmap: Optional["CareerRoadmap"] = None
        self._feedback_store: Optional["FeedbackStore"] = None
        self._personalization: Optional["PersonalizationLayer"] = None
        self._assistant: Optional["StudentAssistant"] = None

    # ------------------------------------------------------------------ fit
    def fit(
        self,
        data: Dict[str, pd.DataFrame],
        features: Dict[str, Any],
        similarities: Dict[str, np.ndarray],
        cluster_model=None,
        cluster_labels: Optional[np.ndarray] = None,
    ) -> "RecommendationEngine":
        """Store all artefacts needed for scoring.

        Parameters
        ----------
        data          : dict from preprocess_all()
        features      : dict from build_all_features()
        similarities  : dict from compute_all_similarities()
        cluster_model : fitted KMeans (optional, enables cold-start)
        cluster_labels: (n_students,) label array
        """
        self._students_df    = data["students"].copy()
        self._opps_df        = data["opportunities"].copy()
        self._papers_df      = data["papers"].copy()
        self._hackathons_df  = data["hackathons"].copy()

        self._feats         = features
        self._sims          = similarities
        self._cluster_model = cluster_model
        self._cluster_labels = cluster_labels

        # Build fast lookup indexes
        self._student_idx = {
            sid: i for i, sid in enumerate(features["student_ids"])
        }
        self._opp_idx = {
            oid: i for i, oid in enumerate(features["opp_ids"])
        }
        self._paper_idx = {
            pid: i for i, pid in enumerate(features["paper_ids"])
        }
        self._hackathon_idx = {
            hid: i for i, hid in enumerate(features["hackathon_ids"])
        }

        self._fitted = True
        log.info(
            "Engine fitted — %d students | %d opps | %d papers | %d hackathons",
            len(self._student_idx),
            len(self._opp_idx),
            len(self._paper_idx),
            len(self._hackathon_idx),
        )
        return self

    # ------------------------------------------- recommend_opportunities
    def recommend_opportunities(
        self,
        student_id: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Recommendation]:
        """Recommend internships / jobs for a student.

        Parameters
        ----------
        student_id : str
        top_k      : number of results
        filters    : optional dict, e.g. {"type": "internship", "remote": True}

        Returns
        -------
        List[Recommendation] sorted by score descending
        """
        self._check_fitted()
        s_idx = self._resolve_student(student_id)
        student_row = self._students_df.iloc[s_idx]

        opps_df = self._filter_df(self._opps_df, filters)

        scores = self._score_items(
            s_idx=s_idx,
            student_row=student_row,
            items_df=opps_df,
            item_type="opportunity",
            cosine_matrix=self._sims["opp_cosine"],
            overlap_matrix=self._sims.get("opp_overlap"),
            item_skill_col="required_skills",
            item_cgpa_col="min_cgpa",
        )

        return scores[:top_k]

    # ------------------------------------------------- recommend_papers
    def recommend_papers(
        self,
        student_id: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Recommendation]:
        """Recommend research papers for a student."""
        self._check_fitted()
        s_idx = self._resolve_student(student_id)
        student_row = self._students_df.iloc[s_idx]

        papers_df = self._filter_df(self._papers_df, filters)

        scores = self._score_items(
            s_idx=s_idx,
            student_row=student_row,
            items_df=papers_df,
            item_type="paper",
            cosine_matrix=self._sims["paper_cosine"],
            overlap_matrix=self._sims.get("paper_overlap"),
            item_skill_col="keywords",
            item_cgpa_col=None,
        )

        return scores[:top_k]

    # ------------------------------------------------- recommend_hackathons
    def recommend_hackathons(
        self,
        student_id: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Recommendation]:
        """Recommend hackathons for a student.

        Parameters
        ----------
        student_id : str
        top_k      : number of results
        filters    : optional dict, e.g. {"mode": "online", "difficulty_level": "intermediate"}

        Returns
        -------
        List[Recommendation] sorted by score descending
        """
        self._check_fitted()
        s_idx = self._resolve_student(student_id)
        student_row = self._students_df.iloc[s_idx]

        hackathons_df = self._filter_df(self._hackathons_df, filters)

        scores = self._score_items(
            s_idx=s_idx,
            student_row=student_row,
            items_df=hackathons_df,
            item_type="hackathon",
            cosine_matrix=self._sims["hackathon_cosine"],
            overlap_matrix=self._sims.get("hackathon_overlap"),
            item_skill_col="required_skills",
            item_cgpa_col=None,
        )

        return scores[:top_k]

    # ------------------------------------------------- recommend_all
    def recommend_all(
        self,
        student_id: str,
        top_k_opps: int = 5,
        top_k_papers: int = 5,
        top_k_hackathons: int = 5,
    ) -> RecommendationResult:
        """Recommend opportunities, papers, and hackathons for a student.

        Returns
        -------
        RecommendationResult
        """
        self._check_fitted()
        s_idx = self._resolve_student(student_id)
        student_row = self._students_df.iloc[s_idx]

        opps       = self.recommend_opportunities(student_id, top_k=top_k_opps)
        papers     = self.recommend_papers(student_id, top_k=top_k_papers)
        hackathons = self.recommend_hackathons(student_id, top_k=top_k_hackathons)

        return RecommendationResult(
            student_id=student_id,
            student_name=student_row.get("name", student_id),
            opportunities=opps,
            papers=papers,
            hackathons=hackathons,
        )

    # ---------------------------------------------- cold-start (new student)
    def recommend_for_new_student(
        self,
        skills: List[str],
        interests: List[str],
        cgpa: float = 7.0,
        top_k: int = 5,
    ) -> RecommendationResult:
        """Recommend for a student not yet in the dataset (cold-start).

        Assigns them to the nearest cluster and uses that cluster's centroid
        as a proxy feature vector.

        Parameters
        ----------
        skills    : list of skill strings
        interests : list of interest strings
        cgpa      : float
        top_k     : results per category
        """
        if self._cluster_model is None:
            raise RuntimeError("No cluster model — call fit() with a cluster_model.")

        # Build a temporary feature vector matching the student feature space
        skill_vocab = self._feats["skill_vocab"]
        vocab_index = {v: i for i, v in enumerate(skill_vocab)}
        n_skill_feats = len(self._feats["student_features"])

        vec = np.zeros(n_skill_feats, dtype=np.float32)
        for sk in skills:
            idx = vocab_index.get(sk.strip().lower())
            if idx is not None:
                vec[idx] = 1.0

        # Assign to cluster; use centroid as feature proxy
        cluster_id = get_cluster_label(vec, self._cluster_model)
        centroid = self._cluster_model.cluster_centers_[cluster_id]

        # Score opportunities against centroid
        n_skill = len(skill_vocab)
        opp_cos = np.array([
            float(np.dot(
                centroid[:n_skill] / (np.linalg.norm(centroid[:n_skill]) + 1e-10),
                self._feats["opp_matrix"][i, :n_skill]
                / (np.linalg.norm(self._feats["opp_matrix"][i, :n_skill]) + 1e-10)
            ))
            for i in range(len(self._feats["opp_ids"]))
        ], dtype=np.float32)

        paper_cos = np.array([
            float(np.dot(
                centroid[:n_skill] / (np.linalg.norm(centroid[:n_skill]) + 1e-10),
                self._feats["paper_matrix"][i, :n_skill]
                / (np.linalg.norm(self._feats["paper_matrix"][i, :n_skill]) + 1e-10)
            ))
            for i in range(len(self._feats["paper_ids"]))
        ], dtype=np.float32)

        hack_cos = np.array([
            float(np.dot(
                centroid[:n_skill] / (np.linalg.norm(centroid[:n_skill]) + 1e-10),
                self._feats["hackathon_matrix"][i, :n_skill]
                / (np.linalg.norm(self._feats["hackathon_matrix"][i, :n_skill]) + 1e-10)
            ))
            for i in range(len(self._feats["hackathon_ids"]))
        ], dtype=np.float32)

        opps       = self._build_recs_from_scores(opp_cos,   self._opps_df,        self._feats["opp_ids"],        "opportunity", skills, cgpa, "required_skills", "min_cgpa", top_k)
        papers     = self._build_recs_from_scores(paper_cos, self._papers_df,      self._feats["paper_ids"],      "paper",       skills, cgpa, "keywords",         None,       top_k)
        hackathons = self._build_recs_from_scores(hack_cos,  self._hackathons_df,  self._feats["hackathon_ids"],  "hackathon",   skills, cgpa, "required_skills",  None,       top_k)

        return RecommendationResult(
            student_id="NEW",
            student_name="New Student",
            opportunities=opps,
            papers=papers,
            hackathons=hackathons,
        )

    # ------------------------------------------------- get_explanation
    def get_explanation(
        self,
        student_id: str,
        item_id: str,
        item_type: str = "opportunity",
    ) -> str:
        """Return a human-readable explanation of why an item was recommended.

        Parameters
        ----------
        student_id : str
        item_id    : str (opportunity_id or paper_id)
        item_type  : "opportunity" | "paper"
        """
        self._check_fitted()
        s_idx = self._resolve_student(student_id)
        student_row = self._students_df.iloc[s_idx]
        student_skills = student_row["skills"] if isinstance(student_row["skills"], list) else []

        if item_type == "opportunity":
            item_row = self._opps_df[self._opps_df["opportunity_id"] == item_id]
            item_skill_col = "required_skills"
        elif item_type == "hackathon":
            item_row = self._hackathons_df[self._hackathons_df["hackathon_id"] == item_id]
            item_skill_col = "required_skills"
        else:
            item_row = self._papers_df[self._papers_df["paper_id"] == item_id]
            item_skill_col = "keywords"

        if item_row.empty:
            return f"Item {item_id} not found."

        item_row = item_row.iloc[0]
        item_skills = item_row[item_skill_col] if isinstance(item_row[item_skill_col], list) else []
        matched = sorted(set(student_skills) & set(item_skills))
        overlap = skill_overlap_score(student_skills, item_skills)

        lines = [
            f"Recommended '{item_row.get('title', item_id)}' for {student_row['name']} because:",
            f"  • Skill overlap : {overlap:.0%} ({len(matched)}/{len(item_skills)} required skills matched)",
            f"  • Matched skills: {', '.join(matched) if matched else 'none'}",
        ]
        if item_type == "opportunity" and "min_cgpa" in item_row:
            gate = cgpa_gate(float(student_row["cgpa"]), float(item_row["min_cgpa"]))
            lines.append(f"  • CGPA eligibility factor: {gate:.2f}  (student={student_row['cgpa']}, required={item_row['min_cgpa']})")

        return "\n".join(lines)

    # ==================================================================
    # PRIVATE HELPERS  (item_type dispatch)
    # ==================================================================

    def _check_fitted(self):
        if not self._fitted:
            raise RuntimeError("Call engine.fit() before making recommendations.")

    def _resolve_student(self, student_id: str) -> int:
        idx = self._student_idx.get(student_id)
        if idx is None:
            raise KeyError(f"Student '{student_id}' not found. Use recommend_for_new_student() for cold-start.")
        return idx

    def _filter_df(
        self,
        df: pd.DataFrame,
        filters: Optional[Dict],
    ) -> pd.DataFrame:
        """Apply optional column-equality filters to a DataFrame."""
        if not filters:
            return df
        mask = pd.Series([True] * len(df), index=df.index)
        for col, val in filters.items():
            if col in df.columns:
                if isinstance(val, bool):
                    mask &= df[col].astype(bool) == val
                else:
                    mask &= df[col].str.lower() == str(val).lower()
        return df[mask].reset_index(drop=True)

    def _score_items(
        self,
        s_idx: int,
        student_row,
        items_df: pd.DataFrame,
        item_type: str,
        cosine_matrix: np.ndarray,
        overlap_matrix: Optional[np.ndarray],
        item_skill_col: str,
        item_cgpa_col: Optional[str],
    ) -> List[Recommendation]:
        """Score every item in items_df for a student and return sorted list."""
        student_skills = student_row["skills"] if isinstance(student_row["skills"], list) else []
        student_cgpa   = float(student_row.get("cgpa", 0.0))

        recs = []
        for _, item_row in items_df.iterrows():
            if item_type == "opportunity":
                item_id = item_row.get("opportunity_id")
                global_idx = self._opp_idx.get(item_id)
            elif item_type == "hackathon":
                item_id = item_row.get("hackathon_id")
                global_idx = self._hackathon_idx.get(item_id)
            else:
                item_id = item_row.get("paper_id")
                global_idx = self._paper_idx.get(item_id)

            if global_idx is None:
                continue

            # Cosine from pre-computed matrix
            cos = float(cosine_matrix[s_idx, global_idx]) if cosine_matrix is not None else 0.0

            # Skill overlap
            item_skills = item_row[item_skill_col] if isinstance(item_row[item_skill_col], list) else []
            if overlap_matrix is not None:
                overlap = float(overlap_matrix[s_idx, global_idx])
            else:
                overlap = skill_overlap_score(student_skills, item_skills)

            # CGPA gate
            min_cgpa = float(item_row.get(item_cgpa_col, 0.0)) if item_cgpa_col else 0.0
            cgpa_f   = cgpa_gate(student_cgpa, min_cgpa)

            score = weighted_similarity(cos, overlap, cgpa_f, self.weights)
            matched = sorted(set(student_skills) & set(item_skills))

            explanation = (
                f"Skill match {overlap:.0%} | cosine {cos:.3f} | CGPA factor {cgpa_f:.2f}"
            )

            recs.append(Recommendation(
                item_id=item_id,
                title=item_row.get("title", item_id),
                item_type=item_type,
                score=round(score, 4),
                cosine_score=round(cos, 4),
                skill_overlap=round(overlap, 4),
                cgpa_factor=round(cgpa_f, 4),
                matched_skills=matched,
                explanation=explanation,
            ))

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs

    def _build_recs_from_scores(
        self,
        cosine_scores: np.ndarray,
        items_df: pd.DataFrame,
        item_ids: List[str],
        item_type: str,
        student_skills: List[str],
        student_cgpa: float,
        item_skill_col: str,
        item_cgpa_col: Optional[str],
        top_k: int,
    ) -> List[Recommendation]:
        """Build Recommendation list directly from a cosine score array (cold-start)."""
        ranked = rank_items(cosine_scores, item_ids, top_k=top_k)
        # Determine the ID column for this item type
        if item_type == "opportunity":
            id_col = "opportunity_id"
        elif item_type == "hackathon":
            id_col = "hackathon_id"
        else:
            id_col = "paper_id"
        recs = []
        for item_id, cos in ranked:
            row = items_df[items_df[id_col] == item_id] if id_col in items_df.columns else pd.DataFrame()
            if row.empty:
                continue
            row = row.iloc[0]
            item_skills = row[item_skill_col] if isinstance(row.get(item_skill_col), list) else []
            overlap = skill_overlap_score(student_skills, item_skills)
            min_cgpa = float(row.get(item_cgpa_col, 0.0)) if item_cgpa_col else 0.0
            cgpa_f = cgpa_gate(student_cgpa, min_cgpa)
            score = weighted_similarity(cos, overlap, cgpa_f, self.weights)
            recs.append(Recommendation(
                item_id=item_id,
                title=row.get("title", item_id),
                item_type=item_type,
                score=round(score, 4),
                cosine_score=round(cos, 4),
                skill_overlap=round(overlap, 4),
                cgpa_factor=round(cgpa_f, 4),
                matched_skills=sorted(set(student_skills) & set(item_skills)),
                explanation=f"Cold-start cluster recommendation | skill match {overlap:.0%}",
            ))
        recs.sort(key=lambda r: r.score, reverse=True)
        return recs


# ===========================================================================
# 3.  BATCH  HELPER
# ===========================================================================

def recommend_all_students(
    engine: RecommendationEngine,
    top_k_opps: int = 5,
    top_k_papers: int = 5,
) -> List[RecommendationResult]:
    """Generate recommendations for ALL students in the engine.

    Returns
    -------
    List[RecommendationResult]
    """
    results = []
    for student_id in engine._student_idx:
        result = engine.recommend_all(student_id, top_k_opps, top_k_papers)
        results.append(result)
    log.info("Generated recommendations for %d students.", len(results))
    return results


def recommendations_to_dataframe(results: List[RecommendationResult]) -> pd.DataFrame:
    """Flatten a list of RecommendationResult into a tidy DataFrame.

    Useful for evaluation or CSV export.
    """
    rows = []
    for res in results:
        for rec in res.opportunities + res.papers + res.hackathons:
            rows.append({
                "student_id": res.student_id,
                "student_name": res.student_name,
                "item_id": rec.item_id,
                "title": rec.title,
                "item_type": rec.item_type,
                "score": rec.score,
                "cosine_score": rec.cosine_score,
                "skill_overlap": rec.skill_overlap,
                "cgpa_factor": rec.cgpa_factor,
                "matched_skills": ", ".join(rec.matched_skills),
            })
    return pd.DataFrame(rows)


# ===========================================================================
# 4.  CLI
# ===========================================================================

if __name__ == "__main__":
    from ml.preprocessing import preprocess_all
    from ml.feature_engineering import build_all_features
    from ml.similarity import compute_all_similarities
    from ml.clustering import cluster_students

    data   = preprocess_all()
    feats  = build_all_features(data)
    sims   = compute_all_similarities(
        feats,
        students_df=data["students"],
        opps_df=data["opportunities"],
        papers_df=data["papers"],
        hackathons_df=data["hackathons"],
    )
    model, labels = cluster_students(feats["student_matrix"])

    engine = RecommendationEngine()
    engine.fit(data, feats, sims, model, labels)

    result = engine.recommend_all("S001", top_k_opps=5, top_k_papers=5)
    print(f"\n{'='*60}")
    print(f"Recommendations for {result.student_name}  ({result.student_id})")
    print(f"\n--- Top Opportunities ---")
    for r in result.opportunities:
        print(f"  [{r.score:.3f}] {r.title}  ({r.item_id})  overlap={r.skill_overlap:.0%}")
    print(f"\n--- Top Papers ---")
    for r in result.papers:
        print(f"  [{r.score:.3f}] {r.title}  ({r.item_id})")

    print(f"\n--- Explanation ---")
    if result.opportunities:
        print(engine.get_explanation("S001", result.opportunities[0].item_id, "opportunity"))
