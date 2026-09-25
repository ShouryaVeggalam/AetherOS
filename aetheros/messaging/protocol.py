"""Shared agent messaging protocol constants and helpers.

Centralizing names prevents drift between publishers and consumers.
Payload helpers keep event bodies consistent without a schema library.
"""

from __future__ import annotations

from typing import Any, Literal

# Broadcast address — every subscribed agent may receive the event.
BROADCAST = "*"

AgentId = Literal[
    "telemetry",
    "performance",
    "battery",
    "security",
    "cluster",
    "research",
    "coordinator",
]

EventType = Literal[
    "deliberation.request",
    "agent.finding",
    "agent.status",
    "coordinator.decision",
    "conflict.detected",
]

ALL_AGENT_IDS: tuple[AgentId, ...] = (
    "telemetry",
    "performance",
    "battery",
    "security",
    "cluster",
    "research",
    "coordinator",
)


def finding_payload(
    *,
    stance: str,
    summary: str,
    confidence: float,
    priority: float,
    metrics: dict[str, float] | None = None,
    evidence: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build a standard agent.finding payload.

    Args:
        stance: Short recommendation stance (e.g. ``increase_cpu``).
        summary: Human-readable finding.
        confidence: Belief in [0, 1].
        priority: Urgency weight in [0, 1].
        metrics: Optional numeric support values.
        evidence: Public systems evidence strings.
    """

    return {
        "stance": stance,
        "summary": summary,
        "confidence": max(0.0, min(1.0, confidence)),
        "priority": max(0.0, min(1.0, priority)),
        "metrics": dict(metrics or {}),
        "evidence": list(evidence),
    }


def decision_payload(
    *,
    recommendation: str,
    confidence: float,
    reasoning: str,
    consensus: bool,
    supporting_agents: tuple[str, ...],
    conflicting_agents: tuple[str, ...],
) -> dict[str, Any]:
    """Build a coordinator.decision payload."""

    return {
        "recommendation": recommendation,
        "confidence": max(0.0, min(1.0, confidence)),
        "reasoning": reasoning,
        "consensus": consensus,
        "supporting_agents": list(supporting_agents),
        "conflicting_agents": list(conflicting_agents),
    }
