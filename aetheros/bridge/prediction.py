"""Prediction bridge — prepare ForecastEngine inputs from the Resource Graph.

Does not call or modify ``aetheros.predictive``. Returns immutable
PredictionContext only.
"""

from __future__ import annotations

from aetheros.bridge.context import PredictionContext
from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.graph.queries import nodes_of_type


def prediction_inputs(
    graph: ResourceGraph,
    *,
    historical_window: int = 60,
) -> PredictionContext:
    """Project graph nodes into a PredictionContext.

    Args:
        graph: Immutable resource graph.
        historical_window: Declared observatory window size (samples). Caller
            supplies the real window; the bridge never invents history.

    Returns:
        Frozen PredictionContext for downstream prediction adapters.
    """

    if historical_window < 0:
        raise ValueError("historical_window must be non-negative")
    intent_node = graph.get_node("intent:active")
    intent = intent_node.name if intent_node is not None else None
    return PredictionContext(
        cpu_nodes=nodes_of_type(graph, "CPU"),
        memory_nodes=nodes_of_type(graph, "Memory"),
        gpu_nodes=nodes_of_type(graph, "GPU"),
        active_processes=nodes_of_type(graph, "Process"),
        intent=intent,
        historical_window=historical_window,
    )


def aggregate_percent(
    nodes: tuple[ResourceNode, ...],
    *,
    key: str = "percent",
) -> float | None:
    """Average a metadata percent across nodes, or None when absent."""

    values: list[float] = []
    for node in nodes:
        for meta_key, raw in node.metadata:
            if meta_key != key:
                continue
            try:
                values.append(float(raw))
            except ValueError:
                continue
    if not values:
        return None
    return sum(values) / len(values)
