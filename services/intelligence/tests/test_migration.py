"""Migration contract tests — SQL + upgrade/downgrade with mocked Alembic."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

mod = importlib.import_module(
    "services.intelligence.migrations.0012_general_intelligence_cognition"
)


def test_migration_sql_defines_table() -> None:
    assert "li_gii_cognition_plans" in mod.UPGRADE_SQL
    assert "UUID PRIMARY KEY" in mod.UPGRADE_SQL
    assert "ix_li_gii_cognition_ws_created" in mod.UPGRADE_SQL
    assert "DROP TABLE IF EXISTS li_gii_cognition_plans" in mod.DOWNGRADE_SQL
    assert mod.revision == "0012_general_intelligence_cognition"
    assert mod.down_revision == "0011_world_ingestion"


def test_upgrade_downgrade_call_op_execute() -> None:
    fake_alembic = ModuleType("alembic")
    fake_op = MagicMock()
    fake_alembic.op = fake_op  # type: ignore[attr-defined]
    sys.modules["alembic"] = fake_alembic
    try:
        mod.upgrade()
        mod.downgrade()
    finally:
        sys.modules.pop("alembic", None)
    assert fake_op.execute.call_count == 2
    first = fake_op.execute.call_args_list[0].args[0]
    second = fake_op.execute.call_args_list[1].args[0]
    assert "CREATE TABLE" in first
    assert "DROP TABLE" in second
