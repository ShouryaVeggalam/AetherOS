"""Atlas Federation — node registry, versions, heartbeat age, protocol.

Consumes Federation RegistryView / Heartbeat models. Read-only.
"""

from __future__ import annotations

from datetime import UTC, datetime

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot
from aetheros.atlas.widgets.table import AtlasTable


def render_federation(
    snapshot: AtlasSnapshot,
    *,
    now: datetime | None = None,
) -> RenderableType:
    """Render Federation registry table from snapshot evidence."""

    stamp = now or datetime.now(UTC)
    registry = snapshot.federation_registry
    rows: list[tuple[str, ...]] = []
    if registry is not None:
        nodes = getattr(registry, "nodes", ()) or ()
        for record in nodes:
            identity = getattr(record, "identity", None)
            node_id = getattr(identity, "node_id", getattr(record, "node_id", "?"))
            version = getattr(identity, "version", "—")
            status = str(getattr(record, "status", "unknown"))
            last_seen = getattr(record, "last_seen", None)
            age = _age_seconds(last_seen, stamp)
            rows.append(
                (
                    str(node_id),
                    str(version),
                    status,
                    age,
                    snapshot.protocol_version or "—",
                )
            )

    table = AtlasTable(
        columns=("Node", "Version", "Status", "Heartbeat Age", "Protocol"),
        rows=tuple(rows),
    )
    body = Group(
        Text("FEDERATION", style="bold bright_cyan"),
        Text("Immutable node snapshots · no remote execution", style="dim"),
        Text(""),
        table if rows else Text("  (no registry evidence)", style="dim"),
        Text(""),
        Text(f"Protocol  {snapshot.protocol_version or '—'}", style="dim"),
        Text(
            f"Heartbeats recorded  {len(snapshot.federation_heartbeats)}", style="dim"
        ),
    )
    return Panel(body, title="Atlas · Federation", border_style="bright_cyan")


def _age_seconds(last_seen: object, now: datetime) -> str:
    if last_seen is None or not isinstance(last_seen, datetime):
        return "—"
    seen = last_seen
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=UTC)
    delta = max(0.0, (now - seen).total_seconds())
    if delta < 60:
        return f"{delta:.0f}s"
    if delta < 3600:
        return f"{delta / 60:.0f}m"
    return f"{delta / 3600:.1f}h"
