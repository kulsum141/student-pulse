"""SQLite persistence for application-owned student and opportunity data."""
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

_DEFAULT_PATH = Path(__file__).parent.parent / "data" / "student_pulse.sqlite3"
_CONFIGURED_PATH = Path(os.environ.get("STUDENT_PULSE_DB_PATH", str(_DEFAULT_PATH))).expanduser()
_DB_PATH = _CONFIGURED_PATH if _CONFIGURED_PATH.is_absolute() else Path(__file__).parent.parent / _CONFIGURED_PATH
_INIT_LOCK = threading.Lock()
_INITIALIZED = False

_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    college TEXT NOT NULL,
    branch TEXT NOT NULL,
    academic_year INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    gpa REAL,
    career_goal TEXT,
    skills_json TEXT NOT NULL DEFAULT '[]',
    interests_json TEXT NOT NULL DEFAULT '[]',
    opportunity_types_json TEXT NOT NULL DEFAULT '[]',
    open_to_remote INTEGER NOT NULL DEFAULT 1,
    preferred_location TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS student_preferences (
    student_id TEXT PRIMARY KEY REFERENCES students(student_id) ON DELETE CASCADE,
    skill_level TEXT,
    preferred_opportunity_type TEXT,
    work_mode TEXT,
    location TEXT,
    learning_style TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id TEXT PRIMARY KEY,
    owner_student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK(category IN ('internship', 'hackathon', 'research', 'job')),
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    skills_json TEXT NOT NULL DEFAULT '[]',
    location TEXT,
    deadline TEXT,
    url TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'closed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS saved_opportunities (
    student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    opportunity_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    title TEXT NOT NULL,
    organization TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    skills_json TEXT NOT NULL DEFAULT '[]',
    location TEXT,
    deadline TEXT,
    url TEXT,
    saved_at TEXT NOT NULL,
    PRIMARY KEY(student_id, opportunity_id)
);
CREATE TABLE IF NOT EXISTS roadmap_progress (
    student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    career_goal TEXT NOT NULL,
    step_number INTEGER NOT NULL CHECK(step_number > 0),
    skill TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1)),
    updated_at TEXT NOT NULL,
    PRIMARY KEY(student_id, career_goal, step_number)
);
CREATE TABLE IF NOT EXISTS student_skills (
    student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    current_level INTEGER NOT NULL CHECK(current_level BETWEEN 0 AND 100),
    target_level INTEGER NOT NULL CHECK(target_level BETWEEN 0 AND 100),
    updated_at TEXT NOT NULL,
    PRIMARY KEY(student_id, skill)
);
CREATE INDEX IF NOT EXISTS idx_opportunities_category_status ON opportunities(category, status);
CREATE INDEX IF NOT EXISTS idx_saved_student ON saved_opportunities(student_id, saved_at DESC);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode_list(value: str) -> list[str]:
    try:
        decoded = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in decoded] if isinstance(decoded, list) else []


def initialize_database() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _INIT_LOCK:
        if _INITIALIZED:
            return
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(_DB_PATH, timeout=10)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(_SCHEMA)
            connection.commit()
            _INITIALIZED = True
        finally:
            connection.close()


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    initialize_database()
    connection = sqlite3.connect(_DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _student_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {
        "student_id": row["student_id"],
        "name": row["name"],
        "email": row["email"],
        "college": row["college"],
        "branch": row["branch"],
        "department": row["branch"],
        "academic_year": row["academic_year"],
        "year_of_study": row["academic_year"],
        "semester": row["semester"],
        "gpa": row["gpa"],
        "cgpa": row["gpa"],
        "career_goal": row["career_goal"],
        "skills": _decode_list(row["skills_json"]),
        "interests": _decode_list(row["interests_json"]),
        "preferred_opportunity_types": _decode_list(row["opportunity_types_json"]),
        "open_to_remote": bool(row["open_to_remote"]),
        "preferred_location": row["preferred_location"],
    }


def create_student(student_id: str, profile: dict, password_hash: str) -> dict:
    timestamp = _now()
    with _connection() as connection:
        connection.execute(
            """INSERT INTO students (
                student_id, email, name, password_hash, college, branch,
                academic_year, semester, gpa, career_goal, skills_json,
                interests_json, opportunity_types_json, open_to_remote,
                preferred_location, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                student_id, profile["email"], profile["name"], password_hash,
                profile["college"], profile["branch"], profile["academic_year"],
                profile["semester"], profile.get("gpa"), profile.get("career_goal"),
                json.dumps(profile.get("skills", [])),
                json.dumps(profile.get("interests", [])),
                json.dumps(profile.get("preferred_opportunity_types", [])),
                int(profile.get("open_to_remote", True)),
                profile.get("preferred_location"), timestamp, timestamp,
            ),
        )
        row = connection.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    return _student_dict(row) or {}


def get_student(student_id: str) -> dict | None:
    with _connection() as connection:
        row = connection.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    return _student_dict(row)


def get_student_by_email(email: str) -> tuple[dict | None, str | None]:
    with _connection() as connection:
        row = connection.execute("SELECT * FROM students WHERE email = ? COLLATE NOCASE", (email,)).fetchone()
    if row is None:
        return None, None
    student = _student_dict(row)
    return student, row["password_hash"]


def update_student(student_id: str, fields: dict) -> dict | None:
    column_map = {
        "name": "name", "email": "email", "college": "college", "branch": "branch",
        "academic_year": "academic_year", "semester": "semester", "gpa": "gpa",
        "career_goal": "career_goal", "skills": "skills_json", "interests": "interests_json",
        "preferred_opportunity_types": "opportunity_types_json", "open_to_remote": "open_to_remote",
        "preferred_location": "preferred_location",
    }
    assignments = []
    values = []
    for key, value in fields.items():
        column = column_map.get(key)
        if column is None:
            continue
        assignments.append(f"{column} = ?")
        if key in {"skills", "interests", "preferred_opportunity_types"}:
            value = json.dumps(value or [])
        elif key == "open_to_remote":
            value = int(bool(value))
        values.append(value)
    if not assignments:
        return get_student(student_id)
    assignments.append("updated_at = ?")
    values.extend([_now(), student_id])
    with _connection() as connection:
        connection.execute(f"UPDATE students SET {', '.join(assignments)} WHERE student_id = ?", values)
        row = connection.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    return _student_dict(row)


def create_session(token_hash: str, student_id: str, expires_at: str) -> None:
    with _connection() as connection:
        connection.execute(
            "INSERT INTO sessions (token_hash, student_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token_hash, student_id, expires_at, _now()),
        )


def get_session_student(token_hash: str) -> dict | None:
    with _connection() as connection:
        row = connection.execute(
            """SELECT students.* FROM sessions
               JOIN students USING(student_id)
               WHERE sessions.token_hash = ? AND sessions.expires_at > ?""",
            (token_hash, _now()),
        ).fetchone()
        if row is None:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    return _student_dict(row)


def delete_session(token_hash: str) -> None:
    with _connection() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


def get_preferences(student_id: str) -> dict:
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM student_preferences WHERE student_id = ?", (student_id,)
        ).fetchone()
        student = connection.execute(
            "SELECT career_goal, interests_json, opportunity_types_json, preferred_location, open_to_remote FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()
    if student is None:
        raise KeyError(student_id)
    return {
        "student_id": student_id,
        "career_goal": row["career_goal"] if row else student["career_goal"],
        "interests": _decode_list(student["interests_json"]),
        "skill_level": row["skill_level"] if row else None,
        "preferred_opportunity_type": row["preferred_opportunity_type"] if row else (
            _decode_list(student["opportunity_types_json"])[0].lower()
            if _decode_list(student["opportunity_types_json"]) else None
        ),
        "work_mode": row["work_mode"] if row else ("remote" if student["open_to_remote"] else "onsite"),
        "location": row["location"] if row else student["preferred_location"],
        "learning_style": row["learning_style"] if row else None,
    }


def save_preferences(student_id: str, preferences: dict) -> dict:
    timestamp = _now()
    fields = {key: value for key, value in preferences.items() if key in {
        "skill_level", "preferred_opportunity_type", "work_mode", "location", "learning_style",
    }}
    with _connection() as connection:
        if connection.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,)).fetchone() is None:
            raise KeyError(student_id)
        columns = ["student_id", *fields.keys(), "updated_at"]
        values = [student_id, *fields.values(), timestamp]
        updates = ", ".join(f"{key}=excluded.{key}" for key in fields)
        if updates:
            updates += ", "
        updates += "updated_at=excluded.updated_at"
        connection.execute(
            f"INSERT INTO student_preferences ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) "
            f"ON CONFLICT(student_id) DO UPDATE SET {updates}",
            values,
        )
        profile_updates = []
        profile_values = []
        if "career_goal" in preferences:
            profile_updates.append("career_goal = ?")
            profile_values.append(preferences["career_goal"])
        if "interests" in preferences:
            profile_updates.append("interests_json = ?")
            profile_values.append(json.dumps(preferences["interests"] or []))
        if "preferred_opportunity_type" in preferences:
            profile_updates.append("opportunity_types_json = ?")
            profile_values.append(json.dumps([preferences["preferred_opportunity_type"]]))
        if profile_updates:
            profile_updates.append("updated_at = ?")
            profile_values.extend([timestamp, student_id])
            connection.execute(
                f"UPDATE students SET {', '.join(profile_updates)} WHERE student_id = ?",
                profile_values,
            )
    return get_preferences(student_id)


def _saved_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["opportunity_id"], "opportunity_id": row["opportunity_id"],
        "type": row["item_type"], "title": row["title"],
        "organization": row["organization"], "description": row["description"],
        "skills": _decode_list(row["skills_json"]), "location": row["location"],
        "deadline": row["deadline"], "url": row["url"], "date": row["saved_at"],
    }


def save_opportunity(student_id: str, opportunity: dict) -> dict:
    timestamp = _now()
    with _connection() as connection:
        connection.execute(
            """INSERT INTO saved_opportunities (
                student_id, opportunity_id, item_type, title, organization,
                description, skills_json, location, deadline, url, saved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, opportunity_id) DO UPDATE SET
                item_type=excluded.item_type, title=excluded.title,
                organization=excluded.organization, description=excluded.description,
                skills_json=excluded.skills_json, location=excluded.location,
                deadline=excluded.deadline, url=excluded.url""",
            (
                student_id, opportunity["opportunity_id"], opportunity["item_type"],
                opportunity.get("title") or "Saved opportunity",
                opportunity.get("organization") or "", opportunity.get("description") or "",
                json.dumps(opportunity.get("skills") or []), opportunity.get("location"),
                opportunity.get("deadline"), opportunity.get("url"), timestamp,
            ),
        )
        row = connection.execute(
            "SELECT * FROM saved_opportunities WHERE student_id = ? AND opportunity_id = ?",
            (student_id, opportunity["opportunity_id"]),
        ).fetchone()
    return _saved_dict(row)


def list_saved_opportunities(student_id: str) -> list[dict]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT * FROM saved_opportunities WHERE student_id = ? ORDER BY saved_at DESC",
            (student_id,),
        ).fetchall()
    return [_saved_dict(row) for row in rows]


def delete_saved_opportunity(student_id: str, opportunity_id: str) -> bool:
    with _connection() as connection:
        result = connection.execute(
            "DELETE FROM saved_opportunities WHERE student_id = ? AND opportunity_id = ?",
            (student_id, opportunity_id),
        )
    return result.rowcount > 0


def _opportunity_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["opportunity_id"], "opportunity_id": row["opportunity_id"],
        "category": row["category"], "title": row["title"],
        "organization": row["organization"], "description": row["description"],
        "skills": _decode_list(row["skills_json"]), "location": row["location"],
        "deadline": row["deadline"], "url": row["url"], "status": row["status"],
    }


def list_opportunities(category: str | None = None, search: str | None = None) -> list[dict]:
    query = "SELECT * FROM opportunities WHERE status = 'active'"
    parameters: list[str] = []
    if category:
        query += " AND category = ?"
        parameters.append(category)
    if search:
        query += " AND (title LIKE ? OR organization LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        parameters.extend([term, term, term])
    query += " ORDER BY created_at DESC"
    with _connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [_opportunity_dict(row) for row in rows]


def create_opportunity(owner_id: str, opportunity_id: str, data: dict) -> dict:
    timestamp = _now()
    with _connection() as connection:
        connection.execute(
            """INSERT INTO opportunities (
                opportunity_id, owner_student_id, category, title, organization,
                description, skills_json, location, deadline, url, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                opportunity_id, owner_id, data["category"], data["title"], data["organization"],
                data.get("description", ""), json.dumps(data.get("skills", [])),
                data.get("location"), data.get("deadline"), data.get("url"),
                data.get("status", "active"), timestamp, timestamp,
            ),
        )
    return {
        "id": opportunity_id,
        "opportunity_id": opportunity_id,
        **data,
    }


def update_opportunity(owner_id: str, opportunity_id: str, data: dict) -> dict | None:
    column_map = {"category": "category", "title": "title", "organization": "organization",
                  "description": "description", "skills": "skills_json", "location": "location",
                  "deadline": "deadline", "url": "url", "status": "status"}
    assignments = []
    values = []
    for key, value in data.items():
        column = column_map.get(key)
        if column is None:
            continue
        assignments.append(f"{column} = ?")
        values.append(json.dumps(value or []) if key == "skills" else value)
    if not assignments:
        return None
    assignments.append("updated_at = ?")
    values.extend([_now(), opportunity_id, owner_id])
    with _connection() as connection:
        result = connection.execute(
            f"UPDATE opportunities SET {', '.join(assignments)} WHERE opportunity_id = ? AND owner_student_id = ?",
            values,
        )
        row = connection.execute(
            "SELECT * FROM opportunities WHERE opportunity_id = ? AND owner_student_id = ?",
            (opportunity_id, owner_id),
        ).fetchone()
    if result.rowcount == 0:
        return None
    return _opportunity_dict(row) if row else None


def delete_opportunity(owner_id: str, opportunity_id: str) -> bool:
    with _connection() as connection:
        result = connection.execute(
            "DELETE FROM opportunities WHERE opportunity_id = ? AND owner_student_id = ?",
            (opportunity_id, owner_id),
        )
    return result.rowcount > 0


def get_roadmap_progress(student_id: str, career_goal: str) -> list[dict]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT step_number, skill, completed FROM roadmap_progress WHERE student_id = ? AND career_goal = ? ORDER BY step_number",
            (student_id, career_goal),
        ).fetchall()
    return [dict(row) | {"completed": bool(row["completed"])} for row in rows]


def set_roadmap_step(student_id: str, career_goal: str, step_number: int, skill: str, completed: bool) -> dict:
    with _connection() as connection:
        connection.execute(
            """INSERT INTO roadmap_progress (student_id, career_goal, step_number, skill, completed, updated_at)
            VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(student_id, career_goal, step_number) DO UPDATE SET
            skill=excluded.skill, completed=excluded.completed, updated_at=excluded.updated_at""",
            (student_id, career_goal, step_number, skill, int(completed), _now()),
        )
    return {"student_id": student_id, "career_goal": career_goal, "step_number": step_number,
            "skill": skill, "completed": completed}


def get_skill_levels(student_id: str) -> list[dict]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT skill, current_level, target_level FROM student_skills WHERE student_id = ? ORDER BY skill",
            (student_id,),
        ).fetchall()
    return [{
        "name": row["skill"], "current": row["current_level"], "target": row["target_level"],
        "gap": max(0, row["target_level"] - row["current_level"]),
    } for row in rows]


def save_skill_levels(student_id: str, levels: list[dict]) -> list[dict]:
    timestamp = _now()
    with _connection() as connection:
        for level in levels:
            connection.execute(
                """INSERT INTO student_skills (student_id, skill, current_level, target_level, updated_at)
                VALUES (?, ?, ?, ?, ?) ON CONFLICT(student_id, skill) DO UPDATE SET
                current_level=excluded.current_level, target_level=excluded.target_level, updated_at=excluded.updated_at""",
                (student_id, level["skill"], level["current_level"], level["target_level"], timestamp),
            )
    return get_skill_levels(student_id)