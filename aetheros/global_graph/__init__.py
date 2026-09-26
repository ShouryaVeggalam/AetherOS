"""Global Knowledge Graph — v6.0 P3 Horizon canonical intelligence model.

Unifies federation, topology, memory, twin, consensus, and research into
one verified, read-only graph. Never fabricates edges. Never mutates cloud.
"""

from __future__ import annotations

from aetheros.global_graph.builder import build_demo_global_graph, build_global_graph
from aetheros.global_graph.evidence import EvidenceIndex, EvidenceRecord
from aetheros.global_graph.formatter import GlobalKnowledgePanel
from aetheros.global_graph.models import (
    GLOBAL_GRAPH_SCHEMA,
    GlobalEdge,
    GlobalKnowledgeGraph,
    GlobalNode,
)
from aetheros.global_graph.ontology import (
    GLOBAL_NODE_TYPES,
    INFRASTRUCTURE_TYPES,
    INTELLIGENCE_TYPES,
    RESOURCE_TYPES,
    GlobalNodeType,
    is_global_node_type,
)
from aetheros.global_graph.relationships import (
    GLOBAL_RELATIONS,
    GlobalRelation,
    is_global_relation,
)
from aetheros.global_graph.serializer import (
    decode_graph,
    encode_evidence,
    encode_graph,
    graph_hash,
    graph_to_json,
)
from aetheros.global_graph.traversal import (
    ImpactReport,
    PathResult,
    downstream,
    find_cluster,
    find_region,
    impact_analysis,
    related_discoveries,
    shortest_path,
    upstream,
)
from aetheros.global_graph.validator import (
    ValidationError,
    ValidationReport,
    validate_graph,
)

__all__ = [
    "GLOBAL_GRAPH_SCHEMA",
    "GLOBAL_NODE_TYPES",
    "GLOBAL_RELATIONS",
    "INFRASTRUCTURE_TYPES",
    "INTELLIGENCE_TYPES",
    "RESOURCE_TYPES",
    "EvidenceIndex",
    "EvidenceRecord",
    "GlobalEdge",
    "GlobalKnowledgeGraph",
    "GlobalKnowledgePanel",
    "GlobalNode",
    "GlobalNodeType",
    "GlobalRelation",
    "ImpactReport",
    "PathResult",
    "ValidationError",
    "ValidationReport",
    "build_demo_global_graph",
    "build_global_graph",
    "decode_graph",
    "downstream",
    "encode_evidence",
    "encode_graph",
    "find_cluster",
    "find_region",
    "graph_hash",
    "graph_to_json",
    "impact_analysis",
    "is_global_node_type",
    "is_global_relation",
    "related_discoveries",
    "shortest_path",
    "upstream",
    "validate_graph",
]
