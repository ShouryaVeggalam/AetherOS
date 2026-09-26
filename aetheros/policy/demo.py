"""Demo policies for Policy Studio dashboard seeding.

Presentation fixtures only. Never executes OS actions.
"""

from __future__ import annotations

from pathlib import Path

from aetheros.policy.engine import PolicyStudio
from aetheros.policy.parser import parse_rule
from aetheros.policy.registry import PolicyRegistry


def seed_demo_policies(
    registry: PolicyRegistry | None = None,
    *,
    root: Path | None = None,
) -> PolicyStudio:
    """Populate a registry with example governance policies."""

    reg = registry or PolicyRegistry(root=root or Path("data/policy_studio_demo"))
    studio = PolicyStudio(registry=reg)

    # Idempotent seed — skip families that already exist.
    existing = {p.id for p in reg.list_policies(include_archived=True)}

    if "battery-saver" not in existing:
        reg.create(
            id="battery-saver",
            name="Battery Saver",
            description="Reject High Performance when battery is critically low.",
            priority=90,
            rules=(
                parse_rule(
                    "battery < 20",
                    action="Reject High Performance",
                ),
            ),
        )
    if "hyderabad-affinity" not in existing:
        reg.create(
            id="hyderabad-affinity",
            name="Hyderabad Affinity",
            description="Keep workloads inside Hyderabad region.",
            priority=70,
            rules=(
                parse_rule(
                    'region IN ["Hyderabad"]',
                    action="Workloads must remain inside Hyderabad",
                ),
            ),
        )
    if "coding-intent" not in existing:
        reg.create(
            id="coding-intent",
            name="Coding Guard",
            description="When intent is CODING, prefer quiet recommendations.",
            priority=40,
            rules=(parse_rule("intent == CODING", action="Filter noisy batch jobs"),),
        )
    if "cpu-sim-cap" not in existing:
        reg.create(
            id="cpu-sim-cap",
            name="CPU Simulation Cap",
            description="Constrain twin simulations when CPU is elevated.",
            priority=55,
            rules=(
                parse_rule("cpu > 85", action="Constrain twin simulation CPU budget"),
            ),
        )
    return studio
