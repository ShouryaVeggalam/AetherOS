"""Consolidation — merge near-duplicate operational memories.

Example: \"Compile latency\" + \"Morning compile latency\" → one verified record
while retaining combined evidence ids and summed evidence counts.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from aetheros.memory.models import MemoryRecord

_TOKEN = re.compile(r"[a-z0-9]+")


def consolidate_records(
    records: Sequence[MemoryRecord],
    *,
    similarity_threshold: float = 60.0,
    now: datetime | None = None,
) -> tuple[MemoryRecord, ...]:
    """Merge duplicate-ish verified records; return consolidated set.

    Non-overlapping records pass through unchanged. Each merge produces a
    single new id and preserves the union of ``evidence_ids``.
    """

    stamp = now or datetime.now(UTC)
    remaining = [r for r in records if r.status == "verified"]
    if len(remaining) <= 1:
        return tuple(remaining)

    clusters: list[list[MemoryRecord]] = []
    for record in remaining:
        placed = False
        for cluster in clusters:
            if title_similarity(record.title, cluster[0].title) >= similarity_threshold:
                cluster.append(record)
                placed = True
                break
        if not placed:
            clusters.append([record])

    merged: list[MemoryRecord] = []
    for cluster in clusters:
        if len(cluster) == 1:
            merged.append(cluster[0])
            continue
        merged.append(_merge_cluster(cluster, stamp=stamp))
    return tuple(merged)


def title_similarity(left: str, right: str) -> float:
    """Token Jaccard similarity in [0, 100]."""

    a = set(_TOKEN.findall(left.lower()))
    b = set(_TOKEN.findall(right.lower()))
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return round(100.0 * inter / union, 2)


def _merge_cluster(
    cluster: Sequence[MemoryRecord],
    *,
    stamp: datetime,
) -> MemoryRecord:
    titles = sorted({r.title.strip() for r in cluster}, key=len)
    # Prefer the most specific (longest) title as canonical.
    title = titles[-1]
    evidence_ids = tuple(dict.fromkeys(eid for r in cluster for eid in r.evidence_ids))
    sources = tuple(dict.fromkeys(src for r in cluster for src in r.sources))
    evidence_count = sum(r.evidence_count for r in cluster)
    confidence = round(
        min(99.0, max(r.confidence for r in cluster) + min(5.0, len(cluster))),
        2,
    )
    created = min(r.created_at for r in cluster)
    descriptions = " | ".join(dict.fromkeys(r.description.strip() for r in cluster))
    return MemoryRecord(
        id=str(uuid.uuid4()),
        title=title,
        description=descriptions,
        evidence_count=evidence_count,
        confidence=confidence,
        created_at=created,
        last_verified=stamp,
        sources=sources,  # type: ignore[arg-type]
        status="verified",
        evidence_ids=evidence_ids,
    )
