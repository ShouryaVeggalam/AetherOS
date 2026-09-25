"""Ontology — structured operational concepts (no private user content).

Encodes systems knowledge as immutable facts operators can inspect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OntologyDomain = Literal[
    "workload",
    "resource",
    "intent",
    "process_pattern",
    "intervention",
]


@dataclass(frozen=True, slots=True)
class OntologyConcept:
    """One concept in the AetherOS systems ontology.

    Attributes:
        concept_id: Stable identifier.
        domain: Concept family.
        label: Display name.
        summary: Public, non-personal systems description.
        tags: Searchable keywords.
    """

    concept_id: str
    domain: OntologyDomain
    label: str
    summary: str
    tags: tuple[str, ...]


CORE_ONTOLOGY: tuple[OntologyConcept, ...] = (
    OntologyConcept(
        "workload.coding",
        "workload",
        "Coding",
        "Interactive development often raises short CPU bursts after editor activity.",
        ("cursor", "ide", "compile"),
    ),
    OntologyConcept(
        "workload.rendering",
        "workload",
        "Video Rendering",
        "Rendering creates sustained CPU and disk activity for long windows.",
        ("export", "encode", "disk"),
    ),
    OntologyConcept(
        "workload.gaming",
        "workload",
        "Gaming",
        "Gaming elevates foreground GPU/CPU utilization with latency sensitivity.",
        ("foreground", "gpu", "latency"),
    ),
    OntologyConcept(
        "process.cursor",
        "process_pattern",
        "Cursor / IDE",
        "Editor launch and indexing commonly precede coding-related CPU rises.",
        ("cursor", "indexing", "compile"),
    ),
    OntologyConcept(
        "process.browser",
        "process_pattern",
        "Browser Rendering",
        "Browser compositor threads can spike CPU during heavy tab rendering.",
        ("chrome", "safari", "renderer"),
    ),
    OntologyConcept(
        "intent.coding",
        "intent",
        "Coding Intent",
        "Coding intent prioritizes latency and interactive responsiveness.",
        ("latency", "interactive"),
    ),
    OntologyConcept(
        "intent.efficiency",
        "intent",
        "Efficiency Intent",
        "Efficiency intent prefers quieter background load and power savings.",
        ("battery", "background"),
    ),
    OntologyConcept(
        "intervention.latency",
        "intervention",
        "Latency Plan",
        "Favor interactive priority and reduce background contention (advice only).",
        ("interactive", "priority"),
    ),
    OntologyConcept(
        "intervention.efficiency",
        "intervention",
        "Efficiency Plan",
        "Favor background reduction and power-aware placement (advice only).",
        ("power", "background"),
    ),
    OntologyConcept(
        "intervention.balanced",
        "intervention",
        "Balanced Plan",
        "Blend responsiveness and efficiency without aggressive swings.",
        ("balanced", "stability"),
    ),
)


def concepts_by_domain(domain: OntologyDomain) -> tuple[OntologyConcept, ...]:
    """Return ontology concepts filtered by domain."""

    return tuple(c for c in CORE_ONTOLOGY if c.domain == domain)


def get_concept(concept_id: str) -> OntologyConcept:
    """Look up one ontology concept."""

    for concept in CORE_ONTOLOGY:
        if concept.concept_id == concept_id:
            return concept
    raise KeyError(f"Unknown concept: {concept_id}")


# ---------------------------------------------------------------------------
# P3 Causal Knowledge Graph node ontology (additive; does not alter concepts)
# ---------------------------------------------------------------------------

KnowledgeNodeType = Literal[
    "CPU",
    "Memory",
    "Disk",
    "GPU",
    "Network",
    "Process",
    "Intent",
    "Battery",
    "Cluster",
    "Simulation",
    "Discovery",
    "Pattern",
    "Context",
    "Research",
]

KNOWLEDGE_NODE_TYPES: frozenset[str] = frozenset(
    {
        "CPU",
        "Memory",
        "Disk",
        "GPU",
        "Network",
        "Process",
        "Intent",
        "Battery",
        "Cluster",
        "Simulation",
        "Discovery",
        "Pattern",
        "Context",
        "Research",
    }
)


def is_knowledge_node_type(value: str) -> bool:
    """Return True when ``value`` is a supported Causal Knowledge node type."""

    return value in KNOWLEDGE_NODE_TYPES
