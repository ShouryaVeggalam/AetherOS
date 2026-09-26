"""Horizon Cloud — multi-cloud federation health (presentation only).

Consumes cloud snapshot / health / provider records. Never provisions.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.table import HorizonTable

_PROVIDER_ORDER = ("aws", "azure", "gcp", "kubernetes", "docker", "edge")


def render_cloud(snapshot: HorizonSnapshot) -> RenderableType:
    """Render Cloud Federation page from immutable cloud fields."""

    records = tuple(snapshot.cloud_records or ())
    by_kind: dict[str, object] = {}
    for record in records:
        provider = getattr(record, "provider", None)
        pid = str(getattr(provider, "id", "") or "").lower()
        pname = str(getattr(provider, "name", "") or "").lower()
        kind = "unknown"
        for token in _PROVIDER_ORDER:
            if (
                pid == token
                or pid.startswith(f"{token}-")
                or pname == token
                or token in pid
                or (token == "gcp" and "google" in pname)
                or (token == "kubernetes" and ("k8s" in pid or "kubernetes" in pname))
            ):
                kind = token
                break
        by_kind[kind] = record

    rows: list[tuple[str, ...]] = []
    for kind in _PROVIDER_ORDER:
        record = by_kind.get(kind)
        if record is None:
            rows.append((kind.upper(), "—", "offline", "—"))
            continue
        status = str(getattr(record, "status", "unknown"))
        age = getattr(record, "snapshot_age_seconds", None)
        if age is None:
            age = getattr(record, "age_seconds", snapshot.cloud_age_seconds)
        resources = getattr(record, "resource_count", 0)
        rows.append(
            (
                kind.upper(),
                str(resources),
                status,
                f"{float(age):.0f}s",
            )
        )

    health = snapshot.cloud_health
    health_line = "  —"
    if health is not None:
        conf = float(getattr(health, "confidence", 0.0))
        if conf <= 1.0:
            conf *= 100.0
        health_line = (
            f"  online={getattr(health, 'online', 0)}  "
            f"degraded={getattr(health, 'degraded', 0)}  "
            f"offline={getattr(health, 'offline', 0)}  "
            f"confidence={conf:.0f}%"
        )

    table = HorizonTable(
        columns=("Provider", "Resources", "Status", "Age"),
        rows=tuple(rows),
    )
    body = Group(
        Text("CLOUD FEDERATION", style="bold bright_cyan"),
        Text("AWS · Azure · GCP · Kubernetes · Docker · Edge", style="dim"),
        Text(""),
        Text("Federation Health", style="bold"),
        Text(health_line),
        Text(""),
        Text(f"Snapshot age  {snapshot.cloud_age_seconds:.0f}s", style="dim"),
        Text(""),
        table,
        Text(""),
        Text("Status  Read-only · no provisioning", style="dim"),
    )
    return Panel(body, title="Horizon · Cloud Federation", border_style="bright_cyan")
