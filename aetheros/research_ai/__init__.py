"""Autonomous Research Engine — Digital Twin scientific experiments only.

Generates hypotheses from verified evidence, runs twin simulations, verifies
reproducible discoveries. Never executes shell commands or mutates live state.
"""

from __future__ import annotations

from aetheros.research_ai.discoveries import AutonomousResearchEngine, DiscoveryStore
from aetheros.research_ai.executor import execute_experiment
from aetheros.research_ai.experiment import DEFAULT_ITERATIONS, build_experiment
from aetheros.research_ai.formatter import ResearchLabPanel
from aetheros.research_ai.hypothesis import generate_hypothesis, generate_questions
from aetheros.research_ai.journal import ResearchJournal
from aetheros.research_ai.models import (
    Discovery,
    Experiment,
    Hypothesis,
    JournalEntry,
    ResearchQuestion,
    Result,
)
from aetheros.research_ai.verifier import VerificationVerdict, verify_result

__all__ = [
    "DEFAULT_ITERATIONS",
    "AutonomousResearchEngine",
    "Discovery",
    "DiscoveryStore",
    "Experiment",
    "Hypothesis",
    "JournalEntry",
    "ResearchJournal",
    "ResearchLabPanel",
    "ResearchQuestion",
    "Result",
    "VerificationVerdict",
    "build_experiment",
    "execute_experiment",
    "generate_hypothesis",
    "generate_questions",
    "verify_result",
]
