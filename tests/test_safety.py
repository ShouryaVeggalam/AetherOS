"""Unit tests for Phase 3 safety layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from aetheros.policy_engine.models import PolicyRecommendation
from aetheros.safety import AuditLogger, CooldownManager, SafetyValidator
from aetheros.safety.cooldown import category_for_title
from aetheros.safety.models import SafetyResult, make_approved, make_blocked


def _rec(
    *,
    title: str = "CPU Overload",
    level: str = "critical",
    reason: str = "CPU usage has exceeded 95%.",
    action: str = "Reduce background workload.",
    confidence: int = 98,
) -> PolicyRecommendation:
    """Build a PolicyRecommendation for tests."""

    return PolicyRecommendation(
        level=level,  # type: ignore[arg-type]
        title=title,
        reason=reason,
        recommended_action=action,
        confidence=confidence,
    )


def test_category_mapping() -> None:
    """Titles should map to the expected cooldown categories."""

    assert category_for_title("CPU Overload") == "cpu"
    assert category_for_title("High Memory Usage") == "memory"
    assert category_for_title("Critical Disk Pressure") == "disk"
    assert category_for_title("Idle System") == "idle"


def test_approve_clean_critical() -> None:
    """High-confidence critical advice without banned words is approved."""

    validator = SafetyValidator(
        cooldown=CooldownManager(),
        audit=AuditLogger(Path("data/test_audit_approve.db")),
    )
    result = validator.validate(_rec(), record=True)
    assert result.approved is True
    assert result.status == "approved"


def test_block_low_confidence_critical() -> None:
    """Critical recommendations below 80 confidence are blocked."""

    validator = SafetyValidator(
        cooldown=CooldownManager(),
        audit=AuditLogger(Path("data/test_audit_lowconf.db")),
    )
    result = validator.validate(_rec(confidence=70), record=False)
    assert result.approved is False
    assert result.status == "blocked"
    assert "confidence" in result.reason.lower()


def test_block_banned_phrase() -> None:
    """Recommendations mentioning kill/sudo/etc. are blocked."""

    validator = SafetyValidator(
        cooldown=CooldownManager(),
        audit=AuditLogger(Path("data/test_audit_banned.db")),
    )
    result = validator.validate(
        _rec(action="Please kill the runaway process."),
        record=False,
    )
    assert result.status == "blocked"
    assert "kill" in result.reason.lower()


def test_cooldown_blocks_duplicate() -> None:
    """A second approval in the same category should hit cooldown."""

    validator = SafetyValidator(
        cooldown=CooldownManager(),
        audit=AuditLogger(Path("data/test_audit_cooldown.db")),
    )
    first = validator.validate(_rec(), record=True)
    second = validator.validate(_rec(), record=True)
    assert first.status == "approved"
    assert second.status == "cooldown"
    assert "cooldown" in second.reason.lower()


def test_contradiction_rejects_idle() -> None:
    """Idle should be blocked when pressure advice is in the same batch."""

    validator = SafetyValidator(
        cooldown=CooldownManager(),
        audit=AuditLogger(Path("data/test_audit_contra.db")),
    )
    idle = _rec(title="Idle System", level="normal", confidence=85)
    cpu = _rec(title="CPU Overload", level="critical", confidence=98)
    batch = [idle, cpu]
    idle_result = validator.validate(idle, batch=batch, record=False)
    cpu_result = validator.validate(cpu, batch=batch, record=False)
    assert idle_result.status == "blocked"
    assert "contradict" in idle_result.reason.lower()
    assert cpu_result.status == "approved"


def test_audit_appends_never_overwrites(tmp_path: Path) -> None:
    """Each log call should insert a new row."""

    db = tmp_path / "audit.db"
    logger = AuditLogger(db)
    rec = _rec()
    logger.log(rec, make_approved("ok"))
    logger.log(rec, make_blocked("nope"))
    assert logger.count() == 2


def test_safety_result_consistency() -> None:
    """approved flag must match status."""

    with pytest.raises(ValueError):
        SafetyResult(
            approved=True,
            status="blocked",
            reason="x",
            timestamp=make_approved("y").timestamp,
        )


def test_validate_all_order(tmp_path: Path) -> None:
    """validate_all should preserve recommendation order."""

    validator = SafetyValidator(
        cooldown=CooldownManager(),
        audit=AuditLogger(tmp_path / "all.db"),
    )
    items = [
        _rec(title="High CPU Usage", level="warning", confidence=90),
        _rec(title="High Memory Usage", level="warning", confidence=90),
    ]
    pairs = validator.validate_all(items, record=False)
    assert [p[0].title for p in pairs] == [i.title for i in items]
