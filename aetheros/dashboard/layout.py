"""Rich Layout skeleton for the operator dashboard.

Creates named regions only. Does not fill them with data — the
renderer assigns widgets into these slots.
"""

from __future__ import annotations

from rich.layout import Layout


def build_layout() -> Layout:
    """Create the dashboard layout tree with named regions.

    Regions:
        header   — top banner
        left     — telemetry metrics
        intent   — current intent profile
        center   — process table (or help overlay)
        right    — AI decision
        research — autonomous research summary
        bottom   — safety / audit
        footer   — key hints

    Returns:
        A Rich Layout ready for the renderer to populate.
    """

    root = Layout(name="root")
    root.split_column(
        Layout(name="header", size=5),
        Layout(name="body", ratio=3),
        Layout(name="bottom", size=8),
        Layout(name="footer", size=3),
    )
    root["body"].split_row(
        Layout(name="left_column", ratio=1),
        Layout(name="center", ratio=2),
        Layout(name="right_column", ratio=1),
    )
    root["left_column"].split_column(
        Layout(name="left", ratio=1),
        Layout(name="intent", ratio=1),
    )
    root["right_column"].split_column(
        Layout(name="right", ratio=1),
        Layout(name="research", ratio=1),
    )
    return root
