"""Sentinel runtime — anomaly → root cause → cascade → recovery → score.

Continuous resilience intelligence. Recommendation-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.graph.topology import DependencyGraph
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.sentinel.anomaly import Anomaly, AnomalyEngine
from aetheros.sentinel.cascade import CascadePrediction, CascadeSimulator
from aetheros.sentinel.recovery import RecoveryPlan, RecoveryPlanner
from aetheros.sentinel.resilience import ResilienceScore, ResilienceScorer
from aetheros.sentinel.root_cause import RootCause, RootCauseEngine


@dataclass(frozen=True, slots=True)
class SentinelReport:
    """Immutable Sentinel intelligence snapshot."""

    anomalies: tuple[Anomaly, ...]
    root_causes: tuple[RootCause, ...]
    cascade: CascadePrediction
    recovery: RecoveryPlan
    resilience: ResilienceScore
    status: str = "Recommendation Only"

    @property
    def health(self) -> float:
        """Resilience health score."""

        return self.resilience.health

    @property
    def risk(self) -> str:
        """Risk label."""

        return self.resilience.risk

    @property
    def recommended_strategy(self) -> str:
        """Top recovery recommendation title or None."""

        if self.recovery.recommended is None:
            return "None"
        return self.recovery.recommended.title

    @property
    def confidence(self) -> float:
        """Confidence of recommended strategy or resilience score."""

        if self.recovery.recommended is not None:
            return self.recovery.recommended.confidence
        return self.resilience.confidence


@dataclass
class SentinelRuntime:
    """Run one Sentinel observation cycle."""

    graph: DependencyGraph = field(default_factory=DependencyGraph)
    anomalies: AnomalyEngine = field(default_factory=AnomalyEngine)
    root_causes: RootCauseEngine = field(default_factory=RootCauseEngine)
    cascades: CascadeSimulator = field(default_factory=CascadeSimulator)
    recovery: RecoveryPlanner = field(default_factory=RecoveryPlanner)
    scorer: ResilienceScorer = field(default_factory=ResilienceScorer)
    last: SentinelReport | None = field(default=None, init=False)

    def observe(
        self,
        snapshot: TelemetrySnapshot,
        *,
        history: tuple[TelemetryPoint, ...] = (),
        cluster_avg_cpu: float | None = None,
    ) -> SentinelReport:
        """Detect, explain, simulate cascade, plan recovery, score resilience."""

        detected = self.anomalies.detect(
            snapshot, history=history, cluster_avg_cpu=cluster_avg_cpu
        )
        causes: list[RootCause] = []
        cascade = CascadePrediction(
            origin="none",
            hops=(),
            severity=0.0,
            summary="Predicted Cascade: None",
            active=False,
        )
        if detected:
            primary = detected[0]
            causes.extend(self.root_causes.explain(primary, snapshot, history=history))
            cascade = self.cascades.predict(primary, self.graph)
            plan = self.recovery.plan(
                primary,
                snapshot,
                root_causes=tuple(causes),
                cascade=cascade,
            )
        else:
            plan = RecoveryPlan(
                strategies=(), recommended=None, rationale="No active anomalies."
            )

        score = self.scorer.score(detected, cascade, self.graph)
        report = SentinelReport(
            anomalies=detected,
            root_causes=tuple(causes),
            cascade=cascade,
            recovery=plan,
            resilience=score,
        )
        self.last = report
        return report
