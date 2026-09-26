"""Global Knowledge Graph validator — reject invalid / unverified structure.

Rejects: cycles, duplicate nodes, duplicate relationships, invalid ontology,
orphan resources (resource nodes with no incident edges).
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from aetheros.global_graph.models import GlobalEdge, GlobalKnowledgeGraph
from aetheros.global_graph.ontology import RESOURCE_TYPES, is_global_node_type
from aetheros.global_graph.relationships import is_global_relation


@dataclass(frozen=True, slots=True)
class ValidationError:
    """One structured validation failure."""

    code: str
    message: str
    node_id: str | None = None
    edge_key: tuple[str, str, str] | None = None


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Full validation outcome."""

    ok: bool
    errors: tuple[ValidationError, ...]

    @property
    def error_count(self) -> int:
        return len(self.errors)


def validate_graph(graph: GlobalKnowledgeGraph) -> ValidationReport:
    """Validate ontology, uniqueness, orphans, and acyclicity."""

    errors: list[ValidationError] = []
    errors.extend(_check_nodes(graph))
    errors.extend(_check_edges(graph))
    errors.extend(_check_orphans(graph))
    errors.extend(_check_cycles(graph))
    return ValidationReport(ok=not errors, errors=tuple(errors))


def _check_nodes(graph: GlobalKnowledgeGraph) -> list[ValidationError]:
    errors: list[ValidationError] = []
    seen: set[str] = set()
    for node in graph.nodes:
        if node.id in seen:
            errors.append(
                ValidationError(
                    code="duplicate_node",
                    message=f"duplicate node id '{node.id}'",
                    node_id=node.id,
                )
            )
        seen.add(node.id)
        if not is_global_node_type(str(node.type)):
            errors.append(
                ValidationError(
                    code="invalid_ontology",
                    message=f"unsupported node type '{node.type}'",
                    node_id=node.id,
                )
            )
    return errors


def _check_edges(graph: GlobalKnowledgeGraph) -> list[ValidationError]:
    errors: list[ValidationError] = []
    ids = graph.node_ids()
    seen: set[tuple[str, str, str]] = set()
    for edge in graph.edges:
        key = edge.key
        if key in seen:
            errors.append(
                ValidationError(
                    code="duplicate_relationship",
                    message=f"duplicate edge {key}",
                    edge_key=key,
                )
            )
        seen.add(key)
        if not is_global_relation(str(edge.relationship)):
            errors.append(
                ValidationError(
                    code="invalid_ontology",
                    message=f"unsupported relationship '{edge.relationship}'",
                    edge_key=key,
                )
            )
        if edge.source not in ids:
            errors.append(
                ValidationError(
                    code="missing_endpoint",
                    message=f"source '{edge.source}' not in graph",
                    edge_key=key,
                )
            )
        if edge.target not in ids:
            errors.append(
                ValidationError(
                    code="missing_endpoint",
                    message=f"target '{edge.target}' not in graph",
                    edge_key=key,
                )
            )
        if edge.evidence_count < 1 or not edge.evidence_ids:
            errors.append(
                ValidationError(
                    code="missing_evidence",
                    message="edge lacks evidence citations",
                    edge_key=key,
                )
            )
    return errors


def _check_orphans(graph: GlobalKnowledgeGraph) -> list[ValidationError]:
    """Resource-type nodes must participate in at least one edge."""

    errors: list[ValidationError] = []
    touched: set[str] = set()
    for edge in graph.edges:
        touched.add(edge.source)
        touched.add(edge.target)
    for node in graph.nodes:
        if node.type in RESOURCE_TYPES and node.id not in touched:
            errors.append(
                ValidationError(
                    code="orphan_resource",
                    message=f"orphan resource node '{node.id}'",
                    node_id=node.id,
                )
            )
    return errors


def _check_cycles(graph: GlobalKnowledgeGraph) -> list[ValidationError]:
    """Reject directed cycles (Kahn / indegree sweep)."""

    errors: list[ValidationError] = []
    ids = list(graph.node_ids())
    indegree: dict[str, int] = {i: 0 for i in ids}
    adj: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        if edge.source in indegree and edge.target in indegree:
            adj[edge.source].append(edge.target)
            indegree[edge.target] += 1
    queue: deque[str] = deque([n for n, d in indegree.items() if d == 0])
    seen = 0
    while queue:
        node = queue.popleft()
        seen += 1
        for nxt in adj[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if ids and seen < len(ids):
        errors.append(
            ValidationError(
                code="cycle",
                message="directed cycle detected in Global Knowledge Graph",
            )
        )
    return errors


def has_duplicate_edges(edges: tuple[GlobalEdge, ...]) -> bool:
    """Utility: True when any duplicate relationship keys exist."""

    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        if edge.key in seen:
            return True
        seen.add(edge.key)
    return False
