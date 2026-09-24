"""DecisionEngine: Telemetry → Policy → Safety → one Decision.

Produces a single prioritized Decision. Never executes actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aetheros.decision.models import Decision, utc_now
from aetheros.decision.prioritizer import ScoredRecommendation, prioritize
from aetheros.decision.scorer import score_recommendation
from aetheros.intent import IntentEngine
from aetheros.policy_engine import PolicyEngine, PolicyRecommendation, TelemetrySnapshot
from aetheros.safety import AuditLogger, CooldownManager, SafetyResult, SafetyValidator


@dataclass(frozen=True, slots=True)
class DecisionReport:
    """Full pipeline output for demos and debugging.

    Attributes:
        snapshot: Input telemetry.
        approved: Recommendations that passed safety.
        rejected: Recommendations blocked or cooled down.
        decision: Winning Decision, or None if nothing approved.
    """

    snapshot: TelemetrySnapshot
    approved: tuple[PolicyRecommendation, ...]
    rejected: tuple[tuple[PolicyRecommendation, SafetyResult], ...]
    decision: Decision | None


@dataclass
class DecisionEngine:
    """Orchestrate policy + safety and pick one prioritized decision.

    Args:
        policy: Policy engine used to generate recommendations.
        safety: Safety validator that approves or blocks advice.
        intent: Intent engine that retunes priority scores.
    """

    policy: PolicyEngine = field(default_factory=PolicyEngine)
    safety: SafetyValidator = field(
        default_factory=lambda: SafetyValidator(
            cooldown=CooldownManager(),
            audit=AuditLogger(Path("data/safety_audit.db")),
        )
    )
    intent: IntentEngine = field(default_factory=IntentEngine)

    def evaluate(self, snapshot: TelemetrySnapshot) -> Decision | None:
        """Run the full pipeline and return one Decision, if any.

        Args:
            snapshot: Flat telemetry sample.

        Returns:
            The highest-priority approved Decision, or None when nothing
            is approved (healthy system or everything blocked).
        """

        return self.evaluate_report(snapshot).decision

    def evaluate_report(
        self,
        snapshot: TelemetrySnapshot,
        *,
        record: bool = True,
    ) -> DecisionReport:
        """Run the pipeline and return decision plus approval context.

        Args:
            snapshot: Flat telemetry sample.
            record: When True, write safety decisions to the audit log and
                update cooldowns. Dashboard live refresh should pass False
                to avoid flooding the log every second.

        Returns:
            A DecisionReport with approved/rejected lists and the winner.
        """

        recommendations = self.policy.evaluate_all(snapshot)
        if not recommendations:
            return DecisionReport(
                snapshot=snapshot,
                approved=(),
                rejected=(),
                decision=None,
            )

        cooled_before = {
            rec.title: self.safety.cooldown.is_cooling_down(rec.title)
            for rec in recommendations
        }

        validated = self.safety.validate_all(recommendations, record=record)
        approved = tuple(rec for rec, result in validated if result.approved)
        rejected = tuple(
            (rec, result) for rec, result in validated if not result.approved
        )

        if not approved:
            return DecisionReport(
                snapshot=snapshot,
                approved=(),
                rejected=rejected,
                decision=None,
            )

        scored: list[ScoredRecommendation] = []
        for rec in approved:
            points = score_recommendation(
                rec,
                snapshot,
                recently_cooled=cooled_before.get(rec.title, False),
            )
            points = int(
                max(
                    0,
                    min(100, points + self.intent.bonus_for_recommendation(rec)),
                )
            )
            scored.append(
                ScoredRecommendation(recommendation=rec, priority_score=points)
            )

        winner = prioritize(scored)
        if winner is None:
            return DecisionReport(
                snapshot=snapshot,
                approved=approved,
                rejected=rejected,
                decision=None,
            )

        rec = winner.recommendation
        draft = Decision(
            title=rec.title,
            severity=rec.level,
            confidence=rec.confidence,
            priority_score=winner.priority_score,
            explanation="",
            action=rec.recommended_action,
            timestamp=utc_now(),
        )
        explanation = self.explain(draft, snapshot=snapshot, approved=list(approved))
        profile = self.intent.current_intent()
        explanation = (
            f"{explanation}\n" f"Active intent: {profile.name} — {profile.description}"
        ).strip()
        decision = Decision(
            title=draft.title,
            severity=draft.severity,
            confidence=draft.confidence,
            priority_score=draft.priority_score,
            explanation=explanation,
            action=self.intent.guidance_text(draft),
            timestamp=draft.timestamp,
        )
        return DecisionReport(
            snapshot=snapshot,
            approved=approved,
            rejected=rejected,
            decision=decision,
        )

    def explain(
        self,
        decision: Decision,
        *,
        snapshot: TelemetrySnapshot | None = None,
        approved: list[PolicyRecommendation] | None = None,
    ) -> str:
        """Build a beginner-friendly explanation for a Decision.

        Args:
            decision: The chosen decision to explain.
            snapshot: Optional telemetry used for resource context.
            approved: Optional list of approved recommendations for context.

        Returns:
            Multi-line explanation string.
        """

        lines: list[str] = []

        if snapshot is not None:
            lines.append(f"CPU usage reached {snapshot.cpu_percent:.0f}%.")
            if snapshot.memory_percent < 85.0:
                lines.append("Memory is stable.")
            else:
                lines.append(
                    f"Memory usage is elevated at {snapshot.memory_percent:.0f}%."
                )
            if snapshot.disk_percent >= 90.0:
                lines.append(f"Disk usage is elevated at {snapshot.disk_percent:.0f}%.")

        lines.append(
            f"This recommendation received the highest priority score "
            f"({decision.priority_score}/100)."
        )

        if approved and len(approved) > 1:
            others = [item.title for item in approved if item.title != decision.title]
            if others:
                lines.append(
                    "Other approved advice was considered but ranked lower: "
                    + ", ".join(others)
                    + "."
                )

        if decision.severity == "critical":
            lines.append(
                f"{decision.title} is the top priority while other resources "
                "were compared for relative stability."
            )

        return "\n".join(lines)
