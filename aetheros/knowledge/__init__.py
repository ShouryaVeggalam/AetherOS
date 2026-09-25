"""AetherOS knowledge layer — declarative ontology + Causal Knowledge Graph.

No I/O. No private user content. P3 Causal Knowledge Graph is read-only and
never fabricates relationships.
"""

from __future__ import annotations

from aetheros.knowledge.builder import build_knowledge_graph
from aetheros.knowledge.formatter import CausalKnowledgePanel
from aetheros.knowledge.graph import KnowledgeGraphView, empty_graph
from aetheros.knowledge.models import (
    CausalKnowledgeGraph,
    KnowledgeEdge,
    KnowledgeNode,
)

# Re-export KnowledgeNodeType from ontology for public API.
from aetheros.knowledge.ontology import (
    CORE_ONTOLOGY,
    KNOWLEDGE_NODE_TYPES,
    KnowledgeNodeType,
    OntologyConcept,
    concepts_by_domain,
    get_concept,
    is_knowledge_node_type,
)
from aetheros.knowledge.relationships import (
    CAUSAL_RELATIONS,
    KNOWLEDGE_RELATIONS,
    KnowledgeRelation,
    is_knowledge_relation,
    map_resource_relation,
)
from aetheros.knowledge.resource_types import (
    RESOURCE_TYPES,
    CausalRelationKind,
    RelationKind,
    ResourceKind,
    ResourceType,
    get_resource_type,
)
from aetheros.knowledge.traversal import (
    downstream,
    find_causes,
    find_effects,
    related_discoveries,
    shortest_causal_path,
    upstream,
)
from aetheros.knowledge.validator import (
    ValidationError,
    ValidationReport,
    validate_graph,
)
from aetheros.knowledge.workload_graph import (
    WORKLOAD_EDGES,
    WorkloadEdge,
    edges_for_workload,
)

__all__ = [
    "CAUSAL_RELATIONS",
    "CORE_ONTOLOGY",
    "KNOWLEDGE_NODE_TYPES",
    "KNOWLEDGE_RELATIONS",
    "RESOURCE_TYPES",
    "WORKLOAD_EDGES",
    "CausalKnowledgeGraph",
    "CausalKnowledgePanel",
    "CausalRelationKind",
    "KnowledgeEdge",
    "KnowledgeGraphView",
    "KnowledgeNode",
    "KnowledgeNodeType",
    "KnowledgeRelation",
    "OntologyConcept",
    "RelationKind",
    "ResourceKind",
    "ResourceType",
    "ValidationError",
    "ValidationReport",
    "WorkloadEdge",
    "build_knowledge_graph",
    "concepts_by_domain",
    "downstream",
    "edges_for_workload",
    "empty_graph",
    "find_causes",
    "find_effects",
    "get_concept",
    "get_resource_type",
    "is_knowledge_node_type",
    "is_knowledge_relation",
    "map_resource_relation",
    "related_discoveries",
    "shortest_causal_path",
    "upstream",
    "validate_graph",
]
