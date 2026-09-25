"""Latency Engine — estimate communication delay from geography.

Never performs real networking tests (no ICMP, no sockets to peers).
Estimates are pure functions of distance, network class, and optional
historical samples provided by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.horizon.geography import GeoPoint, NetworkClass, haversine_km
from aetheros.horizon.world_graph import WorldGraph

# Approximate speed factors (km/ms equivalent) by network class.
_SPEED_KM_PER_MS: dict[NetworkClass, float] = {
    "fiber": 200.0,  # ~0.67c in fiber + routing overhead
    "satellite": 80.0,  # includes LEO hop penalty
    "cellular": 120.0,
    "wifi": 150.0,
    "mesh": 90.0,
}

_BASE_MS: dict[NetworkClass, float] = {
    "fiber": 1.5,
    "satellite": 25.0,
    "cellular": 8.0,
    "wifi": 3.0,
    "mesh": 12.0,
}

_RELIABILITY: dict[NetworkClass, float] = {
    "fiber": 0.995,
    "satellite": 0.92,
    "cellular": 0.94,
    "wifi": 0.90,
    "mesh": 0.88,
}


@dataclass(frozen=True, slots=True)
class LatencyEstimate:
    """Immutable latency estimate between two endpoints.

    Attributes:
        source_id: Origin node id.
        target_id: Destination node id.
        distance_km: Great-circle distance.
        network: Assumed network class.
        estimated_ms: One-way estimated latency.
        reliability: Delivery reliability in [0, 1].
        confidence: Model confidence in [0, 1].
        explanation: Human-readable derivation.
    """

    source_id: str
    target_id: str
    distance_km: float
    network: NetworkClass
    estimated_ms: float
    reliability: float
    confidence: float
    explanation: str


@dataclass
class LatencyEngine:
    """Estimate latency from distance + network class + history."""

    def estimate(
        self,
        source: GeoPoint,
        target: GeoPoint,
        *,
        network: NetworkClass = "fiber",
        source_id: str = "a",
        target_id: str = "b",
        historical_ms: tuple[float, ...] = (),
    ) -> LatencyEstimate:
        """Compute a read-only latency estimate (no network I/O)."""

        distance = haversine_km(source, target)
        speed = _SPEED_KM_PER_MS[network]
        base = _BASE_MS[network]
        prop_ms = distance / speed
        estimated = base + prop_ms
        confidence = 0.7
        if historical_ms:
            hist_avg = sum(historical_ms) / len(historical_ms)
            # Blend model with history (history wins slightly).
            estimated = 0.4 * estimated + 0.6 * hist_avg
            confidence = min(0.95, 0.7 + 0.05 * len(historical_ms))
        reliability = _RELIABILITY[network]
        # Long hauls are slightly less reliable in the model.
        if distance > 8000:
            reliability *= 0.97
            confidence *= 0.95
        explanation = (
            f"Distance {distance:.0f} km over {network}: "
            f"base {base:.1f} ms + propagation {prop_ms:.1f} ms"
            + (
                f"; blended with {len(historical_ms)} historical samples"
                if historical_ms
                else ""
            )
            + ". No live network probe performed."
        )
        return LatencyEstimate(
            source_id=source_id,
            target_id=target_id,
            distance_km=round(distance, 1),
            network=network,
            estimated_ms=round(estimated, 2),
            reliability=round(reliability, 4),
            confidence=round(min(1.0, confidence), 3),
            explanation=explanation,
        )

    def estimate_regions(
        self,
        graph: WorldGraph,
        *,
        network: NetworkClass = "fiber",
    ) -> tuple[LatencyEstimate, ...]:
        """Pairwise latency estimates between region centroids."""

        regions = list(graph.regions())
        estimates: list[LatencyEstimate] = []
        for i, a in enumerate(regions):
            if a.location is None:
                continue
            for b in regions[i + 1 :]:
                if b.location is None:
                    continue
                estimates.append(
                    self.estimate(
                        a.location,
                        b.location,
                        network=network,
                        source_id=a.node_id,
                        target_id=b.node_id,
                    )
                )
        return tuple(estimates)
