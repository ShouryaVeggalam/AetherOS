"""Evidence layer — every Global Knowledge Graph edge must cite evidence.

Evidence records are immutable and reference snapshot / memory / research
artifacts. Unsupported edges are never admitted by the builder.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

EvidenceKind = Literal[
    "federation_snapshot",
    "resource_graph",
    "cluster_topology",
    "operational_memory",
    "research_discovery",
    "digital_twin",
    "infra_twin",
    "consensus",
]


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """One immutable evidence citation backing a relationship."""

    id: str
    kind: EvidenceKind
    summary: str
    source_ref: str
    created_at: datetime
    confidence: float = 100.0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        if not self.source_ref.strip():
            raise ValueError("source_ref must be non-empty")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "id": self.id,
            "kind": self.kind,
            "summary": self.summary,
            "source_ref": self.source_ref,
            "created_at": self.created_at.isoformat(),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceRecord:
        """Parse an EvidenceRecord from a mapping."""

        return cls(
            id=str(data.get("id") or "").strip(),
            kind=str(data.get("kind") or "federation_snapshot").strip(),  # type: ignore[arg-type]
            summary=str(data.get("summary") or "").strip(),
            source_ref=str(data.get("source_ref") or "").strip(),
            created_at=datetime.fromisoformat(str(data.get("created_at") or "")),
            confidence=float(
                data.get("confidence") if data.get("confidence") is not None else 100.0
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceIndex:
    """Immutable evidence catalog referenced by graph edges."""

    records: tuple[EvidenceRecord, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        """Look up one evidence record."""

        for record in self.records:
            if record.id == evidence_id:
                return record
        return None

    def for_edge(self, evidence_ids: tuple[str, ...]) -> tuple[EvidenceRecord, ...]:
        """Resolve evidence ids to records (skips missing)."""

        out: list[EvidenceRecord] = []
        for eid in evidence_ids:
            hit = self.get(eid)
            if hit is not None:
                out.append(hit)
        return tuple(out)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {"records": [r.to_dict() for r in self.records]}
