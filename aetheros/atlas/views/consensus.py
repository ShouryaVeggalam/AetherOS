"""Atlas Global Consensus — findings, conflicts, quorum, recommendation.

References existing ConsensusEngine outputs only. Never approves actions.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot
from aetheros.atlas.widgets.table import AtlasTable


def render_consensus(snapshot: AtlasSnapshot) -> RenderableType:
    """Render multi-agent / global consensus presentation."""

    decision = snapshot.consensus_decision
    findings = snapshot.consensus_findings
    conflicts = snapshot.consensus_conflicts

    if decision is None and not findings:
        body = Text(
            "GLOBAL CONSENSUS idle.\n"
            "No ConsensusDecision / findings in snapshot.\n"
            "Human approval required · never executes.",
            style="dim",
        )
        return Panel(
            body, title="Atlas · Global Consensus", border_style="bright_magenta"
        )

    finding_rows = tuple(
        (
            str(getattr(f, "agent", "?")),
            str(getattr(f, "summary", ""))[:48],
            f"{float(getattr(f, 'confidence', 0.0)):.0f}%",
        )
        for f in findings
    )
    findings_table = AtlasTable(
        columns=("Agent", "Finding", "Confidence"),
        rows=finding_rows,
    )

    supporting = (
        tuple(getattr(decision, "supporting_agents", ()) or ()) if decision else ()
    )
    if not supporting and findings:
        supporting = tuple(str(getattr(f, "agent", "?")) for f in findings)

    conflict_lines: list[Text] = []
    if not conflicts:
        conflict_lines.append(Text("  (none)", style="dim"))
    for conflict in conflicts:
        conflict_lines.append(
            Text(
                f"  · {getattr(conflict, 'topic', 'conflict')}: "
                f"{getattr(conflict, 'summary', conflict)}",
                style="yellow",
            )
        )

    recommendation = "—"
    confidence = 0.0
    quorum = "—"
    if decision is not None:
        recommendation = str(
            getattr(decision, "recommendation", None)
            or getattr(decision, "summary", None)
            or getattr(decision, "action", "—")
        )
        confidence = float(getattr(decision, "confidence", 0.0))
        quorum_val = getattr(decision, "quorum", None)
        if quorum_val is None:
            quorum_val = getattr(decision, "quorum_met", None)
        quorum = (
            str(quorum_val) if quorum_val is not None else f"{len(supporting)} agents"
        )

    body = Group(
        Text("GLOBAL CONSENSUS", style="bold bright_magenta"),
        Text("Evidence merge · human approval required", style="dim"),
        Text(""),
        Text("Node Findings", style="bold"),
        Text(""),
        findings_table if finding_rows else Text("  (none)", style="dim"),
        Text(""),
        Text("Supporting Nodes", style="bold"),
        Text(
            f"  {', '.join(str(a) for a in supporting)}" if supporting else "  (none)",
            style="dim" if not supporting else "",
        ),
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
    return Panel(body, title="Atlas · Global Consensus", border_style="bright_magenta")
