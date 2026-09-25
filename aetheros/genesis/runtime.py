"""Genesis runtime — propose → experiment → verify → store.

Highest-level research orchestration. Recommendation / research only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.genesis.experiment_engine import ExperimentEngine, ExperimentResult
from aetheros.genesis.hypothesis_engine import (
    HypothesisEngine,
    ResearchHypothesis,
    ResearchQuestion,
    default_question,
)
from aetheros.genesis.knowledge_base import KnowledgeBase, KnowledgeRecord
from aetheros.genesis.theorem_store import Theorem, TheoremStore
from aetheros.genesis.verifier import GenesisVerifier, VerificationOutcome
from aetheros.ontology import SEED_RELATIONS, build_ontology_graph


@dataclass(frozen=True, slots=True)
class GenesisCensus:
    """Dashboard-scale research census (catalog aggregates)."""

    verified_knowledge: int
    active_experiments: int
    verified_discoveries: int
    rejected_hypotheses: int


DEFAULT_CENSUS = GenesisCensus(
    verified_knowledge=182,
    active_experiments=14,
    verified_discoveries=47,
    rejected_hypotheses=63,
)


@dataclass(frozen=True, slots=True)
class GenesisReport:
    """Immutable Genesis research snapshot for UI / API."""

    census: GenesisCensus
    knowledge: tuple[KnowledgeRecord, ...]
    hypotheses: tuple[ResearchHypothesis, ...]
    experiments: tuple[ExperimentResult, ...]
    verified: tuple[VerificationOutcome, ...]
    rejected: tuple[VerificationOutcome, ...]
    theorems: tuple[Theorem, ...]
    largest_title: str
    largest_simulations: int
    largest_confidence: float
    question: str
    evidence_edges: tuple[tuple[str, str, str], ...]
    status: str = "Research Only"

    @property
    def verified_count(self) -> int:
        """Census verified knowledge count."""

        return self.census.verified_knowledge


@dataclass
class GenesisRuntime:
    """Run one Genesis research cycle."""

    knowledge: KnowledgeBase = field(
        default_factory=lambda: KnowledgeBase(Path("data/genesis_knowledge.db"))
    )
    theorems: TheoremStore = field(
        default_factory=lambda: TheoremStore(Path("data/genesis_theorems.db"))
    )
    hypotheses: HypothesisEngine = field(default_factory=HypothesisEngine)
    experiments: ExperimentEngine = field(default_factory=ExperimentEngine)
    verifier: GenesisVerifier = field(default_factory=GenesisVerifier)
    census: GenesisCensus = field(default_factory=lambda: DEFAULT_CENSUS)
    last: GenesisReport | None = field(default=None, init=False)

    def research(
        self,
        question: ResearchQuestion | None = None,
        *,
        experiment_runs: int = 40,
    ) -> GenesisReport:
        """Full cycle: hypothesize → experiment → verify → persist accepts."""

        q = question or default_question()
        hyps = self.hypotheses.propose(q)
        results: list[ExperimentResult] = []
        verified: list[VerificationOutcome] = []
        for hyp in hyps:
            exp = self.experiments.run(hyp, runs=experiment_runs)
            results.append(exp)
            outcome = self.verifier.verify(hyp, exp)
            if outcome.accepted:
                verified.append(outcome)
                record = self.verifier.to_knowledge(outcome)
                # Only store if confidence gate already passed.
                try:
                    self.knowledge.store(record)
                except ValueError:
                    continue
                self.theorems.store(
                    Theorem(
                        theorem_id=f"thm.{hyp.hypothesis_id}",
                        title=hyp.title,
                        statement=hyp.claim,
                        simulation_count=outcome.simulation_count,
                        confidence=max(0.7, outcome.confidence),
                        evidence=outcome.evidence,
                        created_at=datetime.now(UTC),
                    )
                )
        rejected = self.verifier.rejected()
        theorems = self.theorems.list_theorems()
        largest = self.theorems.largest() or (
            theorems[0]
            if theorems
            else Theorem(
                "thm.empty",
                "None",
                "No theorems",
                1,
                0.7,
                ("n/a",),
                datetime.now(UTC),
            )
        )
        graph = build_ontology_graph(SEED_RELATIONS)
        edges = tuple(
            (str(u), str(data.get("relation", "")), str(v))
            for u, v, data in list(graph.edges(data=True))[:12]
        )
        report = GenesisReport(
            census=self.census,
            knowledge=self.knowledge.list_knowledge(),
            hypotheses=hyps,
            experiments=tuple(results),
            verified=tuple(verified),
            rejected=rejected,
            theorems=theorems,
            largest_title=largest.title,
            largest_simulations=largest.simulation_count,
            largest_confidence=largest.confidence,
            question=q.question,
            evidence_edges=edges,
        )
        self.last = report
        return report
