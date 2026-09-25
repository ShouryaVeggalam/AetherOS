"""Ontology relationships — typed edges for Genesis knowledge graphs.

Relationships are declarative catalog entries plus a NetworkX builder
for evidence/knowledge graphs. Never mutates live systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import networkx as nx

RelationKind = Literal[
    "CAUSES",
    "USES",
    "ALLOCATES",
    "DEPENDS_ON",
    "IMPROVES",
    "DEGRADES",
]

ExtraEntity = Literal[
    "intent",
    "cluster",
    "process",
    "simulation",
    "research",
]


@dataclass(frozen=True, slots=True)
class OntologyRelation:
    """One immutable relationship template or instance."""

    relation_id: str
    source_id: str
    relation: RelationKind
    target_id: str
    weight: float
    note: str

    def __post_init__(self) -> None:
        """Validate weight."""

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be in [0, 1]")


SEED_RELATIONS: tuple[OntologyRelation, ...] = (
    OntologyRelation(
        "rel.coding.causes.cpu_latency",
        "workload.interactive_coding",
        "CAUSES",
        "resource.cpu",
        0.82,
        "Interactive coding workloads often raise CPU latency before memory pressure.",
    ),
    OntologyRelation(
        "rel.compile.uses.cache",
        "workload.compile",
        "USES",
        "resource.cache",
        0.9,
        "Compilation uses local caches to avoid repeated disk fetches.",
    ),
    OntologyRelation(
        "rel.cache.improves.compile",
        "resource.cache",
        "IMPROVES",
        "workload.compile",
        0.78,
        "Larger cache allocation tends to reduce compile latency in simulation.",
    ),
    OntologyRelation(
        "rel.training.uses.gpu",
        "workload.training",
        "USES",
        "resource.gpu",
        0.95,
        "Training allocates GPU capacity as the primary accelerator.",
    ),
    OntologyRelation(
        "rel.serving.depends.network",
        "workload.serving",
        "DEPENDS_ON",
        "resource.network",
        0.88,
        "Online serving depends on network reliability between clusters.",
    ),
    OntologyRelation(
        "rel.rendering.degrades.disk",
        "workload.rendering",
        "DEGRADES",
        "resource.disk",
        0.7,
        "Sustained rendering can degrade disk headroom for interactive work.",
    ),
    OntologyRelation(
        "rel.research.allocates.simulation",
        "research",
        "ALLOCATES",
        "simulation",
        0.6,
        "Genesis research allocates simulation budget to test hypotheses.",
    ),
)


def build_ontology_graph(
    relations: tuple[OntologyRelation, ...] = SEED_RELATIONS,
) -> nx.DiGraph:
    """Build a NetworkX DiGraph from ontology relations."""

    graph = nx.DiGraph()
    for rel in relations:
        graph.add_node(rel.source_id)
        graph.add_node(rel.target_id)
        graph.add_edge(
            rel.source_id,
            rel.target_id,
            relation=rel.relation,
            weight=rel.weight,
            note=rel.note,
            relation_id=rel.relation_id,
        )
    return graph
