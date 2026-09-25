"""Cascade Simulator — predict ripple effects through the dependency graph.

Simulation only. Never affects infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.graph.topology import DependencyGraph
from aetheros.sentinel.anomaly import Anomaly


@dataclass(frozen=True, slots=True)
class CascadeHop:
    """One hop in a predicted cascade chain."""

    entity_id: str
    stage: str
    pressure: float
    note: str


@dataclass(frozen=True, slots=True)
class CascadePrediction:
    """Immutable cascade simulation result.

    Attributes:
        origin: Starting entity / anomaly focus.
        hops: Ordered ripple hops.
        severity: Aggregate cascade severity 0–100.
        summary: Human-readable chain summary.
        active: Whether any non-trivial cascade is predicted.
    """

    origin: str
    hops: tuple[CascadeHop, ...]
    severity: float
    summary: str
    active: bool


@dataclass
class CascadeSimulator:
    """Predict dependency ripple effects from an anomaly."""

    def predict(
        self,
        anomaly: Anomaly,
        graph: DependencyGraph,
        *,
        origin: str | None = None,
    ) -> CascadePrediction:
        """Simulate cascade from ``origin`` (default derived from anomaly)."""

        start = origin or _origin_for(anomaly)
        order = graph.cascade_order(start, depth=4)
        if not order:
            return CascadePrediction(
                origin=start,
                hops=(),
                severity=0.0,
                summary="Predicted Cascade: None",
                active=False,
            )

        stages = (
            "cluster overload",
            "datacenter pressure",
            "regional latency",
            "edge impact",
        )
        hops: list[CascadeHop] = []
        base = _severity_seed(anomaly)
        pressure = base
        for index, entity in enumerate(order[:4]):
            weight = 0.0
            # Prefer edge weight from previous hop if available.
            prev = start if index == 0 else order[index - 1]
            weight = max(graph.edge_weight(prev, entity), 0.35)
            pressure = min(100.0, pressure * (0.55 + 0.45 * weight))
            stage = stages[min(index, len(stages) - 1)]
            hops.append(
                CascadeHop(
                    entity_id=entity,
                    stage=stage,
                    pressure=round(pressure, 1),
                    note=f"{start} → {entity} via dependency coupling {weight:.2f}",
                )
            )

        # Trivial cascades below threshold are reported as None.
        if not hops or (hops[-1].pressure < 25.0 and anomaly.severity == "low"):
            return CascadePrediction(
                origin=start,
                hops=tuple(hops),
                severity=round(hops[-1].pressure if hops else 0.0, 1),
                summary="Predicted Cascade: None",
                active=False,
            )

        chain = " → ".join(h.stage for h in hops)
        return CascadePrediction(
            origin=start,
            hops=tuple(hops),
            severity=round(hops[-1].pressure, 1),
            summary=f"Node/service stress → {chain}",
            active=True,
        )


def _origin_for(anomaly: Anomaly) -> str:
    """Map anomaly kinds to a graph origin id."""

    mapping = {
        "cpu": "node.local.1",
        "memory_leak": "node.local.1",
        "disk": "node.local.1",
        "battery": "node.local.1",
        "network": "svc.edge",
        "cluster_imbalance": "cluster.local",
    }
    return mapping.get(anomaly.kind, "node.local.1")


def _severity_seed(anomaly: Anomaly) -> float:
    """Initial cascade pressure from anomaly severity."""

    return {"low": 30.0, "medium": 55.0, "high": 80.0}.get(anomaly.severity, 40.0)
