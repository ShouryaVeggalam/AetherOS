"""Operational memory store — persist verified records only.

In-memory append-only store with an archive for rejected / superseded
records. Never accepts speculative memories. No personal data fields.
"""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.memory.models import MemoryRecord


class OperationalMemoryStore:
    """Workspace-scoped store for verified operational memories.

    Verified records are immutable once appended. Updates create a new
    verified record and move the prior id to the archive (consolidation).
    """

    def __init__(self) -> None:
        self._verified: dict[str, MemoryRecord] = {}
        self._archived: dict[str, MemoryRecord] = {}

    def append_verified(self, record: MemoryRecord) -> MemoryRecord:
        """Persist a verified record. Rejects non-verified status."""

        if record.status != "verified":
            raise ValueError("only verified records may be appended to the store")
        if record.id in self._verified:
            raise ValueError(f"memory already exists: {record.id}")
        self._verified[record.id] = record
        return record

    def archive(
        self, record: MemoryRecord, *, reason: str = "rejected"
    ) -> MemoryRecord:
        """Move or insert a record into the archive (immutable copy)."""

        archived = MemoryRecord(
            id=record.id,
            title=record.title,
            description=f"{record.description} [{reason}]",
            evidence_count=record.evidence_count,
            confidence=record.confidence,
            created_at=record.created_at,
            last_verified=record.last_verified,
            sources=record.sources,
            status="archived",
            evidence_ids=record.evidence_ids,
        )
        self._verified.pop(record.id, None)
        self._archived[archived.id] = archived
        return archived

    def get(self, memory_id: str) -> MemoryRecord | None:
        """Fetch a verified memory by id."""

        return self._verified.get(memory_id)

    def get_archived(self, memory_id: str) -> MemoryRecord | None:
        """Fetch an archived memory by id."""

        return self._archived.get(memory_id)

    def list_verified(self, *, limit: int = 200) -> Sequence[MemoryRecord]:
        """List verified memories, highest confidence first."""

        items = sorted(
            self._verified.values(),
            key=lambda r: (-r.confidence, -r.evidence_count, r.title),
        )
        return items[: max(0, limit)]

    def list_archived(self, *, limit: int = 200) -> Sequence[MemoryRecord]:
        """List archived memories (rejected / superseded)."""

        items = sorted(
            self._archived.values(),
            key=lambda r: (-r.last_verified.timestamp(), r.title),
        )
        return items[: max(0, limit)]

    def replace_verified(
        self,
        *,
        remove_ids: Sequence[str],
        new_record: MemoryRecord,
    ) -> MemoryRecord:
        """Archive prior ids and append the consolidated verified record."""

        for mid in remove_ids:
            existing = self._verified.get(mid)
            if existing is not None:
                self.archive(existing, reason="consolidated")
        return self.append_verified(new_record)

    def __len__(self) -> int:
        return len(self._verified)
