"""Memory verifier — promote candidates to permanent operational knowledge.

A memory becomes permanent only when:
* evidence_count >= min_evidence
* reasoning_verified is True
* historical_support is True
* confidence >= min_confidence

Failures are returned as rejected (caller archives them).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aetheros.memory.models import MemoryRecord, MemorySource


@dataclass(frozen=True, slots=True)
class MemoryCandidate:
    """Unverified candidate assembled from upstream intelligence."""

    id: str
    title: str
    description: str
    evidence_count: int
    confidence: float
    sources: tuple[MemorySource, ...]
    evidence_ids: tuple[str, ...]
    reasoning_verified: bool
    historical_support: bool


@dataclass(frozen=True, slots=True)
class VerificationOutcome:
    """Result of attempting to verify a candidate."""

    accepted: MemoryRecord | None
    rejected: MemoryRecord | None
    reasons: tuple[str, ...]


def verify_candidate(
    candidate: MemoryCandidate,
    *,
    min_evidence: int = 5,
    min_confidence: float = 70.0,
    now: datetime | None = None,
) -> VerificationOutcome:
    """Accept or reject a candidate per verification gates."""

    stamp = now or datetime.now(UTC)
    reasons: list[str] = []

    if candidate.evidence_count < min_evidence:
        reasons.append(
            f"evidence_count {candidate.evidence_count} < minimum {min_evidence}"
        )
    if not candidate.reasoning_verified:
        reasons.append("reasoning verification missing")
    if not candidate.historical_support:
        reasons.append("historical telemetry support missing")
    if candidate.confidence < min_confidence:
        reasons.append(
            f"confidence {candidate.confidence:.1f} < minimum {min_confidence:.1f}"
        )
    if not candidate.sources:
        reasons.append("no provenance sources")

    base = MemoryRecord(
        id=candidate.id,
        title=candidate.title.strip(),
        description=candidate.description.strip(),
        evidence_count=candidate.evidence_count,
        confidence=candidate.confidence,
        created_at=stamp,
        last_verified=stamp,
        sources=candidate.sources,
        status="pending",
        evidence_ids=candidate.evidence_ids,
    )

    if reasons:
        rejected = MemoryRecord(
            id=base.id,
            title=base.title,
            description=base.description,
            evidence_count=base.evidence_count,
            confidence=base.confidence,
            created_at=base.created_at,
            last_verified=base.last_verified,
            sources=base.sources,
            status="archived",
            evidence_ids=base.evidence_ids,
        )
        return VerificationOutcome(
            accepted=None,
            rejected=rejected,
            reasons=tuple(reasons),
        )

    accepted = MemoryRecord(
        id=base.id,
        title=base.title,
        description=base.description,
        evidence_count=base.evidence_count,
        confidence=base.confidence,
        created_at=base.created_at,
        last_verified=base.last_verified,
        sources=base.sources,
        status="verified",
        evidence_ids=base.evidence_ids,
    )
    return VerificationOutcome(
        accepted=accepted,
        rejected=None,
        reasons=("Passed evidence, reasoning, history, and confidence gates.",),
    )
