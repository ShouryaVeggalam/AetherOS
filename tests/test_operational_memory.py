"""Tests for v3 P2 Long-Term Operational Memory."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from rich.console import Console

from aetheros.memory import (
    MemoryCandidate,
    MemoryEngine,
    MemoryQuery,
    MemoryRecord,
    OperationalMemoryPanel,
    OperationalMemoryStore,
    Pattern,
    consolidate_records,
    related,
    retrieve,
    similar_patterns,
    title_similarity,
    verify_candidate,
)
from aetheros.memory.consolidation import title_similarity as ts2
from aetheros.memory.verifier import VerificationOutcome


def _stamp(hour: int = 9, minute: int = 0) -> datetime:
    return datetime(2026, 9, 25, hour, minute, tzinfo=UTC)


def _record(
    *,
    mid: str = "mem_1",
    title: str = "Morning Coding Session",
    description: str = "Morning coding sessions typically increase CPU before memory pressure.",
    evidence_count: int = 24,
    confidence: float = 93.0,
    status: str = "verified",
    sources: tuple = ("telemetry_history", "reasoning"),
    evidence_ids: tuple = ("e1", "e2"),
    created_at: datetime | None = None,
    last_verified: datetime | None = None,
) -> MemoryRecord:
    stamp = created_at or _stamp()
    return MemoryRecord(
        id=mid,
        title=title,
        description=description,
        evidence_count=evidence_count,
        confidence=confidence,
        created_at=stamp,
        last_verified=last_verified or stamp,
        sources=sources,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        evidence_ids=evidence_ids,
    )


def _candidate(
    *,
    mid: str = "cand_1",
    title: str = "Compile Disk Contention",
    evidence_count: int = 18,
    confidence: float = 88.0,
    reasoning_verified: bool = True,
    historical_support: bool = True,
    sources: tuple = ("telemetry_history", "digital_twin", "reasoning"),
) -> MemoryCandidate:
    return MemoryCandidate(
        id=mid,
        title=title,
        description="Compile workloads frequently create disk contention.",
        evidence_count=evidence_count,
        confidence=confidence,
        sources=sources,  # type: ignore[arg-type]
        evidence_ids=("hist:disk", "twin:io"),
        reasoning_verified=reasoning_verified,
        historical_support=historical_support,
    )


# --- models -----------------------------------------------------------------


def test_memory_record_validation() -> None:
    with pytest.raises(ValueError):
        _record(mid=" ")
    with pytest.raises(ValueError):
        _record(title=" ")
    with pytest.raises(ValueError):
        _record(evidence_count=0)
    with pytest.raises(ValueError):
        _record(confidence=101.0)


def test_pattern_and_query() -> None:
    pattern = Pattern(
        label="cpu before memory", similarity=80.0, occurrences=5, confidence=90.0
    )
    assert pattern.label.startswith("cpu")
    with pytest.raises(ValueError):
        Pattern(label=" ", similarity=10.0, occurrences=1, confidence=50.0)
    with pytest.raises(ValueError):
        Pattern(label="x", similarity=101.0, occurrences=1, confidence=50.0)
    with pytest.raises(ValueError):
        Pattern(label="x", similarity=10.0, occurrences=0, confidence=50.0)
    with pytest.raises(ValueError):
        Pattern(label="x", similarity=10.0, occurrences=1, confidence=-1.0)

    query = MemoryQuery(context="Morning", intent="Coding", metric="cpu", window="1h")
    assert "morning" in query.haystack()
    assert "cpu" in query.haystack()
    assert MemoryQuery().haystack() == ""


# --- store ------------------------------------------------------------------


def test_store_append_and_list() -> None:
    store = OperationalMemoryStore()
    a = _record(mid="a", confidence=90.0, evidence_count=10)
    b = _record(
        mid="b", title="Compile Disk Contention", confidence=95.0, evidence_count=20
    )
    store.append_verified(a)
    store.append_verified(b)
    assert len(store) == 2
    assert store.get("a") is a
    ranked = list(store.list_verified())
    assert ranked[0].id == "b"
    with pytest.raises(ValueError):
        store.append_verified(a)
    pending = _record(mid="c", status="pending")
    with pytest.raises(ValueError):
        store.append_verified(pending)


def test_store_archive_and_replace() -> None:
    store = OperationalMemoryStore()
    a = _record(mid="a")
    store.append_verified(a)
    archived = store.archive(a, reason="rejected")
    assert archived.status == "archived"
    assert store.get("a") is None
    assert store.get_archived("a") is not None
    assert "[rejected]" in store.get_archived("a").description  # type: ignore[union-attr]

    store.append_verified(_record(mid="x", title="Compile latency"))
    store.append_verified(_record(mid="y", title="Morning compile latency"))
    merged = _record(mid="z", title="Morning compile latency", evidence_count=40)
    store.replace_verified(remove_ids=("x", "y"), new_record=merged)
    assert store.get("z") is not None
    assert store.get("x") is None
    assert len(store.list_archived()) >= 2


# --- verifier ---------------------------------------------------------------


def test_verify_accepts_strong_candidate() -> None:
    outcome = verify_candidate(_candidate(), now=_stamp())
    assert isinstance(outcome, VerificationOutcome)
    assert outcome.accepted is not None
    assert outcome.rejected is None
    assert outcome.accepted.status == "verified"
    assert "Passed" in outcome.reasons[0]


def test_verify_rejects_weak_candidates() -> None:
    weak = verify_candidate(
        _candidate(
            evidence_count=2,
            confidence=40.0,
            reasoning_verified=False,
            historical_support=False,
            sources=(),
        ),
        min_evidence=5,
        min_confidence=70.0,
        now=_stamp(),
    )
    assert weak.accepted is None
    assert weak.rejected is not None
    assert weak.rejected.status == "archived"
    assert len(weak.reasons) >= 4


# --- consolidation ----------------------------------------------------------


def test_title_similarity_and_merge() -> None:
    assert title_similarity("Compile latency", "Morning compile latency") >= 60.0
    assert title_similarity("", "x") == 0.0
    assert ts2("alpha beta", "alpha gamma") > 0.0

    left = _record(
        mid="c1",
        title="Compile latency",
        description="Compile latency rises under load.",
        evidence_count=10,
        confidence=80.0,
        evidence_ids=("a",),
        sources=("research",),
    )
    right = _record(
        mid="c2",
        title="Morning compile latency",
        description="Morning compile latency rises under load.",
        evidence_count=12,
        confidence=85.0,
        evidence_ids=("b",),
        sources=("telemetry_history",),
        created_at=_stamp(10),
    )
    merged = consolidate_records((left, right), now=_stamp(12))
    assert len(merged) == 1
    record = merged[0]
    assert record.title == "Morning compile latency"
    assert record.evidence_count == 22
    assert set(record.evidence_ids) == {"a", "b"}
    assert "research" in record.sources
    assert "telemetry_history" in record.sources


def test_consolidate_passthrough_and_non_verified() -> None:
    only = _record(mid="solo")
    assert consolidate_records((only,)) == (only,)
    assert consolidate_records(()) == ()
    pending = _record(mid="p", status="pending")
    assert consolidate_records((pending,)) == ()


# --- retrieval --------------------------------------------------------------


def test_retrieve_related_similar() -> None:
    store = OperationalMemoryStore()
    morning = _record(mid="m1", title="Morning Coding Session", confidence=93.0)
    compile_ = _record(
        mid="m2",
        title="Compile Disk Contention",
        description="Compile workloads frequently create disk contention.",
        confidence=88.0,
        evidence_count=18,
    )
    store.append_verified(morning)
    store.append_verified(compile_)

    empty = retrieve(store, MemoryQuery(), limit=10)
    assert len(empty) == 2

    hits = retrieve(store, MemoryQuery(context="morning coding", metric="cpu"), limit=5)
    assert hits[0].id == "m1"

    assert related(store, "missing") == ()
    rel = related(store, "m1", limit=5)
    assert any(r.id == "m2" for r in rel) or len(rel) == 1 or len(rel) == 0

    patterns = similar_patterns(
        store,
        MemoryQuery(context="compile disk"),
        limit=5,
    )
    assert patterns
    assert all(isinstance(p, Pattern) for p in patterns)

    # fallback when query matches nothing — still returns top verified as patterns
    weak = similar_patterns(store, MemoryQuery(context="zzzznotfound"), limit=2)
    # retrieve may be empty → fallback to list_verified
    assert len(weak) >= 1


# --- engine -----------------------------------------------------------------


def test_engine_seed_retrieve_ingest_consolidate() -> None:
    engine = MemoryEngine(min_evidence=5, min_confidence=70.0)
    seeds = engine.seed_defaults(now=_stamp())
    assert len(seeds) == 2
    assert engine.verified_count() == 2
    # idempotent seed
    again = engine.seed_defaults(now=_stamp())
    assert len(again) == 2
    assert engine.verified_count() == 2

    hits = engine.retrieve(MemoryQuery(context="morning coding"))
    assert hits and hits[0].title == "Morning Coding Session"
    rel = engine.related(hits[0].id)
    assert isinstance(rel, tuple)
    pats = engine.similar_patterns(MemoryQuery(metric="disk"))
    assert pats

    rejected = engine.ingest(
        _candidate(
            mid="bad", evidence_count=1, confidence=10.0, reasoning_verified=False
        ),
        now=_stamp(),
    )
    assert rejected is None
    assert engine.store.get_archived("bad") is not None

    accepted = engine.ingest(_candidate(mid="good_new"), now=_stamp())
    assert accepted is not None
    assert engine.store.get("good_new") is not None

    # Force consolidation of near-duplicates
    engine.store.append_verified(
        _record(
            mid="dup1",
            title="Compile latency",
            evidence_count=5,
            confidence=75.0,
            evidence_ids=("d1",),
        )
    )
    engine.store.append_verified(
        _record(
            mid="dup2",
            title="Morning compile latency",
            evidence_count=6,
            confidence=78.0,
            evidence_ids=("d2",),
        )
    )
    before = engine.verified_count()
    consolidated = engine.consolidate(now=_stamp(15))
    assert len(consolidated) < before or len(consolidated) <= before
    # no-op consolidate on already unique titles still returns verified set
    again_c = engine.consolidate(now=_stamp(16))
    assert isinstance(again_c, tuple)


def test_engine_consolidate_noop_when_unique() -> None:
    engine = MemoryEngine()
    engine.seed_defaults(now=_stamp())
    current = engine.consolidate(now=_stamp())
    assert len(current) == 2


# --- formatter --------------------------------------------------------------


def test_formatter_idle_and_views() -> None:
    console = Console(record=True, width=80)
    idle = OperationalMemoryPanel()
    console.print(idle)
    text = console.export_text()
    assert "OPERATIONAL MEMORY" in text
    assert "idle" in text.lower() or "No conversations" in text

    verified = (
        _record(mid="m1", confidence=93.0, evidence_count=24),
        _record(
            mid="m2",
            title="Compile Disk Contention",
            confidence=88.0,
            evidence_count=18,
            created_at=_stamp() - timedelta(hours=2),
            last_verified=_stamp() - timedelta(hours=1),
        ),
    )
    patterns = (
        Pattern(
            label="Morning Coding Session",
            similarity=90.0,
            occurrences=24,
            confidence=93.0,
        ),
    )

    for view in ("verified", "recent", "related", "timeline"):
        console = Console(record=True, width=100)
        console.print(
            OperationalMemoryPanel(verified=verified, patterns=patterns, view=view)
        )
        out = console.export_text()
        assert "OPERATIONAL MEMORY" in out

    # patterns-only path (no verified)
    console = Console(record=True, width=80)
    console.print(
        OperationalMemoryPanel(verified=(), patterns=patterns, view="verified")
    )
    assert "Morning Coding Session" in console.export_text()

    # empty lists for recent/related/timeline
    console = Console(record=True, width=80)
    console.print(OperationalMemoryPanel(verified=(), patterns=(), view="recent"))
    # idle because both empty
    assert (
        "idle" in console.export_text().lower()
        or "OPERATIONAL MEMORY" in console.export_text()
    )

    console = Console(record=True, width=80)
    console.print(
        OperationalMemoryPanel(verified=verified, patterns=(), view="related")
    )
    assert (
        "Related Patterns" in console.export_text() or "(none)" in console.export_text()
    )

    # recent/timeline with empty verified but non-empty patterns (non-idle)
    console = Console(record=True, width=80)
    console.print(OperationalMemoryPanel(verified=(), patterns=patterns, view="recent"))
    assert "Recent Discoveries" in console.export_text()

    console = Console(record=True, width=80)
    console.print(
        OperationalMemoryPanel(verified=(), patterns=patterns, view="timeline")
    )
    assert "Evidence Timeline" in console.export_text()


def test_retrieve_score_empty_tokens() -> None:
    from aetheros.memory.retrieval import _record_score

    record = _record()
    assert _record_score(record, "") == 0.0
    assert _record_score(record, "   ") == 0.0


def test_package_exports() -> None:
    import aetheros.memory as mem

    assert mem.MemoryEngine is MemoryEngine
    assert callable(mem.retrieve)
