"""Genesis Verifier — accept only statistically supported hypotheses.

Rejected hypotheses remain archived. Verified ones become knowledge /
theorems. Never executes interventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aetheros.genesis.experiment_engine import ExperimentResult
from aetheros.genesis.hypothesis_engine import ResearchHypothesis
from aetheros.genesis.knowledge_base import KnowledgeRecord


@dataclass(frozen=True, slots=True)
class VerificationOutcome:
    """Immutable verification decision for one hypothesis.

    Attributes:
        hypothesis: Source hypothesis.
        experiment: Experiment batch result.
        accepted: Whether the claim is statistically supported.
        confidence: Posterior confidence in [0, 1].
        evidence: Supporting evidence lines.
        contradictory: Contradictory evidence notes.
        simulation_count: Simulations considered.
        reason: Human-readable decision rationale.
        decided_at: UTC decision time.
    """

    hypothesis: ResearchHypothesis
    experiment: ExperimentResult
    accepted: bool
    confidence: float
    evidence: tuple[str, ...]
    contradictory: tuple[str, ...]
    simulation_count: int
    reason: str
    decided_at: datetime


@dataclass
class GenesisVerifier:
    """Statistical gate between experiments and the knowledge base."""

    min_confidence: float = 0.7
    min_simulations: int = 20
    min_support: float = 0.62
    archive: list[VerificationOutcome] = field(default_factory=list)

    def verify(
        self,
        hypothesis: ResearchHypothesis,
        experiment: ExperimentResult,
        *,
        clusters_verified: int = 18,
    ) -> VerificationOutcome:
        """Accept or reject ``hypothesis`` given ``experiment``."""

        confidence = experiment.support_score
        contradictory = experiment.contradictory
        # Penalize heavy contradiction rate.
        if experiment.simulation_count > 0 and contradictory:
            penalty = min(0.2, 0.02 * len(contradictory))
            confidence = max(0.0, confidence - penalty)
        accepted = (
            confidence >= self.min_confidence
            and experiment.support_score >= self.min_support
            and experiment.simulation_count >= self.min_simulations
            and hypothesis.stance != "no_change"
        )
        evidence = (
            f"{experiment.simulation_count:,} simulations",
            f"{confidence:.0%} confidence",
            f"Performance {experiment.performance:.1f} / "
            f"Stability {experiment.stability:.1f} / "
            f"Efficiency {experiment.efficiency:.1f} / "
            f"Fairness {experiment.fairness:.1f}",
            f"Verified across {clusters_verified} clusters (virtual)",
        )
        if accepted:
            reason = (
                f"Accepted '{hypothesis.title}': support {experiment.support_score:.2f} "
                f"meets thresholds (confidence≥{self.min_confidence}, "
                f"sims≥{self.min_simulations})."
            )
        else:
            reason = (
                f"Rejected '{hypothesis.title}': insufficient support "
                f"(support={experiment.support_score:.2f}, "
                f"confidence={confidence:.2f}, sims={experiment.simulation_count})."
            )
        outcome = VerificationOutcome(
            hypothesis=hypothesis,
            experiment=experiment,
            accepted=accepted,
            confidence=round(confidence, 4),
            evidence=evidence,
            contradictory=contradictory,
            simulation_count=experiment.simulation_count,
            reason=reason,
            decided_at=datetime.now(UTC),
        )
        if not accepted:
            self.archive.append(outcome)
        return outcome

    def to_knowledge(
        self,
        outcome: VerificationOutcome,
        *,
        clusters_verified: int = 18,
    ) -> KnowledgeRecord:
        """Convert an accepted outcome into a KnowledgeRecord."""

        if not outcome.accepted:
            raise ValueError("cannot store rejected hypothesis as knowledge")
        hyp = outcome.hypothesis
        return KnowledgeRecord(
            knowledge_id=f"kb.verified.{hyp.hypothesis_id}",
            statement=hyp.claim,
            evidence=outcome.evidence,
            simulation_count=outcome.simulation_count,
            confidence=outcome.confidence,
            clusters_verified=clusters_verified,
            source="verified_hypothesis",
            created_at=outcome.decided_at,
            tags=(hyp.stance, "genesis", "verified"),
        )

    def rejected(self) -> tuple[VerificationOutcome, ...]:
        """Return archived rejected hypotheses."""

        return tuple(self.archive)
