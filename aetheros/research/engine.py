"""ResearchEngine — orchestrate generate → simulate → rank → report.

Never executes OS commands. Never modifies the real operating system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from aetheros.intent.models import IntentProfile
from aetheros.learning import HistoricalPattern, LearningEngine
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.research.evaluator import StrategyEvaluator
from aetheros.research.generator import generate_strategies
from aetheros.research.models import ResearchReport
from aetheros.research.ranker import rank_strategies
from aetheros.research.reporter import save_report


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

        resolved_patterns = patterns if patterns is not None else self.learning.get_patterns()
        candidates = generate_strategies(snapshot, intent, resolved_patterns)
        evaluated = self.evaluator.evaluate_all(candidates, snapshot, intent)
        ranked = rank_strategies(evaluated)
        winner = ranked[0] if ranked else None
        created_at = datetime.now(timezone.utc)

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
            path = save_report(report, reports_dir=self.reports_dir, created_at=created_at)
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
