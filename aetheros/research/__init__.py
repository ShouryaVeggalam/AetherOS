"""Autonomous research engine — generate, simulate, rank, report."""

from aetheros.research.engine import ResearchEngine
from aetheros.research.evaluator import StrategyEvaluator
from aetheros.research.generator import generate_strategies
from aetheros.research.models import (
    CandidateStrategy,
    EvaluatedStrategy,
    RankedStrategy,
    ResearchReport,
)
from aetheros.research.ranker import rank_strategies
from aetheros.research.reporter import render_markdown, save_report

__all__ = [
    "CandidateStrategy",
    "EvaluatedStrategy",
    "RankedStrategy",
    "ResearchEngine",
    "ResearchReport",
    "StrategyEvaluator",
    "generate_strategies",
    "rank_strategies",
    "render_markdown",
    "save_report",
]
