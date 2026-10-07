"""
feature_engineering.py
-----------------------
StudentPulse ML — Feature Engineering Module

Converts clean DataFrames (from preprocessing.py) into numeric feature
vectors suitable for similarity calculation and the recommendation engine.

Key outputs
-----------
* Student feature matrix  : (n_students  × n_features)
* Opportunity feature matrix : (n_opps × n_features)  — shared skill space
* Paper feature matrix    : (n_papers × n_features)   — shared skill space
* Vocabulary mappings for interpretability

Public API
----------
build_student_features(students_df)
build_opportunity_features(opportunities_df, skill_vocab)
build_paper_features(papers_df, skill_vocab)
build_all_features(data_dict)   ← main entry-point used by train.py
"""

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer

log = logging.getLogger(__name__)


# ===========================================================================
# 1.  STUDENT FEATURES
# ===========================================================================

def build_student_features(
    students_df: pd.DataFrame,
) -> Tuple[np.ndarray, List[str], List[str]]:
    """Build a numeric feature matrix for all students.

    Features (in order)
    -------------------
    1. Skill binary flags     (multi-hot over full skill vocabulary)
    2. Interest binary flags  (multi-hot over interest vocabulary)
    3. cgpa_norm              (MinMax scaled 0-10 → 0-1)
    4. year_norm              (MinMax scaled 1-6  → 0-1)
    5. past_internships_norm  (clipped at 5, then scaled)
    6. open_to_remote         (0 / 1)

    Returns
    -------
    feature_matrix : np.ndarray  shape (n_students, n_features)
    feature_names  : List[str]   human-readable column labels
    student_ids    : List[str]
    """
    log.info("Building student feature matrix …")
    df = students_df.copy()

    # ── skill multi-hot ───────────────────────────────────────────────────
    skill_mlb = MultiLabelBinarizer()
    skill_mat = skill_mlb.fit_transform(df["skills"].tolist()).astype(np.float32)
    skill_cols = [f"skill:{s}" for s in skill_mlb.classes_]

    # ── interest multi-hot ────────────────────────────────────────────────
    interest_mlb = MultiLabelBinarizer()
    interest_mat = interest_mlb.fit_transform(df["interests"].tolist()).astype(np.float32)
    interest_cols = [f"interest:{i}" for i in interest_mlb.classes_]

    # ── scalar features ───────────────────────────────────────────────────
    scaler = MinMaxScaler()
    scalar_data = df[["cgpa", "year_of_study", "past_internships"]].values.astype(np.float32)
    # Clip internships to [0,5] before scaling
    scalar_data[:, 2] = np.clip(scalar_data[:, 2], 0, 5)
    scalar_mat = scaler.fit_transform(scalar_data)
    scalar_cols = ["cgpa_norm", "year_norm", "internships_norm"]

    # ── boolean features ──────────────────────────────────────────────────
    remote_col = df["open_to_remote"].astype(float).values.reshape(-1, 1)

    # ── concatenate ───────────────────────────────────────────────────────
    feature_matrix = np.hstack([skill_mat, interest_mat, scalar_mat, remote_col])
    feature_names = skill_cols + interest_cols + scalar_cols + ["open_to_remote"]

    log.info(
        "  Student feature matrix: %d students × %d features",
        feature_matrix.shape[0], feature_matrix.shape[1],
    )
    return feature_matrix, feature_names, df["student_id"].tolist()


# ===========================================================================
# 2.  OPPORTUNITY FEATURES
# ===========================================================================

def build_opportunity_features(
    opportunities_df: pd.DataFrame,
    skill_vocab: List[str],
) -> Tuple[np.ndarray, List[str], List[str]]:
    """Build a numeric feature matrix for opportunities.

    Uses the SAME skill vocabulary as students so cosine similarity is
    computed in a shared embedding space.

    Features
    --------
    1. Required-skill multi-hot (over shared skill_vocab)
    2. Preferred-skill multi-hot (over shared skill_vocab, weight 0.5)
    3. domain_encoded   (one-hot over unique domains)
    4. type_encoded     (one-hot: internship / full-time / other)
    5. remote           (0 / 1)
    6. stipend_norm     (log-scaled, MinMax)
    7. min_cgpa_norm    (MinMax 0-10 → 0-1)
    """
    log.info("Building opportunity feature matrix …")
    df = opportunities_df.copy()

    # ── shared skill space ────────────────────────────────────────────────
    req_mat  = _multi_hot(df["required_skills"],  skill_vocab, weight=1.0)
    pref_mat = _multi_hot(df["preferred_skills"], skill_vocab, weight=0.5)
    skill_mat = np.clip(req_mat + pref_mat, 0, 1)
    skill_cols = [f"skill:{s}" for s in skill_vocab]

    # ── domain one-hot ────────────────────────────────────────────────────
    domain_ohe, domain_cols = _one_hot(df["domain"], prefix="domain")

    # ── type one-hot ──────────────────────────────────────────────────────
    type_ohe, type_cols = _one_hot(df["type"], prefix="type")

    # ── scalar ────────────────────────────────────────────────────────────
    stipend = np.log1p(df["stipend_monthly"].astype(float).values).reshape(-1, 1)
    stipend = MinMaxScaler().fit_transform(stipend)

    min_cgpa = df["min_cgpa"].astype(float).values.reshape(-1, 1) / 10.0

    remote = df["remote"].astype(float).values.reshape(-1, 1)

    # ── concatenate ───────────────────────────────────────────────────────
    feature_matrix = np.hstack([
        skill_mat, domain_ohe, type_ohe, remote, stipend, min_cgpa
    ])
    feature_names = (
        skill_cols + domain_cols + type_cols
        + ["remote", "stipend_norm", "min_cgpa_norm"]
    )

    log.info(
        "  Opportunity feature matrix: %d items × %d features",
        feature_matrix.shape[0], feature_matrix.shape[1],
    )
    return feature_matrix, feature_names, df["opportunity_id"].tolist()


# ===========================================================================
# 3.  RESEARCH PAPER FEATURES
# ===========================================================================

def build_paper_features(
    papers_df: pd.DataFrame,
    skill_vocab: List[str],
) -> Tuple[np.ndarray, List[str], List[str]]:
    """Build a numeric feature matrix for research papers.

    Features
    --------
    1. Keyword multi-hot         (over shared skill_vocab)
    2. recommended_for multi-hot (over shared skill_vocab)
    3. domain one-hot
    4. difficulty one-hot        (beginner / intermediate / advanced)
    5. year_norm                 (MinMax over dataset years)
    6. citations_norm            (log-scaled, MinMax)
    """
    log.info("Building research paper feature matrix …")
    df = papers_df.copy()

    # ── keyword overlap with skill vocab ──────────────────────────────────
    kw_mat  = _multi_hot(df["keywords"],        skill_vocab, weight=1.0)
    rec_mat = _multi_hot(df["recommended_for"], skill_vocab, weight=0.8)
    skill_mat = np.clip(kw_mat + rec_mat, 0, 1)
    skill_cols = [f"skill:{s}" for s in skill_vocab]

    # ── domain one-hot ────────────────────────────────────────────────────
    domain_ohe, domain_cols = _one_hot(df["domain"], prefix="domain")

    # ── difficulty one-hot ────────────────────────────────────────────────
    diff_ohe, diff_cols = _one_hot(df["difficulty_level"], prefix="difficulty")

    # ── scalar ────────────────────────────────────────────────────────────
    years = df["year"].astype(float).values.reshape(-1, 1)
    year_norm = MinMaxScaler().fit_transform(years)

    cites = np.log1p(df["citations"].astype(float).values).reshape(-1, 1)
    cite_norm = MinMaxScaler().fit_transform(cites)

    # ── concatenate ───────────────────────────────────────────────────────
    feature_matrix = np.hstack([
        skill_mat, domain_ohe, diff_ohe, year_norm, cite_norm
    ])
    feature_names = (
        skill_cols + domain_cols + diff_cols
        + ["year_norm", "citations_norm"]
    )

    log.info(
        "  Paper feature matrix: %d papers × %d features",
        feature_matrix.shape[0], feature_matrix.shape[1],
    )
    return feature_matrix, feature_names, df["paper_id"].tolist()


# ===========================================================================
# 4.  HACKATHON FEATURES
# ===========================================================================

def build_hackathon_features(
    hackathons_df: pd.DataFrame,
    skill_vocab: List[str],
) -> Tuple[np.ndarray, List[str], List[str]]:
    """Build a numeric feature matrix for hackathons.

    Uses the SAME skill vocabulary as students so cosine similarity is
    computed in a shared embedding space.

    Features
    --------
    1. Required-skill multi-hot (over shared skill_vocab)
    2. Preferred-skill multi-hot (over shared skill_vocab, weight 0.5)
    3. domain one-hot
    4. difficulty one-hot  (beginner / intermediate / advanced)
    5. mode one-hot        (online / offline / hybrid)
    6. prize_norm          (log-scaled, MinMax)
    7. team_size_norm      (max team size, MinMax)
    """
    log.info("Building hackathon feature matrix …")
    df = hackathons_df.copy()

    # ── shared skill space ────────────────────────────────────────────────
    req_mat  = _multi_hot(df["required_skills"],  skill_vocab, weight=1.0)
    pref_mat = _multi_hot(df["preferred_skills"], skill_vocab, weight=0.5)
    skill_mat = np.clip(req_mat + pref_mat, 0, 1)
    skill_cols = [f"skill:{s}" for s in skill_vocab]

    # ── domain one-hot ────────────────────────────────────────────────────
    domain_ohe, domain_cols = _one_hot(df["domain"], prefix="domain")

    # ── difficulty one-hot ────────────────────────────────────────────────
    diff_ohe, diff_cols = _one_hot(df["difficulty_level"], prefix="difficulty")

    # ── mode one-hot (online/offline/hybrid) ─────────────────────────────
    mode_ohe, mode_cols = _one_hot(df["mode"], prefix="mode")

    # ── scalar ────────────────────────────────────────────────────────────
    prize = np.log1p(df["prize_pool"].astype(float).values).reshape(-1, 1)
    prize_norm = MinMaxScaler().fit_transform(prize)

    team = df["team_size_max"].astype(float).values.reshape(-1, 1)
    team_norm = MinMaxScaler().fit_transform(team)

    # ── concatenate ───────────────────────────────────────────────────────
    feature_matrix = np.hstack([
        skill_mat, domain_ohe, diff_ohe, mode_ohe, prize_norm, team_norm
    ])
    feature_names = (
        skill_cols + domain_cols + diff_cols + mode_cols
        + ["prize_norm", "team_size_norm"]
    )

    log.info(
        "  Hackathon feature matrix: %d hackathons × %d features",
        feature_matrix.shape[0], feature_matrix.shape[1],
    )
    return feature_matrix, feature_names, df["hackathon_id"].tolist()


# ===========================================================================
# 5.  MASTER ENTRY-POINT
# ===========================================================================

def build_all_features(
    data: Dict[str, pd.DataFrame],
) -> Dict:
    """Build feature matrices for all four item types.

    Parameters
    ----------
    data : dict returned by preprocessing.preprocess_all()

    Returns
    -------
    dict with keys:
        "student_matrix"      np.ndarray  (n_students × F)
        "student_features"    List[str]
        "student_ids"         List[str]
        "opp_matrix"          np.ndarray  (n_opps × F')
        "opp_features"        List[str]
        "opp_ids"             List[str]
        "paper_matrix"        np.ndarray  (n_papers × F')
        "paper_features"      List[str]
        "paper_ids"           List[str]
        "hackathon_matrix"    np.ndarray  (n_hackathons × F')
        "hackathon_features"  List[str]
        "hackathon_ids"       List[str]
        "skill_vocab"         List[str]   shared vocabulary

    Usage
    -----
    >>> from ml.preprocessing import preprocess_all
    >>> from ml.feature_engineering import build_all_features
    >>> data = preprocess_all()
    >>> features = build_all_features(data)
    """
    students_df    = data["students"]
    opps_df        = data["opportunities"]
    papers_df      = data["papers"]
    hackathons_df  = data["hackathons"]

    # Build student features first — their skill vocab is the shared vocab
    s_mat, s_feats, s_ids = build_student_features(students_df)

    # Extract skill portion of vocabulary (strip "skill:" prefix)
    skill_vocab = [f.replace("skill:", "") for f in s_feats if f.startswith("skill:")]

    o_mat, o_feats, o_ids = build_opportunity_features(opps_df, skill_vocab)
    p_mat, p_feats, p_ids = build_paper_features(papers_df, skill_vocab)
    h_mat, h_feats, h_ids = build_hackathon_features(hackathons_df, skill_vocab)

    log.info("Feature engineering complete.")
    return {
        "student_matrix":     s_mat,
        "student_features":   s_feats,
        "student_ids":        s_ids,
        "opp_matrix":         o_mat,
        "opp_features":       o_feats,
        "opp_ids":            o_ids,
        "paper_matrix":       p_mat,
        "paper_features":     p_feats,
        "paper_ids":          p_ids,
        "hackathon_matrix":   h_mat,
        "hackathon_features": h_feats,
        "hackathon_ids":      h_ids,
        "skill_vocab":        skill_vocab,
    }


# ===========================================================================
# 6.  HELPERS
# ===========================================================================

def _multi_hot(
    series: pd.Series,
    vocab: List[str],
    weight: float = 1.0,
) -> np.ndarray:
    """Create a multi-hot matrix from a Series of lists, using a given vocab."""
    vocab_index = {v: i for i, v in enumerate(vocab)}
    mat = np.zeros((len(series), len(vocab)), dtype=np.float32)
    for row_idx, items in enumerate(series):
        if isinstance(items, list):
            for item in items:
                col_idx = vocab_index.get(item.strip().lower())
                if col_idx is not None:
                    mat[row_idx, col_idx] = weight
    return mat


def _one_hot(series: pd.Series, prefix: str = "") -> Tuple[np.ndarray, List[str]]:
    """One-hot encode a categorical Series.  Returns (matrix, column_names)."""
    dummies = pd.get_dummies(series, prefix=prefix, dtype=float)
    return dummies.values.astype(np.float32), list(dummies.columns)


# ===========================================================================
# 6.  CLI
# ===========================================================================

if __name__ == "__main__":
    from ml.preprocessing import preprocess_all

    data = preprocess_all()
    feats = build_all_features(data)
    print(f"Student  matrix : {feats['student_matrix'].shape}")
    print(f"Opp      matrix : {feats['opp_matrix'].shape}")
    print(f"Paper    matrix : {feats['paper_matrix'].shape}")
    print(f"Skill vocab size: {len(feats['skill_vocab'])}")
