"""Theorem store — verified Genesis discoveries.

Theorems are immutable summaries of accepted research with evidence
pointers. Backed by SQLite; rejected claims are never stored here.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

_CREATE = """
CREATE TABLE IF NOT EXISTS genesis_theorems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theorem_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    simulation_count INTEGER NOT NULL,
    confidence REAL NOT NULL,
    evidence TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

_UPSERT = """
INSERT INTO genesis_theorems
    (theorem_id, title, statement, simulation_count, confidence, evidence, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(theorem_id) DO UPDATE SET
    title=excluded.title,
    statement=excluded.statement,
    simulation_count=excluded.simulation_count,
    confidence=excluded.confidence,
    evidence=excluded.evidence;
"""


@dataclass(frozen=True, slots=True)
class Theorem:
    """One immutable verified discovery."""

    theorem_id: str
    title: str
    statement: str
    simulation_count: int
    confidence: float
    evidence: tuple[str, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate theorem strength."""

        if self.simulation_count < 1:
            raise ValueError("theorem requires simulations")
        if not 0.7 <= self.confidence <= 1.0:
            raise ValueError("theorem confidence must be in [0.7, 1]")


SEED_THEOREMS: tuple[Theorem, ...] = (
    Theorem(
        theorem_id="thm.compile.cache",
        title="Compile Latency Optimization",
        statement=(
            "Increasing cache allocation reduces compile latency for "
            "interactive coding workloads under simulated cluster load."
        ),
        simulation_count=2814,
        confidence=0.94,
        evidence=(
            "2,814 simulations",
            "94% confidence",
            "Largest evidence set in Genesis seed catalog",
        ),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    ),
)


@dataclass
class TheoremStore:
    """SQLite store for verified Genesis theorems."""

    db_path: Path = field(default_factory=lambda: Path("data/genesis_theorems.db"))

    def __post_init__(self) -> None:
        """Create schema and seed baseline theorems."""

        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.execute(_CREATE)
            conn.commit()
        if not self.list_theorems():
            for theorem in SEED_THEOREMS:
                self.store(theorem)

    def store(self, theorem: Theorem) -> None:
        """Persist one verified theorem."""

        with self._connection() as conn:
            conn.execute(
                _UPSERT,
                (
                    theorem.theorem_id,
                    theorem.title,
                    theorem.statement,
                    theorem.simulation_count,
                    theorem.confidence,
                    "\n".join(theorem.evidence),
                    theorem.created_at.isoformat(),
                ),
            )
            conn.commit()

    def list_theorems(self) -> tuple[Theorem, ...]:
        """Return all theorems, highest confidence first."""

        with self._connection() as conn:
            rows = conn.execute(
                "SELECT theorem_id, title, statement, simulation_count, "
                "confidence, evidence, created_at FROM genesis_theorems "
                "ORDER BY confidence DESC, simulation_count DESC"
            ).fetchall()
        return tuple(_row_to_theorem(row) for row in rows)

    def largest(self) -> Theorem | None:
        """Theorem with the largest simulation evidence set."""

        items = self.list_theorems()
        if not items:
            return None
        return max(items, key=lambda t: t.simulation_count)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection that always closes."""

        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()


def _row_to_theorem(row: tuple) -> Theorem:
    """Map a SQL row to Theorem."""

    stamp = datetime.fromisoformat(str(row[6]))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    evidence = tuple(line for line in str(row[5]).split("\n") if line.strip())
    return Theorem(
        theorem_id=str(row[0]),
        title=str(row[1]),
        statement=str(row[2]),
        simulation_count=int(row[3]),
        confidence=float(row[4]),
        evidence=evidence,
        created_at=stamp,
    )
