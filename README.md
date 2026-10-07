# 🎓 StudentPulse

**Personalised recommendation system** that matches students with internships, jobs, and research papers based on their skills, interests, and academic profile.

---

## Architecture

```
Student Profile  →  Preprocessing  →  Feature Engineering
                                              ↓
                                     Similarity Calculation
                                       (Cosine + Overlap)
                                              ↓
                                  Content-Based Recommendation
                                              ↓
                                    Personalised Results
                                              ↓
                                     Student Feedback
                                              ↓
                                     Model Improvement
```

---

## Project Structure

```
student-pulse/
│
├── frontend/               # (Member 3 — Dashboard / Web App)
├── backend/                # (Member 2 — API / Services)
│
├── ml/
│   ├── data/
│   │   ├── students.csv            25 student profiles
│   │   ├── opportunities.csv       25 internship/job listings
│   │   └── research_papers.csv     25 academic papers
│   │
│   ├── preprocessing.py            Data loading & cleaning
│   ├── feature_engineering.py      Numeric feature matrices
│   ├── similarity.py               Cosine + skill overlap scoring
│   ├── clustering.py               K-Means for cold-start
│   ├── recommendation_engine.py    Main recommendation class
│   ├── train.py                    Training pipeline + artefact saving
│   └── evaluate.py                 Precision/Recall/NDCG/MRR metrics
│
├── notebooks/
│   └── student_pulse_ml.ipynb      End-to-end demo notebook
│
├── docs/
│   ├── ML_ARCHITECTURE.md          System design & module descriptions
│   ├── DATASET.md                  Schema docs for all three CSVs
│   └── MODEL_REPORT.md             Evaluation results & roadmap
│
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the model (from student-pulse/ directory)
python -m ml.train --demo

# 3. Load the engine and get recommendations
python - <<'EOF'
from ml.train import load_engine
engine = load_engine()
result = engine.recommend_all("S001", top_k_opps=5, top_k_papers=5)
print(result.student_name)
for r in result.opportunities:
    print(f"  [{r.score:.3f}] {r.title}")
EOF

# 4. Run the notebook
cd notebooks
jupyter notebook student_pulse_ml.ipynb
```

---

## Core API

```python
from ml.preprocessing        import preprocess_all
from ml.feature_engineering  import build_all_features
from ml.similarity            import compute_all_similarities
from ml.clustering            import cluster_students
from ml.recommendation_engine import RecommendationEngine

# Full pipeline
data    = preprocess_all()
feats   = build_all_features(data)
sims    = compute_all_similarities(feats, data["students"], data["opportunities"], data["papers"])
model, labels = cluster_students(feats["student_matrix"])

engine  = RecommendationEngine()
engine.fit(data, feats, sims, model, labels)

# Recommend for a known student
result = engine.recommend_all("S001", top_k_opps=5, top_k_papers=5)

# Recommend for a new student (cold-start)
result = engine.recommend_for_new_student(
    skills=["python", "machine learning"],
    interests=["data science"],
    cgpa=8.0
)

# With filters
opps = engine.recommend_opportunities("S001", top_k=5, filters={"type": "internship", "remote": True})

# Explanation
print(engine.get_explanation("S001", "O001", "opportunity"))
```

---

## Evaluation

```bash
python -m ml.evaluate
```

Metrics reported: Precision@K, Recall@K, F1@K, NDCG@K, MRR, Hit Rate@K, Catalogue Coverage.

---

## Docs

| Document | Description |
|---|---|
| [`docs/ML_ARCHITECTURE.md`](docs/ML_ARCHITECTURE.md) | System design, module descriptions, scoring formula |
| [`docs/DATASET.md`](docs/DATASET.md) | Schema for all three CSV files |
| [`docs/MODEL_REPORT.md`](docs/MODEL_REPORT.md) | Evaluation results, limitations, roadmap |

---

## Team

| Member | Responsibility |
|---|---|
| Member 1 (ML) | Data pipeline, recommendation engine, evaluation |
| Member 2 (Backend) | REST API, services, database integration |
| Member 3 (Frontend) | Dashboard, student UI, visualisations |
