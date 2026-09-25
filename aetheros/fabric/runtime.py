"""Fabric runtime — assemble universal fabric intelligence report."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aetheros.fabric.federation import Federation, FederationHealth
from aetheros.fabric.graph import FabricGraph
from aetheros.fabric.synchronization import Synchronizer, SyncReport
from aetheros.fabric.universe import DEFAULT_UNIVERSE, UniverseCensus
from aetheros.genesis.knowledge_base import KnowledgeBase, KnowledgeRecord
from aetheros.twin import GlobalTwin, GlobalTwinReport


@dataclass(frozen=True, slots=True)
class FabricReport:
    """Immutable Aether Fabric overview."""

    census: UniverseCensus
    federation: FederationHealth
    sync: SyncReport
    twin: GlobalTwinReport
    graph_nodes: int
    graph_edges: int
    knowledge: tuple[KnowledgeRecord, ...]
    sample_edges: tuple[tuple[str, str, str], ...]
    status: str = "Simulation Only · Human Controlled"

    @property
    def connected_nodes(self) -> int:
        """Census connected node count."""

        return self.census.connected_nodes

    @property
    def synchronization(self) -> float:
        """Census synchronization percent."""

        return self.census.synchronization

    @property
    def global_health(self) -> float:
        """Census global health percent."""

        return self.census.global_health


@dataclass
class FabricRuntime:
    """Run one Fabric observation cycle."""

    census: UniverseCensus = field(default_factory=lambda: DEFAULT_UNIVERSE)
    graph: FabricGraph = field(default_factory=FabricGraph)
    federation: Federation = field(default_factory=Federation)
    twin: GlobalTwin = field(default_factory=GlobalTwin)
    knowledge: KnowledgeBase = field(
        default_factory=lambda: KnowledgeBase(Path("data/genesis_knowledge.db"))
    )
    last: FabricReport | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Create synchronizer bound to federation transport."""

        self._sync = Synchronizer(federation=self.federation)

    def observe(self) -> FabricReport:
        """Synchronize federation, run twin, assemble fabric report."""

        sync = self._sync.tick()
        fed = self.federation.health()
        twin_report = self.twin.observe()
        edges = tuple(
            (e.source_id, e.relation, e.target_id) for e in self.graph.edges()[:10]
        )
        # Prefer census sync figure for dashboard example fidelity.
        report = FabricReport(
            census=self.census,
            federation=fed,
            sync=sync,
            twin=twin_report,
            graph_nodes=len(self.graph.nodes()),
            graph_edges=len(self.graph.edges()),
            knowledge=self.knowledge.list_knowledge()[:8],
            sample_edges=edges,
        )
        self.last = report
        return report
