"""Unit tests for Phase 4 decision scoring, prioritization, and engine."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from aetheros.decision import DecisionEngine, prioritize, score_recommendation
from aetheros.decision.models import Decision
from aetheros.decision.prioritizer import ScoredRecommendation
from aetheros.decision.scorer import confidence_points, has_system_wide_overload
from aetheros.policy_engine import PolicyEngine, PolicyRecommendation, TelemetrySnapshot
from aetheros.policy_engine.rules import detect_cpu_overload
from aetheros.safety import AuditLogger, CooldownManager, SafetyValidator


def _snap(*, cpu: float = 50.0, memory: float = 50.0, disk: float = 40.0) -> TelemetrySnapshot:
    """Build a TelemetrySnapshot for tests."""

    return TelemetrySnapshot(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        battery_percent=None,
        process_count=3,
        top_processes=("a", "b", "c"),
    )


def _rec(
    *,
    title: str = "CPU Overload",
    level: str = "critical",
    confidence: int = 98,
    action: str = "Reduce background workload.",
) -> PolicyRecommendation:
    """Build a PolicyRecommendation for tests."""

    return PolicyRecommendation(
        level=level,  # type: ignore[arg-type]
        title=title,
        reason=f"{title} detected.",
        recommended_action=action,
        confidence=confidence,
    )


def test_confidence_points_scale() -> None:
    """Confidence 100 should contribute the full 30 points."""

    assert confidence_points(100) == 30
    assert confidence_points(0) == 0
    assert confidence_points(50) == 15


def test_critical_score_without_bonus() -> None:
    """Critical 98% confidence → 60 + ~29 = 89."""

    score = score_recommendation(_rec(confidence=98), _snap(cpu=97.0, memory=68.0))
    assert score == 89
    assert 0 <= score <= 100


def test_cooldown_penalty() -> None:
    """Recent cooldown should subtract 20 points."""

    base = score_recommendation(_rec(), _snap(cpu=97.0, memory=68.0))
    penalized = score_recommendation(
        _rec(), _snap(cpu=97.0, memory=68.0), recently_cooled=True
    )
    assert penalized == max(0, base - 20)


def test_system_wide_overload_bonus() -> None:
    """High CPU and memory together should add the overload bonus."""

    snap = _snap(cpu=90.0, memory=90.0)
    assert has_system_wide_overload(snap) is True
    with_bonus = score_recommendation(_rec(confidence=100), snap)
    without = score_recommendation(_rec(confidence=100), _snap(cpu=90.0, memory=50.0))
    assert with_bonus == without + 10


def test_prioritizer_picks_highest_score() -> None:
    """The candidate with the highest score should win."""

    low = ScoredRecommendation(_rec(title="Idle System", level="normal", confidence=85), 20)
    high = ScoredRecommendation(_rec(title="CPU Overload", confidence=98), 94)
    winner = prioritize([low, high])
    assert winner is not None
    assert winner.recommendation.title == "CPU Overload"


def test_prioritizer_empty() -> None:
    """Empty candidate list should return None."""

    assert prioritize([]) is None


def test_decision_bounds() -> None:
    """Decision should reject out-of-range priority scores."""

    with pytest.raises(ValueError):
        Decision(
            title="x",
            severity="critical",
            confidence=90,
            priority_score=150,
            explanation="nope",
            action="none",
            timestamp=datetime.now(timezone.utc),
        )


def test_engine_picks_cpu_overload(tmp_path: Path) -> None:
    """Hot CPU snapshot should yield a CPU Overload decision."""

    from aetheros.intent import IntentEngine, IntentStorage

    engine = DecisionEngine(
        policy=PolicyEngine(),
        safety=SafetyValidator(
            cooldown=CooldownManager(),
            audit=AuditLogger(tmp_path / "audit.db"),
        ),
        intent=IntentEngine(
            storage=IntentStorage(tmp_path / "intent.db"),
            initial="Balanced",
        ),
    )
    report = engine.evaluate_report(_snap(cpu=97.0, memory=68.0))
    assert report.decision is not None
    assert report.decision.title == "CPU Overload"
    # Base severity+confidence score is 89; Balanced intent adds a CPU bonus.
    assert report.decision.priority_score >= 89
    assert "97" in report.decision.explanation
    assert "Memory is stable" in report.decision.explanation
    assert "Reduce background workload" in report.decision.action


def test_engine_healthy_returns_none_or_idle(tmp_path: Path) -> None:
    """Mid-range usage should not produce a critical decision."""

    engine = DecisionEngine(
        safety=SafetyValidator(
            cooldown=CooldownManager(),
            audit=AuditLogger(tmp_path / "audit2.db"),
        )
    )
    decision = engine.evaluate(_snap(cpu=40.0, memory=50.0, disk=40.0))
    if decision is not None:
        assert decision.severity == "normal"


def test_explain_mentions_score() -> None:
    """explain() should include the priority score fraction."""

    engine = DecisionEngine()
    decision = Decision(
        title="CPU Overload",
        severity="critical",
        confidence=98,
        priority_score=94,
        explanation="",
        action="Reduce background workload.",
        timestamp=datetime.now(timezone.utc),
    )
    text = engine.explain(decision, snapshot=_snap(cpu=97.0, memory=68.0))
    assert "94/100" in text
    assert "CPU usage reached 97%" in text


def test_detect_cpu_still_works_for_fixture() -> None:
    """Sanity: policy rule still fires on the demo fixture numbers."""

    assert detect_cpu_overload(_snap(cpu=97.0, memory=68.0)) is not None
