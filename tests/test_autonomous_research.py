"""Tests for v3 P5 Autonomous Research Engine (Digital Twin only)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from rich.console import Console

from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
from aetheros.memory import MemoryEngine
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.research_ai import (
    AutonomousResearchEngine,
    Discovery,
    DiscoveryStore,
    Experiment,
    Hypothesis,
    ResearchJournal,
    ResearchLabPanel,
    ResearchQuestion,
    Result,
    build_experiment,
    execute_experiment,
    generate_hypothesis,
    generate_questions,
    verify_result,
)
from aetheros.research_ai.experiment import DEFAULT_ITERATIONS
from aetheros.twin.snapshot import create_snapshot


def _stamp() -> datetime:
    return datetime(2026, 9, 25, 12, 0, tzinfo=UTC)


def _snapshot() -> object:
    stamp = _stamp()
    rg = ResourceGraph(
        nodes=(
            ResourceNode("cpu", "CPU", "CPU", (("percent", "40.0"),), stamp),
            ResourceNode("memory", "Memory", "Memory", (("percent", "50.0"),), stamp),
            ResourceNode("disk", "Disk", "Disk", (("percent", "30.0"),), stamp),
            ResourceNode(
                "battery", "Battery", "Battery", (("percent", "80.0"),), stamp
            ),
        ),
        edges=(ResourceEdge("cpu", "memory", "DEPENDS_ON", 0.4),),
    )
    tel = TelemetrySnapshot(
        timestamp=stamp,
        cpu_percent=40.0,
        memory_percent=50.0,
        disk_percent=30.0,
        battery_percent=80.0,
        process_count=2,
        top_processes=("Cursor", "compiler"),
    )
    return create_snapshot(rg, tel, intent="Coding", now=stamp)


def _memories():
    return MemoryEngine().seed_defaults(now=_stamp())


# --- models -----------------------------------------------------------------


def test_model_validation() -> None:
    stamp = _stamp()
    with pytest.raises(ValueError):
        ResearchQuestion(id=" ", title="t", objective="o", created_at=stamp)
    with pytest.raises(ValueError):
        Hypothesis(id="h", statement=" ", rationale="r", expected_outcome="e")
    with pytest.raises(ValueError):
        Experiment(
            id="e",
            hypothesis=Hypothesis(
                id="h", statement="s", rationale="r", expected_outcome="cpu rises"
            ),
            scenario=" ",
            iterations=1,
            snapshot_id="snap",
        )
    with pytest.raises(ValueError):
        Result(
            metrics=(),
            stability=10.0,
            confidence=10.0,
            evidence=("e",),
            successful_iterations=2,
            total_iterations=1,
        )
    with pytest.raises(ValueError):
        Discovery(
            title="t",
            summary="s",
            reproducibility=10.0,
            evidence_count=0,
            confidence=10.0,
        )


# --- questions / hypotheses -------------------------------------------------


def test_generate_questions_from_memory_evidence() -> None:
    assert generate_questions() == ()
    questions = generate_questions(memories=_memories(), now=_stamp(), limit=5)
    assert questions
    assert all(isinstance(q, ResearchQuestion) for q in questions)
    hypo = generate_hypothesis(questions[0], memories=_memories())
    assert hypo.statement
    assert hypo.rationale
    assert hypo.expected_outcome


def test_generate_questions_from_text_evidence() -> None:
    questions = generate_questions(
        evidence_texts=("morning coding cpu memory pressure",),
        now=_stamp(),
        limit=3,
    )
    assert any(
        "morning" in q.title.lower() or "cpu" in q.title.lower() for q in questions
    )


# --- experiment / executor --------------------------------------------------


def test_build_and_execute_experiment() -> None:
    snap = _snapshot()
    memories = _memories()
    question = generate_questions(memories=memories, now=_stamp(), limit=1)[0]
    hypo = generate_hypothesis(question, memories=memories)
    experiment = build_experiment(
        hypo, snap, question=question, iterations=5, now=_stamp()
    )
    assert experiment.iterations == 5
    assert experiment.snapshot_id == snap.id
    assert DEFAULT_ITERATIONS == 30

    result = execute_experiment(experiment, snap, now=_stamp())
    assert result.total_iterations == 5
    assert result.successful_iterations >= 1
    assert result.reproducibility > 0
    assert result.evidence


def test_build_experiment_rejects_bad_iterations() -> None:
    snap = _snapshot()
    hypo = Hypothesis(
        id="h1",
        statement="CPU rises under load",
        rationale="evidence",
        expected_outcome="Higher CPU utilization",
    )
    with pytest.raises(ValueError):
        build_experiment(hypo, snap, iterations=0)


# --- verifier / journal / store ---------------------------------------------


def test_verifier_accepts_strong_result() -> None:
    hypo = Hypothesis(
        id="h1",
        statement="Disk load rises under indexing",
        rationale="compile evidence",
        expected_outcome="Higher disk utilization under twin load",
    )
    experiment = Experiment(
        id="exp1",
        hypothesis=hypo,
        scenario="DISK_SATURATION",
        iterations=10,
        snapshot_id="snap",
    )
    result = Result(
        metrics=(
            ("disk_delta", 25.0),
            ("cpu_delta", 0.0),
            ("memory_delta", 0.0),
        ),
        stability=70.0,
        confidence=80.0,
        evidence=("bottleneck=disk", "iterations=10 successful=10"),
        successful_iterations=9,
        total_iterations=10,
    )
    verdict = verify_result(experiment=experiment, result=result)
    assert verdict.accepted is not None
    assert verdict.rejected is None


def test_verifier_rejects_weak_result() -> None:
    hypo = Hypothesis(
        id="h1",
        statement="Something",
        rationale="r",
        expected_outcome="cpu rises sharply",
    )
    experiment = Experiment(
        id="exp1",
        hypothesis=hypo,
        scenario="CPU_OVERLOAD",
        iterations=10,
        snapshot_id="snap",
    )
    result = Result(
        metrics=(("cpu_delta", 0.0), ("memory_delta", 0.0), ("disk_delta", 0.0)),
        stability=10.0,
        confidence=10.0,
        evidence=("only-one",),
        successful_iterations=1,
        total_iterations=10,
    )
    verdict = verify_result(experiment=experiment, result=result)
    assert verdict.accepted is None
    assert verdict.rejected is not None
    assert verdict.reasons


def test_journal_append_only_and_store() -> None:
    journal = ResearchJournal()
    hypo = Hypothesis(id="h1", statement="s", rationale="r", expected_outcome="cpu")
    experiment = Experiment(
        id="exp1",
        hypothesis=hypo,
        scenario="CPU_OVERLOAD",
        iterations=3,
        snapshot_id="snap",
    )
    result = Result(
        metrics=(("cpu_delta", 5.0),),
        stability=60.0,
        confidence=70.0,
        evidence=("a", "b"),
        successful_iterations=3,
        total_iterations=3,
    )
    e1 = journal.record_result(experiment, result, accepted=True, now=_stamp())
    e2 = journal.record_result(experiment, result, accepted=False, now=_stamp())
    assert len(journal) == 2
    assert journal.entries()[-1].experiment_id == e2.experiment_id
    assert journal.entries(limit=0) == ()
    assert e1.outcome == "supported"

    store = DiscoveryStore()
    ok = Discovery(
        title="t",
        summary="s",
        reproducibility=90.0,
        evidence_count=3,
        confidence=90.0,
        status="verified",
    )
    store.add_verified(ok)
    store.add_rejected(
        Discovery(
            title="bad",
            summary="s",
            reproducibility=10.0,
            evidence_count=1,
            confidence=10.0,
            status="pending",
        )
    )
    assert len(store) == 1
    assert store.list_verified()
    assert store.list_rejected()[0].status == "rejected"
    with pytest.raises(ValueError):
        store.add_verified(
            Discovery(
                title="x",
                summary="s",
                reproducibility=10.0,
                evidence_count=1,
                confidence=10.0,
                status="rejected",
            )
        )


# --- engine / formatter -----------------------------------------------------


def test_autonomous_research_engine_end_to_end() -> None:
    engine = AutonomousResearchEngine(default_iterations=6)
    verified = engine.run(
        _snapshot(),
        memories=_memories(),
        iterations=6,
        now=_stamp(),
        limit_questions=2,
    )
    assert engine.last_questions
    assert engine.last_experiments
    assert engine.last_results
    assert len(engine.journal) >= 1
    # With memory seeds, expect at least one verified discovery typically.
    assert verified or engine.store.list_rejected()


def test_engine_empty_without_evidence() -> None:
    engine = AutonomousResearchEngine()
    assert engine.run(_snapshot(), memories=(), evidence_texts=(), iterations=3) == ()


def test_research_lab_panel_views() -> None:
    engine = AutonomousResearchEngine(default_iterations=5)
    engine.run(
        _snapshot(), memories=_memories(), iterations=5, now=_stamp(), limit_questions=2
    )
    console = Console(record=True, width=100)
    console.print(ResearchLabPanel())
    assert (
        "idle" in console.export_text().lower() or "AUTONOMOUS" in console.export_text()
    )

    for view in ("discoveries", "questions", "experiments", "rejected", "journal"):
        console = Console(record=True, width=110)
        console.print(
            ResearchLabPanel(
                questions=engine.last_questions,
                experiments=engine.last_experiments,
                results=engine.last_results,
                verified=engine.store.list_verified(),
                rejected=engine.store.list_rejected(),
                journal=engine.journal.entries(),
                view=view,
            )
        )
        assert "AUTONOMOUS RESEARCH" in console.export_text()


def test_coverage_edges() -> None:
    stamp = _stamp()
    with pytest.raises(ValueError):
        ResearchQuestion(id="q", title=" ", objective="o", created_at=stamp)
    with pytest.raises(ValueError):
        ResearchQuestion(id="q", title="t", objective=" ", created_at=stamp)
    with pytest.raises(ValueError):
        Hypothesis(id=" ", statement="s", rationale="r", expected_outcome="e")
    with pytest.raises(ValueError):
        Hypothesis(id="h", statement="s", rationale=" ", expected_outcome="e")
    with pytest.raises(ValueError):
        Hypothesis(id="h", statement="s", rationale="r", expected_outcome=" ")
    with pytest.raises(ValueError):
        Experiment(
            id=" ",
            hypothesis=Hypothesis(
                id="h", statement="s", rationale="r", expected_outcome="cpu"
            ),
            scenario="CPU_OVERLOAD",
            iterations=1,
            snapshot_id="snap",
        )
    with pytest.raises(ValueError):
        Experiment(
            id="e",
            hypothesis=Hypothesis(
                id="h", statement="s", rationale="r", expected_outcome="cpu"
            ),
            scenario="CPU_OVERLOAD",
            iterations=0,
            snapshot_id="snap",
        )
    with pytest.raises(ValueError):
        Experiment(
            id="e",
            hypothesis=Hypothesis(
                id="h", statement="s", rationale="r", expected_outcome="cpu"
            ),
            scenario="CPU_OVERLOAD",
            iterations=1,
            snapshot_id=" ",
        )
    with pytest.raises(ValueError):
        Result(
            metrics=(),
            stability=101.0,
            confidence=10.0,
            evidence=("e",),
            successful_iterations=0,
            total_iterations=1,
        )
    with pytest.raises(ValueError):
        Result(
            metrics=(),
            stability=10.0,
            confidence=101.0,
            evidence=("e",),
            successful_iterations=0,
            total_iterations=1,
        )
    with pytest.raises(ValueError):
        Result(
            metrics=(),
            stability=10.0,
            confidence=10.0,
            evidence=("e",),
            successful_iterations=0,
            total_iterations=0,
        )
    with pytest.raises(ValueError):
        Discovery(
            title=" ",
            summary="s",
            reproducibility=10.0,
            evidence_count=1,
            confidence=10.0,
        )
    with pytest.raises(ValueError):
        Discovery(
            title="t",
            summary=" ",
            reproducibility=10.0,
            evidence_count=1,
            confidence=10.0,
        )
    with pytest.raises(ValueError):
        Discovery(
            title="t",
            summary="s",
            reproducibility=101.0,
            evidence_count=1,
            confidence=10.0,
        )
    with pytest.raises(ValueError):
        Discovery(
            title="t",
            summary="s",
            reproducibility=10.0,
            evidence_count=1,
            confidence=101.0,
        )
    from aetheros.research_ai.models import JournalEntry

    with pytest.raises(ValueError):
        JournalEntry(
            experiment_id=" ",
            hypothesis_id="h",
            timestamp=stamp,
            outcome="supported",
            reproducibility=10.0,
        )
    with pytest.raises(ValueError):
        JournalEntry(
            experiment_id="e",
            hypothesis_id=" ",
            timestamp=stamp,
            outcome="supported",
            reproducibility=10.0,
        )
    with pytest.raises(ValueError):
        JournalEntry(
            experiment_id="e",
            hypothesis_id="h",
            timestamp=stamp,
            outcome="supported",
            reproducibility=101.0,
        )

    snap = _snapshot()
    hypo = Hypothesis(
        id="h_generic",
        statement="Generic probe",
        rationale="no keywords",
        expected_outcome="Measurable twin metric shift supporting the question objective.",
    )
    build_experiment(hypo, snap, iterations=3, now=stamp)
    custom_exp = Experiment(
        id="exp_custom",
        hypothesis=hypo,
        scenario="NOT_A_REAL_SCENARIO",
        iterations=3,
        snapshot_id=snap.id,
        variables=(("cpu_delta", "12"),),
    )
    result = execute_experiment(custom_exp, snap, now=stamp)
    assert result.total_iterations == 3

    with pytest.raises(ValueError):
        execute_experiment(
            Experiment(
                id="e",
                hypothesis=hypo,
                scenario="CPU_OVERLOAD",
                iterations=1,
                snapshot_id="snap",
            ),
            type("S", (), {"id": " "})(),  # type: ignore[arg-type]
        )

    journal = ResearchJournal()
    mid = Result(
        metrics=(("cpu_delta", 1.0),),
        stability=50.0,
        confidence=50.0,
        evidence=("a", "b"),
        successful_iterations=6,
        total_iterations=10,
    )
    entry = journal.record_result(
        Experiment(
            id="e2",
            hypothesis=hypo,
            scenario="CPU_OVERLOAD",
            iterations=10,
            snapshot_id="snap",
        ),
        mid,
        accepted=False,
        now=stamp,
    )
    assert entry.outcome == "inconclusive"

    long_hypo = Hypothesis(
        id="hl",
        statement="X" * 120,
        rationale="r",
        expected_outcome="Higher stability under load",
    )
    v = verify_result(
        experiment=Experiment(
            id="el",
            hypothesis=long_hypo,
            scenario="CPU_OVERLOAD",
            iterations=5,
            snapshot_id="snap",
        ),
        result=Result(
            metrics=(("cpu_delta", 2.0),),
            stability=70.0,
            confidence=70.0,
            evidence=("a", "b"),
            successful_iterations=5,
            total_iterations=5,
        ),
    )
    assert v.accepted is not None
    assert len(v.accepted.title) <= 96

    mem_hypo = Hypothesis(
        id="hm",
        statement="Memory rises",
        rationale="r",
        expected_outcome="memory pressure increases",
    )
    assert (
        verify_result(
            experiment=Experiment(
                id="em",
                hypothesis=mem_hypo,
                scenario="MEMORY_PRESSURE",
                iterations=5,
                snapshot_id="snap",
            ),
            result=Result(
                metrics=(
                    ("memory_delta", 5.0),
                    ("cpu_delta", 0.0),
                    ("disk_delta", 0.0),
                ),
                stability=70.0,
                confidence=70.0,
                evidence=("memory bottleneck", "ok"),
                successful_iterations=5,
                total_iterations=5,
            ),
        ).accepted
        is not None
    )

    console = Console(record=True, width=80)
    console.print(
        ResearchLabPanel(
            questions=(
                ResearchQuestion(id="q", title="Q?", objective="o", created_at=stamp),
            ),
            experiments=(),
            results=(),
            verified=(),
            rejected=(),
            journal=(),
            view="experiments",
        )
    )
    assert (
        "Active Experiments" in console.export_text()
        or "(none)" in console.export_text()
    )

    console = Console(record=True, width=80)
    console.print(
        ResearchLabPanel(
            questions=(
                ResearchQuestion(id="q", title="Q?", objective="o", created_at=stamp),
            ),
            view="rejected",
        )
    )
    assert "Rejected" in console.export_text()

    console = Console(record=True, width=80)
    console.print(
        ResearchLabPanel(
            questions=(
                ResearchQuestion(id="q", title="Q?", objective="o", created_at=stamp),
            ),
            view="journal",
        )
    )
    assert "Journal" in console.export_text()

    console = Console(record=True, width=80)
    console.print(
        ResearchLabPanel(
            questions=(
                ResearchQuestion(id="q", title="Q?", objective="o", created_at=stamp),
            ),
            view="discoveries",
        )
    )
    assert "Awaiting" in console.export_text() or "Status" in console.export_text()

    orphan_q = ResearchQuestion(
        id="qo",
        title="Unmapped novel question?",
        objective="objective text",
        created_at=stamp,
    )
    orphan_h = generate_hypothesis(orphan_q, memories=())
    assert orphan_h.statement

    # Force engine rejection path with ultra-strict verify by patching module
    from aetheros.research_ai import discoveries as disc_mod
    from aetheros.research_ai.verifier import VerificationVerdict

    original = disc_mod.verify_result

    def always_reject(**kwargs):
        exp = kwargs["experiment"]
        res = kwargs["result"]
        rejected = Discovery(
            title=exp.hypothesis.statement,
            summary="rejected",
            reproducibility=res.reproducibility,
            evidence_count=max(1, len(res.evidence)),
            confidence=res.confidence,
            status="rejected",
            experiment_id=exp.id,
        )
        return VerificationVerdict(
            accepted=None, rejected=rejected, reasons=("forced",)
        )

    disc_mod.verify_result = always_reject  # type: ignore[assignment]
    try:
        engine = AutonomousResearchEngine(default_iterations=3)
        out = engine.run(
            snap,
            memories=_memories(),
            iterations=3,
            now=stamp,
            limit_questions=1,
        )
        assert out == ()
        assert engine.store.list_rejected()
    finally:
        disc_mod.verify_result = original  # type: ignore[assignment]
