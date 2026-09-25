"""Resource Graph validator — structural integrity checks.

Reuses the P1 cycle-detection approach (DFS colouring) on the directed
resource graph. Rejects cycles, missing endpoints, invalid types, and
duplicate node ids. Never mutates the graph.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.graph.models import (
    EDGE_RELATIONS,
    NODE_TYPES,
    ResourceEdge,
    ResourceGraph,
    ResourceNode,
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One immutable validation finding."""

    code: str
    message: str
    path: str = ""


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Rich validation outcome for a ResourceGraph."""

    ok: bool
    issues: tuple[ValidationIssue, ...]

    @property
    def error_count(self) -> int:
        """Number of issues."""

        return len(self.issues)


def validate_resource_graph(graph: ResourceGraph) -> ValidationResult:
    """Validate node/edge integrity and reject directed cycles.

    Args:
        graph: Candidate resource graph.

    Returns:
        ``ValidationResult`` with ``ok=True`` only when no issues remain.
    """

    issues: list[ValidationIssue] = []
    issues.extend(_duplicate_ids(graph.nodes))
    issues.extend(_node_type_issues(graph.nodes))
    issues.extend(_edge_issues(graph))
    issues.extend(_cycle_issues(graph))
    return ValidationResult(ok=not issues, issues=tuple(issues))


def _duplicate_ids(nodes: tuple[ResourceNode, ...]) -> list[ValidationIssue]:
    """Detect duplicate node identifiers."""

    seen: set[str] = set()
    issues: list[ValidationIssue] = []
    for node in nodes:
        if node.id in seen:
            issues.append(
                ValidationIssue(
                    "duplicate_id",
                    f"Duplicate node id '{node.id}'.",
                    path=node.id,
                )
            )
        seen.add(node.id)
    return issues


def _node_type_issues(nodes: tuple[ResourceNode, ...]) -> list[ValidationIssue]:
    """Reject unknown node types (defence in depth beyond typing)."""

    issues: list[ValidationIssue] = []
    for node in nodes:
        if node.type not in NODE_TYPES:
            issues.append(
                ValidationIssue(
                    "invalid_node_type",
                    f"Unknown node type '{node.type}'.",
                    path=node.id,
                )
            )
    return issues


def _edge_issues(graph: ResourceGraph) -> list[ValidationIssue]:
    """Reject missing endpoints and invalid edge relations."""

    ids = graph.node_ids()
    issues: list[ValidationIssue] = []
    for edge in graph.edges:
        path = f"{edge.source}->{edge.target}:{edge.relationship}"
        if edge.relationship not in EDGE_RELATIONS:
            issues.append(
                ValidationIssue(
                    "invalid_edge_type",
                    f"Unknown edge relationship '{edge.relationship}'.",
                    path=path,
                )
            )
        if edge.source not in ids:
            issues.append(
                ValidationIssue(
                    "missing_node",
                    f"Edge source '{edge.source}' is not a node.",
                    path=path,
                )
            )
        if edge.target not in ids:
            issues.append(
                ValidationIssue(
                    "missing_node",
                    f"Edge target '{edge.target}' is not a node.",
                    path=path,
                )
            )
    return issues


def _cycle_issues(graph: ResourceGraph) -> list[ValidationIssue]:
    """Detect directed cycles via grey/black DFS (P1-style colouring)."""

    adjacency: dict[str, list[str]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.source in adjacency:
            adjacency[edge.source].append(edge.target)

    white, grey, black = 0, 1, 2
    colour = {node_id: white for node_id in adjacency}
    stack: list[str] = []
    issues: list[ValidationIssue] = []

    def dfs(node_id: str) -> None:
        colour[node_id] = grey
        stack.append(node_id)
        for nxt in adjacency.get(node_id, ()):
            if nxt not in colour:
                continue
            if colour[nxt] == grey:
                cycle_start = stack.index(nxt)
                cycle = stack[cycle_start:] + [nxt]
                issues.append(
                    ValidationIssue(
                        "cycle",
                        "Directed cycle: " + " -> ".join(cycle),
                        path=nxt,
                    )
                )
            elif colour[nxt] == white:
                dfs(nxt)
        stack.pop()
        colour[node_id] = black

    for node_id in sorted(adjacency):
        if colour[node_id] == white:
            dfs(node_id)
    return issues


def assert_valid(graph: ResourceGraph) -> ResourceGraph:
    """Return ``graph`` or raise ``ValueError`` with joined issue messages."""

    result = validate_resource_graph(graph)
    if result.ok:
        return graph
    detail = "; ".join(issue.message for issue in result.issues)
    raise ValueError(f"Invalid ResourceGraph: {detail}")


def is_valid_edge(edge: ResourceEdge, node_ids: frozenset[str]) -> bool:
    """True when an edge's endpoints and relationship are sound."""

    return (
        edge.relationship in EDGE_RELATIONS
        and edge.source in node_ids
        and edge.target in node_ids
    )
