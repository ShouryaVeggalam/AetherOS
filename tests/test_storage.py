"""Unit tests for P2 architecture cleanup (storage + relation namespaces)."""

from __future__ import annotations

from pathlib import Path
from typing import get_args

from aetheros.knowledge import CausalRelationKind
from aetheros.knowledge import RelationKind as KnowledgeRelationKind
from aetheros.ontology import (
    OntologyRelationKind,
)
from aetheros.ontology import (
    RelationKind as OntologyRelationKindAlias,
)
from aetheros.storage import apply_schema, closing_connection, connect, ensure_db_path


def test_relation_kinds_are_namespaced() -> None:
    """Causal and ontology relation catalogs must remain distinct types."""

    causal = set(get_args(CausalRelationKind))
    ontology = set(get_args(OntologyRelationKind))
    assert "PREDICTS" in causal
    assert "ALLOCATES" in ontology
    assert "ALLOCATES" not in causal
    assert "PREDICTS" not in ontology
    # Compat aliases still resolve.
    assert KnowledgeRelationKind is CausalRelationKind
    assert OntologyRelationKindAlias is OntologyRelationKind


def test_storage_apply_schema_and_connect(tmp_path: Path) -> None:
    """Shared SQLite helpers should create parents, schema, and connections."""

    db = tmp_path / "nested" / "store.db"
    apply_schema(
        db,
        "CREATE TABLE IF NOT EXISTS demo (id INTEGER PRIMARY KEY, name TEXT)",
    )
    assert db.exists()
    with closing_connection(db) as conn:
        conn.execute("INSERT INTO demo (name) VALUES (?)", ("aether",))
        conn.commit()
    with connect(db) as conn:
        row = conn.execute("SELECT name FROM demo").fetchone()
    assert row is not None
    assert row[0] == "aether"
    assert ensure_db_path(db) == db
