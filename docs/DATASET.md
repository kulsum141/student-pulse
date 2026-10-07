# StudentPulse ML — Dataset Documentation

## Overview

Three CSV datasets power the StudentPulse ML system. All files live in `ml/data/`.

---

## 1. `students.csv`

Represents student profiles used as the query side of the recommendation system.

| Column | Type | Description | Example |
|---|---|---|---|
| `student_id` | string | Unique student identifier | `S001` |
| `name` | string | Full name | `Aarav Sharma` |
| `email` | string | University email | `aarav@university.edu` |
| `department` | string | Department / major | `Computer Science` |
| `year_of_study` | int (1–6) | Current year | `3` |
| `cgpa` | float (0–10) | Cumulative GPA | `8.7` |
| `skills` | comma-separated list | Technical skills | `Python,Machine Learning,SQL` |
| `interests` | comma-separated list | Areas of interest | `AI,Data Science,Research` |
| `preferred_location` | string | Preferred work city | `Bangalore` |
| `open_to_remote` | bool | Open to remote work | `True` |
| `past_internships` | int | Number of prior internships | `1` |
| `courses_completed` | comma-separated list | Completed courses | `Deep Learning,Statistics` |
| `language_known` | comma-separated list | Languages spoken | `English,Hindi` |
| `career_goal` | string | Target role | `Data Scientist` |

**Size**: 25 synthetic records across 8 departments, 4 years of study.

**Validation rules** (applied in `preprocessing.py`):
- `student_id` and `name` are required
- `cgpa` clipped to [0, 10]
- `year_of_study` clipped to [1, 6]
- `past_internships` clipped to [0, 20]
- Duplicates on `student_id` → keep first

---

## 2. `opportunities.csv`

Represents internships and full-time jobs that students can be matched to.

| Column | Type | Description | Example |
|---|---|---|---|
| `opportunity_id` | string | Unique ID | `O001` |
| `title` | string | Role title | `Machine Learning Intern` |
| `company` | string | Company name | `TechCorp AI` |
| `type` | string | `Internship` or `Full-time` | `Internship` |
| `domain` | string | Domain area | `Data Science` |
| `required_skills` | comma-separated list | Must-have skills | `Python,Machine Learning,SQL` |
| `preferred_skills` | comma-separated list | Nice-to-have skills | `TensorFlow,Scikit-learn` |
| `location` | string | Job location | `Bangalore` |
| `remote` | bool | Remote-friendly | `True` |
| `duration` | string | Duration or `Permanent` | `3 months` |
| `stipend_monthly` | float | Monthly pay (INR) | `25000` |
| `min_cgpa` | float (0–10) | Minimum CGPA required | `7.5` |
| `description` | string | Role description | `Work on ML models …` |
| `tags` | comma-separated list | Search tags | `ml,ai,python,internship` |

**Size**: 25 records — 15 internships, 10 full-time roles across 10 domains.

**Validation rules**:
- `opportunity_id` and `title` are required
- `min_cgpa` clipped to [0, 10]
- `stipend_monthly` log-scaled for feature normalisation
- Duplicates on `opportunity_id` → keep first

---

## 3. `research_papers.csv`

Represents academic papers recommended to students for learning and research.

| Column | Type | Description | Example |
|---|---|---|---|
| `paper_id` | string | Unique ID | `P001` |
| `title` | string | Paper title | `Attention Is All You Need` |
| `authors` | string | Author(s) | `Vaswani et al.` |
| `year` | int | Publication year | `2017` |
| `domain` | string | Research domain | `NLP` |
| `keywords` | comma-separated list | Technical keywords | `Transformers,Attention,NLP` |
| `abstract` | string | Short abstract | `Introduces the Transformer …` |
| `journal` | string | Venue | `NeurIPS` |
| `citations` | int | Citation count | `90000` |
| `difficulty_level` | string | `Beginner`/`Intermediate`/`Advanced` | `Advanced` |
| `recommended_for` | comma-separated list | Target audience domains | `NLP,AI Research,Deep Learning` |

**Size**: 25 records covering 10 domains (NLP, ML, CV, RL, Bioinformatics, Blockchain, etc.).

**Validation rules**:
- `paper_id` and `title` are required
- `year` defaults to 2000 if missing
- `citations` defaults to 0 if missing; log-scaled for features
- Duplicates on `paper_id` → keep first

---

## Extending the Datasets

To add more records:
1. Open the relevant CSV in `ml/data/`
2. Append rows following the schema above
3. Re-run `python -m ml.train` to retrain the engine

To add a completely new item type (e.g., `courses.csv`):
1. Add the CSV to `ml/data/`
2. Add a `clean_courses()` function in `preprocessing.py`
3. Add `build_course_features()` in `feature_engineering.py`
4. Add course similarity in `similarity.py`
5. Add `recommend_courses()` method to `RecommendationEngine`

---

## Synthetic Data Notes

All data is **synthetic** and generated for development/testing purposes.
Student names, emails, and company names are fictitious.
Skills and domains are based on real industry categories (NASSCOM, LinkedIn Skills taxonomy).
