"""Long-term operational memory models — verified system knowledge only.

Never stores user conversations, files, prompts, or personal data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

MemorySource = Literal[
    "research",
    "reasoning",
    "digital_twin",
    "telemetry_history",
    "cognition",
]
MemoryStatus = Literal["verified", "archived", "pending"]


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """One verified (or archived) operational knowledge record.

    Attributes:
        id: Stable memory identifier.
        title: Short operational fact title.
        description: Public systems description (no personal content).
        evidence_count: Supporting evidence units / sessions.
        confidence: Confidence 0–100.
        created_at: First acceptance time (UTC).
        last_verified: Most recent verification time (UTC).
        sources: Provenance channels that contributed evidence.
        status: verified | archived | pending.
        evidence_ids: Immutable evidence references retained after merges.
    """

    id: str
    title: str
    description: str
    evidence_count: int
    confidence: float
    created_at: datetime
    last_verified: datetime
    sources: tuple[MemorySource, ...] = ()
    status: MemoryStatus = "verified"
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if self.evidence_count < 1:
            raise ValueError("evidence_count must be >= 1")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class Pattern:
    """Aggregated recurring operational pattern for similarity retrieval."""

    label: str
    similarity: float
    occurrences: int
    confidence: float

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("label must be non-empty")
        if not 0.0 <= self.similarity <= 100.0:
            raise ValueError("similarity must be in [0, 100]")
        if self.occurrences < 1:
            raise ValueError("occurrences must be >= 1")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    """Retrieval query over operational memory (no personal fields)."""

    context: str = ""
    intent: str = ""
    metric: str = ""
    window: str = ""

    def haystack(self) -> str:
        """Flatten query fields for deterministic token matching."""

        return " ".join(
            part.strip().lower()
            for part in (self.context, self.intent, self.metric, self.window)
            if part and part.strip()
        )
