"""Unit tests for Phase 6 intent engine, storage, and weighting."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from aetheros.decision.models import Decision
from aetheros.intent import IntentEngine, IntentStorage
from aetheros.intent.profiles import CODING, GAMING, get_profile
from aetheros.policy_engine.models import PolicyRecommendation


def _rec(
    title: str = "CPU Overload", level: str = "critical", confidence: int = 98
) -> PolicyRecommendation:
    """Build a recommendation for intent bonus tests."""

    return PolicyRecommendation(
        level=level,  # type: ignore[arg-type]
        title=title,
        reason="test",
        recommended_action="Reduce background workload.",
        confidence=confidence,
    )


def test_get_profile_aliases() -> None:
    """Common aliases should resolve to canonical profiles."""

    assert get_profile("editing").name == "Video Editing"
    assert get_profile("battery").name == "Battery Saver"
    assert get_profile("AI").name == "AI Training"


def test_storage_roundtrip(tmp_path: Path) -> None:
    """Selected intent should persist and reload from SQLite."""

    db = tmp_path / "intent.db"
    storage = IntentStorage(db)
    storage.save(CODING)
    assert storage.load() == CODING


def test_engine_restores_on_startup(tmp_path: Path) -> None:
    """IntentEngine should restore the last saved profile."""

    db = tmp_path / "intent.db"
    IntentEngine(storage=IntentStorage(db)).set_intent(GAMING)
    restored = IntentEngine(storage=IntentStorage(db))
    assert restored.current_intent().name == GAMING


def test_hotkey_sets_coding(tmp_path: Path) -> None:
    """Hotkey 1 should select Coding."""

    engine = IntentEngine(storage=IntentStorage(tmp_path / "i.db"), initial="Balanced")
    profile = engine.set_intent_by_hotkey("1")
    assert profile is not None
    assert profile.name == CODING


def test_cpu_bonus_higher_for_gaming(tmp_path: Path) -> None:
    """Gaming should boost CPU recommendations more than Balanced."""

    gaming = IntentEngine(storage=IntentStorage(tmp_path / "g.db"), initial=GAMING)
    balanced = IntentEngine(
        storage=IntentStorage(tmp_path / "b.db"), initial="Balanced"
    )
    rec = _rec("CPU Overload")
    assert gaming.bonus_for_recommendation(rec) > balanced.bonus_for_recommendation(rec)


def test_apply_weights_clamps_score(tmp_path: Path) -> None:
    """apply_weights should keep the priority score in 0–100."""

    engine = IntentEngine(storage=IntentStorage(tmp_path / "a.db"), initial=CODING)
    decision = Decision(
        title="CPU Overload",
        severity="critical",
        confidence=98,
        priority_score=95,
        explanation="base",
        action="Reduce background workload.",
        timestamp=datetime.now(UTC),
    )
    adjusted = engine.apply_weights(decision)
    assert 0 <= adjusted.priority_score <= 100
    assert "Coding" in adjusted.explanation or "Intent" in adjusted.explanation


def test_unknown_intent_raises() -> None:
    """Unknown profile names should raise KeyError."""

    with pytest.raises(KeyError):
        get_profile("time-travel")


def test_guidance_coding() -> None:
    """Coding guidance should mention interactive development."""

    engine = IntentEngine(
        storage=IntentStorage(Path("data/test_intent_guidance.db")),
        initial=CODING,
    )
    text = engine.guidance_text()
    assert "interactive development" in text.lower()
