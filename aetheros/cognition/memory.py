"""Cognitive memory — long-term structured operational knowledge.

Stores public systems patterns only (never private user content).
Persisted in SQLite under data/cognition_memory.db by default.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.storage import apply_schema, closing_connection

_CREATE = """
CREATE TABLE IF NOT EXISTS cognitive_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_key TEXT NOT NULL UNIQUE,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    confidence REAL NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    notes TEXT NOT NULL
);
"""

_UPSERT = """
INSERT INTO cognitive_facts
    (fact_key, subject, predicate, object, confidence, source, created_at, notes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(fact_key) DO UPDATE SET
    confidence=excluded.confidence,
    notes=excluded.notes,
    source=excluded.source;
"""


@dataclass(frozen=True, slots=True)
class CognitiveFact:
    """One immutable operational knowledge fact.

    Attributes:
        fact_key: Stable unique key.
        subject: Entity (process/workload/resource).
        predicate: Relation verb (increases, precedes, sustains).
        object: Related entity or metric.
        confidence: 0.0–1.0 belief strength.
        source: Provenance (seed, verified_hypothesis, history).
        created_at: UTC timestamp.
        notes: Public systems note (no private content).
    """

    fact_key: str
    subject: str
    predicate: str
    object: str
    confidence: float
    source: str
    created_at: datetime
    notes: str

    def __post_init__(self) -> None:
        """Validate confidence."""

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


SEED_FACTS: tuple[CognitiveFact, ...] = (
    CognitiveFact(
        "coding_cpu_after_cursor",
        "Cursor",
        "precedes_increase",
        "cpu",
        0.8,
        "seed",
        datetime(2026, 1, 1, tzinfo=UTC),
        "Coding usually increases CPU after Cursor launches.",
    ),
    CognitiveFact(
        "rendering_sustained_disk",
        "Video Rendering",
        "sustains",
        "disk",
        0.85,
        "seed",
        datetime(2026, 1, 1, tzinfo=UTC),
        "Video rendering creates sustained disk activity.",
    ),
    CognitiveFact(
        "gaming_foreground_util",
        "Gaming",
        "increases",
        "foreground_utilization",
        0.8,
        "seed",
        datetime(2026, 1, 1, tzinfo=UTC),
        "Gaming increases foreground utilization.",
    ),
    CognitiveFact(
        "indexing_background_cpu",
        "Background indexing",
        "causes",
        "cpu",
        0.7,
        "seed",
        datetime(2026, 1, 1, tzinfo=UTC),
        "Background indexing can sustain elevated CPU.",
    ),
)


@dataclass
class CognitiveMemory:
    """SQLite-backed cognitive memory store."""

    db_path: Path = field(default_factory=lambda: Path("data/cognition_memory.db"))

    def __post_init__(self) -> None:
        """Create table and seed baseline operational facts."""

        self.db_path = apply_schema(self.db_path, _CREATE)
        if not self.list_facts():
            for fact in SEED_FACTS:
                self.remember(fact)

    def remember(self, fact: CognitiveFact) -> None:
        """Upsert one structured fact (public systems knowledge only)."""

        with self._connection() as conn:
            conn.execute(
                _UPSERT,
                (
                    fact.fact_key,
                    fact.subject,
                    fact.predicate,
                    fact.object,
                    fact.confidence,
                    fact.source,
                    fact.created_at.isoformat(),
                    fact.notes,
                ),
            )
            conn.commit()

    def list_facts(self) -> tuple[CognitiveFact, ...]:
        """Return all stored facts."""

        with self._connection() as conn:
            rows = conn.execute(
                "SELECT fact_key, subject, predicate, object, confidence, "
                "source, created_at, notes FROM cognitive_facts "
                "ORDER BY confidence DESC, fact_key"
            ).fetchall()
        return tuple(_row_to_fact(row) for row in rows)

    def search(self, needle: str) -> tuple[CognitiveFact, ...]:
        """Case-insensitive substring search across subject/object/notes."""

        needle_l = needle.lower()
        return tuple(
            fact
            for fact in self.list_facts()
            if needle_l in fact.subject.lower()
            or needle_l in fact.object.lower()
            or needle_l in fact.notes.lower()
            or needle_l in fact.predicate.lower()
        )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection that always closes on exit."""

        with closing_connection(self.db_path) as conn:
            yield conn


def _row_to_fact(row: tuple) -> CognitiveFact:
    """Map a SQL row to CognitiveFact."""

    stamp = datetime.fromisoformat(str(row[6]))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return CognitiveFact(
        fact_key=str(row[0]),
        subject=str(row[1]),
        predicate=str(row[2]),
        object=str(row[3]),
        confidence=float(row[4]),
        source=str(row[5]),
        created_at=stamp,
        notes=str(row[7]),
    )
