"""
Saturn Engine — SQLite-backed version control for every MilkyWay action.
Stores runs, diffs, challenges, sessions, and annotations.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, List, Optional


# ─── Paths ────────────────────────────────────────────────────────────────────

def get_global_db_path() -> Path:
    home = Path.home() / ".milkyway"
    home.mkdir(parents=True, exist_ok=True)
    return home / "global.db"


def get_local_db_path() -> Optional[Path]:
    """Walk up from cwd to find a .milkyway/local.db (challenge scope)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / ".milkyway" / "local.db"
        if candidate.exists():
            return candidate
    return None


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Run:
    id: int
    timestamp: datetime
    planet: str
    action: str
    command_line: str
    parameters: dict
    exit_code: int
    output_hash: Optional[str]
    output_file: Optional[str]
    working_dir: str
    challenge_id: Optional[int]
    session_id: Optional[str]
    notes: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    @property
    def timestamp_str(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp_str,
            "planet": self.planet,
            "action": self.action,
            "command_line": self.command_line,
            "parameters": self.parameters,
            "exit_code": self.exit_code,
            "output_hash": self.output_hash,
            "output_file": self.output_file,
            "working_dir": self.working_dir,
            "challenge_id": self.challenge_id,
            "session_id": self.session_id,
            "notes": self.notes,
        }


@dataclass
class Challenge:
    id: int
    name: str
    category: str
    created: datetime
    folder_path: str
    notes: str
    tags: List[str] = field(default_factory=list)
    url: Optional[str] = None

    @property
    def path(self) -> Path:
        return Path(self.folder_path)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
            "folder_path": self.folder_path,
            "notes": self.notes,
            "tags": self.tags,
            "url": self.url,
        }


@dataclass
class Session:
    id: str
    name: str
    started: datetime
    challenge_id: Optional[int]
    ended: Optional[datetime] = None

    @property
    def duration(self) -> Optional[str]:
        if self.ended:
            delta = self.ended - self.started
            hours, rem = divmod(int(delta.total_seconds()), 3600)
            mins, secs = divmod(rem, 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return None


# ─── Schema ───────────────────────────────────────────────────────────────────

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS challenges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    UNIQUE NOT NULL,
    category    TEXT    NOT NULL DEFAULT 'misc',
    created     DATETIME DEFAULT CURRENT_TIMESTAMP,
    folder_path TEXT,
    notes       TEXT    DEFAULT '',
    tags        TEXT    DEFAULT '[]',
    url         TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id           TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL,
    started      DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended        DATETIME,
    challenge_id INTEGER REFERENCES challenges(id)
);

CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    planet          TEXT    NOT NULL,
    action          TEXT    NOT NULL,
    command_line    TEXT    NOT NULL,
    parameters_json TEXT    DEFAULT '{}',
    exit_code       INTEGER DEFAULT 0,
    output_hash     TEXT,
    output_file     TEXT,
    working_dir     TEXT,
    challenge_id    INTEGER REFERENCES challenges(id),
    session_id      TEXT    REFERENCES sessions(id),
    notes           TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS annotations (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id  INTEGER NOT NULL REFERENCES runs(id),
    author  TEXT    DEFAULT 'me',
    text    TEXT    NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id  INTEGER NOT NULL REFERENCES runs(id),
    label   TEXT    NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_runs_challenge  ON runs(challenge_id);
CREATE INDEX IF NOT EXISTS idx_runs_timestamp  ON runs(timestamp);
CREATE INDEX IF NOT EXISTS idx_runs_planet     ON runs(planet);
CREATE INDEX IF NOT EXISTS idx_runs_session    ON runs(session_id);
CREATE INDEX IF NOT EXISTS idx_runs_exit_code  ON runs(exit_code);
"""


# ─── DB Manager ───────────────────────────────────────────────────────────────

class SaturnDB:
    """Thread-safe SQLite wrapper with WAL mode for MilkyWay's version control."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_global_db_path()
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ── Runs ──────────────────────────────────────────────────────────────────

    def record_run(
        self,
        planet: str,
        action: str,
        command_line: str,
        parameters: dict,
        exit_code: int,
        output: str = "",
        working_dir: Optional[str] = None,
        challenge_id: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> int:
        output_hash = hashlib.sha256(output.encode()).hexdigest()[:16] if output else None
        output_file = self._save_output(output, planet, action) if output else None

        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO runs
                   (planet, action, command_line, parameters_json, exit_code,
                    output_hash, output_file, working_dir, challenge_id, session_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    planet, action, command_line,
                    json.dumps(parameters), exit_code,
                    output_hash, output_file,
                    working_dir or str(Path.cwd()),
                    challenge_id, session_id,
                ),
            )
            return cur.lastrowid

    def _save_output(self, output: str, planet: str, action: str) -> str:
        output_dir = Path.home() / ".milkyway" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = output_dir / f"{planet}_{action}_{ts}.txt"
        fname.write_text(output, encoding="utf-8")
        return str(fname)

    def get_runs(
        self,
        limit: int = 20,
        challenge_id: Optional[int] = None,
        session_id: Optional[str] = None,
        planet: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Run]:
        conditions = []
        params: list = []

        if challenge_id is not None:
            conditions.append("r.challenge_id = ?")
            params.append(challenge_id)
        if session_id:
            conditions.append("r.session_id = ?")
            params.append(session_id)
        if planet:
            conditions.append("r.planet = ?")
            params.append(planet)
        if search:
            conditions.append("r.command_line LIKE ?")
            params.append(f"%{search}%")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(
                f"""SELECT r.*, c.name as challenge_name
                    FROM runs r
                    LEFT JOIN challenges c ON r.challenge_id = c.id
                    {where}
                    ORDER BY r.timestamp DESC LIMIT ?""",
                params,
            ).fetchall()

        return [self._row_to_run(r) for r in rows]

    def get_run(self, run_id: int) -> Optional[Run]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE id = ?", (run_id,)
            ).fetchone()
        return self._row_to_run(row) if row else None

    def _row_to_run(self, row: sqlite3.Row) -> Run:
        ts = row["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return Run(
            id=row["id"],
            timestamp=ts,
            planet=row["planet"],
            action=row["action"],
            command_line=row["command_line"],
            parameters=json.loads(row["parameters_json"] or "{}"),
            exit_code=row["exit_code"] or 0,
            output_hash=row["output_hash"],
            output_file=row["output_file"],
            working_dir=row["working_dir"] or "",
            challenge_id=row["challenge_id"],
            session_id=row["session_id"],
            notes=row["notes"],
        )

    def get_run_output(self, run: Run) -> str:
        if run.output_file and Path(run.output_file).exists():
            return Path(run.output_file).read_text(encoding="utf-8", errors="replace")
        return ""

    def diff_runs(self, run_id1: int, run_id2: int) -> str:
        run1 = self.get_run(run_id1)
        run2 = self.get_run(run_id2)
        if not run1 or not run2:
            return "One or both runs not found."

        out1 = self.get_run_output(run1)
        out2 = self.get_run_output(run2)

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f1:
            f1.write(out1); f1_path = f1.name
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f2:
            f2.write(out2); f2_path = f2.name

        result = subprocess.run(
            ["diff", "-u", f1_path, f2_path],
            capture_output=True, text=True
        )
        os.unlink(f1_path)
        os.unlink(f2_path)
        return result.stdout or "No differences found."

    def annotate_run(self, run_id: int, text: str, author: str = "me") -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO annotations (run_id, author, text) VALUES (?,?,?)",
                (run_id, author, text),
            )

    def bookmark_run(self, run_id: int, label: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO bookmarks (run_id, label) VALUES (?,?)",
                (run_id, label),
            )

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            success = conn.execute("SELECT COUNT(*) FROM runs WHERE exit_code=0").fetchone()[0]
            by_planet = conn.execute(
                "SELECT planet, COUNT(*) as cnt FROM runs GROUP BY planet ORDER BY cnt DESC"
            ).fetchall()
            challenges = conn.execute("SELECT COUNT(*) FROM challenges").fetchone()[0]
        return {
            "total_runs": total,
            "successful_runs": success,
            "failed_runs": total - success,
            "by_planet": {r["planet"]: r["cnt"] for r in by_planet},
            "challenges": challenges,
        }

    # ── Challenges ────────────────────────────────────────────────────────────

    def create_challenge(
        self,
        name: str,
        category: str,
        folder_path: str,
        url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO challenges (name, category, folder_path, url, tags) VALUES (?,?,?,?,?)",
                (name, category, folder_path, url, json.dumps(tags or [])),
            )
            return cur.lastrowid

    def get_challenge(self, name: str) -> Optional[Challenge]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM challenges WHERE name = ?", (name,)
            ).fetchone()
        return self._row_to_challenge(row) if row else None

    def get_challenge_by_id(self, cid: int) -> Optional[Challenge]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM challenges WHERE id = ?", (cid,)
            ).fetchone()
        return self._row_to_challenge(row) if row else None

    def list_challenges(self, category: Optional[str] = None) -> List[Challenge]:
        if category:
            with self._conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM challenges WHERE category=? ORDER BY created DESC", (category,)
                ).fetchall()
        else:
            with self._conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM challenges ORDER BY created DESC"
                ).fetchall()
        return [self._row_to_challenge(r) for r in rows]

    def update_challenge_notes(self, name: str, notes: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE challenges SET notes=? WHERE name=?", (notes, name)
            )

    def delete_challenge(self, name: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM challenges WHERE name=?", (name,))
            return cur.rowcount > 0

    def _row_to_challenge(self, row: sqlite3.Row) -> Challenge:
        ts = row["created"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return Challenge(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            created=ts,
            folder_path=row["folder_path"] or "",
            notes=row["notes"] or "",
            tags=json.loads(row["tags"] or "[]"),
            url=row["url"],
        )

    # ── Sessions ──────────────────────────────────────────────────────────────

    def start_session(self, name: str, challenge_id: Optional[int] = None) -> str:
        import uuid
        sid = str(uuid.uuid4())[:8]
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, name, challenge_id) VALUES (?,?,?)",
                (sid, name, challenge_id),
            )
        return sid

    def end_session(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET ended=CURRENT_TIMESTAMP WHERE id=?",
                (session_id,),
            )

    def get_current_session(self) -> Optional[str]:
        """Read session id from env or config."""
        return os.environ.get("MILKYWAY_SESSION")

    def export_session(self, session_id: str) -> str:
        """Export session as markdown write-up."""
        with self._conn() as conn:
            session = conn.execute(
                "SELECT * FROM sessions WHERE id=?", (session_id,)
            ).fetchone()
            if not session:
                return "Session not found."
            runs = conn.execute(
                "SELECT * FROM runs WHERE session_id=? ORDER BY timestamp",
                (session_id,),
            ).fetchall()

        lines = [
            f"# CTF Session: {session['name']}",
            f"**Started**: {session['started']}",
            f"**Session ID**: `{session_id}`",
            "",
            "## Timeline",
            "",
        ]
        for i, run in enumerate(runs, 1):
            status = "✅" if (run["exit_code"] or 0) == 0 else "❌"
            lines += [
                f"### Step {i} — {run['planet'].capitalize()} `{run['action']}` {status}",
                f"**Time**: {run['timestamp']}",
                f"```bash",
                run["command_line"],
                "```",
                "",
            ]

        return "\n".join(lines)
