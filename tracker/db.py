import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "tracker.db"
VALID_TASK_STATUSES = {"todo", "doing", "done", "blocked"}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS work_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL,
                category TEXT NOT NULL,
                planned_minutes INTEGER NOT NULL,
                completed_minutes INTEGER NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                evidence_path TEXT,
                repo_link TEXT,
                verdict TEXT,
                severity TEXT DEFAULT 'Medium',
                incident_ref TEXT DEFAULT '',
                mitre_tactic TEXT DEFAULT '',
                mitre_technique TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                query_used TEXT DEFAULT '',
                recommendation TEXT DEFAULT '',
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_progress (
                work_date TEXT PRIMARY KEY,
                sc200_modules INTEGER DEFAULT 0,
                labs_completed INTEGER DEFAULT 0,
                commits_pushed INTEGER DEFAULT 0,
                assignments_done INTEGER DEFAULT 0,
                review_note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sprint_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_number INTEGER NOT NULL,
                task_date TEXT NOT NULL,
                track TEXT NOT NULL,
                task_title TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('todo','doing','done','blocked')) DEFAULT 'todo',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL,
                session_type TEXT NOT NULL,
                title TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                outcome TEXT,
                started_at TEXT,
                ended_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auto_activity_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL,
                app_name TEXT NOT NULL,
                window_title TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                source TEXT NOT NULL DEFAULT 'auto',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Backward-compatible migrations for existing local DBs.
        _ensure_column(conn, "work_blocks", "updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP")
        _ensure_column(conn, "artifacts", "objective", "TEXT DEFAULT ''")
        _ensure_column(conn, "artifacts", "query_used", "TEXT DEFAULT ''")
        _ensure_column(conn, "artifacts", "recommendation", "TEXT DEFAULT ''")
        _ensure_column(conn, "artifacts", "updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP")
        _ensure_column(conn, "artifacts", "severity", "TEXT DEFAULT 'Medium'")
        _ensure_column(conn, "artifacts", "incident_ref", "TEXT DEFAULT ''")
        _ensure_column(conn, "artifacts", "mitre_tactic", "TEXT DEFAULT ''")
        _ensure_column(conn, "artifacts", "mitre_technique", "TEXT DEFAULT ''")
        _ensure_column(conn, "focus_sessions", "started_at", "TEXT")
        _ensure_column(conn, "focus_sessions", "ended_at", "TEXT")
        _ensure_column(conn, "focus_sessions", "is_active", "INTEGER NOT NULL DEFAULT 0")


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_def: str) -> None:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if any(row[1] == column for row in cols):
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")


def upsert_daily_progress(
    work_date: str,
    sc200_modules: int,
    labs_completed: int,
    commits_pushed: int,
    assignments_done: int,
    review_note: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_progress (
                work_date, sc200_modules, labs_completed, commits_pushed, assignments_done, review_note
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(work_date) DO UPDATE SET
                sc200_modules=excluded.sc200_modules,
                labs_completed=excluded.labs_completed,
                commits_pushed=excluded.commits_pushed,
                assignments_done=excluded.assignments_done,
                review_note=excluded.review_note,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                work_date,
                sc200_modules,
                labs_completed,
                commits_pushed,
                assignments_done,
                review_note,
            ),
        )


def add_work_block(
    work_date: str,
    category: str,
    planned_minutes: int,
    completed_minutes: int,
    note: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO work_blocks (work_date, category, planned_minutes, completed_minutes, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (work_date, category, planned_minutes, completed_minutes, note),
        )


def update_work_block(
    block_id: int,
    category: str,
    planned_minutes: int,
    completed_minutes: int,
    note: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE work_blocks
            SET category = ?, planned_minutes = ?, completed_minutes = ?, note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (category, planned_minutes, completed_minutes, note, block_id),
        )


def delete_work_block(block_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM work_blocks WHERE id = ?", (block_id,))


def add_artifact(
    work_date: str,
    title: str,
    category: str,
    evidence_path: str,
    repo_link: str,
    verdict: str,
    severity: str,
    incident_ref: str,
    mitre_tactic: str,
    mitre_technique: str,
    objective: str,
    query_used: str,
    recommendation: str,
    note: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO artifacts (
                work_date, title, category, evidence_path, repo_link, verdict, severity, incident_ref, mitre_tactic, mitre_technique, objective, query_used, recommendation, note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                work_date,
                title,
                category,
                evidence_path,
                repo_link,
                verdict,
                severity,
                incident_ref,
                mitre_tactic,
                mitre_technique,
                objective,
                query_used,
                recommendation,
                note,
            ),
        )


def add_focus_session(
    work_date: str,
    session_type: str,
    title: str,
    duration_minutes: int,
    outcome: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO focus_sessions (work_date, session_type, title, duration_minutes, outcome, started_at, ended_at, is_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """,
            (work_date, session_type, title, duration_minutes, outcome),
        )


def add_auto_activity_segment(
    work_date: str,
    app_name: str,
    window_title: str,
    started_at: str,
    ended_at: str,
    duration_seconds: int,
    source: str = "auto",
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO auto_activity_segments (
                work_date, app_name, window_title, started_at, ended_at, duration_seconds, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                work_date,
                app_name,
                window_title,
                started_at,
                ended_at,
                duration_seconds,
                source,
            ),
        )


def get_auto_activity_segments(work_date: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM auto_activity_segments
            WHERE work_date = ?
            ORDER BY started_at DESC, id DESC
            """,
            (work_date,),
        ).fetchall()
    return [dict(row) for row in rows]


def start_focus_session(work_date: str, session_type: str, title: str) -> int:
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT id
            FROM focus_sessions
            WHERE work_date = ? AND is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (work_date,),
        ).fetchone()
        if existing:
            return int(existing["id"])

        cursor = conn.execute(
            """
            INSERT INTO focus_sessions (work_date, session_type, title, duration_minutes, outcome, started_at, is_active)
            VALUES (?, ?, ?, 0, '', CURRENT_TIMESTAMP, 1)
            """,
            (work_date, session_type, title),
        )
        return int(cursor.lastrowid)


def stop_focus_session(session_id: int, outcome: str) -> None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT started_at
            FROM focus_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        if not row or not row["started_at"]:
            return

        minutes_row = conn.execute(
            """
            SELECT CAST((julianday(CURRENT_TIMESTAMP) - julianday(?)) * 24 * 60 AS INTEGER) AS elapsed
            """,
            (row["started_at"],),
        ).fetchone()
        elapsed = int(minutes_row["elapsed"] or 0)
        duration = max(1, elapsed)

        conn.execute(
            """
            UPDATE focus_sessions
            SET
                duration_minutes = ?,
                outcome = CASE WHEN ? <> '' THEN ? ELSE outcome END,
                ended_at = CURRENT_TIMESTAMP,
                is_active = 0
            WHERE id = ?
            """,
            (duration, outcome, outcome, session_id),
        )


def get_active_focus_session(work_date: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM focus_sessions
            WHERE work_date = ? AND is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (work_date,),
        ).fetchone()
    return dict(row) if row else None


def update_artifact(
    artifact_id: int,
    title: str,
    category: str,
    evidence_path: str,
    repo_link: str,
    verdict: str,
    severity: str,
    incident_ref: str,
    mitre_tactic: str,
    mitre_technique: str,
    objective: str,
    query_used: str,
    recommendation: str,
    note: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE artifacts
            SET
                title = ?,
                category = ?,
                evidence_path = ?,
                repo_link = ?,
                verdict = ?,
                severity = ?,
                incident_ref = ?,
                mitre_tactic = ?,
                mitre_technique = ?,
                objective = ?,
                query_used = ?,
                recommendation = ?,
                note = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                title,
                category,
                evidence_path,
                repo_link,
                verdict,
                severity,
                incident_ref,
                mitre_tactic,
                mitre_technique,
                objective,
                query_used,
                recommendation,
                note,
                artifact_id,
            ),
        )


def delete_artifact(artifact_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))


def get_day_summary(work_date: str) -> dict:
    with get_connection() as conn:
        progress = conn.execute(
            "SELECT * FROM daily_progress WHERE work_date = ?",
            (work_date,),
        ).fetchone()
        blocks = conn.execute(
            "SELECT * FROM work_blocks WHERE work_date = ? ORDER BY id DESC",
            (work_date,),
        ).fetchall()
        artifacts = conn.execute(
            "SELECT * FROM artifacts WHERE work_date = ? ORDER BY id DESC",
            (work_date,),
        ).fetchall()
        focus_sessions = conn.execute(
            "SELECT * FROM focus_sessions WHERE work_date = ? ORDER BY COALESCE(ended_at, created_at) DESC, id DESC",
            (work_date,),
        ).fetchall()
        auto_activity_rows = conn.execute(
            "SELECT * FROM auto_activity_segments WHERE work_date = ? ORDER BY started_at DESC, id DESC",
            (work_date,),
        ).fetchall()

    return {
        "progress": dict(progress) if progress else None,
        "blocks": [dict(row) for row in blocks],
        "artifacts": [dict(row) for row in artifacts],
        "focus_sessions": [dict(row) for row in focus_sessions],
        "auto_activity": [dict(row) for row in auto_activity_rows],
    }


def get_week_data(start_date: str, end_date: str) -> dict:
    with get_connection() as conn:
        progress_rows = conn.execute(
            """
            SELECT *
            FROM daily_progress
            WHERE work_date BETWEEN ? AND ?
            ORDER BY work_date ASC
            """,
            (start_date, end_date),
        ).fetchall()
        block_rows = conn.execute(
            """
            SELECT *
            FROM work_blocks
            WHERE work_date BETWEEN ? AND ?
            ORDER BY work_date ASC
            """,
            (start_date, end_date),
        ).fetchall()
        artifact_rows = conn.execute(
            """
            SELECT *
            FROM artifacts
            WHERE work_date BETWEEN ? AND ?
            ORDER BY work_date ASC
            """,
            (start_date, end_date),
        ).fetchall()
        focus_rows = conn.execute(
            """
            SELECT *
            FROM focus_sessions
            WHERE work_date BETWEEN ? AND ?
            ORDER BY work_date ASC, created_at ASC, id ASC
            """,
            (start_date, end_date),
        ).fetchall()
        auto_rows = conn.execute(
            """
            SELECT *
            FROM auto_activity_segments
            WHERE work_date BETWEEN ? AND ?
            ORDER BY work_date ASC, started_at ASC, id ASC
            """,
            (start_date, end_date),
        ).fetchall()

    return {
        "progress": [dict(row) for row in progress_rows],
        "blocks": [dict(row) for row in block_rows],
        "artifacts": [dict(row) for row in artifact_rows],
        "focus_sessions": [dict(row) for row in focus_rows],
        "auto_activity": [dict(row) for row in auto_rows],
    }


def get_sprint_tasks(start_date: str, end_date: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM sprint_tasks
            WHERE task_date BETWEEN ? AND ?
            ORDER BY task_date ASC, priority ASC, id ASC
            """,
            (start_date, end_date),
        ).fetchall()
    return [dict(row) for row in rows]


def update_sprint_task_status(task_id: int, status: str) -> None:
    if status not in VALID_TASK_STATUSES:
        raise ValueError(f"Invalid sprint status: {status}")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sprint_tasks
            SET status = ?
            WHERE id = ?
            """,
            (status, task_id),
        )


def add_sprint_task(task_date: str, track: str, task_title: str, priority: int) -> None:
    with get_connection() as conn:
        max_day = conn.execute(
            "SELECT COALESCE(MAX(day_number), 0) FROM sprint_tasks WHERE task_date = ?",
            (task_date,),
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO sprint_tasks (day_number, task_date, track, task_title, priority, status)
            VALUES (?, ?, ?, ?, ?, 'todo')
            """,
            (max_day if max_day > 0 else 1, task_date, track, task_title, priority),
        )


def delete_sprint_task(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sprint_tasks WHERE id = ?", (task_id,))


def seed_14_day_plan(start_day: date | None = None) -> int:
    if start_day is None:
        start_day = date.today()

    plan = [
        (1, "SC-200", "Complete two SC-200 modules", 1),
        (1, "Assignment", "Submit top-priority assignment", 2),
        (1, "Artifact", "Publish one daily evidence note", 3),
        (2, "SC-200", "Complete two SC-200 modules", 1),
        (2, "Lab", "Run one Sentinel alert triage", 2),
        (2, "Artifact", "Commit investigation summary", 3),
        (3, "SC-200", "Review weak SC-200 areas", 1),
        (3, "Project", "SIEM project setup and datasource plan", 2),
        (3, "Artifact", "Ship setup notes to repo", 3),
        (4, "Project", "Build brute-force detection rule", 1),
        (4, "Lab", "Validate detection with test events", 2),
        (4, "Artifact", "Log screenshots and verdict", 3),
        (5, "Project", "Tune false positives for rule 1", 1),
        (5, "Assignment", "Close pending assignment tasks", 2),
        (5, "Artifact", "Publish tuning report", 3),
        (6, "Project", "Implement impossible travel detection", 1),
        (6, "Lab", "Run a Splunk style timeline analysis", 2),
        (6, "Artifact", "Commit timeline write-up", 3),
        (7, "Review", "Weekly review and score check", 1),
        (7, "Project", "Refactor SIEM rule naming and severity", 2),
        (7, "Artifact", "Post weekly retrospective", 3),
        (8, "Project", "Integrate Wazuh monitoring signals", 1),
        (8, "Lab", "Trigger and capture two alerts", 2),
        (8, "Artifact", "Upload alert evidence", 3),
        (9, "Project", "Build SOAR response flow draft", 1),
        (9, "Lab", "Run one incident automation simulation", 2),
        (9, "Artifact", "Commit SOAR runbook", 3),
        (10, "Project", "SOC simulation scenario definition", 1),
        (10, "Lab", "Execute multi-alert triage", 2),
        (10, "Artifact", "Publish incident timeline", 3),
        (11, "Project", "Add MITRE mapping to detections", 1),
        (11, "Assignment", "Finish any remaining coursework", 2),
        (11, "Artifact", "Commit ATT&CK mapping update", 3),
        (12, "Project", "Polish SIEM dashboard metrics", 1),
        (12, "Lab", "Validate dashboard against sample data", 2),
        (12, "Artifact", "Post dashboard review", 3),
        (13, "Project", "Capstone dry-run end to end", 1),
        (13, "Lab", "Run final SOC simulation", 2),
        (13, "Artifact", "Commit capstone evidence", 3),
        (14, "Review", "Final sprint review and gap list", 1),
        (14, "Project", "Prepare interview talking points", 2),
        (14, "Artifact", "Publish sprint closure report", 3),
    ]

    inserted = 0
    with get_connection() as conn:
        for day_number, track, task_title, priority in plan:
            task_date = date.fromordinal(start_day.toordinal() + day_number - 1).isoformat()
            exists = conn.execute(
                """
                SELECT 1 FROM sprint_tasks
                WHERE task_date = ? AND task_title = ?
                """,
                (task_date, task_title),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                """
                INSERT INTO sprint_tasks (day_number, task_date, track, task_title, priority, status)
                VALUES (?, ?, ?, ?, ?, 'todo')
                """,
                (day_number, task_date, track, task_title, priority),
            )
            inserted += 1
    return inserted


def seed_today_if_missing() -> None:
    today = date.today().isoformat()
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM daily_progress WHERE work_date = ?",
            (today,),
        ).fetchone()
        if not exists:
            conn.execute(
                """
                INSERT INTO daily_progress (work_date, sc200_modules, labs_completed, commits_pushed, assignments_done, review_note)
                VALUES (?, 0, 0, 0, 0, '')
                """,
                (today,),
            )
