"""Research engines — strategy research + P9 Research Intelligence.

``ResearchEngine``: generate → simulate → rank → markdown (unchanged).
``ResearchIntelligenceEngine``: evidence pipeline → SystemResearchReport.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aetheros.graph.models import ResourceGraph
from aetheros.intent.models import IntentProfile
from aetheros.learning import HistoricalPattern, LearningEngine
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.research.analyzer import analyze_observations, context_label_from_mapping
from aetheros.research.bottlenecks import detect_bottlenecks
from aetheros.research.discoveries import verify_discoveries
from aetheros.research.evaluator import StrategyEvaluator
from aetheros.research.generator import generate_strategies
from aetheros.research.models import ReportKind, ResearchReport, SystemResearchReport
from aetheros.research.ranker import rank_strategies
from aetheros.research.report import build_report, export_markdown
from aetheros.research.reporter import save_report
from aetheros.research.trends import analyze_trends


@dataclass
class ResearchEngine:
    """Autonomous research pipeline (advice + markdown only).

    Args:
        learning: Source of historical patterns.
        evaluator: Strategy simulation evaluator.
        reports_dir: Directory for markdown reports.
    """

    learning: LearningEngine = field(default_factory=LearningEngine)
    evaluator: StrategyEvaluator = field(default_factory=StrategyEvaluator)
    reports_dir: Path = field(default_factory=lambda: Path("reports"))

    def run(
        self,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
        *,
        patterns: tuple[HistoricalPattern, ...] | None = None,
        write_report: bool = True,
    ) -> ResearchReport:
        """Run a full research cycle and optionally save markdown.

        Args:
            snapshot: Current telemetry.
            intent: Active intent profile.
            patterns: Optional explicit patterns; otherwise learned defaults.
            write_report: When True, write reports/YYYY-MM-DD_HHMM_research.md.

        Returns:
            A ResearchReport with ranked strategies and optional file path.
        """

        resolved_patterns = (
            patterns if patterns is not None else self.learning.get_patterns()
        )
        candidates = generate_strategies(snapshot, intent, resolved_patterns)
        evaluated = self.evaluator.evaluate_all(candidates, snapshot, intent)
        ranked = rank_strategies(evaluated)
        winner = ranked[0] if ranked else None
        created_at = datetime.now(UTC)

        report = ResearchReport(
            created_at=created_at,
            snapshot=snapshot,
            intent=intent,
            patterns=tuple(resolved_patterns),
            candidates=candidates,
            ranked=ranked,
            winner=winner,
            report_path=None,
        )

        if write_report:
            path = save_report(
                report, reports_dir=self.reports_dir, created_at=created_at
            )
            report = ResearchReport(
                created_at=report.created_at,
                snapshot=report.snapshot,
                intent=report.intent,
                patterns=report.patterns,
                candidates=report.candidates,
                ranked=report.ranked,
                winner=report.winner,
                report_path=str(path),
            )
        return report


@dataclass
class ResearchIntelligenceEngine:
    """P9 Research Intelligence — evidence → publishable system reports.

    Read-only consumer of Resource Graph, telemetry history, optional
    GraphContext, verified reasoning, and twin/simulation summaries.
    Never invents discoveries. Never mutates host state.
    """

    reports_dir: Path = field(default_factory=lambda: Path("reports"))
    min_evidence: int = 5
    min_simulation_agreement: float = 80.0

    def generate(
        self,
        *,
        graph: ResourceGraph | None = None,
        history: Sequence[TelemetryPoint] = (),
        context: Mapping[str, Any] | object | str | None = None,
        verified_reasoning: Sequence[str] = (),
        twin_summaries: Sequence[str] = (),
        simulation_agreement: float | None = None,
        session_count: int | None = None,
        network_series: Sequence[float] | None = None,
        cluster_health_series: Sequence[float] | None = None,
        kind: ReportKind = "research_summary",
        write_markdown: bool = False,
        now: datetime | None = None,
    ) -> SystemResearchReport:
        """Run the evidence pipeline and return an immutable system report."""

        stamp = now or datetime.now(UTC)
        label: str | None
        if isinstance(context, str):
            label = context.strip() or None
        else:
            label = context_label_from_mapping(
                context if isinstance(context, Mapping) else None
            )
            if label is None and context is not None:
                label = context_label_from_mapping(context)  # type: ignore[arg-type]

        observations = analyze_observations(
            graph=graph,
            history=history,
            context_label=label,
            reasoning_verified=verified_reasoning,
            twin_summaries=twin_summaries,
            now=stamp,
        )
        trends = analyze_trends(
            history,
            now=stamp,
            network_series=network_series,
            cluster_health_series=cluster_health_series,
        )
        bottlenecks = detect_bottlenecks(graph=graph, history=history)
        discoveries = verify_discoveries(
            observations=observations,
            trends=trends,
            verified_reasoning=verified_reasoning,
            simulation_agreement=simulation_agreement,
            session_count=session_count,
            min_evidence=self.min_evidence,
            min_simulation_agreement=self.min_simulation_agreement,
        )
        report = build_report(
            context=label or "BALANCED",
            observations=observations,
            trends=trends,
            bottlenecks=bottlenecks,
            discoveries=discoveries,
            simulations=twin_summaries,
            kind=kind,
            generated_at=stamp,
        )
        if write_markdown:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            path = (
                self.reports_dir
                / f"{stamp.strftime('%Y-%m-%d_%H%M')}_system_research.md"
            )
            path.write_text(export_markdown(report), encoding="utf-8")
        return report

    def daily(self, **kwargs: Any) -> SystemResearchReport:
        """Generate a daily report."""

        kwargs.setdefault("kind", "daily")
        return self.generate(**kwargs)

    def weekly(self, **kwargs: Any) -> SystemResearchReport:
        """Generate a weekly report."""

        kwargs.setdefault("kind", "weekly")
        return self.generate(**kwargs)
