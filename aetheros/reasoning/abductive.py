"""Abductive reasoning — infer plausible causes from observations.

Wraps hypothesis generation with a pure functional façade.
"""

from __future__ import annotations

from aetheros.cognition.hypotheses import (
    HypothesisSet,
    Observation,
    generate_hypotheses,
)
from aetheros.cognition.memory import CognitiveMemory
from aetheros.observatory.models import TelemetryPoint


def abduct(
    observation: Observation,
    *,
    memory: CognitiveMemory | None = None,
    history: tuple[TelemetryPoint, ...] = (),
    top_processes: tuple[str, ...] = (),
) -> HypothesisSet:
    """Generate abductive hypotheses for an observation."""

    return generate_hypotheses(
        observation,
        memory=memory,
        history=history,
        top_processes=top_processes,
    )
