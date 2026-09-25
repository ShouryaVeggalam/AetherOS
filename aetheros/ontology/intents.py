"""Ontology intents — operator intent entities for Genesis research."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IntentConcept:
    """One intent entity in the Genesis ontology."""

    entity_id: str
    label: str
    summary: str
    prefers: tuple[str, ...]


INTENT_ENTITIES: tuple[IntentConcept, ...] = (
    IntentConcept(
        "intent.latency",
        "Latency",
        "Minimize interactive response time.",
        ("IMPROVES:resource.cache", "DEGRADES:resource.cpu.contention"),
    ),
    IntentConcept(
        "intent.efficiency",
        "Efficiency",
        "Prefer lower power and quieter background work.",
        ("IMPROVES:resource.cpu.efficiency",),
    ),
    IntentConcept(
        "intent.throughput",
        "Throughput",
        "Maximize sustained work completion rate.",
        ("IMPROVES:resource.gpu", "IMPROVES:resource.cpu"),
    ),
    IntentConcept(
        "intent.balanced",
        "Balanced",
        "Trade modestly across latency, efficiency, and throughput.",
        (),
    ),
)
