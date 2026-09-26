"""Atlas Health — unified green / yellow / red subsystem diagnostics.

Presentation indicators only. Never runs health probes itself.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot, HealthSignal
from aetheros.atlas.widgets.table import AtlasTable

_DEFAULT_NAMES = (
    "Telemetry",
    "Graph",
    "Memory",
    "Reasoning",
    "Scheduler",
    "Consensus",
    "Federation",
)


def render_health(snapshot: AtlasSnapshot) -> RenderableType:
    """Render unified health board from snapshot signals."""

    signals = snapshot.health_signals or _derive_signals(snapshot)
    rows = tuple(
        (
            signal.name,
            _glyph(signal.status),
            signal.status.upper(),
            signal.detail or "—",
        )
        for signal in signals
    )
    table = AtlasTable(
        columns=("Subsystem", "", "Status", "Detail"),
        rows=rows,
    )
    body = Group(
        Text("HEALTH", style="bold bright_white"),
        Text("Unified diagnostics · green / yellow / red only", style="dim"),
        Text(""),
        table,
        Text(""),
        Text("Legend  ● green  ● yellow  ● red", style="dim"),
    )
    return Panel(body, title="Atlas · Health", border_style="bright_white")


def _glyph(status: str) -> str:
    if status == "green":
        return "●"
    if status == "yellow":
        return "●"
    return "●"


def _derive_signals(snapshot: AtlasSnapshot) -> tuple[HealthSignal, ...]:
    """Best-effort signals from snapshot presence / thresholds (presentation)."""

    def _resource(name: str, percent: float) -> HealthSignal:
        if percent >= 85.0:
            return HealthSignal(name, "red", f"{percent:.0f}%")
        if percent >= 70.0:
            return HealthSignal(name, "yellow", f"{percent:.0f}%")
        return HealthSignal(name, "green", f"{percent:.0f}%")

    telemetry = _resource(
        "Telemetry", max(snapshot.cpu_percent, snapshot.memory_percent)
    )
    federation = (
        HealthSignal("Federation", "green", f"{snapshot.online_nodes} online")
        if snapshot.online_nodes > 0
        else HealthSignal("Federation", "yellow", "no online nodes")
    )
    graph = (
        HealthSignal("Graph", "green", "topology present")
        if snapshot.topology_graph is not None
        else HealthSignal("Graph", "yellow", "no topology")
    )
    memory = HealthSignal(
        "Memory",
        "green" if snapshot.memory_percent < 85 else "red",
        f"{snapshot.memory_percent:.0f}%",
    )
    reasoning = (
        HealthSignal("Reasoning", "green", "consensus ready")
        if snapshot.consensus_decision is not None
        else HealthSignal("Reasoning", "yellow", "no consensus")
    )
    scheduler = (
        HealthSignal("Scheduler", "green", "plan ready")
        if snapshot.schedule_result is not None
        else HealthSignal("Scheduler", "yellow", "idle")
    )
    consensus = (
        HealthSignal(
            "Consensus",
            "green",
            f"{float(getattr(snapshot.consensus_decision, 'confidence', 0)):.0f}%",
        )
        if snapshot.consensus_decision is not None
        else HealthSignal("Consensus", "yellow", "idle")
    )
    # Keep order aligned with _DEFAULT_NAMES, substituting Telemetry for host.
    ordered = {
        "Telemetry": telemetry,
        "Graph": graph,
        "Memory": memory,
        "Reasoning": reasoning,
        "Scheduler": scheduler,
        "Consensus": consensus,
        "Federation": federation,
    }
    return tuple(ordered[name] for name in _DEFAULT_NAMES)
