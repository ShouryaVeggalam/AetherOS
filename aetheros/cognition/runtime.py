"""Cognitive runtime — observe → hypothesize → verify → plan → explain.

Central orchestrator for v3 cognition. Recommendation-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.cognition.causal_graph import (
    CausalGraph,
    CausalGraphBuilder,
    GraphEdge,
    GraphNode,
)
from aetheros.cognition.hypotheses import (
    HypothesisSet,
    Observation,
    generate_hypotheses,
    observe_from_snapshot,
)
from aetheros.cognition.memory import CognitiveFact, CognitiveMemory
from aetheros.cognition.planner import CognitivePlanner
from aetheros.cognition.report import CognitiveReport, build_cognitive_report
from aetheros.cognition.verifier import VerifiedExplanation, verify_hypotheses
from aetheros.intent.models import IntentProfile
from aetheros.knowledge.resource_types import ResourceKind
from aetheros.knowledge.workload_graph import WORKLOAD_EDGES
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot


@dataclass
class CognitiveRuntime:
    """Run one cognitive cycle against live telemetry and history."""

    memory: CognitiveMemory = field(
        default_factory=lambda: CognitiveMemory(Path("data/cognition_memory.db"))
    )
    planner: CognitivePlanner = field(default_factory=CognitivePlanner)

    def build_graph(
        self,
        snapshot: TelemetrySnapshot,
        *,
        intent_name: str,
    ) -> CausalGraph:
        """Construct a causal graph snapshot from knowledge + live metrics."""

        builder = CausalGraphBuilder()
        for kind, label, load in (
            ("cpu", "CPU", snapshot.cpu_percent),
            ("memory", "Memory", snapshot.memory_percent),
            ("disk", "Disk", snapshot.disk_percent),
        ):
            builder.add_node(
                GraphNode(
                    f"resource:{kind}",
                    kind,  # type: ignore[arg-type]
                    label,
                    (("load", f"{load:.1f}"),),
                )
            )
        builder.add_node(
            GraphNode("resource:network", "network", "Network", (("latency", "n/a"),))
        )
        builder.add_node(
            GraphNode(
                "intent:active",
                "intent",
                intent_name,
                (("profile", intent_name),),
            )
        )
        builder.add_node(
            GraphNode(
                "simulation:active",
                "simulation",
                "Simulation",
                (("mode", "what-if"),),
            )
        )
        known = {
            "resource:cpu",
            "resource:memory",
            "resource:disk",
            "resource:network",
            "intent:active",
            "simulation:active",
        }
        for index, name in enumerate(snapshot.top_processes[:5]):
            node_id = f"process:{name}:{index}"
            builder.add_node(GraphNode(node_id, "process", name, ()))
            known.add(node_id)
            builder.add_edge(
                GraphEdge(
                    node_id,
                    "resource:cpu",
                    "USES",
                    0.5,
                    f"{name} contended for CPU in the latest sample.",
                )
            )
        builder.add_edge(
            GraphEdge(
                "intent:active",
                "resource:cpu",
                "EXPLAINS",
                0.4,
                f"Active intent {intent_name} shapes CPU priority advice.",
            )
        )
        for edge in WORKLOAD_EDGES:
            source = f"knowledge:{edge.workload_id}"
            target = f"resource:{edge.resource}"
            if source not in known:
                rk: ResourceKind = (
                    "process" if edge.workload_id.startswith("process.") else "intent"
                )
                builder.add_node(GraphNode(source, rk, edge.workload_id, ()))
                known.add(source)
            if target not in known:
                continue
            builder.add_edge(
                GraphEdge(
                    source,
                    target,
                    edge.relation,
                    edge.intensity,
                    edge.note,
                )
            )
        return builder.build()

    def reason(
        self,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
        *,
        history: tuple[TelemetryPoint, ...] = (),
    ) -> CognitiveReport:
        """Full cognitive cycle returning an immutable CognitiveReport."""

        graph = self.build_graph(snapshot, intent_name=intent.name)
        observation = observe_from_snapshot(snapshot)
        if observation is None:
            stable = Observation(
                kind="stable",
                summary="No critical resource pressure detected.",
                metric="cpu",
                value=snapshot.cpu_percent,
                timestamp=snapshot.timestamp,
            )
            empty = HypothesisSet(observation=stable, hypotheses=())
            verified = VerifiedExplanation(
                observation=stable,
                result=None,
                rejected=(),
                confidence=0,
            )
            return build_cognitive_report(
                observation=stable,
                hypotheses=empty,
                verified=verified,
                plans=None,
                graph=graph,
                memory_notes=tuple(f.notes for f in self.memory.list_facts()[:5]),
            )

        hypotheses = generate_hypotheses(
            observation,
            memory=self.memory,
            history=history,
            top_processes=snapshot.top_processes,
        )
        verified = verify_hypotheses(
            hypotheses,
            history=history,
            memory=self.memory,
        )
        plans = self.planner.plan(
            observation,
            snapshot,
            intent,
            verified=verified,
        )
        if verified.result is not None and verified.confidence >= 70:
            hyp = verified.result.hypothesis
            self.memory.remember(
                CognitiveFact(
                    fact_key=f"verified:{hyp.hypothesis_id}",
                    subject=hyp.title,
                    predicate="explains",
                    object=observation.metric,
                    confidence=verified.result.support_score,
                    source="verified_hypothesis",
                    created_at=datetime.now(UTC),
                    notes=hyp.description,
                )
            )
        return build_cognitive_report(
            observation=observation,
            hypotheses=hypotheses,
            verified=verified,
            plans=plans,
            graph=graph,
            memory_notes=tuple(f.notes for f in self.memory.list_facts()[:5]),
        )
