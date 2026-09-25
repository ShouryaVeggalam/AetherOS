"""Infinity runtime — unify generation health into one explainable report.

Composes existing runtimes without replacing them. Read-only observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aetheros.fabric import FabricRuntime
from aetheros.genesis import GenesisRuntime
from aetheros.genesis.knowledge_base import KnowledgeBase
from aetheros.genesis.theorem_store import TheoremStore
from aetheros.horizon import HorizonRuntime
from aetheros.infinity.generations import GENERATIONS, Generation
from aetheros.infinity.pipeline import PIPELINE, PipelineStage
from aetheros.kernel import KernelIntelligence
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.sentinel import SentinelRuntime


@dataclass(frozen=True, slots=True)
class LayerStatus:
    """Immutable health line for one intelligence layer."""

    name: str
    ready: bool
    detail: str


@dataclass(frozen=True, slots=True)
class InfinityReport:
    """Platform-wide Infinity snapshot for UI / API / docs."""

    generations: tuple[Generation, ...]
    pipeline: tuple[PipelineStage, ...]
    layers: tuple[LayerStatus, ...]
    principles: tuple[str, ...]
    identity: str
    status: str = "Explainable Operating Intelligence · Human-in-the-loop"

    @property
    def generation_count(self) -> int:
        """Number of catalogued generations including Infinity."""

        return len(self.generations)

    @property
    def layers_ready(self) -> int:
        """Count of ready layers."""

        return sum(1 for layer in self.layers if layer.ready)


PRINCIPLES: tuple[str, ...] = (
    "Observe before acting.",
    "Explain every recommendation.",
    "Simulation before intervention.",
    "Humans remain in control.",
    "Immutable telemetry.",
    "Research-grade architecture.",
    "Modular by design.",
)


@dataclass
class InfinityRuntime:
    """Observe all major layers and assemble an InfinityReport."""

    horizon: HorizonRuntime = field(default_factory=HorizonRuntime)
    genesis: GenesisRuntime | None = None
    sentinel: SentinelRuntime = field(default_factory=SentinelRuntime)
    fabric: FabricRuntime | None = None
    kernel: KernelIntelligence = field(default_factory=KernelIntelligence)
    last: InfinityReport | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Wire optional SQLite-backed runtimes with default paths."""

        if self.genesis is None:
            self.genesis = GenesisRuntime(
                knowledge=KnowledgeBase(Path("data/genesis_knowledge.db")),
                theorems=TheoremStore(Path("data/genesis_theorems.db")),
            )
        if self.fabric is None:
            self.fabric = FabricRuntime(
                knowledge=KnowledgeBase(Path("data/genesis_knowledge.db"))
            )

    def observe(
        self,
        snapshot: TelemetrySnapshot | None = None,
    ) -> InfinityReport:
        """Probe layer readiness and return an immutable InfinityReport."""

        assert self.genesis is not None
        assert self.fabric is not None
        layers: list[LayerStatus] = []

        horizon_report = self.horizon.observe()
        layers.append(
            LayerStatus(
                "Horizon",
                True,
                f"world health {horizon_report.world_health:.1f}%",
            )
        )

        genesis_report = self.genesis.research(experiment_runs=4)
        layers.append(
            LayerStatus(
                "Genesis",
                True,
                f"knowledge {len(genesis_report.knowledge)} · "
                f"largest {genesis_report.largest_simulations:,} sims",
            )
        )

        from datetime import UTC, datetime

        snap = snapshot or TelemetrySnapshot(
            timestamp=datetime.now(UTC),
            cpu_percent=45.0,
            memory_percent=50.0,
            disk_percent=40.0,
            battery_percent=80.0,
            process_count=3,
            top_processes=("python", "Cursor", "chrome"),
        )
        sentinel_report = self.sentinel.observe(snap)
        layers.append(
            LayerStatus(
                "Sentinel",
                True,
                f"health {sentinel_report.health:.0f} · risk {sentinel_report.risk}",
            )
        )

        fabric_report = self.fabric.observe()
        layers.append(
            LayerStatus(
                "Fabric",
                True,
                f"nodes {fabric_report.connected_nodes:,} · "
                f"sync {fabric_report.synchronization:.2f}%",
            )
        )

        ctx = self.kernel.context()
        layers.append(
            LayerStatus(
                "Kernel (userspace)",
                True,
                f"{len(ctx.resources)} resources · {ctx.relation_count} ontology edges",
            )
        )

        report = InfinityReport(
            generations=GENERATIONS,
            pipeline=PIPELINE,
            layers=tuple(layers),
            principles=PRINCIPLES,
            identity=(
                "AetherOS is an Explainable Operating Intelligence Platform — "
                "not an OS, kernel, or autonomous controller."
            ),
        )
        self.last = report
        return report
