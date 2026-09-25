"""Retrieval helpers — immutable query results over operational memory."""

from __future__ import annotations

from aetheros.memory.consolidation import title_similarity
from aetheros.memory.models import MemoryQuery, MemoryRecord, Pattern
from aetheros.memory.store import OperationalMemoryStore


def retrieve(
    store: OperationalMemoryStore,
    query: MemoryQuery,
    *,
    limit: int = 20,
) -> tuple[MemoryRecord, ...]:
    """Retrieve verified memories matching the query haystack."""

    needle = query.haystack()
    records = list(store.list_verified(limit=10_000))
    if not needle:
        return tuple(records[: max(0, limit)])
    scored: list[tuple[float, MemoryRecord]] = []
    for record in records:
        score = _record_score(record, needle)
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda item: (-item[0], -item[1].confidence, item[1].title))
    return tuple(record for _, record in scored[: max(0, limit)])


def related(
    store: OperationalMemoryStore,
    memory_id: str,
    *,
    limit: int = 10,
) -> tuple[MemoryRecord, ...]:
    """Return related verified memories by title/token overlap."""

    seed = store.get(memory_id)
    if seed is None:
        return ()
    others = [r for r in store.list_verified(limit=10_000) if r.id != memory_id]
    ranked = sorted(
        others,
        key=lambda r: (
            -title_similarity(seed.title, r.title),
            -r.confidence,
            r.title,
        ),
    )
    return tuple(ranked[: max(0, limit)])


def similar_patterns(
    store: OperationalMemoryStore,
    query: MemoryQuery,
    *,
    limit: int = 10,
) -> tuple[Pattern, ...]:
    """Aggregate similar recurring patterns for a query."""

    records = retrieve(store, query, limit=50)
    if not records:
        # Fall back to top verified memories as weak patterns.
        records = tuple(store.list_verified(limit=limit))
    patterns: list[Pattern] = []
    for record in records[: max(0, limit)]:
        similarity = (
            title_similarity(record.title, query.haystack())
            if query.haystack()
            else min(100.0, record.confidence)
        )
        patterns.append(
            Pattern(
                label=record.title,
                similarity=similarity,
                occurrences=max(1, record.evidence_count),
                confidence=record.confidence,
            )
        )
    return tuple(patterns)


def _record_score(record: MemoryRecord, needle: str) -> float:
    blob = f"{record.title} {record.description} {' '.join(record.sources)}".lower()
    tokens = [t for t in needle.split() if t]
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t in blob)
    if hits == 0:
        return 0.0
    return (hits / len(tokens)) * 100.0 + record.confidence * 0.1
