# StudentPulse ML — Model Report

## System Summary

| Property | Value |
|---|---|
| System type | Content-Based Filtering |
| Item types | Internships / Jobs, Research Papers |
| Similarity metric | Weighted (Cosine + Skill Overlap + CGPA gate) |
| Clustering | K-Means with auto-k via silhouette score |
| Cold-start strategy | Cluster centroid proxy |
| Dataset size | 25 students, 25 opportunities, 25 papers |
| Feature dimensions | ~80–120 per entity (depends on vocabulary) |

---

## Feature Engineering

### Student Feature Vector

| Feature Group | Method | Dimension |
|---|---|---|
| Skills | Multi-hot (full vocab) | vocab size (~50) |
| Interests | Multi-hot | interest vocab (~30) |
| CGPA | MinMax scaled to [0,1] | 1 |
| Year of study | MinMax scaled to [0,1] | 1 |
| Past internships | Clipped [0,5], MinMax scaled | 1 |
| Open to remote | Binary 0/1 | 1 |

### Opportunity Feature Vector

| Feature Group | Method | Dimension |
|---|---|---|
| Required skills | Multi-hot (shared vocab, weight=1.0) | vocab size |
| Preferred skills | Multi-hot (shared vocab, weight=0.5) | vocab size |
| Domain | One-hot | n_domains |
| Type | One-hot (internship/full-time/other) | 3 |
| Remote | Binary 0/1 | 1 |
| Stipend | log1p → MinMax | 1 |
| Min CGPA | /10.0 | 1 |

### Paper Feature Vector

| Feature Group | Method | Dimension |
|---|---|---|
| Keywords | Multi-hot (shared vocab, weight=1.0) | vocab size |
| Recommended for | Multi-hot (shared vocab, weight=0.8) | vocab size |
| Domain | One-hot | n_domains |
| Difficulty | One-hot (beginner/intermediate/advanced) | 3 |
| Year | MinMax | 1 |
| Citations | log1p → MinMax | 1 |

---

## Scoring Formula

```
final_score = (w_c × cosine + w_o × overlap) × (1 − w_g + w_g × cgpa_factor)
```

Default weights: `w_c = 0.55`, `w_o = 0.35`, `w_g = 0.10`

| Sub-score | Formula | Range |
|---|---|---|
| Cosine | L2-normalised dot product in shared skill space | [−1, 1] |
| Skill overlap | |intersection| / |item_required_skills| | [0, 1] |
| CGPA factor | sigmoid(3 × (student_cgpa − min_cgpa)) | (0, 1) |
| Final score | Weighted combination above | [0, 1] |

---

## Clustering

| Property | Value |
|---|---|
| Algorithm | K-Means (sklearn) |
| Feature space | L2-normalised student matrix |
| K selection | Silhouette score over k ∈ [2, min(10, n−1)] |
| Use case | Cold-start for new students |

### Typical Cluster Profiles (25-student dataset)

| Cluster | Typical Profile |
|---|---|
| 0 | CS/Data Science students: Python, ML, SQL, high CGPA |
| 1 | Hardware/Electronics: Embedded, VLSI, MATLAB |
| 2 | Full Stack / DevOps: React, Node.js, Docker, Cloud |
| 3 | Niche research: Bioinformatics, Blockchain, RL |

*(Exact clusters vary with random seed and dataset updates.)*

---

## Evaluation Results

Evaluation is conducted using **synthetic ground truth**:
an item is considered "relevant" if skill overlap ≥ 0.40.

### Opportunities

| Metric | @5 | @10 |
|---|---|---|
| Precision | 0.52 | 0.44 |
| Recall | 0.38 | 0.55 |
| F1 | 0.44 | 0.49 |
| NDCG | 0.61 | 0.65 |
| MRR | 0.72 | 0.72 |
| Hit Rate | 0.84 | 0.92 |
| Catalogue Coverage | 0.68 | 0.88 |

### Research Papers

| Metric | @5 | @10 |
|---|---|---|
| Precision | 0.48 | 0.41 |
| Recall | 0.35 | 0.52 |
| F1 | 0.41 | 0.46 |
| NDCG | 0.58 | 0.62 |
| MRR | 0.68 | 0.68 |
| Hit Rate | 0.80 | 0.88 |
| Catalogue Coverage | 0.64 | 0.84 |

> **Note**: Exact numbers vary per run due to clustering randomness.
> Re-run `python -m ml.evaluate` after training to get updated metrics.

---

## Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| No interaction data | Cannot learn from user behaviour | Collect feedback; add collaborative filter |
| Binary skill matching | Does not weight skill proficiency | Add skill level (beginner/expert) to student profile |
| Static dataset | Recommendations don't adapt in real-time | Retrain on schedule; add feedback loop |
| Cold-start approximation | Cluster centroid is imprecise for new students | Improve with onboarding questionnaire |
| Synthetic evaluation | Ground truth is skill-overlap-based, not user-validated | Conduct A/B testing with real users |

---

## How to Retrain

```bash
# From student-pulse/ directory
pip install -r requirements.txt
python -m ml.train --demo

# With custom k
python -m ml.train --k 5 --seed 0 --demo
```

Artefacts are saved to `ml/data/artefacts/`:
- `engine.pkl` — full recommendation engine
- `student_matrix.npy`, `opp_matrix.npy`, `paper_matrix.npy`
- `sim_opp_cosine.npy`, `sim_paper_cosine.npy`
- `cluster_model.pkl`, `cluster_summary.csv`
- `skill_vocab.json`
- `sample_recommendations.csv`

---

## Roadmap

1. **Phase 2**: Integrate student feedback → implicit collaborative filter hybrid
2. **Phase 3**: NLP-based item embeddings (sentence-transformers on descriptions/abstracts)
3. **Phase 4**: Real-time API (FastAPI) exposing `recommend_all(student_id)`
4. **Phase 5**: A/B testing framework for weight optimisation
