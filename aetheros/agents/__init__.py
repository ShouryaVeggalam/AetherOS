"""Agentic specialists and coordinator for multi-agent deliberation.

P4 adds a synchronous ConsensusEngine + EventBus overlay. Legacy
AgenticRuntime (dashboard M) is unchanged.
"""

from aetheros.agents.base import (
    AgentFinding,
    AgentStatus,
    BaseAgent,
    Conflict,
    ConsensusFinding,
    DeliberationContext,
)
from aetheros.agents.battery import BatteryAgent
from aetheros.agents.bus import BROADCAST, EventBus
from aetheros.agents.cluster_agent import ClusterAgent
from aetheros.agents.coordinator import (
    ConsensusDecision,
    ConsensusEngine,
    Coordinator,
    CoordinatorDecision,
    detect_conflicts,
)
from aetheros.agents.events import Event, make_consensus_event
from aetheros.agents.formatter import ConsensusPanel
from aetheros.agents.performance import PerformanceAgent
from aetheros.agents.renderer import MultiAgentPanel
from aetheros.agents.report import AgenticReport, AgentStatusRow
from aetheros.agents.research import ResearchAgent
from aetheros.agents.security import SecurityAgent
from aetheros.agents.telemetry import TelemetryAgent

__all__ = [
    "BROADCAST",
    "AgentFinding",
    "AgentStatus",
    "AgentStatusRow",
    "AgenticReport",
    "BaseAgent",
    "BatteryAgent",
    "ClusterAgent",
    "Conflict",
    "ConsensusDecision",
    "ConsensusEngine",
    "ConsensusFinding",
    "ConsensusPanel",
    "Coordinator",
    "CoordinatorDecision",
    "DeliberationContext",
    "Event",
    "EventBus",
    "MultiAgentPanel",
    "PerformanceAgent",
    "ResearchAgent",
    "SecurityAgent",
    "TelemetryAgent",
    "detect_conflicts",
    "make_consensus_event",
]
