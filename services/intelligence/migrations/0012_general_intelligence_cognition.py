"""Alembic-compatible migration: li_gii_cognition_plans.

Revision ID: 0012_general_intelligence_cognition
Revises: (apply after LI 0011 or standalone in GII deployments)

Runtime Module 1 uses an in-memory repository; this schema is the
forward-compatible PostgreSQL contract (UUID PKs, append-only).
"""

from __future__ import annotations

from collections.abc import Sequence

# Alembic revision metadata (consumed when wired into an Alembic env).
revision: str = "0012_general_intelligence_cognition"
down_revision: str | None = "0011_world_ingestion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS li_gii_cognition_plans (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
    plan JSONB NOT NULL DEFAULT '{}'::jsonb,
    complexity JSONB NOT NULL DEFAULT '{}'::jsonb,
    agents JSONB NOT NULL DEFAULT '[]'::jsonb,
    knowledge JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_li_gii_cognition_ws_created
    ON li_gii_cognition_plans (workspace_id, created_at DESC);
"""

DOWNGRADE_SQL = """
DROP INDEX IF EXISTS ix_li_gii_cognition_ws_created;
DROP TABLE IF EXISTS li_gii_cognition_plans;
"""


def upgrade() -> None:
    """Apply cognition plans schema (requires Alembic ``op`` context)."""

    from alembic import op  # type: ignore[import-not-found]

    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    """Drop cognition plans schema."""

    from alembic import op  # type: ignore[import-not-found]

    op.execute(DOWNGRADE_SQL)
