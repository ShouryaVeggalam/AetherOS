"""Genesis knowledge base — verified operational knowledge only.

Persists immutable KnowledgeRecords in SQLite. Rejects unsupported
claims at the write boundary. Never stores private user content.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

_CREATE = """
CREATE TABLE IF NOT EXISTS genesis_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id TEXT NOT NULL UNIQUE,
    statement TEXT NOT NULL,
    evidence TEXT NOT NULL,
    simulation_count INTEGER NOT NULL,
    confidence REAL NOT NULL,
    clusters_verified INTEGER NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    tags TEXT NOT NULL
);
"""

_UPSERT = """
INSERT INTO genesis_knowledge
    (knowledge_id, statement, evidence, simulation_count, confidence,
     clusters_verified, source, created_at, tags)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(knowledge_id) DO UPDATE SET
    statement=excluded.statement,
    evidence=excluded.evidence,
    simulation_count=excluded.simulation_count,
    confidence=excluded.confidence,
    clusters_verified=excluded.clusters_verified,
    source=excluded.source,
    tags=excluded.tags;
"""


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    """One immutable verified operational knowledge claim.

    Attributes:
        knowledge_id: Stable unique key.
        statement: Public systems claim.
        evidence: Supporting evidence lines.
        simulation_count: Simulations that support the claim.
        confidence: Belief in [0, 1].
        clusters_verified: Distinct clusters where verified.
        source: Provenance (seed, verified_hypothesis).
        created_at: UTC timestamp.
        tags: Searchable public tags.
    """

    knowledge_id: str
    statement: str
    evidence: tuple[str, ...]
    simulation_count: int
    confidence: float
    clusters_verified: int
    source: str
    created_at: datetime
    tags: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject unsupported or malformed claims."""

        if not self.statement.strip():
            raise ValueError("statement must be non-empty")
        if self.simulation_count < 1:
            raise ValueError("unsupported claim: simulation_count must be >= 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if self.confidence < 0.7:
            raise ValueError("unsupported claim: confidence must be >= 0.7 to store")
        if self.clusters_verified < 1:
            raise ValueError("unsupported claim: clusters_verified must be >= 1")
        if not self.evidence:
            raise ValueError("unsupported claim: evidence required")


SEED_KNOWLEDGE: tuple[KnowledgeRecord, ...] = (
    KnowledgeRecord(
        knowledge_id="kb.coding.cpu_before_memory",
        statement=(
            "Interactive coding workloads consistently increase CPU latency "
            "before memory pressure."
        ),
        evidence=(
            "2,814 simulations",
            "91% confidence",
            "Verified across 18 clusters",
        ),
        simulation_count=2814,
        confidence=0.91,
        clusters_verified=18,
        source="seed",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        tags=("coding", "cpu", "latency", "memory"),
    ),
    KnowledgeRecord(
        knowledge_id="kb.compile.cache_helps",
        statement=(
            "Increasing cache allocation reduces compile latency under "
            "interactive coding intent."
        ),
        evidence=(
            "2,814 simulations",
            "94% confidence",
            "Compile Latency Optimization evidence set",
        ),
        simulation_count=2814,
        confidence=0.94,
        clusters_verified=18,
        source="seed",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        tags=("compile", "cache", "latency"),
    ),
    KnowledgeRecord(
        knowledge_id="kb.rendering.disk_sustained",
        statement=(
            "Video rendering creates sustained disk activity that can degrade "
            "interactive I/O fairness."
        ),
        evidence=("1,200 simulations", "88% confidence", "Verified across 12 clusters"),
        simulation_count=1200,
        confidence=0.88,
        clusters_verified=12,
        source="seed",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        tags=("rendering", "disk", "fairness"),
    ),
)


@dataclass
class KnowledgeBase:
    """SQLite-backed store for verified Genesis knowledge."""

    db_path: Path = field(default_factory=lambda: Path("data/genesis_knowledge.db"))

    def __post_init__(self) -> None:
        """Create schema and seed verified baseline knowledge."""

        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.execute(_CREATE)
            conn.commit()
        if not self.list_knowledge():
            for record in SEED_KNOWLEDGE:
                self.store(record)

    def store(self, record: KnowledgeRecord) -> None:
        """Persist one verified knowledge record (validation in ``__post_init__``)."""

        with self._connection() as conn:
            conn.execute(
                _UPSERT,
                (
                    record.knowledge_id,
                    record.statement,
                    "\n".join(record.evidence),
                    record.simulation_count,
                    record.confidence,
                    record.clusters_verified,
                    record.source,
                    record.created_at.isoformat(),
                    ",".join(record.tags),
                ),
            )
            conn.commit()

    def list_knowledge(self) -> tuple[KnowledgeRecord, ...]:
        """Return all verified knowledge, highest confidence first."""

        with self._connection() as conn:
            rows = conn.execute(
                "SELECT knowledge_id, statement, evidence, simulation_count, "
                "confidence, clusters_verified, source, created_at, tags "
                "FROM genesis_knowledge ORDER BY confidence DESC, knowledge_id"
            ).fetchall()
        return tuple(_row_to_record(row) for row in rows)

    def largest_evidence_set(self) -> KnowledgeRecord | None:
        """Return the knowledge record with the most simulations."""

        items = self.list_knowledge()
        if not items:
            return None
        return max(items, key=lambda r: r.simulation_count)

    def count(self) -> int:
        """Number of verified knowledge records in this store."""

        return len(self.list_knowledge())

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection that always closes."""

        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()


def _row_to_record(row: tuple) -> KnowledgeRecord:
    """Map a SQL row to KnowledgeRecord."""

    stamp = datetime.fromisoformat(str(row[7]))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    evidence = tuple(line for line in str(row[2]).split("\n") if line.strip())
    tags = tuple(t for t in str(row[8]).split(",") if t)
    return KnowledgeRecord(
        knowledge_id=str(row[0]),
        statement=str(row[1]),
        evidence=evidence,
        simulation_count=int(row[3]),
        confidence=float(row[4]),
        clusters_verified=int(row[5]),
        source=str(row[6]),
        created_at=stamp,
        tags=tags,
    )
