"""
preprocessing.py
----------------
StudentPulse ML — Data Preprocessing Module

Handles loading, cleaning, and normalising the three raw CSV datasets
(students, opportunities, research_papers) into pandas DataFrames ready
for feature engineering.

Pipeline:
    load_raw_data()
        → clean_students()
        → clean_opportunities()
        → clean_papers()
        → preprocess_all()   ← single entry-point used by train.py
"""

import logging
import re
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default data paths  (relative to this file so the module is portable)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
DATA_DIR = _HERE / "data"

STUDENTS_CSV = DATA_DIR / "students.csv"
OPPORTUNITIES_CSV = DATA_DIR / "opportunities.csv"
PAPERS_CSV = DATA_DIR / "research_papers.csv"
HACKATHONS_CSV = DATA_DIR / "hackathons.csv"


# ===========================================================================
# 1.  RAW LOADERS
# ===========================================================================

def load_raw_data(
    students_path: Path = STUDENTS_CSV,
    opportunities_path: Path = OPPORTUNITIES_CSV,
    papers_path: Path = PAPERS_CSV,
    hackathons_path: Path = HACKATHONS_CSV,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the four CSV files and return raw DataFrames.

    Parameters
    ----------
    students_path, opportunities_path, papers_path, hackathons_path : Path
        Override default paths (useful in tests).

    Returns
    -------
    (students_df, opportunities_df, papers_df, hackathons_df)
    """
    log.info("Loading raw CSV data …")

    students_df = _read_csv(students_path, "students")
    opportunities_df = _read_csv(opportunities_path, "opportunities")
    papers_df = _read_csv(papers_path, "research_papers")
    hackathons_df = _read_csv(hackathons_path, "hackathons")

    log.info(
        "Loaded  students=%d  opportunities=%d  papers=%d  hackathons=%d",
        len(students_df), len(opportunities_df), len(papers_df), len(hackathons_df),
    )
    return students_df, opportunities_df, papers_df, hackathons_df


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    """Read a CSV file with basic error handling."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"[{label}] CSV not found: {path}")
    df = pd.read_csv(path, dtype=str)          # read everything as str first
    df.columns = [c.strip().lower() for c in df.columns]
    log.debug("  %-20s  rows=%d  cols=%d", label, len(df), len(df.columns))
    return df


# ===========================================================================
# 2.  STUDENTS  CLEANING
# ===========================================================================

def clean_students(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the students DataFrame.

    Steps
    -----
    * Drop rows missing student_id / name.
    * Strip whitespace from all string columns.
    * Normalise cgpa → float, clamp to [0, 10].
    * Normalise year_of_study → int, clamp to [1, 6].
    * Normalise open_to_remote → bool.
    * Normalise past_internships → int (default 0).
    * Parse comma-separated list columns into Python lists.
    * Lowercase all list-type values.
    * Drop duplicates on student_id (keep first).
    """
    log.info("Cleaning students …")
    df = df.copy()

    # ── strip whitespace ──────────────────────────────────────────────────
    df = _strip_string_columns(df)

    # ── drop critical-field nulls ─────────────────────────────────────────
    before = len(df)
    df.dropna(subset=["student_id", "name"], inplace=True)
    df = df[df["student_id"].str.strip() != ""]
    log.info("  Dropped %d rows with missing student_id/name", before - len(df))

    # ── numeric fields ────────────────────────────────────────────────────
    df["cgpa"] = pd.to_numeric(df["cgpa"], errors="coerce")
    df["cgpa"] = df["cgpa"].clip(0.0, 10.0).fillna(0.0).round(2)

    df["year_of_study"] = pd.to_numeric(df["year_of_study"], errors="coerce")
    df["year_of_study"] = df["year_of_study"].clip(1, 6).fillna(1).astype(int)

    df["past_internships"] = pd.to_numeric(df["past_internships"], errors="coerce")
    df["past_internships"] = df["past_internships"].clip(0, 20).fillna(0).astype(int)

    # ── boolean field ─────────────────────────────────────────────────────
    df["open_to_remote"] = _parse_bool(df["open_to_remote"])

    # ── list fields ───────────────────────────────────────────────────────
    for col in ["skills", "interests", "courses_completed", "language_known"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_list)

    # ── fill remaining text nulls ─────────────────────────────────────────
    for col in ["department", "preferred_location", "career_goal"]:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").str.lower().str.strip()

    # ── dedup ─────────────────────────────────────────────────────────────
    before = len(df)
    df.drop_duplicates(subset=["student_id"], keep="first", inplace=True)
    log.info("  Removed %d duplicate student_id rows", before - len(df))

    df.reset_index(drop=True, inplace=True)
    log.info("  Students after cleaning: %d", len(df))
    return df


# ===========================================================================
# 3.  OPPORTUNITIES  CLEANING
# ===========================================================================

def clean_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the opportunities DataFrame.

    Steps
    -----
    * Drop rows missing opportunity_id / title.
    * Strip whitespace.
    * Normalise stipend_monthly → float.
    * Normalise min_cgpa → float, clamp [0, 10].
    * Normalise remote → bool.
    * Parse list columns (required_skills, preferred_skills, tags).
    * Lowercase domain and type.
    * Drop duplicates on opportunity_id.
    """
    log.info("Cleaning opportunities …")
    df = df.copy()

    df = _strip_string_columns(df)

    before = len(df)
    df.dropna(subset=["opportunity_id", "title"], inplace=True)
    df = df[df["opportunity_id"].str.strip() != ""]
    log.info("  Dropped %d rows with missing opportunity_id/title", before - len(df))

    df["stipend_monthly"] = pd.to_numeric(df["stipend_monthly"], errors="coerce").fillna(0.0)
    df["min_cgpa"] = pd.to_numeric(df["min_cgpa"], errors="coerce")
    df["min_cgpa"] = df["min_cgpa"].clip(0.0, 10.0).fillna(0.0)

    df["remote"] = _parse_bool(df["remote"])

    for col in ["required_skills", "preferred_skills", "tags"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_list)

    for col in ["domain", "type", "location", "company"]:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").str.lower().str.strip()

    before = len(df)
    df.drop_duplicates(subset=["opportunity_id"], keep="first", inplace=True)
    log.info("  Removed %d duplicate opportunity_id rows", before - len(df))

    df.reset_index(drop=True, inplace=True)
    log.info("  Opportunities after cleaning: %d", len(df))
    return df


# ===========================================================================
# 4.  RESEARCH PAPERS  CLEANING
# ===========================================================================

def clean_papers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the research_papers DataFrame.

    Steps
    -----
    * Drop rows missing paper_id / title.
    * Strip whitespace.
    * Normalise year → int.
    * Normalise citations → int.
    * Parse list columns (keywords, recommended_for).
    * Lowercase domain, difficulty_level.
    * Drop duplicates on paper_id.
    """
    log.info("Cleaning research papers …")
    df = df.copy()

    df = _strip_string_columns(df)

    before = len(df)
    df.dropna(subset=["paper_id", "title"], inplace=True)
    df = df[df["paper_id"].str.strip() != ""]
    log.info("  Dropped %d rows with missing paper_id/title", before - len(df))

    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(2000).astype(int)
    df["citations"] = pd.to_numeric(df["citations"], errors="coerce").fillna(0).astype(int)

    for col in ["keywords", "recommended_for"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_list)

    for col in ["domain", "difficulty_level", "journal"]:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").str.lower().str.strip()

    before = len(df)
    df.drop_duplicates(subset=["paper_id"], keep="first", inplace=True)
    log.info("  Removed %d duplicate paper_id rows", before - len(df))

    df.reset_index(drop=True, inplace=True)
    log.info("  Papers after cleaning: %d", len(df))
    return df


# ===========================================================================
# 5.  HACKATHONS  CLEANING
# ===========================================================================

def clean_hackathons(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the hackathons DataFrame.

    Steps
    -----
    * Drop rows missing hackathon_id / title.
    * Strip whitespace.
    * Normalise prize_pool → float.
    * Normalise team_size_min / team_size_max → int.
    * Parse list columns (required_skills, preferred_skills, tags).
    * Lowercase domain, difficulty_level, mode.
    * Drop duplicates on hackathon_id.
    """
    log.info("Cleaning hackathons …")
    df = df.copy()

    df = _strip_string_columns(df)

    before = len(df)
    df.dropna(subset=["hackathon_id", "title"], inplace=True)
    df = df[df["hackathon_id"].str.strip() != ""]
    log.info("  Dropped %d rows with missing hackathon_id/title", before - len(df))

    df["prize_pool"] = pd.to_numeric(df["prize_pool"], errors="coerce").fillna(0.0)
    df["team_size_min"] = pd.to_numeric(df["team_size_min"], errors="coerce").fillna(1).astype(int)
    df["team_size_max"] = pd.to_numeric(df["team_size_max"], errors="coerce").fillna(4).astype(int)

    for col in ["required_skills", "preferred_skills", "tags"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_list)

    for col in ["domain", "difficulty_level", "mode", "organizer", "theme"]:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").str.lower().str.strip()

    before = len(df)
    df.drop_duplicates(subset=["hackathon_id"], keep="first", inplace=True)
    log.info("  Removed %d duplicate hackathon_id rows", before - len(df))

    df.reset_index(drop=True, inplace=True)
    log.info("  Hackathons after cleaning: %d", len(df))
    return df


# ===========================================================================
# 6.  MASTER ENTRY-POINT
# ===========================================================================

def preprocess_all(
    students_path: Path = STUDENTS_CSV,
    opportunities_path: Path = OPPORTUNITIES_CSV,
    papers_path: Path = PAPERS_CSV,
    hackathons_path: Path = HACKATHONS_CSV,
) -> Dict[str, pd.DataFrame]:
    """Full preprocessing pipeline: load → clean all four datasets.

    Returns
    -------
    dict with keys "students", "opportunities", "papers", "hackathons"
    each mapping to a clean DataFrame.

    Usage
    -----
    >>> from ml.preprocessing import preprocess_all
    >>> data = preprocess_all()
    >>> students    = data["students"]
    >>> opps        = data["opportunities"]
    >>> papers      = data["papers"]
    >>> hackathons  = data["hackathons"]
    """
    raw_students, raw_opps, raw_papers, raw_hackathons = load_raw_data(
        students_path, opportunities_path, papers_path, hackathons_path
    )
    return {
        "students": clean_students(raw_students),
        "opportunities": clean_opportunities(raw_opps),
        "papers": clean_papers(raw_papers),
        "hackathons": clean_hackathons(raw_hackathons),
    }


# ===========================================================================
# 7.  HELPERS
# ===========================================================================

def _strip_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all object columns."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


def _parse_bool(series: pd.Series) -> pd.Series:
    """Convert string booleans ('True'/'False'/'1'/'0'/'yes'/'no') to bool."""
    mapping = {
        "true": True, "1": True, "yes": True,
        "false": False, "0": False, "no": False,
    }
    return series.str.lower().str.strip().map(mapping).fillna(False)


def _parse_list(value) -> list:
    """Parse a comma-separated string into a lowercased, stripped list."""
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [item.strip().lower() for item in re.split(r",", str(value)) if item.strip()]


def normalize_skill(skill: str) -> str:
    """Lowercase, strip, and collapse whitespace in a skill string."""
    return re.sub(r"\s+", " ", skill.strip().lower())


def get_all_skills(students_df: pd.DataFrame) -> list:
    """Return a sorted list of all unique skills across all students."""
    all_skills = set()
    for skills in students_df["skills"]:
        if isinstance(skills, list):
            all_skills.update(normalize_skill(s) for s in skills)
    return sorted(all_skills)


def get_all_item_skills(df: pd.DataFrame, col: str = "required_skills") -> list:
    """Return a sorted list of all unique skills in an opportunity/paper DataFrame."""
    all_skills = set()
    for skills in df[col]:
        if isinstance(skills, list):
            all_skills.update(normalize_skill(s) for s in skills)
    return sorted(all_skills)


# ===========================================================================
# 7.  CLI  (quick smoke-test)
# ===========================================================================

if __name__ == "__main__":
    data = preprocess_all()
    for name, df in data.items():
        print(f"\n{'─'*60}")
        print(f"  {name.upper()}  ({len(df)} rows × {len(df.columns)} cols)")
        print(df.head(3).to_string(index=False))
