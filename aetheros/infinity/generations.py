"""Infinity generation catalog — immutable map of AetherOS eras.

Documents v1–v9 without mutating runtime behavior of prior packages.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Generation:
    """One immutable platform generation descriptor.

    Attributes:
        version: Semver major label (e.g. ``v3``).
        codename: Marketing / research name.
        package: Primary package path under ``aetheros``.
        summary: One-line capability statement.
        principles: Core invariants for the generation.
    """

    version: str
    codename: str
    package: str
    summary: str
    principles: tuple[str, ...]


GENERATIONS: tuple[Generation, ...] = (
    Generation(
        "v1",
        "Operating Intelligence",
        "aetheros.telemetry / policy / safety / decision / observatory / explainability",
        "Observe, advise, record, and explain local host pressure.",
        ("read-only telemetry", "human approval", "userspace"),
    ),
    Generation(
        "v2",
        "Resource Graph",
        "aetheros.kernel / knowledge / orchestrator",
        "Userspace resource context and workload planning.",
        ("no kernel modules", "recommendation-only placement"),
    ),
    Generation(
        "v3",
        "Cognitive Reasoning",
        "aetheros.cognition / reasoning / knowledge",
        "Causal graphs, hypotheses, verification, memory.",
        ("systems reasoning not LLM", "verified claims only"),
    ),
    Generation(
        "v4",
        "Multi-Agent Intelligence",
        "aetheros.agents / messaging / runtime",
        "Specialist agents on an immutable message bus.",
        ("no direct agent coupling", "coordinator conflict resolution"),
    ),
    Generation(
        "v5",
        "Atlas",
        "aetheros.atlas",
        "Global infrastructure hierarchy + digital twin facade.",
        ("World→Region→DC→Cluster→Node", "simulation-first"),
    ),
    Generation(
        "v6",
        "Horizon",
        "aetheros.horizon / edge / robotics",
        "Planetary latency, capacity, and resilience intelligence.",
        ("no live network probes", "census + sample graph"),
    ),
    Generation(
        "v7",
        "Genesis",
        "aetheros.genesis / ontology",
        "Research hypotheses, experiments, verified knowledge.",
        ("unsupported claims rejected", "research only"),
    ),
    Generation(
        "v8",
        "Sentinel",
        "aetheros.sentinel / graph",
        "Anomaly detection, root cause, cascade, recovery advice.",
        ("never executes recovery", "simulation only"),
    ),
    Generation(
        "v9",
        "Fabric",
        "aetheros.fabric / protocol / twin",
        "Universal federation graph and global digital twin.",
        ("eventual consistency", "human controlled"),
    ),
    Generation(
        "∞",
        "Infinity",
        "aetheros.infinity",
        "Unifying intelligence layer — pipeline, map, and evidence.",
        ("preserve all prior versions", "explainable end-to-end"),
    ),
)
