"""Unit tests for Phase 9 autonomous research engine."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from aetheros.intent.profiles import get_profile
from aetheros.learning.models import HistoricalPattern
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.research import ResearchEngine, generate_strategies, rank_strategies
from aetheros.research.evaluator import StrategyEvaluator
from aetheros.research.reporter import render_markdown, save_report
from aetheros.simulation import SimulationEngine, SimulatableStrategy


def _snap(*, cpu: float = 72.0, memory: float = 58.0) -> TelemetrySnapshot:
    """Build a telemetry snapshot for research tests."""

    return TelemetrySnapshot(
        timestamp=datetime(2026, 9, 23, tzinfo=timezone.utc),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=40.0,
        battery_percent=None,
        process_count=8,
        top_processes=("code", "chrome"),
    )


def test_generator_creates_at_least_five() -> None:
    """Generator should emit at least five named strategies."""

    intent = get_profile("Coding")
    patterns = (
        HistoricalPattern("t", "d", cpu_bias=10, memory_bias=0, confidence=70),
    )
    strategies = generate_strategies(_snap(), intent, patterns)
    assert len(strategies) >= 5
    titles = {s.title for s in strategies}
    assert "Reduce Background Workload" in titles
    assert "Interactive Priority Boost" in titles
    assert "Power Efficient Mode" in titles


def test_simulation_is_immutable_and_bounded() -> None:
    """Simulation scores must stay within 0–100."""

    intent = get_profile("Coding")
    strategy = SimulatableStrategy(
        title="Interactive Priority Boost",
        description="test",
        expected_cpu_delta=-14.0,
        expected_memory_delta=-2.0,
        expected_efficiency_delta=8.0,
    )
    result = SimulationEngine().simulate(strategy, _snap(), intent)
    assert 0 <= result.performance_score <= 100
    assert 0 <= result.stability_score <= 100
    assert 0 <= result.efficiency_score <= 100
    assert 0 <= result.overall_improvement <= 100


def test_ranker_orders_by_weighted_score() -> None:
    """Ranker should place the highest weighted score first."""

    intent = get_profile("Coding")
    strategies = generate_strategies(_snap(), intent, ())
    evaluated = StrategyEvaluator().evaluate_all(strategies, _snap(), intent)
    ranked = rank_strategies(evaluated)
    assert ranked[0].rank == 1
    assert ranked[0].rank_score >= ranked[-1].rank_score


def test_research_engine_writes_markdown(tmp_path: Path) -> None:
    """Full research run should produce a markdown report on disk."""

    engine = ResearchEngine(reports_dir=tmp_path)
    report = engine.run(_snap(), get_profile("Coding"), patterns=(), write_report=True)
    assert report.winner is not None
    assert report.report_path is not None
    path = Path(report.report_path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "# AetherOS Research Report" in text
    assert "## Winning Strategy" in text
    assert "Why It Won" in text


def test_render_markdown_contains_sections(tmp_path: Path) -> None:
    """Rendered markdown should include ranking and intent sections."""

    engine = ResearchEngine(reports_dir=tmp_path)
    report = engine.run(_snap(), get_profile("Gaming"), write_report=False)
    md = render_markdown(report)
    assert "## Intent" in md
    assert "## Ranking Table" in md
    saved = save_report(report, reports_dir=tmp_path)
    assert saved.name.endswith("_research.md")


def test_coding_prefers_interactive_style(tmp_path: Path) -> None:
    """Under Coding intent, an interactive strategy should rank near the top."""

    engine = ResearchEngine(reports_dir=tmp_path)
    report = engine.run(_snap(cpu=75, memory=55), get_profile("Coding"), write_report=False)
    assert report.winner is not None
    top_titles = {item.strategy.title for item in report.ranked[:2]}
    assert (
        "Interactive Priority Boost" in top_titles
        or "Increase Interactive Priority" in top_titles
        or "Reduce Background Workload" in top_titles
    )
