"""Forward PostgreSQL schema for Aether attention allocations.

Applied by ops when the Aether Lab PostgreSQL database is provisioned.
In-memory repositories remain the default for local / test runs.
"""

from __future__ import annotations

REVISION = "0001_aether_attention"
DOWN_REVISION = None

UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS aether_attention_allocations (
    id              TEXT PRIMARY KEY,
    goal_id         TEXT NOT NULL,
    task_complexity DOUBLE PRECISION NOT NULL,
    available_context DOUBLE PRECISION NOT NULL,
    memory_relevance DOUBLE PRECISION NOT NULL,
    uncertainty     DOUBLE PRECISION NOT NULL,
    weight_focus    DOUBLE PRECISION NOT NULL,
    weight_memory   DOUBLE PRECISION NOT NULL,
    weight_exploration DOUBLE PRECISION NOT NULL,
    weight_verification DOUBLE PRECISION NOT NULL,
    reasoning_budget DOUBLE PRECISION NOT NULL,
    retrieval_budget DOUBLE PRECISION NOT NULL,
    factors         JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence      DOUBLE PRECISION NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aether_attention_goal
    ON aether_attention_allocations (goal_id, created_at DESC);

CREATE TABLE IF NOT EXISTS aether_cognition_plans (
    id               TEXT PRIMARY KEY,
    goal_id          TEXT NOT NULL,
    complexity       TEXT NOT NULL,
    attention_budget DOUBLE PRECISION NOT NULL,
    stages           JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence       DOUBLE PRECISION NOT NULL,
    attention_id     TEXT REFERENCES aether_attention_allocations(id),
    status           TEXT NOT NULL DEFAULT 'draft',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aether_plans_goal
    ON aether_cognition_plans (goal_id, created_at DESC);
"""

DOWNGRADE_SQL = """
DROP TABLE IF EXISTS aether_cognition_plans;
DROP TABLE IF EXISTS aether_attention_allocations;
"""
