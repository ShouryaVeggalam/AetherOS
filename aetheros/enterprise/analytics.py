"""Enterprise usage analytics — read-only counters.

Exposes API / plugin / research / simulation / policy evaluation metrics.
Never mutates product counters outside this metadata store.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class UsageMetrics:
    """Immutable analytics snapshot."""

    api_usage: int
    plugin_usage: int
    research_activity: int
    simulation_counts: int
    policy_evaluations: int
    generated_at: datetime

    def to_dict(self) -> dict[str, object]:
        """Serialize metrics for JSON reports / UI."""

        return {
            "api_usage": self.api_usage,
            "plugin_usage": self.plugin_usage,
            "research_activity": self.research_activity,
            "simulation_counts": self.simulation_counts,
            "policy_evaluations": self.policy_evaluations,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class AnalyticsService:
    """JSON-backed read/write counter store (metadata only).

    ``record_*`` methods increment counters for enterprise telemetry.
    ``snapshot`` is the read-only public surface for dashboards.
    """

    root: Path = field(default_factory=lambda: Path("data/enterprise"))
    _counts: dict[str, int] = field(default_factory=dict, init=False)
    _loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def store_path(self) -> Path:
        """Path to analytics JSON counters."""

        return self.root / "analytics.json"

    def ensure_loaded(self) -> None:
        """Load counters from disk once."""

        if self._loaded:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._counts = self._read()
        self._loaded = True

    def record_api_usage(self, n: int = 1) -> None:
        """Increment API usage counter."""

        self._bump("api_usage", n)

    def record_plugin_usage(self, n: int = 1) -> None:
        """Increment plugin usage counter."""

        self._bump("plugin_usage", n)

    def record_research_activity(self, n: int = 1) -> None:
        """Increment research activity counter."""

        self._bump("research_activity", n)

    def record_simulation(self, n: int = 1) -> None:
        """Increment simulation counter."""

        self._bump("simulation_counts", n)

    def record_policy_evaluation(self, n: int = 1) -> None:
        """Increment policy evaluation counter."""

        self._bump("policy_evaluations", n)

    def snapshot(self) -> UsageMetrics:
        """Return a read-only metrics snapshot."""

        self.ensure_loaded()
        return UsageMetrics(
            api_usage=int(self._counts.get("api_usage", 0)),
            plugin_usage=int(self._counts.get("plugin_usage", 0)),
            research_activity=int(self._counts.get("research_activity", 0)),
            simulation_counts=int(self._counts.get("simulation_counts", 0)),
            policy_evaluations=int(self._counts.get("policy_evaluations", 0)),
            generated_at=datetime.now(UTC),
        )

    def _bump(self, key: str, n: int) -> None:
        if n < 0:
            raise ValueError("increment must be non-negative")
        self.ensure_loaded()
        self._counts[key] = int(self._counts.get(key, 0)) + n
        self._write()

    def _read(self) -> dict[str, int]:
        if not self.store_path.is_file():
            return {
                "api_usage": 0,
                "plugin_usage": 0,
                "research_activity": 0,
                "simulation_counts": 0,
                "policy_evaluations": 0,
            }
        raw = json.loads(self.store_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        return {str(k): int(v) for k, v in raw.items() if isinstance(v, (int, float))}

    def _write(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps(self._counts, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
