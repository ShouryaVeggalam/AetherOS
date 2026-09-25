"""AetherOS knowledge layer — declarative systems ontology.

No I/O. No private user content. Seeds cognition and reasoning.
"""

from __future__ import annotations

from aetheros.knowledge.ontology import (
    CORE_ONTOLOGY,
    OntologyConcept,
    concepts_by_domain,
    get_concept,
)
from aetheros.knowledge.resource_types import (
    RESOURCE_TYPES,
    CausalRelationKind,
    RelationKind,
    ResourceKind,
    ResourceType,
    get_resource_type,
)
from aetheros.knowledge.workload_graph import (
    WORKLOAD_EDGES,
    WorkloadEdge,
    edges_for_workload,
)

__all__ = [
    "CORE_ONTOLOGY",
    "RESOURCE_TYPES",
    "WORKLOAD_EDGES",
    "CausalRelationKind",
    "OntologyConcept",
    "RelationKind",
    "ResourceKind",
    "ResourceType",
    "WorkloadEdge",
    "concepts_by_domain",
    "edges_for_workload",
    "get_concept",
    "get_resource_type",
]
