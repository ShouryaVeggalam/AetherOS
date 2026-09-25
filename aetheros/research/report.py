"""Report generator — assemble and export SystemResearchReport artifacts.

Export formats: JSON, Markdown. Rich terminal rendering lives in formatter.py.
No PDF.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from aetheros.research.models import (
    BottleneckFinding,
    Discovery,
    ReportKind,
    ResearchObservation,
    SystemResearchReport,
    TrendAnalysis,
)


def build_report(
    *,
    context: str,
    observations: Sequence[ResearchObservation] = (),
    trends: Sequence[TrendAnalysis] = (),
    bottlenecks: Sequence[BottleneckFinding] = (),
    discoveries: Sequence[Discovery] = (),
    simulations: Sequence[str] = (),
    kind: ReportKind = "research_summary",
    generated_at: datetime | None = None,
    report_id: str | None = None,
) -> SystemResearchReport:
    """Assemble an immutable system research report with a grounded conclusion."""

    stamp = generated_at or datetime.now(UTC)
    obs = tuple(observations)
    tr = tuple(trends)
    bn = tuple(bottlenecks)
    disc = tuple(discoveries)
    sims = tuple(s for s in simulations if s.strip())
    conclusion = _conclusion(
        context=context or "BALANCED",
        observations=obs,
        discoveries=disc,
        bottlenecks=bn,
        kind=kind,
    )
    return SystemResearchReport(
        id=report_id or str(uuid.uuid4()),
        generated_at=stamp,
        context=context or "BALANCED",
        observations=obs,
        trends=tr,
        bottlenecks=bn,
        discoveries=disc,
        simulations=sims,
        conclusion=conclusion,
        kind=kind,
    )


def report_to_dict(report: SystemResearchReport) -> dict[str, Any]:
    """Serialize a report to a JSON-ready dictionary."""

    return {
        "id": report.id,
        "generated_at": report.generated_at.isoformat(),
        "context": report.context,
        "kind": report.kind,
        "observations": [
            {
                "id": o.id,
                "timestamp": o.timestamp.isoformat(),
                "title": o.title,
                "metric": o.metric,
                "value": o.value,
                "evidence": list(o.evidence),
            }
            for o in report.observations
        ],
        "trends": [
            {
                "metric": t.metric,
                "window": t.window,
                "direction": t.direction,
                "confidence": t.confidence,
            }
            for t in report.trends
        ],
        "bottlenecks": [
            {
                "kind": b.kind,
                "title": b.title,
                "summary": b.summary,
                "graph_paths": list(b.graph_paths),
                "evidence_count": b.evidence_count,
                "confidence": b.confidence,
            }
            for b in report.bottlenecks
        ],
        "discoveries": [
            {
                "title": d.title,
                "summary": d.summary,
                "evidence_count": d.evidence_count,
                "confidence": d.confidence,
                "supporting_reasoning": list(d.supporting_reasoning),
                "simulation_agreement": d.simulation_agreement,
            }
            for d in report.discoveries
        ],
        "simulations": list(report.simulations),
        "conclusion": report.conclusion,
    }


def export_json(report: SystemResearchReport, *, indent: int = 2) -> str:
    """Export report as JSON text."""

    return json.dumps(report_to_dict(report), indent=indent)


def export_markdown(report: SystemResearchReport) -> str:
    """Export report as Markdown (publishable, evidence-linked)."""

    lines = [
        f"# Research Report ({report.kind.replace('_', ' ').title()})",
        "",
        f"- **ID:** `{report.id}`",
        f"- **Generated:** {report.generated_at.isoformat()}",
        f"- **Context:** {report.context}",
        f"- **Observations:** {len(report.observations)}",
        f"- **Verified Discoveries:** {len(report.discoveries)}",
        "",
        "## Observations",
        "",
    ]
    if not report.observations:
        lines.append("_None — insufficient evidence._")
        lines.append("")
    for obs in report.observations:
        lines.append(f"### {obs.title}")
        lines.append(f"- Metric: `{obs.metric}` = {obs.value}")
        lines.append("- Evidence:")
        for item in obs.evidence:
            lines.append(f"  - {item}")
        lines.append("")
    lines.extend(["## Trends", ""])
    for trend in report.trends:
        lines.append(
            f"- `{trend.metric}` / `{trend.window}`: **{trend.direction}** "
            f"(confidence {trend.confidence:.0f}%)"
        )
    if not report.trends:
        lines.append("_None._")
    lines.extend(["", "## Bottlenecks", ""])
    if not report.bottlenecks:
        lines.append("_None detected with graph-path evidence._")
        lines.append("")
    for bn in report.bottlenecks:
        lines.append(f"### {bn.title}")
        lines.append(bn.summary)
        lines.append("- Graph paths:")
        for path in bn.graph_paths:
            lines.append(f"  - `{path}`")
        lines.append(
            f"- Evidence count: {bn.evidence_count} · Confidence: {bn.confidence:.0f}%"
        )
        lines.append("")
    lines.extend(["## Discoveries", ""])
    if not report.discoveries:
        lines.append("_No discoveries passed verification gates._")
        lines.append("")
    for disc in report.discoveries:
        lines.append(f"### {disc.title}")
        lines.append(disc.summary)
        lines.append(f"- Evidence: {disc.evidence_count} sessions/samples")
        if disc.simulation_agreement is not None:
            lines.append(f"- Simulation agreement: {disc.simulation_agreement:.0f}%")
        lines.append(f"- Confidence: {disc.confidence:.0f}%")
        lines.append("- Reasoning:")
        for reason in disc.supporting_reasoning:
            lines.append(f"  - {reason}")
        lines.append("")
    lines.extend(["## Simulation Evidence", ""])
    if not report.simulations:
        lines.append("_None provided._")
        lines.append("")
    else:
        for sim in report.simulations:
            lines.append(f"- {sim}")
        lines.append("")
    lines.extend(["## Conclusion", "", report.conclusion, ""])
    lines.append("**Status:** Research Grade — evidence only, no speculative claims.")
    lines.append("")
    return "\n".join(lines)


def _conclusion(
    *,
    context: str,
    observations: Sequence[ResearchObservation],
    discoveries: Sequence[Discovery],
    bottlenecks: Sequence[BottleneckFinding],
    kind: ReportKind,
) -> str:
    if discoveries:
        top = discoveries[0]
        return (
            f"{kind.replace('_', ' ').title()} under context {context}: "
            f"top verified discovery — {top.title} "
            f"(evidence={top.evidence_count}, confidence={top.confidence:.0f}%)."
        )
    if bottlenecks:
        bn = bottlenecks[0]
        return (
            f"{kind.replace('_', ' ').title()} under context {context}: "
            f"primary bottleneck {bn.title} with {bn.evidence_count} evidence "
            f"unit(s); no discovery gates cleared."
        )
    if observations:
        return (
            f"{kind.replace('_', ' ').title()} under context {context}: "
            f"{len(observations)} observation(s) recorded; "
            f"awaiting additional evidence for discovery verification."
        )
    return (
        f"{kind.replace('_', ' ').title()} under context {context}: "
        f"insufficient verified evidence for observations or discoveries."
    )
