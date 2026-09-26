"""Reusable Rich widgets for the operator dashboard.

Widgets accept plain view-model fields and return renderables.
They must not collect telemetry, run policy, or touch the OS.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text


def level_style(percent: float, *, warn: float = 85.0, critical: float = 95.0) -> str:
    """Map a utilization percent to a color style name."""

    if percent >= critical:
        return "bold red"
    if percent >= warn:
        return "bold yellow"
    return "bold green"


def metric_bar(
    label: str, percent: float, *, warn: float = 85.0, critical: float = 95.0
) -> Table:
    """Build a labeled progress bar for one resource metric."""

    style = level_style(percent, warn=warn, critical=critical)
    progress = Progress(
        TextColumn(f"[bold]{label}[/bold]"),
        BarColumn(bar_width=20, complete_style=style, finished_style=style),
        TextColumn(f"[{style}]{{task.percentage:>5.1f}}%[/]"),
        expand=False,
    )
    progress.add_task(label, total=100.0, completed=min(percent, 100.0))
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(progress)
    return grid


@dataclass(frozen=True, slots=True)
class ProcessRow:
    """One process row for the process table widget."""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


@dataclass(frozen=True, slots=True)
class HeaderPanel:
    """Top banner for the dashboard."""

    version: str
    subtitle: str = "Aether Fabric · Simulation Only · Human Controlled"

    def __rich__(self) -> RenderableType:
        """Render the header panel."""

        title = Text(f"AetherOS v{self.version}", style="bold blue")
        sub = Text(self.subtitle, style="cyan")
        return Panel(
            Align.center(Group(title, sub)),
            border_style="blue",
            padding=(0, 1),
        )


@dataclass(frozen=True, slots=True)
class TelemetryPanel:
    """Left-column host resource metrics."""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_text: str
    uptime_text: str

    def __rich__(self) -> RenderableType:
        """Render CPU, memory, disk, battery, and uptime."""

        body = Group(
            metric_bar("CPU", self.cpu_percent),
            metric_bar("Memory", self.memory_percent),
            metric_bar("Disk", self.disk_percent, warn=90.0, critical=95.0),
            Text(""),
            Text.assemble(("Battery  ", "bold"), (self.battery_text, "cyan")),
            Text.assemble(("Uptime   ", "bold"), (self.uptime_text, "cyan")),
        )
        return Panel(body, title="Telemetry", border_style="green")


@dataclass(frozen=True, slots=True)
class ProcessTable:
    """Center-column top processes table."""

    rows: tuple[ProcessRow, ...]

    def __rich__(self) -> RenderableType:
        """Render the top-process table."""

        table = Table(expand=True, show_lines=False)
        table.add_column("PID", justify="right", style="cyan")
        table.add_column("Name", style="white", overflow="fold")
        table.add_column("CPU", justify="right")
        table.add_column("Memory", justify="right")
        for row in self.rows:
            cpu_style = level_style(row.cpu_percent)
            mem_style = level_style(row.memory_percent)
            table.add_row(
                str(row.pid),
                row.name,
                Text(f"{row.cpu_percent:.1f}%", style=cpu_style),
                Text(f"{row.memory_percent:.1f}%", style=mem_style),
            )
        if not self.rows:
            table.add_row("—", "no processes", "—", "—")
        return Panel(table, title="Top 5 Processes", border_style="cyan")


@dataclass(frozen=True, slots=True)
class DecisionPanel:
    """Right-column AI decision summary."""

    title: str
    priority_score: int
    status: str
    explanation: str
    status_style: str = "green"

    def __rich__(self) -> RenderableType:
        """Render the prioritized decision."""

        body = Group(
            Text(self.title, style=f"bold {self.status_style}"),
            Text(""),
            Text.assemble(
                ("Priority Score: ", "bold"),
                (str(self.priority_score), self.status_style),
            ),
            Text.assemble(("Status: ", "bold"), (self.status, self.status_style)),
            Text(""),
            Text("Explanation:", style="bold"),
            Text(self.explanation or "—", style="white"),
        )
        return Panel(body, title="AI Decision", border_style="magenta")


@dataclass(frozen=True, slots=True)
class SafetyPanel:
    """Bottom-row safety and audit summary."""

    status: str
    status_style: str
    approved_count: int
    blocked_count: int
    cooldown_seconds: float
    last_audit_summary: str

    def __rich__(self) -> RenderableType:
        """Render safety status, cooldown, and last audit line."""

        body = Group(
            Text.assemble(
                ("Status: ", "bold"),
                (self.status, self.status_style),
            ),
            Text.assemble(
                ("Approved / Blocked: ", "bold"),
                (f"{self.approved_count} / {self.blocked_count}", "white"),
            ),
            Text.assemble(
                ("Cooldown: ", "bold"),
                (
                    f"{self.cooldown_seconds:.0f}s",
                    "yellow" if self.cooldown_seconds else "green",
                ),
            ),
            Text(""),
            Text("Last Audit Entry:", style="bold"),
            Text(self.last_audit_summary, style="cyan"),
        )
        return Panel(body, title="Safety", border_style="yellow")


@dataclass(frozen=True, slots=True)
class IntentPanel:
    """Panel showing the active user intent and hotkeys."""

    name: str
    description: str
    cpu_weight: int
    memory_weight: int
    disk_weight: int
    latency_weight: int
    efficiency_weight: int

    def __rich__(self) -> RenderableType:
        """Render the current intent profile."""

        body = Group(
            Text(self.name, style="bold cyan"),
            Text(""),
            Text("Focus:", style="bold"),
            Text(self.description, style="white"),
            Text(""),
            Text("Profile:", style="bold"),
            Text(f"CPU {self.cpu_weight}", style="green"),
            Text(f"Memory {self.memory_weight}", style="green"),
            Text(f"Disk {self.disk_weight}", style="green"),
            Text(f"Latency {self.latency_weight}", style="green"),
            Text(f"Efficiency {self.efficiency_weight}", style="green"),
            Text(""),
            Text("1 Coding  2 Gaming  3 Editing", style="dim"),
            Text("4 Battery  5 AI  6 Balanced", style="dim"),
        )
        return Panel(body, title="Current Intent", border_style="cyan")


@dataclass(frozen=True, slots=True)
class ResearchPanel:
    """Panel summarizing the latest autonomous research run."""

    status: str
    strategies_generated: int
    best_score: float
    winning_strategy: str
    estimated_improvement: str
    report_path: str

    def __rich__(self) -> RenderableType:
        """Render research status for the operator."""

        body = Group(
            Text.assemble(("Status: ", "bold"), (self.status, "cyan")),
            Text.assemble(
                ("Strategies Generated: ", "bold"),
                (str(self.strategies_generated), "white"),
            ),
            Text.assemble(
                ("Best Score: ", "bold"),
                (f"{self.best_score:.0f}", "magenta"),
            ),
            Text(""),
            Text("Winning Strategy:", style="bold"),
            Text(self.winning_strategy, style="green"),
            Text(""),
            Text("Estimated Improvement:", style="bold"),
            Text(self.estimated_improvement, style="yellow"),
            Text(""),
            Text(self.report_path, style="dim"),
            Text("Press A → Autonomous Research", style="dim cyan"),
        )
        return Panel(body, title="Research", border_style="magenta")


@dataclass(frozen=True, slots=True)
class DeveloperConsolePanel:
    """Developer Console listing installed plugins and safety summary."""

    rows: tuple[tuple[str, str, str, str, str], ...]
    verified: int
    unsafe: int

    def __rich__(self) -> RenderableType:
        """Render the developer console."""

        table = Table(expand=True, show_lines=False)
        table.add_column("Plugin", style="bold")
        table.add_column("Version")
        table.add_column("Status")
        table.add_column("Author")
        table.add_column("Safety")
        for name, version, status, author, safety in self.rows:
            status_style = "green" if status == "Enabled" else "yellow"
            if status == "Rejected":
                status_style = "red"
            safety_style = "green" if safety == "Verified" else "red"
            table.add_row(
                name,
                version,
                Text(status, style=status_style),
                author,
                Text(safety, style=safety_style),
            )
        body = Group(
            Text("Installed Plugins", style="bold cyan"),
            Text(""),
            table,
            Text(""),
            Text("Safety", style="bold"),
            Text(f"{self.verified} Verified", style="green"),
            Text(f"{self.unsafe} Unsafe", style="red" if self.unsafe else "dim"),
            Text(""),
            Text("Press D to leave Developer Console", style="dim"),
        )
        return Panel(body, title="Developer Console", border_style="blue")


@dataclass(frozen=True, slots=True)
class HelpPanel:
    """Keyboard help overlay content."""

    def __rich__(self) -> RenderableType:
        """Render the help overlay."""

        text = Text.from_markup(
            "[bold cyan]Keyboard[/bold cyan]\n\n"
            "[bold]Q[/bold]  Quit dashboard\n"
            "[bold]?[/bold]  Toggle this help overlay\n"
            "[bold]A[/bold]  Run autonomous research\n"
            "[bold]B[/bold]  Research Lab (twin experiments)\n"
            "[bold]J[/bold]  Multi-Agent Consensus (human approval)\n"
            "[bold]X[/bold]  Research Intelligence (evidence reports)\n"
            "[bold]L[/bold]  Operational Memory (verified patterns)\n"
            "[bold]N[/bold]  Causal Knowledge Graph (verified relations)\n"
            "[bold]D[/bold]  Developer Console (plugins)\n"
            "[bold]V[/bold]  Digital Twin (host what-if)\n"
            "[bold]G[/bold]  Genesis (research intelligence)\n"
            "[bold]S[/bold]  Sentinel (resilience intelligence)\n"
            "[bold]F[/bold]  Fabric (universal intelligence)\n"
            "[bold]U[/bold]  Federation Protocol (node snapshots)\n"
            "[bold]Z[/bold]  Cluster Topology (world → nodes)\n"
            "[bold]/[/bold]  Distributed Scheduler (simulation only)\n"
            "[bold]I[/bold]  Infrastructure Twin (simulation only)\n"
            "[bold]~[/bold]  Infinity (∞ platform overview)\n"
            "[bold]Y[/bold]  Resource Graph (host intelligence)\n"
            "[bold]R[/bold]  Graph Reasoning (causal paths)\n"
            "[bold]H[/bold]  Horizon (planetary intelligence)\n"
            "[bold]M[/bold]  Multi-Agent View (agentic intelligence)\n"
            "[bold]K[/bold]  Cognitive Graph (systems reasoning)\n"
            "[bold]W[/bold]  Workload Planner (orchestrator)\n"
            "[bold]][/bold]  Cycle view / workload\n"
            "[bold]C[/bold]  Cloud Federation (multi-cloud · read-only)\n"
            "[bold];[/bold]  Cluster (multi-device overview)\n"
            "[bold]P[/bold]  Policies (Policy Studio · governance rules)\n"
            "[bold]#[/bold]  Predictive Intelligence (forecasts)\n"
            "[bold]E[/bold]  Enterprise (orgs · RBAC · audit · compliance)\n"
            "[bold]@[/bold]  Extensions (marketplace · sandboxed plugins)\n"
            "[bold]=[/bold]  Explainability (evidence + confidence)\n"
            "[bold]O[/bold]  Observatory (graphs + timeline)\n"
            "[bold]←[/bold]  Scroll observatory history\n"
            "[bold]T[/bold]  Toggle CPU / Memory / Disk graph\n"
            "[bold]ESC[/bold]  Leave overlays\n\n"
            "[bold]1–6[/bold]  Switch intent profile\n"
            "  1 Coding · 2 Gaming · 3 Editing\n"
            "  4 Battery · 5 AI · 6 Balanced\n\n"
            "[dim]Dashboard is read-only. No OS commands are executed.[/dim]"
        )
        return Panel(Align.center(text), title="Help", border_style="blue")
