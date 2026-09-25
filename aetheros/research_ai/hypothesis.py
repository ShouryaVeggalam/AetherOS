"""Hypothesis generator — deterministic questions from existing evidence.

Questions originate from Operational Memory titles, twin scenario cues, and
resource pressure signals. Never invents random topics.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha1

from aetheros.memory.models import MemoryRecord
from aetheros.research_ai.models import Hypothesis, ResearchQuestion

# Evidence keyword → (question template, objective, expected outcome cue)
_TEMPLATES: tuple[tuple[tuple[str, ...], str, str, str, str], ...] = (
    (
        ("compile", "indexing", "disk"),
        "Does background indexing increase compile latency?",
        "Measure whether indexing pressure correlates with compile-time disk contention.",
        "Background indexing increases average compile latency under twin load.",
        "Higher disk / latency pressure when indexing is active.",
    ),
    (
        ("compile", "disk"),
        "Would reducing background disk activity improve compile latency?",
        "Test whether lowering concurrent disk load shortens compile-related pressure.",
        "Reducing background disk activity improves compile latency.",
        "Lower disk utilization and improved stability during compile scenarios.",
    ),
    (
        ("charging", "thermal", "battery"),
        "Does charging reduce thermal throttling?",
        "Evaluate twin battery/charge scenarios against thermal-linked CPU stability.",
        "Charging conditions reduce thermal throttling versus low-battery load.",
        "Higher stability and lower CPU bottleneck risk while charging.",
    ),
    (
        ("battery", "thermal"),
        "Does low battery amplify thermal-related CPU pressure?",
        "Compare low-battery twin runs against nominal charge for CPU stability.",
        "Low battery amplifies thermal-related CPU pressure.",
        "Lower stability under BATTERY_LOW twin scenarios.",
    ),
    (
        ("morning", "coding", "memory"),
        "Do morning coding sessions produce lower memory pressure?",
        "Relate morning coding patterns to twin memory-pressure outcomes.",
        "Morning coding sessions produce lower memory pressure than peak load windows.",
        "Lower predicted memory utilization for morning-coded baselines.",
    ),
    (
        ("morning", "coding", "cpu"),
        "Do morning coding sessions increase CPU before memory pressure?",
        "Validate the operational memory pattern of CPU-leading morning coding load.",
        "Morning coding raises CPU utilization before memory pressure.",
        "CPU bottleneck precedes memory in twin progression.",
    ),
    (
        ("cpu", "memory"),
        "Does sustained CPU overload precede memory pressure?",
        "Run CPU_OVERLOAD twins and observe subsequent memory metrics.",
        "Sustained CPU overload precedes elevated memory pressure.",
        "Memory rises after CPU overload scenario application.",
    ),
)


def generate_questions(
    *,
    memories: Sequence[MemoryRecord] = (),
    evidence_texts: Sequence[str] = (),
    now: datetime | None = None,
    limit: int = 5,
) -> tuple[ResearchQuestion, ...]:
    """Generate research questions from verified evidence only."""

    stamp = now or datetime.now(UTC)
    corpus = " ".join(
        [
            *(f"{m.title} {m.description}" for m in memories if m.status == "verified"),
            *evidence_texts,
        ]
    ).lower()
    if not corpus.strip():
        return ()

    questions: list[ResearchQuestion] = []
    for keywords, title, objective, _statement, _expected in _TEMPLATES:
        if all(k in corpus for k in keywords) or (
            len(keywords) >= 2 and sum(1 for k in keywords if k in corpus) >= 2
        ):
            qid = _stable_id("q", title)
            questions.append(
                ResearchQuestion(
                    id=qid,
                    title=title,
                    objective=objective,
                    created_at=stamp,
                )
            )
        if len(questions) >= max(0, limit):
            break
    return tuple(questions)


def generate_hypothesis(
    question: ResearchQuestion,
    *,
    memories: Sequence[MemoryRecord] = (),
) -> Hypothesis:
    """Build one hypothesis for ``question`` using matching template rationale."""

    rationale_bits = [
        m.title for m in memories if m.status == "verified" and _overlaps(question, m)
    ]
    rationale = (
        "Grounded in operational evidence: " + ", ".join(rationale_bits)
        if rationale_bits
        else f"Grounded in research question objective: {question.objective}"
    )
    statement, expected = _template_pair(question.title)
    return Hypothesis(
        id=_stable_id("h", question.id + statement),
        statement=statement,
        rationale=rationale,
        expected_outcome=expected,
    )


def _template_pair(title: str) -> tuple[str, str]:
    for _keywords, tmpl_title, _obj, statement, expected in _TEMPLATES:
        if tmpl_title == title:
            return statement, expected
    return (
        f"Testing: {title}",
        "Measurable twin metric shift supporting the question objective.",
    )


def _overlaps(question: ResearchQuestion, memory: MemoryRecord) -> bool:
    blob = f"{memory.title} {memory.description}".lower()
    tokens = [t for t in question.title.lower().replace("?", "").split() if len(t) > 3]
    return sum(1 for t in tokens if t in blob) >= 2


def _stable_id(prefix: str, material: str) -> str:
    digest = sha1(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"
