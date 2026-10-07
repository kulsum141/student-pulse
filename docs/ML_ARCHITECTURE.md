# StudentPulse ML — Architecture

## Overview

StudentPulse is a content-based personalised recommendation system that matches
students with internships, jobs, hackathons, and research papers based on their
skills, interests, academic profile, and career goals. It also analyses skill
gaps, generates career roadmaps, provides an AI assistant interface, and learns
from student feedback to personalise future results.

---

## Full System Architecture

```
                         STUDENT PULSE
                              │
                       Student Profile
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
        Skill Gap Model              Recommendation Model
        (skill_gap.py)              (recommendation_engine.py)
               │                             │
               ▼                             ▼
         Career Roadmap              Opportunities │ Hackathons │ Research
        (skill_gap.py)                             │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                                Internship     Hackathon      Research
                                               │
                                    └──────────┼──────────────┘
                                               ▼
                                         AI Assistant
                                        (ai_assistant.py)
                                               │
                                               ▼
                                       Student Feedback
                                        (feedback.py)
                                               │
                                               ▼
                                  Future Personalization
                                  (PersonalizationLayer)
```

---

## Data Flow

```
students.csv ──┐
opportunities.csv─┤
hackathons.csv ───┼──→ preprocessing.py ──→ feature_engineering.py ──→ similarity.py
research_papers ──┘         │                       │                       │
                             ▼                       ▼                       ▼
                       clean DataFrames     numeric matrices          cosine + overlap
                                                    │                  similarity matrices
                                                    └──────────────────────┐
                                                                           ▼
                                                                  clustering.py (K-Means)
                                                                           │
                                                                           ▼
                                                              RecommendationEngine.fit()
                                                                           │
                                                   ┌───────────────────────┼───────────────────────┐
                                                   ▼                       ▼                       ▼
                                          recommend_opportunities   recommend_hackathons   recommend_papers
                                                   │                       │                       │
                                                   └───────────────────────┼───────────────────────┘
                                                                           ▼
                                                                     SkillGapAnalyzer
                                                                           │
                                                                     CareerRoadmap
                                                                           │
                                                                     StudentAssistant
                                                                           │
                                                                    FeedbackStore
                                                                           │
                                                                PersonalizationLayer
                                                                           │
                                                              Re-ranked Recommendations
```

---

## Module Descriptions

### `ml/preprocessing.py`
- Loads `students.csv`, `opportunities.csv`, `research_papers.csv`, `hackathons.csv`
- `clean_students()`, `clean_opportunities()`, `clean_papers()`, `clean_hackathons()`
- Strips whitespace, normalises booleans, parses comma-separated lists, deduplicates
- Entry-point: `preprocess_all()` → `{"students", "opportunities", "papers", "hackathons"}`

### `ml/feature_engineering.py`
- `build_student_features()` → multi-hot skills + interest + scalar
- `build_opportunity_features()` → shared skill space + domain + type + scalar
- `build_paper_features()` → shared skill space + domain + difficulty + year + citations
- `build_hackathon_features()` → shared skill space + domain + difficulty + mode + prize + team size
- Entry-point: `build_all_features(data)` → feature dict with matrices for all four item types

### `ml/similarity.py`
- `cosine_similarity_matrix(A, B)` — vectorised L2-normalised cosine in shared skill space
- `skill_overlap_score()` — Jaccard recall (|intersection| / |required|)
- `cgpa_gate()` — soft sigmoid eligibility factor
- `weighted_similarity()` — final score: `(0.55×cosine + 0.35×overlap) × cgpa_factor`
- `compute_all_similarities()` — pre-computes opp, paper, **and hackathon** similarity matrices

### `ml/clustering.py`
- K-Means over L2-normalised student vectors; auto-k via silhouette score
- `get_cluster_label()` for cold-start (new student → nearest centroid)
- `summarize_clusters()` — human-readable cluster profiles
- `pca_2d()` — 2D projection for notebook visualisation

### `ml/recommendation_engine.py`
- `RecommendationEngine` class — central inference interface
- `.recommend_opportunities(student_id, top_k, filters)`
- `.recommend_papers(student_id, top_k, filters)`
- `.recommend_hackathons(student_id, top_k, filters)` ← **new**
- `.recommend_all(student_id)` → `RecommendationResult` (all three item types)
- `.recommend_for_new_student(skills, interests, cgpa)` → cold-start
- `.get_explanation(student_id, item_id, item_type)` → plain-English reasoning

### `ml/skill_gap.py` ← **new**
- `SkillGapAnalyzer` — analyses skill gap between student and any target
  - `.analyze(student_id, item_id, item_type)` → `SkillGapReport`
  - `.analyze_for_career_goal(student_id)` → `SkillGapReport`
  - `.analyze_all_for_student(student_id)` → ranked list of gaps
- `CareerRoadmap` — generates ordered learning plans
  - `.generate(student_id)` → `RoadmapResult`
  - `.generate_from_goal(skills, goal)` → cold-start roadmap
- Built-in skill-difficulty tiers (1=foundation, 2=intermediate, 3=advanced)
- Built-in career-goal → skill mappings for 20 tech roles

### `ml/ai_assistant.py` ← **new**
- `IntentClassifier` — rule-based NL intent classification (no external API needed)
- `ResponseFormatter` — converts ML results to plain-English Markdown
- `StudentAssistant` — conversational interface
  - `.ask(student_id, query)` → `AssistantResponse`
  - `.ask_for_new_student(query, skills, interests, cgpa)` → cold-start
  - `.get_suggestions(student_id)` → proactive follow-up prompts
- `build_llm_context()` — packages student data as a payload for Gemini/Claude/GPT

### `ml/feedback.py` ← **new**
- `FeedbackStore` — persistent feedback log (CSV + JSON)
  - `.record(student_id, item_id, type, feedback_type)`
  - `.get_student_feedback()`, `.get_item_stats()`
  - `.export_csv()`, `.load_csv()`
- `PersonalizationLayer` — re-ranks recommendations using feedback signals
  - `.preference_profile(student_id)` → `PreferenceProfile`
  - `.apply(student_id, recommendations)` → re-ranked list
- `FeedbackCollector` — high-level convenience wrapper
  - `.thumbs_up()`, `.thumbs_down()`, `.applied()`, `.saved()`, `.ignored()`

### `ml/train.py`
- 6-step pipeline: preprocess → features → similarity → cluster → engine → **auxiliary modules**
- Saves all artefacts to `ml/data/artefacts/`
- Attaches `_skill_gap_analyzer`, `_career_roadmap`, `_feedback_store`,
  `_personalization`, `_assistant` to engine after fit for convenience

### `ml/evaluate.py`
- Synthetic ground-truth: item relevant if skill overlap ≥ 0.4
- Metrics: Precision@K, Recall@K, F1@K, NDCG@K, MRR, Hit Rate@K, Catalogue Coverage
- `full_evaluation_report(engine, data, k_values=[5, 10, 20])`

---

## Scoring Formula

```
final_score = (0.55 × cosine + 0.35 × overlap) × (0.90 + 0.10 × cgpa_factor)
```

| Sub-score | Formula | Range |
|---|---|---|
| cosine | L2-normalised dot product in shared skill space | [−1, 1] |
| overlap | \|intersection\| / \|required_skills\| | [0, 1] |
| cgpa_factor | sigmoid(3 × (student_cgpa − min_cgpa)) | (0, 1) |
| final | weighted combination × cgpa gate | [0, 1] |

Weights configurable via `RecommendationEngine(weights={...})`.

---

## Personalization Signal Flow

```
Student interacts (apply / save / thumbs-up / ignore)
        ↓
FeedbackCollector.record()
        ↓
FeedbackStore (in-memory + CSV)
        ↓
PersonalizationLayer.preference_profile()
  → liked_domains, disliked_domains, liked_skills
        ↓
PersonalizationLayer.apply(recommendations)
  → multiplier per item: ×1.25 (liked domain), ×0.70 (disliked domain)
        ↓
Re-ranked recommendations
```

---

## Quick-Start

```python
from ml.train import train, load_engine

# Train (includes all modules)
engine = train()

# Recommend
result = engine.recommend_all("S001")

# Skill gap
report = engine._skill_gap_analyzer.analyze_for_career_goal("S001")

# Career roadmap
roadmap = engine._career_roadmap.generate("S001")

# AI assistant
resp = engine._assistant.ask("S001", "Show me remote internships in Bangalore")

# Feedback
engine._feedback_store.record("S001", "O001", "opportunity", "applied")
reranked = engine._personalization.apply("S001", result.opportunities, engine)
```

---

## Extensibility

| Feature | How to Add |
|---|---|
| New item type (e.g. courses) | Add CSV + `clean_X()` + `build_X_features()` + similarity + `recommend_X()` |
| Collaborative filtering | Add `user_interactions.csv`; hybrid blend with content score |
| External LLM (Gemini/Claude) | Use `build_llm_context()` from `ai_assistant.py` |
| Real-time API | Wrap `engine.recommend_all()` in a FastAPI route |
| More career goals | Extend `CAREER_GOAL_SKILLS` dict in `skill_gap.py` |
| More skill resources | Extend `SKILL_RESOURCES` dict in `skill_gap.py` |
