"""Aether Agent — lightweight local telemetry publisher for the cluster bus."""

from __future__ import annotations

from aetheros.agent.collector import AgentCollector, AgentSnapshot, stable_node_id
from aetheros.agent.publisher import (
    AgentPublisher,
    SyntheticPeer,
    default_demo_peers,
)

__all__ = [
    "AgentCollector",
    "AgentPublisher",
    "AgentSnapshot",
    "SyntheticPeer",
    "default_demo_peers",
    "stable_node_id",
]
