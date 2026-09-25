"""Infinity intelligence pipeline — ordered explainable stages.

Maps the platform principle: observe → evidence → reason → simulate →
predict → explain → recommend → human approval.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PipelineStage:
    """One immutable stage in the operating-intelligence pipeline."""

    stage_id: str
    name: str
    package: str
    description: str
    produces: str


PIPELINE: tuple[PipelineStage, ...] = (
    PipelineStage(
        "telemetry",
        "Telemetry",
        "aetheros.telemetry",
        "Collect immutable host metrics.",
        "SystemSnapshot / TelemetrySnapshot",
    ),
    PipelineStage(
        "observatory",
        "Observatory",
        "aetheros.observatory",
        "Record temporal history and events.",
        "TelemetryPoint history",
    ),
    PipelineStage(
        "evidence",
        "Evidence",
        "aetheros.explainability",
        "Attach measurable evidence to claims.",
        "EvidenceChain",
    ),
    PipelineStage(
        "reasoning",
        "Reasoning",
        "aetheros.cognition / aetheros.reasoning",
        "Causal / abductive / deductive systems reasoning.",
        "Hypotheses + causal graph",
    ),
    PipelineStage(
        "simulation",
        "Simulation",
        "aetheros.simulation / aetheros.twin",
        "What-if scoring without side effects.",
        "SimulationResult / TwinOutcome",
    ),
    PipelineStage(
        "prediction",
        "Prediction",
        "aetheros.predictive / aetheros.sentinel",
        "Forecast load and cascading risk.",
        "Forecast / CascadePrediction",
    ),
    PipelineStage(
        "explainability",
        "Explainability",
        "aetheros.explainability / aetheros.genesis",
        "Narrative confidence and verified knowledge.",
        "Explanation / KnowledgeRecord",
    ),
    PipelineStage(
        "recommendation",
        "Recommendation",
        "aetheros.decision / aetheros.orchestrator / aetheros.sentinel",
        "Ranked operator advice.",
        "Decision / RecoveryStrategy",
    ),
    PipelineStage(
        "human_approval",
        "Human Approval",
        "aetheros.safety / dashboard",
        "Operators approve; platform never auto-executes.",
        "Audit log entry",
    ),
)
