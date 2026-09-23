"""IntentEngine: select a profile and retune decision priority scores.

Read-only regarding the OS — only scoring and persistence change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from aetheros.intent.models import IntentProfile
from aetheros.intent.profiles import (
    DEFAULT_INTENT,
    INTENT_HOTKEYS,
    get_profile,
    list_profile_names,
)
from aetheros.intent.storage import IntentStorage
from aetheros.policy_engine.models import PolicyRecommendation

if TYPE_CHECKING:
    from aetheros.decision.models import Decision

# How strongly profile weights shift a base score (weights are ~0–35).
_WEIGHT_SCALE = 0.35


@dataclass
class IntentEngine:
    """Manage the active intent and apply its weights to decisions.

    Args:
        storage: SQLite-backed persistence for the selected intent.
        initial: Optional override; otherwise restore from storage.
    """

    storage: IntentStorage = field(
        default_factory=lambda: IntentStorage(Path("data/intent.db"))
    )
    initial: str | None = None
    _profile: IntentProfile = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Restore the last intent (or default) on startup."""

        name = self.initial if self.initial is not None else self.storage.load()
        try:
            self._profile = get_profile(name)
        except KeyError:
            self._profile = get_profile(DEFAULT_INTENT)
            self.storage.save(self._profile.name)

    def set_intent(self, name: str) -> IntentProfile:
        """Select a new intent profile and persist it.

        Args:
            name: Profile name or alias.

        Returns:
            The newly active IntentProfile.
        """

        profile = get_profile(name)
        self._profile = profile
        self.storage.save(profile.name)
        return profile

    def set_intent_by_hotkey(self, key: str) -> IntentProfile | None:
        """Select an intent from a dashboard hotkey (1–6).

        Args:
            key: Single character hotkey.

        Returns:
            The new profile, or None if the key is not bound.
        """

        name = INTENT_HOTKEYS.get(key)
        if name is None:
            return None
        return self.set_intent(name)

    def current_intent(self) -> IntentProfile:
        """Return the active IntentProfile."""

        return self._profile

    def available_intents(self) -> tuple[str, ...]:
        """Return built-in intent names in display order."""

        return list_profile_names()

    def bonus_for_recommendation(self, recommendation: PolicyRecommendation) -> int:
        """Compute an additive score bonus for one recommendation.

        Args:
            recommendation: Policy advice being scored.

        Returns:
            Signed integer bonus derived from the active profile weights.
        """

        return self._bonus_for_title(recommendation.title)

    def apply_weights(self, decision: Decision) -> Decision:
        """Return a new Decision with priority adjusted by the active intent.

        Args:
            decision: Base decision from the decision engine.

        Returns:
            A Decision with updated priority_score, action hint, and note.
        """

        from aetheros.decision.models import Decision as DecisionModel

        bonus = self._bonus_for_title(decision.title)
        new_score = int(max(0, min(100, decision.priority_score + bonus)))
        note = (
            f"Intent '{self._profile.name}' adjusted priority "
            f"by {bonus:+d} (score {new_score}/100)."
        )
        explanation = decision.explanation
        if note not in explanation:
            explanation = f"{explanation}\n{note}".strip() if explanation else note
        return DecisionModel(
            title=decision.title,
            severity=decision.severity,
            confidence=decision.confidence,
            priority_score=new_score,
            explanation=explanation,
            action=self.guidance_text(decision),
            timestamp=decision.timestamp,
        )

    def guidance_text(self, decision: Decision | None = None) -> str:
        """Return intent-flavored operator guidance (text only)."""

        profile = self._profile
        if decision is not None and decision.severity in ("warning", "critical"):
            return (
                f"{decision.action} "
                f"(under {profile.name}: {profile.description})"
            ).strip()
        guidance = {
            "Coding": "Prioritize interactive development workloads.",
            "Gaming": "Prioritize foreground game performance; limit background load.",
            "Video Editing": "Protect sustained CPU, memory, and disk throughput.",
            "Battery Saver": "Favor efficiency; reduce unnecessary background work.",
            "AI Training": "Protect maximum compute and memory for training jobs.",
            "Balanced": "Keep resources balanced; no special bias applied.",
        }
        return guidance.get(profile.name, profile.description)

    def _bonus_for_title(self, title: str) -> int:
        """Map a recommendation title onto weighted profile bonuses."""

        profile = self._profile
        lowered = title.lower()
        bonus = 0.0

        if "cpu" in lowered:
            bonus += profile.cpu_weight * _WEIGHT_SCALE
            bonus += profile.latency_weight * _WEIGHT_SCALE * 0.5
        if "memory" in lowered:
            bonus += profile.memory_weight * _WEIGHT_SCALE
        if "disk" in lowered:
            bonus += profile.disk_weight * _WEIGHT_SCALE
        if "idle" in lowered:
            # Battery Saver values idle; performance intents de-emphasize it.
            bonus += profile.efficiency_weight * _WEIGHT_SCALE * 0.5
            if profile.name in {"Gaming", "AI Training", "Video Editing"}:
                bonus -= 8

        # Mild global efficiency nudge for battery mode on any tip.
        if profile.name == "Battery Saver" and "idle" not in lowered:
            bonus += profile.efficiency_weight * _WEIGHT_SCALE * 0.15

        return int(round(bonus))
