"""Policy Studio models — immutable governance rules and evaluation results.

Policies never control the OS. They only filter recommendations, constrain
Digital Twin simulations / Scheduler placement, and annotate research.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Supported comparison operators (uppercase tokens + symbolic forms).
OPERATORS: frozenset[str] = frozenset(
    {
        "==",
        "!=",
        ">",
        "<",
        ">=",
        "<=",
        "IN",
        "NOT_IN",
    }
)

PolicyStatus = str  # "draft" | "published" | "archived"


@dataclass(frozen=True, slots=True)
class Rule:
    """One immutable governance predicate + advisory action.

    Attributes:
        field: Context field name (e.g. ``battery``, ``region``, ``intent``).
        operator: Comparison operator from ``OPERATORS``.
        value: Right-hand side literal (scalar or tuple for IN / NOT_IN).
        action: Advisory action label (never executed against the OS).
    """

    field: str
    operator: str
    value: Any
    action: str

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("field must be non-empty")
        op = self.operator.strip().upper().replace(" ", "")
        # Normalize aliases
        aliases = {">=": ">=", "<=": "<=", "NOTIN": "NOT_IN"}
        normalized = aliases.get(op, op)
        if normalized == "NOTIN":
            normalized = "NOT_IN"
        if self.operator != normalized:
            object.__setattr__(self, "operator", normalized)
        if self.operator not in OPERATORS:
            raise ValueError(f"unsupported operator: {self.operator!r}")
        if not str(self.action).strip():
            raise ValueError("action must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON persistence."""

        value: Any = self.value
        if isinstance(value, tuple):
            value = list(value)
        return {
            "field": self.field,
            "operator": self.operator,
            "value": value,
            "action": self.action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Build a Rule from a mapping."""

        raw_value = data.get("value")
        if isinstance(raw_value, list):
            raw_value = tuple(raw_value)
        return cls(
            field=str(data.get("field") or "").strip(),
            operator=str(data.get("operator") or "").strip(),
            value=raw_value,
            action=str(data.get("action") or "").strip(),
        )


@dataclass(frozen=True, slots=True)
class Policy:
    """Versioned, immutable governance policy (after publication).

    Attributes:
        id: Stable policy family id (unchanged across versions).
        name: Human-readable name.
        description: Short summary.
        priority: Higher wins when multiple policies match (int).
        enabled: Whether the policy participates in evaluation.
        created_at: Version creation timestamp.
        version: Monotonic version number within the family.
        status: ``draft`` | ``published`` | ``archived``.
        rules: Immutable rule tuple.
    """

    id: str
    name: str
    description: str
    priority: int
    enabled: bool
    created_at: datetime
    version: int = 1
    status: str = "draft"
    rules: tuple[Rule, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if self.version < 1:
            raise ValueError("version must be >= 1")
        if self.status not in {"draft", "published", "archived"}:
            raise ValueError(f"invalid status: {self.status!r}")

    @property
    def key(self) -> str:
        """Unique versioned key ``{id}@v{version}``."""

        return f"{self.id}@v{self.version}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON persistence."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
            "status": self.status,
            "rules": [r.to_dict() for r in self.rules],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Policy:
        """Parse a Policy from a mapping."""

        raw_rules = data.get("rules") or ()
        rules: list[Rule] = []
        if isinstance(raw_rules, list):
            for item in raw_rules:
                if isinstance(item, dict):
                    rules.append(Rule.from_dict(item))
        return cls(
            id=str(data.get("id") or "").strip(),
            name=str(data.get("name") or "").strip(),
            description=str(data.get("description") or "").strip(),
            priority=int(data.get("priority") or 0),
            enabled=bool(data.get("enabled", True)),
            created_at=datetime.fromisoformat(str(data.get("created_at") or "")),
            version=int(data.get("version") or 1),
            status=str(data.get("status") or "draft"),
            rules=tuple(rules),
        )


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Deterministic outcome of evaluating one policy against a context."""

    matched: bool
    policy: Policy
    explanation: str
    confidence: float
    action: str = ""
    rule: Rule | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for presentation / tests."""

        return {
            "matched": self.matched,
            "policy_id": self.policy.id,
            "policy_version": self.policy.version,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "action": self.action,
            "rule": self.rule.to_dict() if self.rule else None,
        }


@dataclass(frozen=True, slots=True)
class SimulationImpact:
    """Read-only summary of how policies would constrain a simulation."""

    matched: tuple[EvaluationResult, ...]
    filtered_recommendations: tuple[str, ...]
    constraints: tuple[str, ...]
    explanations: tuple[str, ...]

    @property
    def applied(self) -> bool:
        """True when at least one policy matched."""

        return any(r.matched for r in self.matched)
