"""Operator dashboard — read-only Rich Live UI for the AetherOS pipeline."""

from aetheros.dashboard.app import main, run_dashboard
from aetheros.dashboard.renderer import DashboardFrame, render_frame

__all__ = [
    "DashboardFrame",
    "main",
    "render_frame",
    "run_dashboard",
]
