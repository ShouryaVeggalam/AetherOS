"""Hypothesis engine — candidate explanations from ResourceGraph only.

Never invents causes. Each hypothesis references real process→resource paths.
"""

from __future__ import annotations

from aetheros.graph.models import ResourceGraph
from aetheros.graph.queries import get_process_resources, nodes_of_type
from aetheros.reasoning.causal import CAUSAL_EDGE_TYPES, infer_causal_chain
from aetheros.reasoning.models import Hypothesis, Observation, ReasoningPath
from aetheros.reasoning.traversal import find_all_paths


def generate_hypotheses(
    graph: ResourceGraph,
    observation: Observation,
    *,
    limit: int = 8,
) -> tuple[Hypothesis, ...]:
    """Generate hypotheses for a pressure observation from graph processes.

    Args:
        graph: Immutable resource graph.
        observation: Measurable observation (e.g. CPU overload).
        limit: Maximum hypotheses to return.

    Returns:
        Hypotheses sorted by provisional confidence (descending).
    """

    target_ids = _observation_targets(graph, observation.metric)
    if not target_ids:
        return ()
    hypotheses: list[Hypothesis] = []
    for process in nodes_of_type(graph, "Process"):
        paths = _supporting_paths(graph, process.id, target_ids)
        if not paths:
            continue
        # Require at least one outbound resource edge (real dependency).
        if not get_process_resources(graph, process.id):  # pragma: no cover
            continue
        provisional = _provisional_confidence(observation, paths)
        title = f"{process.name} {observation.metric} pressure"
        description = (
            f"{process.name} participates in {len(paths)} graph path(s) "
            f"reaching {observation.metric} resources while "
            f"{observation.title} ({observation.value:.1f})."
        )
        hypotheses.append(
            Hypothesis(
                id=f"hyp:{process.id}:{observation.metric}",
                title=title,
                description=description,
                supporting_paths=paths,
                confidence=provisional,
            )
        )
        if len(hypotheses) >= limit:
            break
    hypotheses.sort(key=lambda item: item.confidence, reverse=True)
    return tuple(hypotheses)


def _observation_targets(graph: ResourceGraph, metric: str) -> tuple[str, ...]:
    """Resolve graph node ids implicated by an observation metric."""

    metric_key = metric.strip().lower()
    type_map = {
        "cpu": "CPU",
        "memory": "Memory",
        "disk": "Disk",
        "gpu": "GPU",
        "battery": "Battery",
        "network": "Network",
    }
    node_type = type_map.get(metric_key)
    if node_type is None:
        return ()
    nodes = nodes_of_type(graph, node_type)
    if metric_key == "cpu" and graph.get_node("cpu") is not None:
        # Prefer package + cores when present.
        return tuple(node.id for node in nodes)
    return tuple(node.id for node in nodes)


def _supporting_paths(
    graph: ResourceGraph,
    process_id: str,
    target_ids: tuple[str, ...],
) -> tuple[ReasoningPath, ...]:
    """Collect real paths from a process to observation target nodes."""

    paths: list[ReasoningPath] = []
    for target_id in target_ids:
        shortest = infer_causal_chain(graph, process_id, target_id)
        if shortest is not None and shortest.depth > 0:
            paths.append(shortest)
            continue
        for path in find_all_paths(  # pragma: no cover
            graph,
            process_id,
            target_id,
            relations=CAUSAL_EDGE_TYPES,
            max_depth=5,
            limit=2,
        ):
            if path.depth > 0:
                paths.append(path)
    # Deduplicate by node-id tuple
    unique: dict[tuple[str, ...], ReasoningPath] = {}
    for path in paths:
        key = tuple(node.id for node in path.nodes)
        unique.setdefault(key, path)
    return tuple(unique.values())


def _provisional_confidence(
    observation: Observation,
    paths: tuple[ReasoningPath, ...],
) -> int:
    """Score from path depth + pressure magnitude (not a final verdict)."""

    if not paths:  # pragma: no cover
        return 0
    avg_depth = sum(path.depth for path in paths) / len(paths)
    depth_score = min(1.0, avg_depth / 4.0)
    overshoot = max(0.0, observation.value - observation.threshold)
    pressure = min(1.0, overshoot / max(observation.threshold, 1.0))
    path_bonus = min(1.0, len(paths) / 3.0)
    raw = 0.45 * depth_score + 0.35 * pressure + 0.20 * path_bonus
    return int(round(100 * raw))
