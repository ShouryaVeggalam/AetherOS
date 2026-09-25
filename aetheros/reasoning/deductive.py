"""Deductive reasoning — apply ontology rules to live metrics.

If metric exceeds threshold AND workload pattern matches, conclude risk.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.knowledge.ontology import CORE_ONTOLOGY
from aetheros.policy_engine.models import TelemetrySnapshot


@dataclass(frozen=True, slots=True)
class DeductiveConclusion:
    """One immutable deductive conclusion."""

    rule_id: str
    statement: str
    severity: str


def deduce(
    snapshot: TelemetrySnapshot, intent_name: str
) -> tuple[DeductiveConclusion, ...]:
    """Derive rule-based conclusions from snapshot + intent."""

    out: list[DeductiveConclusion] = []
    if snapshot.cpu_percent >= 90.0:
        out.append(
            DeductiveConclusion(
                "cpu_critical",
                f"CPU {snapshot.cpu_percent:.0f}% exceeds critical threshold 90%.",
                "critical",
            )
        )
    if snapshot.memory_percent >= 85.0:
        out.append(
            DeductiveConclusion(
                "memory_elevated",
                f"Memory {snapshot.memory_percent:.0f}% is elevated.",
                "warning",
            )
        )
    for concept in CORE_ONTOLOGY:
        if concept.domain == "intent" and intent_name.lower() in concept.label.lower():
            out.append(
                DeductiveConclusion(
                    f"intent:{concept.concept_id}",
                    f"Intent context: {concept.summary}",
                    "info",
                )
            )
    return tuple(out)
