"""Discovery store — verified and rejected research discoveries.

Rejected hypotheses remain archived. Verified discoveries are immutable.
Also hosts ``AutonomousResearchEngine`` — the twin-only research orchestrator.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aetheros.memory.models import MemoryRecord
from aetheros.research_ai.executor import execute_experiment
from aetheros.research_ai.experiment import DEFAULT_ITERATIONS, build_experiment
from aetheros.research_ai.hypothesis import generate_hypothesis, generate_questions
from aetheros.research_ai.journal import ResearchJournal
from aetheros.research_ai.models import (
    Discovery,
    Experiment,
    Hypothesis,
    ResearchQuestion,
    Result,
)
from aetheros.research_ai.verifier import verify_result
from aetheros.twin.models import TwinSnapshot


class DiscoveryStore:
    """In-memory store for verified and rejected discoveries."""

    def __init__(self) -> None:
        self._verified: list[Discovery] = []
        self._rejected: list[Discovery] = []

    def add_verified(self, discovery: Discovery) -> Discovery:
        if discovery.status != "verified":
            raise ValueError("only verified discoveries may be stored as verified")
        self._verified.append(discovery)
        return discovery

    def add_rejected(self, discovery: Discovery) -> Discovery:
        rejected = discovery
        if discovery.status != "rejected":
            rejected = Discovery(
                title=discovery.title,
                summary=discovery.summary,
                reproducibility=discovery.reproducibility,
                evidence_count=discovery.evidence_count,
                confidence=discovery.confidence,
                status="rejected",
                question_id=discovery.question_id,
                experiment_id=discovery.experiment_id,
            )
        self._rejected.append(rejected)
        return rejected

    def list_verified(self, *, limit: int = 50) -> tuple[Discovery, ...]:
        items = sorted(
            self._verified,
            key=lambda d: (-d.confidence, -d.reproducibility, d.title),
        )
        return tuple(items[: max(0, limit)])

    def list_rejected(self, *, limit: int = 50) -> tuple[Discovery, ...]:
        items = sorted(
            self._rejected,
            key=lambda d: (-d.confidence, d.title),
        )
        return tuple(items[: max(0, limit)])

    def __len__(self) -> int:
        return len(self._verified)


@dataclass
class AutonomousResearchEngine:
    """Twin-only autonomous research orchestrator (advice / discovery only)."""

    store: DiscoveryStore = field(default_factory=DiscoveryStore)
    journal: ResearchJournal = field(default_factory=ResearchJournal)
    last_questions: tuple[ResearchQuestion, ...] = ()
    last_hypotheses: tuple[Hypothesis, ...] = ()
    last_experiments: tuple[Experiment, ...] = ()
    last_results: tuple[Result, ...] = ()
    default_iterations: int = DEFAULT_ITERATIONS

    def run(
        self,
        snapshot: TwinSnapshot,
        *,
        memories: Sequence[MemoryRecord] = (),
        evidence_texts: Sequence[str] = (),
        iterations: int | None = None,
        now: datetime | None = None,
        limit_questions: int = 3,
    ) -> tuple[Discovery, ...]:
        """Generate → experiment → execute (twin) → verify → journal."""

        stamp = now or datetime.now(UTC)
        iters = iterations if iterations is not None else self.default_iterations
        questions = generate_questions(
            memories=memories,
            evidence_texts=evidence_texts,
            now=stamp,
            limit=limit_questions,
        )
        self.last_questions = questions
        if not questions:
            self.last_hypotheses = ()
            self.last_experiments = ()
            self.last_results = ()
            return ()

        hypotheses: list[Hypothesis] = []
        experiments: list[Experiment] = []
        results: list[Result] = []
        verified: list[Discovery] = []

        for question in questions:
            hypothesis = generate_hypothesis(question, memories=memories)
            hypotheses.append(hypothesis)
            experiment = build_experiment(
                hypothesis,
                snapshot,
                question=question,
                iterations=iters,
                now=stamp,
            )
            experiments.append(experiment)
            result = execute_experiment(experiment, snapshot, now=stamp)
            results.append(result)
            verdict = verify_result(experiment=experiment, result=result)
            if verdict.accepted is not None:
                discovery = Discovery(
                    title=verdict.accepted.title,
                    summary=verdict.accepted.summary,
                    reproducibility=verdict.accepted.reproducibility,
                    evidence_count=verdict.accepted.evidence_count,
                    confidence=verdict.accepted.confidence,
                    status="verified",
                    question_id=question.id,
                    experiment_id=experiment.id,
                )
                self.store.add_verified(discovery)
                self.journal.record_result(experiment, result, accepted=True, now=stamp)
                verified.append(discovery)
            elif verdict.rejected is not None:
                rejected = Discovery(
                    title=verdict.rejected.title,
                    summary=verdict.rejected.summary,
                    reproducibility=verdict.rejected.reproducibility,
                    evidence_count=verdict.rejected.evidence_count,
                    confidence=verdict.rejected.confidence,
                    status="rejected",
                    question_id=question.id,
                    experiment_id=experiment.id,
                )
                self.store.add_rejected(rejected)
                self.journal.record_result(
                    experiment, result, accepted=False, now=stamp
                )

        self.last_hypotheses = tuple(hypotheses)
        self.last_experiments = tuple(experiments)
        self.last_results = tuple(results)
        return tuple(verified)
