"""
similarity.py
-------------
StudentPulse ML — Similarity Calculation Module

Provides all distance / similarity functions used by the recommendation
engine to score how well an item (opportunity or paper) matches a student.

Supported metrics
-----------------
* cosine_similarity_matrix   – vectorised cosine similarity (students × items)
* skill_overlap_score        – Jaccard-like skill overlap (per student-item pair)
* weighted_similarity        – combines cosine + skill overlap + CGPA gate
* rank_items                 – sort items by score descending

Public API
----------
cosine_similarity_matrix(student_matrix, item_matrix)
skill_overlap_score(student_skills, item_skills)
weighted_similarity(student_vec, item_vec, student_row, item_row, weights)
rank_items(scores, item_ids, top_k)
compute_all_similarities(features_dict)   ← entry-point used by engine
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger(__name__)


# ===========================================================================
# 1.  COSINE SIMILARITY
# ===========================================================================

def cosine_similarity_matrix(
    A: np.ndarray,
    B: np.ndarray,
) -> np.ndarray:
    """Compute pairwise cosine similarity between rows of A and rows of B.

    Parameters
    ----------
    A : (m, F)  student feature matrix
    B : (n, F)  item feature matrix   (must share same feature space)

    Returns
    -------
    similarity : (m, n) float matrix,  values in [-1, 1]
    """
    # L2-normalise each row
    norm_A = _l2_normalise(A)   # (m, F)
    norm_B = _l2_normalise(B)   # (n, F)
    sim = norm_A @ norm_B.T     # (m, n)
    return np.clip(sim, -1.0, 1.0).astype(np.float32)


def cosine_similarity_vector(
    vec: np.ndarray,
    matrix: np.ndarray,
) -> np.ndarray:
    """Cosine similarity of a single vector against every row of a matrix.

    Parameters
    ----------
    vec    : (F,)   single feature vector
    matrix : (n, F) item feature matrix

    Returns
    -------
    scores : (n,)
    """
    norm_v = vec / (np.linalg.norm(vec) + 1e-10)
    norms  = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    return np.clip((matrix / norms) @ norm_v, -1.0, 1.0).astype(np.float32)


# ===========================================================================
# 2.  SKILL OVERLAP  (Jaccard)
# ===========================================================================

def skill_overlap_score(
    student_skills: List[str],
    item_skills: List[str],
) -> float:
    """Jaccard-like skill overlap between a student's skills and an item's
    required skills.

    Returns a float in [0, 1].
    """
    if not item_skills:
        return 0.0
    student_set = set(s.strip().lower() for s in student_skills)
    item_set    = set(s.strip().lower() for s in item_skills)
    intersection = student_set & item_set
    return len(intersection) / len(item_set)   # recall-style: covers all requirements


def batch_skill_overlap(
    students_df,
    items_df,
    item_skill_col: str = "required_skills",
) -> np.ndarray:
    """Compute a (n_students × n_items) skill-overlap matrix.

    Parameters
    ----------
    students_df     : cleaned students DataFrame
    items_df        : cleaned opportunities or papers DataFrame
    item_skill_col  : column in items_df that holds the required skills list

    Returns
    -------
    overlap_matrix : (n_students, n_items) float32
    """
    n_s = len(students_df)
    n_i = len(items_df)
    mat = np.zeros((n_s, n_i), dtype=np.float32)

    for i, student_skills in enumerate(students_df["skills"]):
        for j, item_skills in enumerate(items_df[item_skill_col]):
            mat[i, j] = skill_overlap_score(
                student_skills if isinstance(student_skills, list) else [],
                item_skills    if isinstance(item_skills,    list) else [],
            )
    return mat


# ===========================================================================
# 3.  CGPA GATE
# ===========================================================================

def cgpa_gate(
    student_cgpa: float,
    item_min_cgpa: float,
    soft: bool = True,
) -> float:
    """Return a penalty/boost factor based on CGPA eligibility.

    Parameters
    ----------
    student_cgpa   : student's CGPA (0–10)
    item_min_cgpa  : minimum CGPA required by the item (0 means no requirement)
    soft           : if True apply a soft sigmoid penalty instead of a hard 0/1

    Returns
    -------
    factor : float in (0, 1]
    """
    if item_min_cgpa <= 0:
        return 1.0
    diff = student_cgpa - item_min_cgpa
    if not soft:
        return 1.0 if diff >= 0 else 0.0
    # Sigmoid: 0.5 at exactly the threshold, ~1 when well above, ~0 when well below
    return float(1.0 / (1.0 + np.exp(-3.0 * diff)))


# ===========================================================================
# 4.  WEIGHTED COMBINED SCORE
# ===========================================================================

def weighted_similarity(
    cosine_score: float,
    overlap_score: float,
    cgpa_factor: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Combine sub-scores into a single relevance score.

    Default weights
    ---------------
    cosine  : 0.55
    overlap : 0.35
    cgpa    : 0.10  (multiplied in as a gate, not added)

    Returns
    -------
    float in [0, 1]
    """
    w = weights or {"cosine": 0.55, "overlap": 0.35, "cgpa": 0.10}
    base = w["cosine"] * cosine_score + w["overlap"] * overlap_score
    # CGPA factor is a multiplicative gate; low CGPA deflates the score
    score = base * (1.0 - w["cgpa"] + w["cgpa"] * cgpa_factor)
    return float(np.clip(score, 0.0, 1.0))


# ===========================================================================
# 5.  RANKING
# ===========================================================================

def rank_items(
    scores: np.ndarray,
    item_ids: List[str],
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """Return the top-k (item_id, score) pairs sorted by score descending.

    Parameters
    ----------
    scores   : (n,) array of relevance scores
    item_ids : list of item identifiers, same order as scores
    top_k    : number of results to return

    Returns
    -------
    List of (item_id, score) sorted high → low
    """
    top_k = min(top_k, len(scores))
    idx = np.argpartition(scores, -top_k)[-top_k:]
    idx = idx[np.argsort(scores[idx])[::-1]]
    return [(item_ids[i], float(scores[i])) for i in idx]


# ===========================================================================
# 6.  MASTER ENTRY-POINT
# ===========================================================================

def compute_all_similarities(
    features: Dict,
    students_df=None,
    opps_df=None,
    papers_df=None,
    hackathons_df=None,
) -> Dict:
    """Pre-compute cosine similarity matrices for student↔opp, student↔paper, student↔hackathon.

    Parameters
    ----------
    features      : dict from feature_engineering.build_all_features()
    students_df   : clean students DataFrame (for skill-overlap computation)
    opps_df       : clean opportunities DataFrame
    papers_df     : clean papers DataFrame
    hackathons_df : clean hackathons DataFrame

    Returns
    -------
    dict with keys:
        "opp_cosine"         (n_students × n_opps)        float32
        "paper_cosine"       (n_students × n_papers)      float32
        "hackathon_cosine"   (n_students × n_hackathons)  float32
        "opp_overlap"        float32  (if dfs provided)
        "paper_overlap"      float32  (if dfs provided)
        "hackathon_overlap"  float32  (if dfs provided)
    """
    log.info("Computing similarity matrices …")

    # The student and item matrices share the skill space (first len(skill_vocab) cols)
    n_skill = len(features["skill_vocab"])

    # Slice out only the shared skill dimensions for cosine comparison
    s_skill  = features["student_matrix"][:,    :n_skill]
    o_skill  = features["opp_matrix"][:,        :n_skill]
    p_skill  = features["paper_matrix"][:,      :n_skill]
    h_skill  = features["hackathon_matrix"][:,  :n_skill]

    opp_cos      = cosine_similarity_matrix(s_skill, o_skill)
    paper_cos    = cosine_similarity_matrix(s_skill, p_skill)
    hackathon_cos = cosine_similarity_matrix(s_skill, h_skill)

    log.info("  opp_cosine        shape: %s", opp_cos.shape)
    log.info("  paper_cosine      shape: %s", paper_cos.shape)
    log.info("  hackathon_cosine  shape: %s", hackathon_cos.shape)

    result = {
        "opp_cosine":       opp_cos,
        "paper_cosine":     paper_cos,
        "hackathon_cosine": hackathon_cos,
    }

    # Skill overlap (optional — needs raw DataFrames)
    if students_df is not None and opps_df is not None:
        log.info("  Computing skill-overlap matrix (student↔opp) …")
        result["opp_overlap"] = batch_skill_overlap(students_df, opps_df, "required_skills")
    if students_df is not None and papers_df is not None:
        log.info("  Computing skill-overlap matrix (student↔paper) …")
        result["paper_overlap"] = batch_skill_overlap(students_df, papers_df, "keywords")
    if students_df is not None and hackathons_df is not None:
        log.info("  Computing skill-overlap matrix (student↔hackathon) …")
        result["hackathon_overlap"] = batch_skill_overlap(students_df, hackathons_df, "required_skills")

    log.info("Similarity computation complete.")
    return result


# ===========================================================================
# 7.  HELPERS
# ===========================================================================

def _l2_normalise(matrix: np.ndarray) -> np.ndarray:
    """L2-normalise each row of a 2-D matrix."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    return matrix / norms


# ===========================================================================
# 8.  CLI
# ===========================================================================

if __name__ == "__main__":
    from ml.preprocessing import preprocess_all
    from ml.feature_engineering import build_all_features

    data = preprocess_all()
    feats = build_all_features(data)
    sims = compute_all_similarities(
        feats,
        students_df=data["students"],
        opps_df=data["opportunities"],
        papers_df=data["papers"],
        hackathons_df=data["hackathons"],
    )
    for k, v in sims.items():
        print(f"{k:20s}  shape={v.shape}  min={v.min():.3f}  max={v.max():.3f}")
