"""SQLite persistence for the selected intent profile.

Stores a single current-intent row. Never executes OS commands.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aetheros.intent.profiles import DEFAULT_INTENT
from aetheros.storage import apply_schema, connect

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS intent_selection (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

_UPSERT_SQL = """
INSERT INTO intent_selection (id, name, updated_at)
VALUES (1, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    updated_at = excluded.updated_at;
"""

_SELECT_SQL = "SELECT name FROM intent_selection WHERE id = 1;"


@dataclass
class IntentStorage:
    """Load and save the active intent name.

    Args:
        db_path: Path to the SQLite database file.
    """

    db_path: Path

    def __post_init__(self) -> None:
        """Ensure the parent directory and table exist."""

        self.db_path = apply_schema(self.db_path, _CREATE_SQL)

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""

        return connect(self.db_path)

    def load(self) -> str:
        """Return the persisted intent name, or the default if unset."""

        with self._connect() as conn:
            row = conn.execute(_SELECT_SQL).fetchone()
        if row is None:
            return DEFAULT_INTENT
        return str(row[0])

    def save(self, name: str) -> None:
        """Persist the selected intent name (single-row upsert)."""

        stamp = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(_UPSERT_SQL, (name, stamp))
            conn.commit()
