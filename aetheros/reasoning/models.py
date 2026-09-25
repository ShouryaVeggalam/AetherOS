"""Graph Reasoning Engine models — immutable explanation contracts.

Every field is derived from ResourceGraph traversal or measurable agreement
signals. No fabricated relationships.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aetheros.explainability.models import Evidence
from aetheros.graph.models import ResourceEdge, ResourceNode


@dataclass(frozen=True, slots=True)
class Observation:
    """One measurable system observation to explain.

    Attributes:
        metric: Resource key (``cpu``, ``memory``, ``disk``, …).
        value: Observed magnitude (typically a percent).
        title: Operator-facing observation label.
        threshold: Pressure threshold that triggered analysis.
    """

    metric: str
    value: float
    title: str
    threshold: float = 90.0


@dataclass(frozen=True, slots=True)
class ReasoningPath:
    """One immutable directed path through the Resource Graph.

    Attributes:
        source: Start node id.
        target: End node id.
        edges: Ordered edges along the path.
        nodes: Ordered nodes including endpoints.
        depth: Number of edges (``len(edges)``).
    """

    source: str
    target: str
    edges: tuple[ResourceEdge, ...]
    nodes: tuple[ResourceNode, ...]
    depth: int

    def __post_init__(self) -> None:
        """Reject inconsistent path geometry."""

        if self.depth != len(self.edges):
            raise ValueError("depth must equal len(edges)")
        expected_nodes = 1 if self.depth == 0 else self.depth + 1
        if len(self.nodes) != expected_nodes:
            raise ValueError("nodes length must equal depth + 1")


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """One candidate explanation grounded in graph paths.

    Attributes:
        id: Stable hypothesis id.
        title: Short label (e.g. process name + pressure).
        description: Operator-facing statement.
        supporting_paths: Graph paths that support the claim.
        confidence: Provisional score 0–100 before verification.
    """

    id: str
    title: str
    description: str
    supporting_paths: tuple[ReasoningPath, ...]
    confidence: int

    def __post_init__(self) -> None:
        """Reject confidence outside 0–100."""

        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class VerifiedExplanation:
    """Verified, explainable outcome of graph reasoning.

    Attributes:
        summary: Final conclusion sentence.
        evidence: Traceable Evidence facts (graph / telemetry / history).
        reasoning_paths: Supporting graph paths.
        confidence: Final confidence 0–100.
        timestamp: When verification completed (UTC).
        observation: The observation that was explained.
        rejected: Titles of hypotheses rejected by the verifier.
    """

    summary: str
    evidence: tuple[Evidence, ...]
    reasoning_paths: tuple[ReasoningPath, ...]
    confidence: int
    timestamp: datetime
    observation: Observation
    rejected: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject confidence outside 0–100."""

        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")
