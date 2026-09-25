"""Resilience Score — explainable health / stability / redundancy / risk.

Pure scoring from anomalies, cascade, and graph redundancy.
Never triggers failovers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aetheros.graph.topology import DependencyGraph
from aetheros.sentinel.anomaly import Anomaly
from aetheros.sentinel.cascade import CascadePrediction

RiskLabel = Literal["Low", "Medium", "High"]


@dataclass(frozen=True, slots=True)
class ResilienceScore:
    """Immutable explainable resilience metrics.

    Attributes:
        health: Overall health 0–100.
        stability: Stability 0–100.
        redundancy: Redundancy headroom 0–100.
        risk: Low | Medium | High.
        confidence: Scoring confidence 0–1.
        explanation: Human-readable derivation.
    """

    health: float
    stability: float
    redundancy: float
    risk: RiskLabel
    confidence: float
    explanation: str

    def __post_init__(self) -> None:
        """Clamp numeric fields."""

        for name in ("health", "stability", "redundancy"):
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(f"{name} must be in [0, 100]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass
class ResilienceScorer:
    """Compute a ResilienceScore from Sentinel signals."""

    def score(
        self,
        anomalies: tuple[Anomaly, ...],
        cascade: CascadePrediction | None,
        graph: DependencyGraph,
    ) -> ResilienceScore:
        """Derive explainable resilience metrics."""

        health = 100.0
        for anomaly in anomalies:
            health -= {"low": 3.0, "medium": 6.0, "high": 12.0}.get(
                anomaly.severity, 5.0
            )
        health = max(0.0, health)

        stability = 92.0
        if cascade and cascade.active:
            stability -= min(40.0, cascade.severity * 0.35)
        stability -= 4.0 * sum(1 for a in anomalies if a.severity == "high")
        stability = max(0.0, min(100.0, stability))

        # Redundancy ≈ inverse of critical service coupling concentration.
        services = graph.services()
        critical = [s for s in services if s.tier == "critical"]
        if critical:
            mean_health = sum(s.health for s in critical) / len(critical)
            redundancy = mean_health * 100.0 * 0.85 + 10.0
        else:
            redundancy = 70.0
        redundancy = max(0.0, min(100.0, redundancy))

        if (
            health < 70
            or stability < 55
            or (cascade and cascade.active and cascade.severity >= 60)
        ):
            risk: RiskLabel = "High"
        elif anomalies or (cascade and cascade.active):
            risk = "Medium"
        else:
            risk = "Low"

        confidence = 0.9 if anomalies or (cascade and cascade.active) else 0.75
        explanation = (
            f"Health {health:.0f} from {len(anomalies)} anomalies; "
            f"stability {stability:.0f}"
            + (
                f" with cascade severity {cascade.severity:.0f}"
                if cascade and cascade.active
                else " with no active cascade"
            )
            + f"; redundancy {redundancy:.0f} from critical service health. "
            f"Risk={risk}."
        )
        return ResilienceScore(
            health=round(health, 1),
            stability=round(stability, 1),
            redundancy=round(redundancy, 1),
            risk=risk,
            confidence=confidence,
            explanation=explanation,
        )
