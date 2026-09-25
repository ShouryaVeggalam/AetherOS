"""Research verifier — accept discoveries only with evidence gates.

Gates:
* Statistical consistency (stability / confidence floors)
* Simulation reproducibility threshold
* Reasoning agreement (expected outcome cues vs metrics)
* Minimum evidence count
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.research_ai.models import Discovery, Experiment, Hypothesis, Result


@dataclass(frozen=True, slots=True)
class VerificationVerdict:
    """Outcome of verifying one experiment result."""

    accepted: Discovery | None
    rejected: Discovery | None
    reasons: tuple[str, ...]


def verify_result(
    *,
    experiment: Experiment,
    result: Result,
    hypothesis: Hypothesis | None = None,
    min_reproducibility: float = 70.0,
    min_confidence: float = 55.0,
    min_stability: float = 40.0,
    min_evidence: int = 2,
) -> VerificationVerdict:
    """Accept or reject a discovery from twin experiment results."""

    hypo = hypothesis or experiment.hypothesis
    reasons: list[str] = []
    repro = result.reproducibility

    if repro < min_reproducibility:
        reasons.append(
            f"reproducibility {repro:.1f}% < minimum {min_reproducibility:.1f}%"
        )
    if result.confidence < min_confidence:
        reasons.append(
            f"confidence {result.confidence:.1f} < minimum {min_confidence:.1f}"
        )
    if result.stability < min_stability:
        reasons.append(
            f"stability {result.stability:.1f} < minimum {min_stability:.1f}"
        )
    if len(result.evidence) < min_evidence:
        reasons.append(
            f"evidence_count {len(result.evidence)} < minimum {min_evidence}"
        )
    if not _reasoning_agrees(hypo, result):
        reasons.append("reasoning does not agree with expected outcome cues")

    title = _discovery_title(hypo)
    summary = _discovery_summary(hypo, result)
    base = Discovery(
        title=title,
        summary=summary,
        reproducibility=repro,
        evidence_count=max(1, len(result.evidence)),
        confidence=result.confidence,
        status="pending",
        question_id="",
        experiment_id=experiment.id,
    )

    if reasons:
        rejected = Discovery(
            title=base.title,
            summary=base.summary,
            reproducibility=base.reproducibility,
            evidence_count=base.evidence_count,
            confidence=base.confidence,
            status="rejected",
            question_id=base.question_id,
            experiment_id=base.experiment_id,
        )
        return VerificationVerdict(
            accepted=None,
            rejected=rejected,
            reasons=tuple(reasons),
        )

    accepted = Discovery(
        title=base.title,
        summary=base.summary,
        reproducibility=base.reproducibility,
        evidence_count=base.evidence_count,
        confidence=base.confidence,
        status="verified",
        question_id=base.question_id,
        experiment_id=base.experiment_id,
    )
    return VerificationVerdict(
        accepted=accepted,
        rejected=None,
        reasons=(
            "Passed reproducibility, confidence, stability, and reasoning gates.",
        ),
    )


def _reasoning_agrees(hypothesis: Hypothesis, result: Result) -> bool:
    expected = hypothesis.expected_outcome.lower()
    metrics = dict(result.metrics)
    evidence_blob = " ".join(result.evidence).lower()

    if "latency" in expected or "disk" in expected:
        return metrics.get("disk_delta", 0.0) != 0.0 or "disk" in evidence_blob
    if "memory" in expected:
        return metrics.get("memory_delta", 0.0) != 0.0 or "memory" in evidence_blob
    if "cpu" in expected or "thermal" in expected:
        return metrics.get("cpu_delta", 0.0) != 0.0 or "cpu" in evidence_blob
    if "stability" in expected:
        return result.stability > 0.0
    # Generic: any non-zero twin delta or evidence present.
    return any(abs(v) > 0.01 for v in metrics.values()) or bool(result.evidence)


def _discovery_title(hypothesis: Hypothesis) -> str:
    statement = hypothesis.statement.strip()
    if len(statement) > 96:
        return statement[:93] + "..."
    return statement


def _discovery_summary(hypothesis: Hypothesis, result: Result) -> str:
    metrics = dict(result.metrics)
    cpu_delta = metrics.get("cpu_delta", 0.0)
    disk_delta = metrics.get("disk_delta", 0.0)
    mem_delta = metrics.get("memory_delta", 0.0)
    return (
        f"{hypothesis.statement} Twin runs ({result.successful_iterations}/"
        f"{result.total_iterations}) show cpuΔ={cpu_delta:+.1f}, "
        f"memΔ={mem_delta:+.1f}, diskΔ={disk_delta:+.1f} "
        f"(stability {result.stability:.0f}%, confidence {result.confidence:.0f}%)."
    )
