"""Causal Knowledge Graph validator — reject invalid / speculative structure.

Rejects: cycles, invalid ontology, orphan nodes, duplicate relationships,
unsupported edge types. Returns rich structured errors. Never mutates.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from aetheros.knowledge.models import CausalKnowledgeGraph, KnowledgeEdge
from aetheros.knowledge.ontology import is_knowledge_node_type
from aetheros.knowledge.relationships import is_knowledge_relation


@dataclass(frozen=True, slots=True)
class ValidationError:
    """One structured validation failure."""

    code: str
    message: str
    node_id: str | None = None
    edge_key: tuple[str, str, str] | None = None


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Full validation outcome for a Causal Knowledge Graph."""

    ok: bool
    errors: tuple[ValidationError, ...]

    @property
    def error_count(self) -> int:
        return len(self.errors)


def validate_graph(graph: CausalKnowledgeGraph) -> ValidationReport:
    """Validate ontology, uniqueness, connectivity, and acyclicity."""

    errors: list[ValidationError] = []
    errors.extend(_check_nodes(graph))
    errors.extend(_check_edges(graph))
    errors.extend(_check_orphans(graph))
    errors.extend(_check_cycles(graph))
    return ValidationReport(ok=not errors, errors=tuple(errors))


def _check_nodes(graph: CausalKnowledgeGraph) -> list[ValidationError]:
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
        if not is_knowledge_node_type(node.type):
            errors.append(
                ValidationError(
                    code="invalid_ontology",
                    message=f"unsupported node type '{node.type}'",
                    node_id=node.id,
                )
            )
    return errors


def _check_edges(graph: CausalKnowledgeGraph) -> list[ValidationError]:
    errors: list[ValidationError] = []
    ids = graph.node_ids()
    seen_keys: set[tuple[str, str, str]] = set()
    for edge in graph.edges:
        key = edge.key
        if key in seen_keys:
            errors.append(
                ValidationError(
                    code="duplicate_relationship",
                    message=(
                        f"duplicate edge {edge.source} -[{edge.relationship}]-> "
                        f"{edge.target}"
                    ),
                    edge_key=key,
                )
            )
        seen_keys.add(key)
        if not is_knowledge_relation(edge.relationship):
            errors.append(
                ValidationError(
                    code="unsupported_edge_type",
                    message=f"unsupported relationship '{edge.relationship}'",
                    edge_key=key,
                )
            )
        if edge.source not in ids:
            errors.append(
                ValidationError(
                    code="dangling_source",
                    message=f"edge source '{edge.source}' missing from nodes",
                    edge_key=key,
                )
            )
        if edge.target not in ids:
            errors.append(
                ValidationError(
                    code="dangling_target",
                    message=f"edge target '{edge.target}' missing from nodes",
                    edge_key=key,
                )
            )
    return errors


def _check_orphans(graph: CausalKnowledgeGraph) -> list[ValidationError]:
    if not graph.nodes:
        return []
    connected: set[str] = set()
    for edge in graph.edges:
        connected.add(edge.source)
        connected.add(edge.target)
    errors: list[ValidationError] = []
    for node in graph.nodes:
        if node.id not in connected:
            errors.append(
                ValidationError(
                    code="orphan_node",
                    message=f"orphan node '{node.id}' has no relationships",
                    node_id=node.id,
                )
            )
    return errors


def _check_cycles(graph: CausalKnowledgeGraph) -> list[ValidationError]:
    """Detect directed cycles via Kahn topological sort."""

    if not graph.edges:
        return []
    adj: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {node.id: 0 for node in graph.nodes}
    for edge in graph.edges:
        adj[edge.source].append(edge.target)
        if edge.target in indegree:
            indegree[edge.target] = indegree.get(edge.target, 0) + 1
        else:
            indegree[edge.target] = indegree.get(edge.target, 0) + 1
        indegree.setdefault(edge.source, indegree.get(edge.source, 0))

    queue: deque[str] = deque(nid for nid, deg in indegree.items() if deg == 0)
    seen = 0
    while queue:
        node = queue.popleft()
        seen += 1
        for nxt in adj.get(node, ()):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if seen < len(indegree):
        return [
            ValidationError(
                code="cycle",
                message="directed cycle detected in Causal Knowledge Graph",
            )
        ]
    return []


def assert_unique_edges(edges: tuple[KnowledgeEdge, ...]) -> None:
    """Raise ValueError when duplicate edge keys exist."""

    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        if edge.key in seen:
            raise ValueError(f"duplicate relationship: {edge.key}")
        seen.add(edge.key)
