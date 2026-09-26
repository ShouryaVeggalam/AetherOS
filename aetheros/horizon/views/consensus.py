"""Horizon Consensus — node findings, votes, conflicts, quorum.

Consumes consensus decision / findings. Presentation only.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.table import HorizonTable


def render_consensus(snapshot: HorizonSnapshot) -> RenderableType:
    """Render global consensus presentation from snapshot fields."""

    decision = snapshot.consensus_decision
    findings = tuple(snapshot.consensus_findings or ())
    conflicts = tuple(snapshot.consensus_conflicts or ())

    if decision is None and not findings:
        body = Text(
            "GLOBAL CONSENSUS idle.\nNo consensus decision in snapshot.\nRead-only.",
            style="dim",
        )
        return Panel(
            body, title="Horizon · Global Consensus", border_style="bright_green"
        )

    finding_rows = tuple(
        (
            str(getattr(f, "node_id", getattr(f, "agent", "?"))),
            str(getattr(f, "finding", getattr(f, "summary", "—"))),
            str(getattr(f, "vote", "—")),
        )
        for f in findings
    )
    findings_table = HorizonTable(
        columns=("Node", "Finding", "Vote"),
        rows=finding_rows,
    )
    conflict_lines: list[Text] = []
    if not conflicts:
        conflict_lines.append(Text("  (none)", style="dim"))
    for item in conflicts:
        topic = getattr(item, "topic", getattr(item, "versus_node", "conflict"))
        detail = getattr(item, "detail", getattr(item, "summary", ""))
        conflict_lines.append(Text(f"  · {topic}"))
        if detail:
            conflict_lines.append(Text(f"    {detail}", style="dim"))

    recommendation = (
        str(getattr(decision, "recommendation", getattr(decision, "summary", "—")))
        if decision is not None
        else "—"
    )
    confidence = (
        float(getattr(decision, "confidence", snapshot.consensus_confidence))
        if decision is not None
        else snapshot.consensus_confidence
    )
    quorum = (
        "met"
        if bool(getattr(decision, "quorum_met", True))
        else "not met" if decision is not None else "—"
    )
    votes = "—"
    if decision is not None:
        votes = (
            f"for={getattr(decision, 'votes_for', '?')}  "
            f"against={getattr(decision, 'votes_against', '?')}"
        )

    body = Group(
        Text("GLOBAL CONSENSUS", style="bold bright_green"),
        Text("Multi-node findings · read-only", style="dim"),
        Text(""),
        Text("Node Findings", style="bold"),
        Text(""),
        findings_table if finding_rows else Text("  (none)", style="dim"),
        Text(""),
        Text("Votes", style="bold"),
        Text(f"  {votes}"),
        Text(""),
        Text("Conflicts", style="bold"),
        *conflict_lines,
        Text(""),
        Text("Quorum", style="bold"),
        Text(f"  {quorum}"),
        Text(""),
        Text("Final Recommendation", style="bold"),
        Text(f"  {recommendation}"),
        Text(""),
        Text("Confidence", style="bold"),
        Text(f"  {confidence:.0f}%"),
    )
    return Panel(body, title="Horizon · Global Consensus", border_style="bright_green")
