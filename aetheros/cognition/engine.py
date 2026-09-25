"""CognitionEngine — v3 Cognition Core public interface.

observe → reason → verify → plan over graph evidence.
Deterministic. Not an LLM. Never executes OS actions.

Isolated from legacy ``CognitiveRuntime`` (unchanged).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aetheros.cognition.evidence import collect_evidence, context_label
from aetheros.cognition.hypotheses import generate_core_hypotheses
from aetheros.cognition.memory import OperationalMemory
from aetheros.cognition.models import (
    CognitionPlan,
    CognitionState,
    Evidence,
    Hypothesis,
    VerifiedCoreExplanation,
)
from aetheros.cognition.planner import generate_cognition_plans
from aetheros.cognition.verifier import verify_core_hypotheses
from aetheros.graph.models import ResourceGraph
from aetheros.observatory.models import TelemetryPoint


@dataclass
class CognitionEngine:
    """Convert graph evidence into structured operational understanding."""

    memory: OperationalMemory = field(default_factory=OperationalMemory)
    _evidence: tuple[Evidence, ...] = ()
    _hypotheses: tuple[Hypothesis, ...] = ()
    _verified: tuple[VerifiedCoreExplanation, ...] = ()
    _plans: tuple[CognitionPlan, ...] = ()
    _context: str = "BALANCED"
    _simulation_agreement: float | None = None

    def observe(
        self,
        *,
        graph: ResourceGraph | None = None,
        history: Sequence[TelemetryPoint] = (),
        context: Mapping[str, Any] | object | str | None = None,
        twin_summaries: Sequence[str] = (),
        now: datetime | None = None,
    ) -> tuple[Evidence, ...]:
        """Collect evidence from Resource Graph / context / twin / history."""

        patterns = self.memory.statements()
        self._context = context_label(context)
        self._evidence = collect_evidence(
            graph=graph,
            history=history,
            context=context,
            twin_summaries=twin_summaries,
            memory_patterns=patterns,
            now=now,
        )
        return self._evidence

    def reason(self) -> tuple[Hypothesis, ...]:
        """Propose hypotheses strictly from observed evidence + memory patterns."""

        self._hypotheses = generate_core_hypotheses(
            self._evidence,
            context_label=self._context,
            patterns=self.memory.statements(),
        )
        return self._hypotheses

    def verify(
        self,
        *,
        simulation_agreement: float | None = None,
        min_confidence: float = 60.0,
    ) -> tuple[VerifiedCoreExplanation, ...]:
        """Accept hypotheses only with graph / history / simulation support."""

        self._simulation_agreement = simulation_agreement
        self._verified = verify_core_hypotheses(
            self._hypotheses,
            self._evidence,
            simulation_agreement=simulation_agreement,
            min_confidence=min_confidence,
        )
        return self._verified

    def plan(self) -> tuple[CognitionPlan, ...]:
        """Generate simulation-backed recommendation plans (never executes)."""

        self._plans = generate_cognition_plans(
            verified=self._verified,
            simulation_agreement=self._simulation_agreement,
            context_label=self._context,
        )
        return self._plans

    def state(self, *, now: datetime | None = None) -> CognitionState:
        """Assemble the current immutable CognitionState."""

        stamp = now or datetime.now(UTC)
        if self._verified:
            conf = sum(v.confidence for v in self._verified) / len(self._verified)
        elif self._hypotheses:
            conf = (
                sum(h.confidence for h in self._hypotheses)
                / len(self._hypotheses)
                * 0.5
            )
        else:
            conf = 0.0
        return CognitionState(
            context=self._context,
            active_hypotheses=self._hypotheses,
            verified_explanations=self._verified,
            confidence=round(conf, 2),
            timestamp=stamp,
            evidence=self._evidence,
            plans=self._plans,
        )

    def run(
        self,
        *,
        graph: ResourceGraph | None = None,
        history: Sequence[TelemetryPoint] = (),
        context: Mapping[str, Any] | object | str | None = None,
        twin_summaries: Sequence[str] = (),
        simulation_agreement: float | None = None,
        now: datetime | None = None,
    ) -> CognitionState:
        """Full observe → reason → verify → plan cycle → CognitionState."""

        self.observe(
            graph=graph,
            history=history,
            context=context,
            twin_summaries=twin_summaries,
            now=now,
        )
        self.reason()
        self.verify(simulation_agreement=simulation_agreement)
        self.plan()
        return self.state(now=now)
