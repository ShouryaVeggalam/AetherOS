"""Autonomous strategy research + P9 Research Intelligence Engine.

Strategy path (unchanged): generate → simulate → rank → markdown.
Intelligence path (P9): graph/context/history → observations → trends →
bottlenecks → gated discoveries → SystemResearchReport.
"""

from aetheros.research.analyzer import analyze_observations, context_label_from_mapping
from aetheros.research.bottlenecks import detect_bottlenecks
from aetheros.research.discoveries import verify_discoveries
from aetheros.research.engine import ResearchEngine, ResearchIntelligenceEngine
from aetheros.research.evaluator import StrategyEvaluator
from aetheros.research.formatter import ResearchIntelligencePanel
from aetheros.research.generator import generate_strategies
from aetheros.research.models import (
    BottleneckFinding,
    CandidateStrategy,
    Discovery,
    EvaluatedStrategy,
    RankedStrategy,
    ResearchObservation,
    ResearchReport,
    SystemResearchReport,
    TrendAnalysis,
)
from aetheros.research.ranker import rank_strategies
from aetheros.research.report import (
    build_report,
    export_json,
    export_markdown,
    report_to_dict,
)
from aetheros.research.reporter import render_markdown, save_report
from aetheros.research.trends import analyze_trends

__all__ = [
    "BottleneckFinding",
    "CandidateStrategy",
    "Discovery",
    "EvaluatedStrategy",
    "RankedStrategy",
    "ResearchEngine",
    "ResearchIntelligenceEngine",
    "ResearchIntelligencePanel",
    "ResearchObservation",
    "ResearchReport",
    "StrategyEvaluator",
    "SystemResearchReport",
    "TrendAnalysis",
    "analyze_observations",
    "analyze_trends",
    "build_report",
    "context_label_from_mapping",
    "detect_bottlenecks",
    "export_json",
    "export_markdown",
    "generate_strategies",
    "rank_strategies",
    "render_markdown",
    "report_to_dict",
    "save_report",
    "verify_discoveries",
]
