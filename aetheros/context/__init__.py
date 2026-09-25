"""Context Intelligence Engine — single operational GraphContext aggregate.

P8 integration layer. Does not rewrite telemetry, prediction, reasoning,
simulation, or dashboard modules.
"""

from aetheros.context.adapters import (
    PredictionContextView,
    ReasoningContextView,
    SimulationContextView,
    for_prediction,
    for_reasoning,
    for_simulation,
)
from aetheros.context.builder import build_context
from aetheros.context.engine import ContextEngine
from aetheros.context.formatter import ContextPanel
from aetheros.context.history import match_historical_pattern
from aetheros.context.intent import resolve_intent
from aetheros.context.models import (
    GraphContext,
    HistoricalPattern,
    IntentContext,
    IntentName,
    IntentSource,
)
from aetheros.context.resolver import (
    resolve_historical_match,
    resolve_operational_intent,
)

__all__ = [
    "ContextEngine",
    "ContextPanel",
    "GraphContext",
    "HistoricalPattern",
    "IntentContext",
    "IntentName",
    "IntentSource",
    "PredictionContextView",
    "ReasoningContextView",
    "SimulationContextView",
    "build_context",
    "for_prediction",
    "for_reasoning",
    "for_simulation",
    "match_historical_pattern",
    "resolve_historical_match",
    "resolve_intent",
    "resolve_operational_intent",
]
