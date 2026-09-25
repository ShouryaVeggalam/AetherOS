"""Append-only SQLite audit log for safety decisions.

Every validation is inserted as a new row. Records are never updated
or deleted by this module.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aetheros.policy_engine.models import PolicyRecommendation
from aetheros.safety.models import SafetyResult
from aetheros.storage import apply_schema, connect

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS safety_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    title TEXT NOT NULL,
    level TEXT NOT NULL,
    approved INTEGER NOT NULL,
    reason TEXT NOT NULL,
    confidence INTEGER NOT NULL
);
"""

_INSERT_SQL = """
INSERT INTO safety_audit (
    timestamp, title, level, approved, reason, confidence
) VALUES (?, ?, ?, ?, ?, ?);
"""


@dataclass
class AuditLogger:
    """Persists every safety decision to SQLite (append-only).

    Args:
        db_path: Path to the SQLite database file.
    """

    db_path: Path

    def __post_init__(self) -> None:
        """Ensure the parent directory and table exist."""

        self.db_path = apply_schema(self.db_path, _CREATE_TABLE_SQL)

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection with row factory disabled (simple)."""

        return connect(self.db_path)

    def log(
        self,
        recommendation: PolicyRecommendation,
        result: SafetyResult,
    ) -> None:
        """Insert one validation decision. Never overwrites prior rows.

        Args:
            recommendation: The policy advice that was checked.
            result: The safety decision for that advice.
        """

        timestamp = _format_timestamp(result.timestamp)
        with self._connect() as conn:
            conn.execute(
                _INSERT_SQL,
                (
                    timestamp,
                    recommendation.title,
                    recommendation.level,
                    1 if result.approved else 0,
                    result.reason,
                    recommendation.confidence,
                ),
            )
            conn.commit()

    def count(self) -> int:
        """Return how many audit rows exist (for tests and demos)."""

        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM safety_audit;").fetchone()
        return int(row[0]) if row else 0

    def latest(self) -> dict[str, object] | None:
        """Return the most recent audit row, or None if the log is empty.

        Returns:
            A dict with keys timestamp, title, level, approved, reason,
            confidence — or None when no rows exist.
        """

        with self._connect() as conn:
            row = conn.execute("""
                SELECT timestamp, title, level, approved, reason, confidence
                FROM safety_audit
                ORDER BY id DESC
                LIMIT 1;
                """).fetchone()
        if row is None:
            return None
        return {
            "timestamp": row[0],
            "title": row[1],
            "level": row[2],
            "approved": bool(row[3]),
            "reason": row[4],
            "confidence": int(row[5]),
        }


def _format_timestamp(value: datetime) -> str:
    """Serialize a datetime to an ISO-8601 UTC string."""

    return value.isoformat()
