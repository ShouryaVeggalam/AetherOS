"""Pure dashboard formatting helpers — no Live loop, no IO.

Extracted from ``app.py`` so unit tests can cover presentation math without
running the Rich Live TUI (which remains coverage-omitted).
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.sdk.registry import PluginRecord
from aetheros.telemetry.models import SystemSnapshot


def format_uptime(seconds: float) -> str:
    """Format boot uptime as a short human string."""

    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def format_battery(system: SystemSnapshot) -> str:
    """Format battery status for the telemetry panel."""

    if system.battery is None:
        return "n/a"
    plugged = "AC" if system.battery.is_plugged_in else "battery"
    return f"{system.battery.percent:.0f}% ({plugged})"


def relative_time(iso_timestamp: str, *, now: datetime | None = None) -> str:
    """Approximate relative time from an ISO timestamp string.

    Args:
        iso_timestamp: ISO-8601 stamp (tz optional).
        now: Optional clock override for deterministic tests.
    """

    try:
        parsed = datetime.fromisoformat(iso_timestamp)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
    except ValueError:
        return "recently"
    anchor = now if now is not None else datetime.now(UTC)
    delta = anchor.astimezone(UTC) - parsed.astimezone(UTC)
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def format_audit_summary(entry: dict[str, object] | None) -> str:
    """Turn the latest audit row into a one-line summary."""

    if entry is None:
        return "No audit entries yet."
    title = str(entry["title"])
    approved = bool(entry["approved"])
    stamp = str(entry["timestamp"])
    verb = "approved" if approved else "blocked"
    ago = relative_time(stamp)
    return f"{title} {verb} {ago}."


def plugin_console_rows(
    records: list[PluginRecord],
) -> tuple[tuple[str, str, str, str, str], ...]:
    """Map plugin records into developer-console table rows."""

    rows: list[tuple[str, str, str, str, str]] = []
    for record in records:
        if not record.verified:
            status = "Rejected"
            safety = "Unsafe"
        elif record.enabled:
            status = "Enabled"
            safety = "Verified"
        else:
            status = "Disabled"
            safety = "Verified"
        rows.append((record.name, record.version, status, record.author, safety))
    return tuple(rows)
