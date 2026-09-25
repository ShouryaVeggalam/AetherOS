"""MemoryEngine — public interface for long-term operational memory.

retrieve / related / similar_patterns + ingest/consolidate helpers.
Read-only toward upstream engines; writes only verified operational facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aetheros.memory.consolidation import consolidate_records
from aetheros.memory.models import MemoryQuery, MemoryRecord, Pattern
from aetheros.memory.retrieval import related, retrieve, similar_patterns
from aetheros.memory.store import OperationalMemoryStore
from aetheros.memory.verifier import MemoryCandidate, verify_candidate


@dataclass
class MemoryEngine:
    """Long-term operational memory orchestrator."""

    store: OperationalMemoryStore = field(default_factory=OperationalMemoryStore)
    min_evidence: int = 5
    min_confidence: float = 70.0

    def retrieve(
        self,
        query: MemoryQuery,
        *,
        limit: int = 20,
    ) -> tuple[MemoryRecord, ...]:
        """Retrieve immutable verified memories for a query."""

        return retrieve(self.store, query, limit=limit)

    def related(
        self,
        memory_id: str,
        *,
        limit: int = 10,
    ) -> tuple[MemoryRecord, ...]:
        """Return related verified memories."""

        return related(self.store, memory_id, limit=limit)

    def similar_patterns(
        self,
        query: MemoryQuery,
        *,
        limit: int = 10,
    ) -> tuple[Pattern, ...]:
        """Return similar recurring operational patterns."""

        return similar_patterns(self.store, query, limit=limit)

    def ingest(
        self,
        candidate: MemoryCandidate,
        *,
        now: datetime | None = None,
    ) -> MemoryRecord | None:
        """Verify a candidate; persist if accepted, archive if rejected."""

        outcome = verify_candidate(
            candidate,
            min_evidence=self.min_evidence,
            min_confidence=self.min_confidence,
            now=now,
        )
        if outcome.accepted is not None:
            return self.store.append_verified(outcome.accepted)
        if outcome.rejected is not None:
            self.store.archive(outcome.rejected, reason="verification_failed")
        return None

    def consolidate(self, *, now: datetime | None = None) -> tuple[MemoryRecord, ...]:
        """Merge near-duplicate verified memories in the store."""

        stamp = now or datetime.now(UTC)
        current = tuple(self.store.list_verified(limit=10_000))
        merged = consolidate_records(current, now=stamp)
        if len(merged) == len(current) and all(
            m.id in {c.id for c in current} for m in merged
        ):
            return current
        # Rebuild verified set from consolidation output.
        # Archive anything no longer present.
        keep_ids = {m.id for m in merged}
        for record in current:
            if record.id not in keep_ids:
                self.store.archive(record, reason="consolidated")
        for record in merged:
            if self.store.get(record.id) is None:
                self.store.append_verified(record)
        return tuple(self.store.list_verified(limit=10_000))

    def verified_count(self) -> int:
        """Number of verified operational memories."""

        return len(self.store)

    def seed_defaults(self, *, now: datetime | None = None) -> tuple[MemoryRecord, ...]:
        """Load curated seed memories that already meet verification gates."""

        stamp = now or datetime.now(UTC)
        seeds = (
            MemoryCandidate(
                id="mem_morning_coding_cpu",
                title="Morning Coding Session",
                description=(
                    "Morning coding sessions typically increase CPU before "
                    "memory pressure."
                ),
                evidence_count=24,
                confidence=93.0,
                sources=("telemetry_history", "reasoning", "research"),
                evidence_ids=("hist:cpu", "reason:path", "research:obs"),
                reasoning_verified=True,
                historical_support=True,
            ),
            MemoryCandidate(
                id="mem_compile_disk",
                title="Compile Disk Contention",
                description=("Compile workloads frequently create disk contention."),
                evidence_count=18,
                confidence=88.0,
                sources=("telemetry_history", "digital_twin", "reasoning"),
                evidence_ids=("hist:disk", "twin:io", "reason:disk"),
                reasoning_verified=True,
                historical_support=True,
            ),
        )
        stored: list[MemoryRecord] = []
        for candidate in seeds:
            if self.store.get(candidate.id) is not None:
                existing = self.store.get(candidate.id)
                if existing is not None:
                    stored.append(existing)
                continue
            record = self.ingest(candidate, now=stamp)
            if record is not None:
                stored.append(record)
        return tuple(stored)
