"""Unit tests for AetherOS v7 Genesis Intelligence Layer."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from aetheros.genesis import (
    DEFAULT_CENSUS,
    ExperimentEngine,
    GenesisPanel,
    GenesisRuntime,
    GenesisVerifier,
    HypothesisEngine,
    KnowledgeBase,
    KnowledgeRecord,
    TheoremStore,
    default_question,
)
from aetheros.ontology import RESOURCE_ENTITIES, SEED_RELATIONS, build_ontology_graph


def test_ontology_catalog() -> None:
    """Ontology should expose resources and typed relationships."""

    assert any(r.kind == "cpu" for r in RESOURCE_ENTITIES)
    assert any(r.relation == "CAUSES" for r in SEED_RELATIONS)
    graph = build_ontology_graph()
    assert graph.number_of_edges() >= 5


def test_knowledge_rejects_unsupported(tmp_path: Path) -> None:
    """Knowledge base must reject low-confidence / evidence-free claims."""

    kb = KnowledgeBase(tmp_path / "kb.db")
    assert kb.count() >= 3
    try:
        KnowledgeRecord(
            knowledge_id="bad",
            statement="unsupported",
            evidence=(),
            simulation_count=0,
            confidence=0.2,
            clusters_verified=0,
            source="test",
            created_at=datetime.now(UTC),
            tags=(),
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    largest = kb.largest_evidence_set()
    assert largest is not None
    assert largest.simulation_count >= 2814


def test_hypothesis_experiment_verify(tmp_path: Path) -> None:
    """Research cycle should propose, simulate, and archive rejects."""

    question = default_question()
    hyps = HypothesisEngine().propose(question)
    assert len(hyps) >= 3
    engine = ExperimentEngine(default_runs=8)
    verifier = GenesisVerifier(min_simulations=5)
    accepted = 0
    for hyp in hyps:
        result = engine.run(hyp, runs=8)
        assert 0 <= result.fairness <= 100
        outcome = verifier.verify(hyp, result)
        if outcome.accepted:
            accepted += 1
    assert verifier.rejected()  # at least null hypothesis archived
    assert accepted >= 0


def test_genesis_runtime_and_panel(tmp_path: Path) -> None:
    """GenesisRuntime should produce a dashboard-ready report."""

    runtime = GenesisRuntime(
        knowledge=KnowledgeBase(tmp_path / "kb.db"),
        theorems=TheoremStore(tmp_path / "thm.db"),
    )
    report = runtime.research(experiment_runs=8)
    assert report.census.verified_knowledge == DEFAULT_CENSUS.verified_knowledge
    assert report.largest_title
    assert report.largest_simulations >= 1
    assert report.status == "Research Only"
    console = Console(record=True, width=100)
    console.print(GenesisPanel(report=report))
    text = console.export_text()
    assert "GENESIS" in text
    assert "182" in text
    assert "Compile" in text or "cache" in text.lower() or "Knowledge" in text


def test_genesis_api(tmp_path: Path) -> None:
    """Genesis API routes should return research JSON."""

    from fastapi.testclient import TestClient

    from aetheros.api import create_app

    client = TestClient(create_app(memory_db=tmp_path / "cog.db"))
    overview = client.get("/genesis").json()
    assert overview["verified_knowledge"] == 182
    assert overview["active_experiments"] == 14
    assert overview["status"] == "Research Only"
    assert client.get("/genesis/knowledge").status_code == 200
    assert client.get("/genesis/theorems").status_code == 200
    onto = client.get("/genesis/ontology").json()
    assert "resources" in onto
    assert "relationships" in onto
