"""
evaluate.py
-----------
StudentPulse ML — Evaluation Module

Measures recommendation quality using standard IR metrics:
    - Precision@K
    - Recall@K
    - F1@K
    - NDCG@K  (Normalised Discounted Cumulative Gain)
    - MRR     (Mean Reciprocal Rank)
    - Hit Rate@K
    - Skill Coverage (diversity metric)

Since StudentPulse is content-based with no historical interaction data,
evaluation is done with two strategies:

  1. Synthetic ground-truth  : mark an item as "relevant" if skill overlap ≥ threshold.
  2. Leave-one-skill-out     : hide one of the student's skills, check if dropped items
                               still rank in top-K.

Public API
----------
build_ground_truth(students_df, items_df, item_type, threshold)
precision_at_k(recommended, relevant, k)
recall_at_k(recommended, relevant, k)
ndcg_at_k(recommended, relevant, k)
mrr(recommended, relevant)
hit_rate_at_k(recommended, relevant, k)
evaluate_engine(engine, students_df, ground_truth_opps, ground_truth_papers, k)
full_evaluation_report(engine, data, k_values)
"""

import logging
import math
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from ml.similarity import skill_overlap_score

log = logging.getLogger(__name__)


# ===========================================================================
# 1.  GROUND-TRUTH GENERATION
# ===========================================================================

def build_ground_truth(
    students_df: pd.DataFrame,
    items_df: pd.DataFrame,
    item_type: str = "opportunity",
    overlap_threshold: float = 0.4,
) -> Dict[str, Set[str]]:
    """Build synthetic ground-truth relevance labels.

    An item is "relevant" to a student when:
        skill_overlap(student_skills, item_required_skills) >= threshold

    Parameters
    ----------
    students_df       : clean students DataFrame
    items_df          : clean opportunities or papers DataFrame
    item_type         : "opportunity" | "paper"
    overlap_threshold : minimum overlap to be considered relevant

    Returns
    -------
    ground_truth : dict  {student_id: set of relevant item_ids}
    """
    id_col        = "opportunity_id" if item_type == "opportunity" else "paper_id"
    skill_col     = "required_skills" if item_type == "opportunity" else "keywords"

    gt: Dict[str, Set[str]] = {}
    for _, student in students_df.iterrows():
        student_skills = student["skills"] if isinstance(student["skills"], list) else []
        relevant = set()
        for _, item in items_df.iterrows():
            item_skills = item[skill_col] if isinstance(item[skill_col], list) else []
            if skill_overlap_score(student_skills, item_skills) >= overlap_threshold:
                relevant.add(item[id_col])
        gt[student["student_id"]] = relevant

    n_pairs = sum(len(v) for v in gt.values())
    log.info(
        "Ground truth built — %d students | %d relevant %s pairs | avg=%.1f per student",
        len(gt), n_pairs, item_type, n_pairs / max(len(gt), 1),
    )
    return gt


# ===========================================================================
# 2.  METRIC FUNCTIONS
# ===========================================================================

def precision_at_k(
    recommended: List[str],
    relevant: Set[str],
    k: int,
) -> float:
    """Fraction of the top-k recommendations that are relevant."""
    if not recommended or k == 0:
        return 0.0
    top_k = recommended[:k]
    hits  = sum(1 for item in top_k if item in relevant)
    return hits / k


def recall_at_k(
    recommended: List[str],
    relevant: Set[str],
    k: int,
) -> float:
    """Fraction of all relevant items that appear in the top-k."""
    if not relevant or not recommended or k == 0:
        return 0.0
    top_k = recommended[:k]
    hits  = sum(1 for item in top_k if item in relevant)
    return hits / len(relevant)


def f1_at_k(
    recommended: List[str],
    relevant: Set[str],
    k: int,
) -> float:
    """Harmonic mean of Precision@K and Recall@K."""
    p = precision_at_k(recommended, relevant, k)
    r = recall_at_k(recommended, relevant, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def ndcg_at_k(
    recommended: List[str],
    relevant: Set[str],
    k: int,
) -> float:
    """Normalised Discounted Cumulative Gain @ K.

    Assumes binary relevance (1 if in relevant set, else 0).
    """
    if not relevant or not recommended or k == 0:
        return 0.0

    top_k = recommended[:k]
    dcg   = sum(
        1.0 / math.log2(i + 2)
        for i, item in enumerate(top_k)
        if item in relevant
    )
    # Ideal DCG: all relevant items at the top
    n_ideal = min(len(relevant), k)
    idcg    = sum(1.0 / math.log2(i + 2) for i in range(n_ideal))

    return dcg / idcg if idcg > 0 else 0.0


def mrr(
    recommended: List[str],
    relevant: Set[str],
) -> float:
    """Mean Reciprocal Rank (single-query version).

    Returns 1/rank of the first hit, or 0 if no hit.
    """
    for rank, item in enumerate(recommended, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def hit_rate_at_k(
    recommended: List[str],
    relevant: Set[str],
    k: int,
) -> float:
    """1 if at least one relevant item is in top-k, else 0."""
    top_k = recommended[:k]
    return 1.0 if any(item in relevant for item in top_k) else 0.0


def skill_coverage(
    recommendations: List[List[str]],
    all_item_ids: List[str],
) -> float:
    """Fraction of the item catalogue covered across all recommendations.

    Measures diversity/coverage of the recommendation set.
    """
    covered = set()
    for rec_list in recommendations:
        covered.update(rec_list)
    return len(covered) / len(all_item_ids) if all_item_ids else 0.0


# ===========================================================================
# 3.  PER-STUDENT EVALUATION
# ===========================================================================

def evaluate_student(
    recommended_ids: List[str],
    relevant: Set[str],
    k: int,
) -> Dict[str, float]:
    """Return all metrics for one student's recommendations."""
    return {
        f"precision@{k}": precision_at_k(recommended_ids, relevant, k),
        f"recall@{k}":    recall_at_k(recommended_ids, relevant, k),
        f"f1@{k}":        f1_at_k(recommended_ids, relevant, k),
        f"ndcg@{k}":      ndcg_at_k(recommended_ids, relevant, k),
        "mrr":             mrr(recommended_ids, relevant),
        f"hit_rate@{k}":  hit_rate_at_k(recommended_ids, relevant, k),
    }


# ===========================================================================
# 4.  ENGINE-LEVEL EVALUATION
# ===========================================================================

def evaluate_engine(
    engine,
    students_df: pd.DataFrame,
    ground_truth_opps: Dict[str, Set[str]],
    ground_truth_papers: Dict[str, Set[str]],
    k: int = 10,
) -> Dict[str, float]:
    """Evaluate the engine across all students and return averaged metrics.

    Parameters
    ----------
    engine              : fitted RecommendationEngine
    students_df         : clean students DataFrame
    ground_truth_opps   : from build_ground_truth(..., item_type="opportunity")
    ground_truth_papers : from build_ground_truth(..., item_type="paper")
    k                   : cutoff rank

    Returns
    -------
    dict of metric_name → mean value across all students
    """
    log.info("Evaluating engine at k=%d …", k)

    opp_metrics_list   = []
    paper_metrics_list = []
    all_opp_recs       = []
    all_paper_recs     = []

    for _, student in students_df.iterrows():
        sid = student["student_id"]
        if sid not in engine._student_idx:
            continue

        # Opportunities
        opp_recs = engine.recommend_opportunities(sid, top_k=k)
        opp_ids  = [r.item_id for r in opp_recs]
        relevant_opps = ground_truth_opps.get(sid, set())
        opp_metrics_list.append(evaluate_student(opp_ids, relevant_opps, k))
        all_opp_recs.append(opp_ids)

        # Papers
        paper_recs = engine.recommend_papers(sid, top_k=k)
        paper_ids  = [r.item_id for r in paper_recs]
        relevant_papers = ground_truth_papers.get(sid, set())
        paper_metrics_list.append(evaluate_student(paper_ids, relevant_papers, k))
        all_paper_recs.append(paper_ids)

    def _mean(metric_list, key):
        vals = [m[key] for m in metric_list if key in m]
        return float(np.mean(vals)) if vals else 0.0

    metric_keys = list(opp_metrics_list[0].keys()) if opp_metrics_list else []

    result = {}
    for key in metric_keys:
        result[f"opp_{key}"]   = round(_mean(opp_metrics_list,   key), 4)
        result[f"paper_{key}"] = round(_mean(paper_metrics_list, key), 4)

    # Catalogue coverage
    all_opp_ids   = engine._feats["opp_ids"]
    all_paper_ids = engine._feats["paper_ids"]
    result["opp_catalogue_coverage"]   = round(skill_coverage(all_opp_recs,   all_opp_ids),   4)
    result["paper_catalogue_coverage"] = round(skill_coverage(all_paper_recs, all_paper_ids), 4)

    return result


# ===========================================================================
# 5.  FULL  EVALUATION  REPORT
# ===========================================================================

def full_evaluation_report(
    engine,
    data: Dict[str, pd.DataFrame],
    k_values: List[int] = None,
    overlap_threshold: float = 0.4,
) -> pd.DataFrame:
    """Run evaluation at multiple K values and return a summary DataFrame.

    Parameters
    ----------
    engine            : fitted RecommendationEngine
    data              : dict from preprocess_all()
    k_values          : list of K values (default [5, 10, 20])
    overlap_threshold : for build_ground_truth()

    Returns
    -------
    pd.DataFrame  with one row per K value
    """
    k_values = k_values or [5, 10, 20]

    gt_opps   = build_ground_truth(data["students"], data["opportunities"], "opportunity", overlap_threshold)
    gt_papers = build_ground_truth(data["students"], data["papers"],        "paper",       overlap_threshold)

    rows = []
    for k in k_values:
        metrics = evaluate_engine(engine, data["students"], gt_opps, gt_papers, k=k)
        metrics["k"] = k
        rows.append(metrics)
        log.info("k=%d  opp_ndcg=%.4f  paper_ndcg=%.4f", k, metrics.get(f"opp_ndcg@{k}", 0), metrics.get(f"paper_ndcg@{k}", 0))

    report_df = pd.DataFrame(rows)
    # Put k column first
    cols = ["k"] + [c for c in report_df.columns if c != "k"]
    return report_df[cols]


def print_report(report_df: pd.DataFrame) -> None:
    """Pretty-print the evaluation report."""
    print("\n" + "=" * 70)
    print("  StudentPulse ML — Evaluation Report")
    print("=" * 70)
    print(report_df.to_string(index=False))
    print("=" * 70)


# ===========================================================================
# 6.  CLI
# ===========================================================================

if __name__ == "__main__":
    from ml.train import train

    engine = train()
    from ml.preprocessing import preprocess_all
    data = preprocess_all()

    report = full_evaluation_report(engine, data, k_values=[5, 10])
    print_report(report)
