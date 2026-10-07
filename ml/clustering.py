"""
clustering.py
-------------
StudentPulse ML — Student Clustering Module

Groups students into clusters based on their skill/interest profile using
K-Means. Clusters serve two purposes:

1. Cold-start: a new student with few interactions can receive cluster-level
   recommendations before individual preference data accumulates.
2. Diversity: the engine can pull top-N from a student's own cluster as a
   diversity boost.

Public API
----------
cluster_students(student_matrix, n_clusters, random_state)
get_cluster_label(student_vec, cluster_model)
get_cluster_members(cluster_id, student_ids, labels)
summarize_clusters(students_df, labels)
save_cluster_model(model, path)
load_cluster_model(path)
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

log = logging.getLogger(__name__)

# Default model save path
_HERE = Path(__file__).parent
DEFAULT_MODEL_PATH = _HERE / "data" / "cluster_model.pkl"


# ===========================================================================
# 1.  OPTIMAL K  (elbow / silhouette heuristic)
# ===========================================================================

def find_optimal_k(
    matrix: np.ndarray,
    k_min: int = 2,
    k_max: int = 10,
    random_state: int = 42,
) -> Tuple[int, Dict[int, float]]:
    """Find the best number of clusters using the silhouette score.

    Parameters
    ----------
    matrix       : (n_students, F) feature matrix
    k_min, k_max : range of k values to try
    random_state : for reproducibility

    Returns
    -------
    best_k  : int
    scores  : dict  {k: silhouette_score}
    """
    # Need at least k_min+1 samples
    n = matrix.shape[0]
    k_max = min(k_max, n - 1)
    if k_min >= k_max:
        log.warning("Too few samples for clustering; defaulting to k=2")
        return 2, {}

    # Normalise first
    mat = normalize(matrix, norm="l2")

    scores: Dict[int, float] = {}
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=random_state, n_init="auto")
        labels = km.fit_predict(mat)
        score = silhouette_score(mat, labels)
        scores[k] = float(score)
        log.debug("  k=%d  silhouette=%.4f", k, score)

    best_k = max(scores, key=scores.get)
    log.info("Optimal k=%d  (silhouette=%.4f)", best_k, scores[best_k])
    return best_k, scores


# ===========================================================================
# 2.  CLUSTER  STUDENTS
# ===========================================================================

def cluster_students(
    student_matrix: np.ndarray,
    n_clusters: Optional[int] = None,
    random_state: int = 42,
    auto_k: bool = True,
) -> Tuple[KMeans, np.ndarray]:
    """Fit K-Means on the student feature matrix.

    Parameters
    ----------
    student_matrix : (n_students, F)
    n_clusters     : explicit k; if None and auto_k=True, search for best k
    random_state   : for reproducibility
    auto_k         : whether to auto-search for k when n_clusters is None

    Returns
    -------
    model  : fitted KMeans
    labels : (n_students,) cluster label array
    """
    mat = normalize(student_matrix, norm="l2")

    if n_clusters is None:
        if auto_k:
            n_clusters, _ = find_optimal_k(mat, random_state=random_state)
        else:
            n_clusters = max(2, int(np.sqrt(len(mat) / 2)))

    log.info("Clustering %d students into %d clusters …", len(mat), n_clusters)
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    labels = model.fit_predict(mat)

    # Log cluster sizes
    unique, counts = np.unique(labels, return_counts=True)
    for cid, cnt in zip(unique, counts):
        log.info("  Cluster %d : %d students", cid, cnt)

    return model, labels


# ===========================================================================
# 3.  ASSIGN  A NEW STUDENT  TO  A CLUSTER
# ===========================================================================

def get_cluster_label(
    student_vec: np.ndarray,
    model: KMeans,
) -> int:
    """Predict the cluster for a single student feature vector.

    Parameters
    ----------
    student_vec : (F,) or (1, F)
    model       : fitted KMeans

    Returns
    -------
    cluster_id : int
    """
    vec = student_vec.reshape(1, -1)
    vec = normalize(vec, norm="l2")
    return int(model.predict(vec)[0])


# ===========================================================================
# 4.  CLUSTER MEMBERSHIP
# ===========================================================================

def get_cluster_members(
    cluster_id: int,
    student_ids: List[str],
    labels: np.ndarray,
) -> List[str]:
    """Return the student_ids belonging to a given cluster.

    Parameters
    ----------
    cluster_id  : int
    student_ids : list of student ID strings (same order as labels)
    labels      : (n_students,) cluster assignments

    Returns
    -------
    List[str] of student_ids in that cluster
    """
    return [sid for sid, lbl in zip(student_ids, labels) if lbl == cluster_id]


# ===========================================================================
# 5.  CLUSTER SUMMARY
# ===========================================================================

def summarize_clusters(
    students_df: pd.DataFrame,
    labels: np.ndarray,
) -> pd.DataFrame:
    """Build a human-readable summary of each cluster.

    Returns a DataFrame with one row per cluster showing:
    - cluster_id
    - size
    - avg_cgpa
    - top_skills  (3 most common skills)
    - top_interests
    - common_career_goals
    """
    students_df = students_df.copy()
    students_df["_cluster"] = labels

    rows = []
    for cid, group in students_df.groupby("_cluster"):
        # Top skills
        all_skills = []
        for sk in group["skills"]:
            if isinstance(sk, list):
                all_skills.extend(sk)
        skill_counts = pd.Series(all_skills).value_counts()
        top_skills = skill_counts.head(3).index.tolist()

        # Top interests
        all_interests = []
        for it in group["interests"]:
            if isinstance(it, list):
                all_interests.extend(it)
        interest_counts = pd.Series(all_interests).value_counts()
        top_interests = interest_counts.head(3).index.tolist()

        # Common career goals
        goals = group["career_goal"].value_counts().head(3).index.tolist()

        rows.append({
            "cluster_id": int(cid),
            "size": len(group),
            "avg_cgpa": round(group["cgpa"].astype(float).mean(), 2),
            "top_skills": ", ".join(top_skills),
            "top_interests": ", ".join(top_interests),
            "common_career_goals": ", ".join(goals),
        })

    summary = pd.DataFrame(rows).sort_values("cluster_id").reset_index(drop=True)
    log.info("Cluster summary:\n%s", summary.to_string(index=False))
    return summary


# ===========================================================================
# 6.  PCA  VISUALISATION HELPER
# ===========================================================================

def pca_2d(student_matrix: np.ndarray, labels: np.ndarray) -> pd.DataFrame:
    """Reduce to 2D with PCA for plotting.

    Returns a DataFrame with columns: x, y, cluster
    """
    mat = normalize(student_matrix, norm="l2")
    coords = PCA(n_components=2, random_state=42).fit_transform(mat)
    return pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "cluster": labels})


# ===========================================================================
# 7.  PERSIST / LOAD
# ===========================================================================

def save_cluster_model(
    model: KMeans,
    labels: np.ndarray,
    student_ids: List[str],
    path: Path = DEFAULT_MODEL_PATH,
) -> None:
    """Persist the cluster model + labels to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"model": model, "labels": labels.tolist(), "student_ids": student_ids}
    with open(path, "wb") as f:
        pickle.dump(payload, f)
    log.info("Cluster model saved → %s", path)


def load_cluster_model(
    path: Path = DEFAULT_MODEL_PATH,
) -> Tuple[KMeans, np.ndarray, List[str]]:
    """Load a previously saved cluster model."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Cluster model not found: {path}")
    with open(path, "rb") as f:
        payload = pickle.load(f)
    labels = np.array(payload["labels"])
    log.info("Cluster model loaded ← %s  (k=%d)", path, payload["model"].n_clusters)
    return payload["model"], labels, payload["student_ids"]


# ===========================================================================
# 8.  CLI
# ===========================================================================

if __name__ == "__main__":
    from ml.preprocessing import preprocess_all
    from ml.feature_engineering import build_all_features

    data = preprocess_all()
    feats = build_all_features(data)

    model, labels = cluster_students(feats["student_matrix"])
    summary = summarize_clusters(data["students"], labels)
    print(summary.to_string(index=False))

    pca_df = pca_2d(feats["student_matrix"], labels)
    print("\nPCA sample (first 5 rows):")
    print(pca_df.head().to_string(index=False))
