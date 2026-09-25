"""Capacity Planner — forecast planetary demand horizons.

Horizons: 1 hour, 24 hours, 7 days.
Explainable pure-math forecasts. Never provisions resources.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aetheros.horizon.world_graph import WorldGraph

HorizonWindow = Literal["1h", "24h", "7d"]

_HORIZON_HOURS: dict[HorizonWindow, float] = {
    "1h": 1.0,
    "24h": 24.0,
    "7d": 168.0,
}

# Gentle growth rates per hour (fraction of baseline demand).
_GROWTH = {
    "compute": 0.0012,
    "memory": 0.0009,
    "gpu": 0.0018,
    "storage": 0.0004,
}


@dataclass(frozen=True, slots=True)
class DemandForecast:
    """One resource forecast for one horizon.

    Attributes:
        resource: compute | memory | gpu | storage.
        horizon: 1h | 24h | 7d.
        baseline: Current normalized demand units.
        projected: Forecast demand units.
        growth_pct: Percent growth vs baseline.
        explanation: Why this projection was produced.
        confidence: Model confidence 0–1.
    """

    resource: str
    horizon: HorizonWindow
    baseline: float
    projected: float
    growth_pct: float
    explanation: str
    confidence: float


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    """Full multi-horizon capacity plan."""

    forecasts: tuple[DemandForecast, ...]
    narrative: tuple[str, ...]
    overall_confidence: float


@dataclass
class CapacityPlanner:
    """Forecast compute / memory / GPU / storage demand."""

    def plan(self, graph: WorldGraph) -> CapacityPlan:
        """Build explainable forecasts across all horizons."""

        census = graph.census
        # Normalize baselines from census (arbitrary but stable units).
        baselines = {
            "compute": census.nodes / 1000.0,
            "memory": census.nodes / 800.0,
            "gpu": max(1.0, census.hpc_clusters * 64.0),
            "storage": census.datacenters * 12.0,
        }
        forecasts: list[DemandForecast] = []
        for resource, baseline in baselines.items():
            rate = _GROWTH[resource]
            for horizon, hours in _HORIZON_HOURS.items():
                projected = baseline * (1.0 + rate * hours)
                # Weekend / diurnal dampening for short horizons.
                if horizon == "1h":
                    projected *= 1.01
                    confidence = 0.88
                elif horizon == "24h":
                    projected *= 1.03
                    confidence = 0.8
                else:
                    projected *= 1.08
                    confidence = 0.72
                growth_pct = ((projected - baseline) / baseline) * 100.0
                explanation = (
                    f"{resource} demand over {horizon}: baseline {baseline:.1f} → "
                    f"{projected:.1f} ({growth_pct:+.2f}%) using hourly growth "
                    f"{rate:.4%} scaled by census "
                    f"(nodes={census.nodes}, hpc={census.hpc_clusters}, "
                    f"dcs={census.datacenters}). Simulation forecast only."
                )
                forecasts.append(
                    DemandForecast(
                        resource=resource,
                        horizon=horizon,
                        baseline=round(baseline, 2),
                        projected=round(projected, 2),
                        growth_pct=round(growth_pct, 3),
                        explanation=explanation,
                        confidence=confidence,
                    )
                )
        narrative = (
            "Capacity plan derived from planetary census baselines.",
            "Growth rates are conservative public-model estimates.",
            "No cloud APIs called; no resources provisioned.",
        )
        overall = sum(f.confidence for f in forecasts) / len(forecasts)
        return CapacityPlan(
            forecasts=tuple(forecasts),
            narrative=narrative,
            overall_confidence=round(overall, 3),
        )
