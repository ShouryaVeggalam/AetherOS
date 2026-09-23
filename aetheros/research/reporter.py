"""Markdown research report writer.

Writes reports/YYYY-MM-DD_HHMM_research.md without touching the OS config.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aetheros.research.models import ResearchReport


def render_markdown(report: ResearchReport) -> str:
    """Render a ResearchReport as a markdown document string."""

    snapshot = report.snapshot
    intent = report.intent
    winner = report.winner

    lines: list[str] = [
        "# AetherOS Research Report",
        "",
        f"Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## System Snapshot",
        "",
        f"- CPU: {snapshot.cpu_percent:.1f}%",
        f"- Memory: {snapshot.memory_percent:.1f}%",
        f"- Disk: {snapshot.disk_percent:.1f}%",
        f"- Processes: {snapshot.process_count}",
        "",
        "## Intent",
        "",
        f"- Name: **{intent.name}**",
        f"- Focus: {intent.description}",
        (
            f"- Weights: CPU {intent.cpu_weight}, Memory {intent.memory_weight}, "
            f"Disk {intent.disk_weight}, Latency {intent.latency_weight}, "
            f"Efficiency {intent.efficiency_weight}"
        ),
        "",
        "## Historical Patterns",
        "",
    ]
    if report.patterns:
        for pattern in report.patterns:
            lines.append(
                f"- **{pattern.name}** (confidence {pattern.confidence}): "
                f"{pattern.description}"
            )
    else:
        lines.append("- None available.")

    lines.extend(["", "## Candidate Strategies", ""])
    for strategy in report.candidates:
        lines.extend(
            [
                f"### {strategy.title}",
                "",
                strategy.description,
                "",
                f"- Expected CPU Δ: {strategy.expected_cpu_delta:+.1f}%",
                f"- Expected Memory Δ: {strategy.expected_memory_delta:+.1f}%",
                f"- Expected Efficiency Δ: {strategy.expected_efficiency_delta:+.1f}",
                "",
            ]
        )

    lines.extend(
        [
            "## Simulation Results",
            "",
            "| Strategy | Performance | Stability | Efficiency | Overall |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for item in report.ranked:
        sim = item.simulation
        lines.append(
            f"| {item.strategy.title} | {sim.performance_score:.1f} | "
            f"{sim.stability_score:.1f} | {sim.efficiency_score:.1f} | "
            f"{sim.overall_improvement:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Ranking Table",
            "",
            "| Rank | Strategy | Rank Score | Reason |",
            "|---:|---|---:|---|",
        ]
    )
    for item in report.ranked:
        lines.append(
            f"| {item.rank} | {item.strategy.title} | {item.rank_score:.1f} | "
            f"{item.reason} |"
        )

    lines.extend(["", "## Winning Strategy", ""])
    if winner is None:
        lines.append("No winning strategy — no candidates were evaluated.")
    else:
        cpu_delta = winner.strategy.expected_cpu_delta
        improvement = abs(cpu_delta) if cpu_delta < 0 else cpu_delta
        lines.extend(
            [
                f"**{winner.strategy.title}**",
                "",
                winner.strategy.description,
                "",
                f"- Rank score: **{winner.rank_score:.0f}**",
                f"- Estimated CPU improvement: **{improvement:.0f}%** "
                f"(delta {cpu_delta:+.1f})",
                f"- Performance: {winner.simulation.performance_score:.1f}",
                f"- Stability: {winner.simulation.stability_score:.1f}",
                f"- Efficiency: {winner.simulation.efficiency_score:.1f}",
                "",
                "## Why It Won",
                "",
                winner.reason,
                "",
                "## Future Recommendation",
                "",
                (
                    f"Keep intent **{intent.name}** active and re-run autonomous "
                    "research after major workload changes. This report is advisory "
                    "only — AetherOS did not modify the operating system."
                ),
            ]
        )

    lines.append("")
    return "\n".join(lines)


def save_report(
    report: ResearchReport,
    *,
    reports_dir: Path | None = None,
    created_at: datetime | None = None,
) -> Path:
    """Write the markdown report to reports/YYYY-MM-DD_HHMM_research.md.

    Args:
        report: Research outcome to serialize.
        reports_dir: Output directory (default: ./reports).
        created_at: Optional timestamp override for the filename.

    Returns:
        Path to the written markdown file.
    """

    stamp = created_at or report.created_at
    directory = Path(reports_dir) if reports_dir is not None else Path("reports")
    directory.mkdir(parents=True, exist_ok=True)
    filename = stamp.strftime("%Y-%m-%d_%H%M_research.md")
    path = directory / filename
    path.write_text(render_markdown(report), encoding="utf-8")
    return path
