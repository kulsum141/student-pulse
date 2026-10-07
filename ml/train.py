"""
train.py
--------
StudentPulse ML — Training Pipeline

Orchestrates the full ML pipeline from raw CSV data to a fitted
RecommendationEngine that is ready to serve predictions.

Pipeline
--------
1. preprocess_all()         — load + clean all three datasets
2. build_all_features()     — convert to numeric feature matrices
3. compute_all_similarities()— pre-compute cosine + overlap matrices
4. cluster_students()       — group students for cold-start support
5. RecommendationEngine.fit()— assemble all artefacts into the engine
6. save artefacts to disk   — for serving / evaluation

Usage
-----
    # From project root
    python -m ml.train

    # Or with custom paths
    python -m ml.train --students ml/data/students.csv \
                       --opps    ml/data/opportunities.csv \
                       --papers  ml/data/research_papers.csv \
                       --out     ml/data/artefacts/
"""

import argparse
import logging
import pickle
import time
from pathlib import Path
from typing import Optional

import numpy as np

from ml.preprocessing import preprocess_all
from ml.feature_engineering import build_all_features
from ml.similarity import compute_all_similarities
from ml.clustering import cluster_students, save_cluster_model, summarize_clusters
from ml.recommendation_engine import RecommendationEngine, recommend_all_students, recommendations_to_dataframe
from ml.skill_gap import SkillGapAnalyzer, CareerRoadmap
from ml.ai_assistant import StudentAssistant
from ml.feedback import FeedbackStore, PersonalizationLayer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Default artefact output directory
_HERE = Path(__file__).parent
DEFAULT_OUT = _HERE / "data" / "artefacts"


# ===========================================================================
# 1.  MAIN  TRAINING  FUNCTION
# ===========================================================================

def train(
    students_path: Optional[Path] = None,
    opps_path: Optional[Path] = None,
    papers_path: Optional[Path] = None,
    hackathons_path: Optional[Path] = None,
    output_dir: Path = DEFAULT_OUT,
    n_clusters: Optional[int] = None,
    random_state: int = 42,
) -> RecommendationEngine:
    """Run the full training pipeline.

    Parameters
    ----------
    students_path   : override default students CSV
    opps_path       : override default opportunities CSV
    papers_path     : override default research_papers CSV
    hackathons_path : override default hackathons CSV
    output_dir      : directory to save trained artefacts
    n_clusters      : explicit k for clustering (None → auto)
    random_state    : for reproducibility

    Returns
    -------
    Fitted RecommendationEngine
    """
    t0 = time.time()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info("StudentPulse ML — Training Pipeline")
    log.info("=" * 60)

    # ── Step 1: Preprocessing ─────────────────────────────────────────────
    log.info("[1/6] Preprocessing …")
    kwargs = {}
    if students_path:   kwargs["students_path"]      = students_path
    if opps_path:       kwargs["opportunities_path"]  = opps_path
    if papers_path:     kwargs["papers_path"]          = papers_path
    if hackathons_path: kwargs["hackathons_path"]      = hackathons_path
    data = preprocess_all(**kwargs)

    log.info(
        "  students=%d  opportunities=%d  papers=%d  hackathons=%d",
        len(data["students"]), len(data["opportunities"]),
        len(data["papers"]),   len(data["hackathons"]),
    )

    # ── Step 2: Feature Engineering ──────────────────────────────────────
    log.info("[2/6] Feature engineering …")
    features = build_all_features(data)

    log.info(
        "  student_matrix=%s  opp_matrix=%s  paper_matrix=%s  hackathon_matrix=%s",
        features["student_matrix"].shape,
        features["opp_matrix"].shape,
        features["paper_matrix"].shape,
        features["hackathon_matrix"].shape,
    )

    # ── Step 3: Similarity matrices ───────────────────────────────────────
    log.info("[3/6] Computing similarity matrices …")
    similarities = compute_all_similarities(
        features,
        students_df=data["students"],
        opps_df=data["opportunities"],
        papers_df=data["papers"],
        hackathons_df=data["hackathons"],
    )

    # ── Step 4: Clustering ────────────────────────────────────────────────
    log.info("[4/6] Clustering students …")
    cluster_model, cluster_labels = cluster_students(
        features["student_matrix"],
        n_clusters=n_clusters,
        random_state=random_state,
    )
    cluster_summary = summarize_clusters(data["students"], cluster_labels)
    log.info("Cluster summary:\n%s", cluster_summary.to_string(index=False))

    # ── Step 5: Fit engine ────────────────────────────────────────────────
    log.info("[5/6] Fitting recommendation engine …")
    engine = RecommendationEngine()
    engine.fit(data, features, similarities, cluster_model, cluster_labels)

    # ── Step 6: Initialise auxiliary modules ─────────────────────────────
    log.info("[6/6] Initialising skill-gap, assistant, and feedback modules …")
    analyzer  = SkillGapAnalyzer(engine)
    roadmap   = CareerRoadmap(engine)
    store     = FeedbackStore()
    pl_layer  = PersonalizationLayer(store)
    assistant = StudentAssistant(engine, analyzer, roadmap)
    log.info("  All modules initialised.")

    # ── Save artefacts ────────────────────────────────────────────────────
    _save_artefacts(
        output_dir, engine, features, similarities, cluster_model, cluster_labels, cluster_summary
    )

    # Attach auxiliary objects to engine for convenience access after load
    engine._skill_gap_analyzer = analyzer
    engine._career_roadmap     = roadmap
    engine._feedback_store     = store
    engine._personalization    = pl_layer
    engine._assistant          = assistant

    elapsed = time.time() - t0
    log.info("=" * 60)
    log.info("Training complete in %.2f seconds.", elapsed)
    log.info("Artefacts saved to: %s", output_dir)
    log.info("=" * 60)

    return engine


# ===========================================================================
# 2.  SAVE  ARTEFACTS
# ===========================================================================

def _save_artefacts(
    output_dir: Path,
    engine: RecommendationEngine,
    features: dict,
    similarities: dict,
    cluster_model,
    cluster_labels: np.ndarray,
    cluster_summary,
) -> None:
    """Persist all trained artefacts to output_dir."""

    # Engine (full pickle)
    engine_path = output_dir / "engine.pkl"
    with open(engine_path, "wb") as f:
        pickle.dump(engine, f)
    log.info("  Saved engine → %s", engine_path)

    # Feature matrices (numpy)
    for name in ["student_matrix", "opp_matrix", "paper_matrix"]:
        np_path = output_dir / f"{name}.npy"
        np.save(np_path, features[name])
        log.info("  Saved %s → %s", name, np_path)

    # Similarity matrices
    for name in similarities:
        np_path = output_dir / f"sim_{name}.npy"
        np.save(np_path, similarities[name])
        log.info("  Saved similarity %s → %s", name, np_path)

    # Cluster model
    save_cluster_model(
        cluster_model, cluster_labels, features["student_ids"],
        path=output_dir / "cluster_model.pkl"
    )

    # Cluster summary CSV
    cluster_summary.to_csv(output_dir / "cluster_summary.csv", index=False)
    log.info("  Saved cluster_summary → %s", output_dir / "cluster_summary.csv")

    # Vocabulary
    import json
    vocab_path = output_dir / "skill_vocab.json"
    with open(vocab_path, "w") as f:
        json.dump(features["skill_vocab"], f, indent=2)
    log.info("  Saved skill_vocab (%d tokens) → %s", len(features["skill_vocab"]), vocab_path)

    # Sample recommendation output (now includes hackathons)
    results = recommend_all_students(engine, top_k_opps=5, top_k_papers=5)
    df = recommendations_to_dataframe(results)
    recs_path = output_dir / "sample_recommendations.csv"
    df.to_csv(recs_path, index=False)
    log.info("  Saved sample recommendations → %s", recs_path)


# ===========================================================================
# 3.  LOAD  ENGINE
# ===========================================================================

def load_engine(output_dir: Path = DEFAULT_OUT) -> RecommendationEngine:
    """Load a previously trained engine from disk.

    Parameters
    ----------
    output_dir : directory containing engine.pkl

    Returns
    -------
    Fitted RecommendationEngine

    Usage
    -----
    >>> from ml.train import load_engine
    >>> engine = load_engine()
    >>> result = engine.recommend_all("S001")
    """
    engine_path = Path(output_dir) / "engine.pkl"
    if not engine_path.exists():
        raise FileNotFoundError(
            f"No trained engine found at {engine_path}. Run train.py first."
        )
    with open(engine_path, "rb") as f:
        engine = pickle.load(f)
    log.info("Engine loaded ← %s", engine_path)
    return engine


# ===========================================================================
# 4.  CLI  ENTRY-POINT
# ===========================================================================

def _parse_args():
    p = argparse.ArgumentParser(description="StudentPulse ML — Training Pipeline")
    p.add_argument("--students",   type=Path, default=None, help="Path to students.csv")
    p.add_argument("--opps",       type=Path, default=None, help="Path to opportunities.csv")
    p.add_argument("--papers",     type=Path, default=None, help="Path to research_papers.csv")
    p.add_argument("--hackathons", type=Path, default=None, help="Path to hackathons.csv")
    p.add_argument("--out",        type=Path, default=DEFAULT_OUT, help="Output directory for artefacts")
    p.add_argument("--k",          type=int,  default=None, help="Number of clusters (default: auto)")
    p.add_argument("--seed",       type=int,  default=42,   help="Random seed")
    p.add_argument("--demo",       action="store_true",     help="Print demo recommendations after training")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    engine = train(
        students_path=args.students,
        opps_path=args.opps,
        papers_path=args.papers,
        hackathons_path=args.hackathons,
        output_dir=args.out,
        n_clusters=args.k,
        random_state=args.seed,
    )

    if args.demo:
        result = engine.recommend_all("S001", top_k_opps=5, top_k_papers=5, top_k_hackathons=5)
        print(f"\n{'='*60}")
        print(f"Demo — {result.student_name}")
        print("Top Opportunities:")
        for r in result.opportunities:
            print(f"  [{r.score:.3f}] {r.title}")
        print("Top Hackathons:")
        for r in result.hackathons:
            print(f"  [{r.score:.3f}] {r.title}")
        print("Top Papers:")
        for r in result.papers:
            print(f"  [{r.score:.3f}] {r.title}")

        # Demo assistant
        if engine._assistant is not None:
            resp = engine._assistant.ask("S001", "Show my career roadmap")
            safe_answer = resp.answer[:400].encode("ascii", errors="replace").decode("ascii")
            print(f"\n--- AI Assistant ---\n{safe_answer}")
