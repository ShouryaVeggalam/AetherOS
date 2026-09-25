"""Hypothesis Engine — generate research hypotheses for Genesis.

Produces multiple candidates with initial confidence. Never executes
changes; hypotheses are passed into simulation only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1


@dataclass(frozen=True, slots=True)
class ResearchQuestion:
    """Immutable research question posed to Genesis."""

    question: str
    focus_workload: str
    focus_resource: str
    asked_at: datetime


@dataclass(frozen=True, slots=True)
class ResearchHypothesis:
    """One immutable research hypothesis.

    Attributes:
        hypothesis_id: Stable id derived from the question + stance.
        title: Short label.
        claim: Testable claim.
        stance: Machine stance (increase_cache, reduce_batch, …).
        initial_confidence: Prior belief in [0, 1].
        rationale: Why this hypothesis was proposed.
        expected_cpu_delta: Simulation strategy delta.
        expected_memory_delta: Simulation strategy delta.
        expected_efficiency_delta: Simulation strategy delta.
    """

    hypothesis_id: str
    title: str
    claim: str
    stance: str
    initial_confidence: float
    rationale: str
    expected_cpu_delta: float
    expected_memory_delta: float
    expected_efficiency_delta: float

    def __post_init__(self) -> None:
        """Clamp confidence."""

        if not 0.0 <= self.initial_confidence <= 1.0:
            raise ValueError("initial_confidence must be in [0, 1]")


@dataclass
class HypothesisEngine:
    """Generate multiple research hypotheses from a question."""

    def propose(self, question: ResearchQuestion) -> tuple[ResearchHypothesis, ...]:
        """Create a diverse hypothesis set for simulation."""

        q = question.question.strip()
        if not q:
            raise ValueError("question must be non-empty")
        base = _hid(q)
        templates = (
            (
                "increase_cache",
                "Increase Cache Allocation",
                (
                    f"Increasing cache allocation for {question.focus_workload} "
                    f"would reduce latency on {question.focus_resource}."
                ),
                0.62,
                "Cache hits typically cut compile/fetch stalls.",
                -12.0,
                -2.0,
                4.0,
            ),
            (
                "defer_background",
                "Defer Background Indexing",
                (
                    f"Deferring background work during {question.focus_workload} "
                    "would improve interactive latency."
                ),
                0.55,
                "Background indexing often contends for CPU with compile loops.",
                -10.0,
                -1.0,
                8.0,
            ),
            (
                "pin_affinity",
                "CPU Affinity Pinning",
                (
                    f"Pinning {question.focus_workload} threads would stabilize "
                    f"{question.focus_resource} latency."
                ),
                0.48,
                "Affinity can reduce cross-core cache thrash in simulation.",
                -6.0,
                0.0,
                -2.0,
            ),
            (
                "no_change",
                "Null / No Change",
                (
                    f"No allocation change for {question.focus_workload} yields "
                    "material latency improvement."
                ),
                0.35,
                "Control hypothesis — expected weak effect.",
                0.0,
                0.0,
                0.0,
            ),
        )
        hyps: list[ResearchHypothesis] = []
        for stance, title, claim, conf, rationale, cpu, mem, eff in templates:
            hyps.append(
                ResearchHypothesis(
                    hypothesis_id=f"{base}:{stance}",
                    title=title,
                    claim=claim,
                    stance=stance,
                    initial_confidence=conf,
                    rationale=rationale,
                    expected_cpu_delta=cpu,
                    expected_memory_delta=mem,
                    expected_efficiency_delta=eff,
                )
            )
        return tuple(hyps)


def default_question(
    text: str = "Would increasing cache allocation reduce compile latency?",
) -> ResearchQuestion:
    """Build the canonical Genesis research question."""

    return ResearchQuestion(
        question=text,
        focus_workload="workload.compile",
        focus_resource="resource.cache",
        asked_at=datetime.now(UTC),
    )


def _hid(question: str) -> str:
    """Stable short hash prefix for hypothesis ids."""

    return sha1(question.encode("utf-8")).hexdigest()[:10]
