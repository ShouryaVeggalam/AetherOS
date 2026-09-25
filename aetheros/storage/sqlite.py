"""Shared SQLite helpers — path normalize, schema bootstrap, connections.

Minimal data-access utilities for AetherOS stores. No ORM, no migrations
framework — just one place for connect + CREATE TABLE IF NOT EXISTS.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def ensure_db_path(path: Path | str) -> Path:
    """Normalize a DB path and create parent directories."""

    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def connect(path: Path | str) -> sqlite3.Connection:
    """Open a SQLite connection after ensuring the parent directory exists."""

    return sqlite3.connect(ensure_db_path(path))


@contextmanager
def closing_connection(path: Path | str) -> Iterator[sqlite3.Connection]:
    """Yield a connection that always closes on exit."""

    conn = connect(path)
    try:
        yield conn
    finally:
        conn.close()


def apply_schema(path: Path | str, *statements: str) -> Path:
    """Ensure path exists and execute one or more DDL statements.

    Returns:
        Normalized database path.
    """

    db_path = ensure_db_path(path)
    with closing_connection(db_path) as conn:
        for statement in statements:
            conn.execute(statement)
        conn.commit()
    return db_path
