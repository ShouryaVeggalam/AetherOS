"""Tests for v5.0 P4 Policy Studio."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from rich.console import Console

from aetheros.policy import (
    OPERATORS,
    Comparison,
    EvaluationResult,
    FieldRef,
    Literal,
    Policy,
    PolicyEngine,
    PolicyRegistry,
    PolicyStudio,
    PolicyStudioPanel,
    Rule,
    SimulationImpact,
    TelemetrySnapshot,
    constraints_from_results,
    evaluate_policy,
    evaluate_rule,
    filter_recommendations,
    parse_expression,
    parse_rule,
    rule_to_expression,
    seed_demo_policies,
)


def _print(renderable: object) -> str:
    console = Console(record=True, width=100)
    console.print(renderable)
    return console.export_text()


def _policy(**overrides: object) -> Policy:
    base: dict[str, object] = dict(
        id="battery-saver",
        name="Battery Saver",
        description="demo",
        priority=90,
        enabled=True,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        version=1,
        status="published",
        rules=(parse_rule("battery < 20", action="Reject High Performance"),),
    )
    base.update(overrides)
    return Policy(**base)  # type: ignore[arg-type]


def test_legacy_reexports_intact() -> None:
    assert PolicyEngine is not None
    assert TelemetrySnapshot is not None


def test_parser_ast_and_operators() -> None:
    assert "==" in OPERATORS
    cmp = parse_expression("battery < 20")
    assert isinstance(cmp, Comparison)
    assert isinstance(cmp.field, FieldRef)
    assert isinstance(cmp.value, Literal)
    assert cmp.operator == "<"
    assert cmp.value.value == 20
    rule = parse_rule('region IN ["Hyderabad", "Pune"]', action="Stay local")
    assert rule.operator == "IN"
    assert rule.value == ("Hyderabad", "Pune")
    assert "region IN" in rule_to_expression(rule)
    assert parse_expression("intent == CODING").value.value == "CODING"
    assert parse_expression("flag != false").value.value is False
    assert parse_expression("x >= 1.5").operator == ">="
    assert parse_expression("y NOT IN [1, 2]").operator == "NOT_IN"
    with pytest.raises(ValueError):
        parse_expression("")
    with pytest.raises(ValueError):
        parse_expression("battery")
    with pytest.raises(ValueError):
        parse_expression("< 20")


def test_rule_and_policy_models() -> None:
    rule = Rule(
        field="battery", operator="<", value=20, action="Reject High Performance"
    )
    assert rule.to_dict()["operator"] == "<"
    assert Rule.from_dict(rule.to_dict()).action.startswith("Reject")
    with pytest.raises(ValueError):
        Rule(field="", operator="<", value=1, action="x")
    with pytest.raises(ValueError):
        Rule(field="a", operator="~~", value=1, action="x")
    with pytest.raises(ValueError):
        Rule(field="a", operator="<", value=1, action="")

    policy = _policy()
    assert policy.key == "battery-saver@v1"
    assert Policy.from_dict(policy.to_dict()).name == "Battery Saver"
    with pytest.raises(ValueError):
        _policy(id="")
    with pytest.raises(ValueError):
        _policy(version=0)
    with pytest.raises(ValueError):
        _policy(status="bogus")

    result = EvaluationResult(
        matched=True, policy=policy, explanation="ok", confidence=0.9, action="Reject"
    )
    assert result.to_dict()["matched"] is True
    impact = SimulationImpact(
        matched=(result,),
        filtered_recommendations=("Balanced",),
        constraints=("c",),
        explanations=("e",),
    )
    assert impact.applied is True


def test_evaluator_comparisons() -> None:
    ctx = {"battery": 15, "intent": "CODING", "region": "Hyderabad", "cpu": 90}
    ok, _ = evaluate_rule(parse_rule("battery < 20", action="a"), ctx)
    assert ok is True
    ok, _ = evaluate_rule(parse_rule("battery > 20", action="a"), ctx)
    assert ok is False
    ok, _ = evaluate_rule(parse_rule("intent == CODING", action="a"), ctx)
    assert ok is True
    ok, _ = evaluate_rule(parse_rule('region IN ["Hyderabad"]', action="a"), ctx)
    assert ok is True
    ok, _ = evaluate_rule(parse_rule('region NOT_IN ["Hyderabad"]', action="a"), ctx)
    assert ok is False
    ok, _ = evaluate_rule(parse_rule("missing == 1", action="a"), ctx)
    assert ok is False
    ok, _ = evaluate_rule(parse_rule("intent > 5", action="a"), ctx)
    assert ok is False

    policy = _policy()
    matched = evaluate_policy(policy, ctx)
    assert matched.matched is True
    disabled = evaluate_policy(_policy(enabled=False), ctx)
    assert disabled.matched is False
    archived = evaluate_policy(_policy(status="archived"), ctx)
    assert archived.matched is False
    empty = evaluate_policy(_policy(rules=()), ctx)
    assert empty.matched is False


def test_registry_versioning(tmp_path: Path) -> None:
    reg = PolicyRegistry(root=tmp_path / "ps")
    p1 = reg.create(
        id="battery-saver",
        name="Battery Saver",
        description="v1",
        rules=(parse_rule("battery < 20", action="Reject High Performance"),),
        priority=90,
    )
    assert p1.version == 1
    with pytest.raises(ValueError):
        reg.create(
            id="battery-saver",
            name="dup",
            description="d",
            rules=(parse_rule("battery < 10", action="x"),),
        )
    p2 = reg.new_version(
        "battery-saver",
        description="v2",
        rules=(parse_rule("battery < 15", action="Reject High Performance"),),
    )
    assert p2.version == 2
    assert len(reg.versions("battery-saver")) == 2
    disabled = reg.disable("battery-saver")
    assert disabled.enabled is False
    assert disabled.version == 3
    enabled = reg.enable("battery-saver")
    assert enabled.enabled is True
    archived = reg.archive("battery-saver")
    assert archived.status == "archived"
    assert reg.list_policies() == ()
    assert reg.list_policies(include_archived=True)
    assert reg.get_policy("battery-saver", version=1) is not None
    assert reg.get_policy("nope") is None
    with pytest.raises(KeyError):
        reg.enable("missing")
    with pytest.raises(ValueError):
        reg.enable("battery-saver")  # archived head

    # persistence round-trip
    reg2 = PolicyRegistry(root=tmp_path / "ps")
    assert reg2.get_policy("battery-saver") is not None
    # corrupt store
    reg2.store_path.write_text("[]\n", encoding="utf-8")
    reg2.reload()
    assert reg2.list_policies(include_archived=True) == ()


def test_engine_validate_evaluate_simulate(tmp_path: Path) -> None:
    studio = seed_demo_policies(PolicyRegistry(root=tmp_path / "ps"))
    policies = studio.list_policies()
    assert len(policies) >= 3
    ok, reasons = studio.validate(policies[0])
    assert ok is True
    assert reasons == ()
    bad = Policy(
        id="bad",
        name="Bad",
        description="",
        priority=-1,
        enabled=True,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        rules=(),
    )
    ok, reasons = studio.validate(bad)
    assert ok is False
    assert any("rule" in r or "priority" in r for r in reasons)

    ctx = {"battery": 10, "region": "Hyderabad", "intent": "CODING", "cpu": 10}
    results = studio.evaluate(ctx)
    assert any(r.matched for r in results)
    one = studio.evaluate(ctx, policy_id="battery-saver")
    assert len(one) == 1
    assert studio.evaluate(ctx, policy_id="missing") == ()

    impact = studio.simulate(
        ctx, recommendations=("High Performance", "Balanced", "Quiet")
    )
    assert "High Performance" not in impact.filtered_recommendations
    assert "Balanced" in impact.filtered_recommendations
    assert impact.constraints


def test_constraints_helpers() -> None:
    policy = _policy()
    results = (
        EvaluationResult(
            matched=True,
            policy=policy,
            explanation="e",
            confidence=0.9,
            action="Reject High Performance",
        ),
        EvaluationResult(
            matched=True,
            policy=_policy(id="region", name="Region"),
            explanation="e2",
            confidence=0.8,
            action="Workloads must remain inside Hyderabad",
        ),
        EvaluationResult(
            matched=False,
            policy=policy,
            explanation="no",
            confidence=1.0,
        ),
    )
    cons = constraints_from_results(results)
    assert any(c.kind == "filter_recommendation" for c in cons)
    assert any(c.kind == "region_affinity" for c in cons)
    filtered = filter_recommendations(("High Performance", "Balanced"), results)
    assert filtered == ("Balanced",)


def test_formatter_views(tmp_path: Path) -> None:
    studio = seed_demo_policies(PolicyRegistry(root=tmp_path / "ps"))
    ctx = {"battery": 10, "region": "Hyderabad", "intent": "CODING", "cpu": 90}
    results = studio.evaluate(ctx)
    impact = studio.simulate(ctx, recommendations=("High Performance", "Balanced"))
    policies = studio.list_policies()
    idle = _print(PolicyStudioPanel())
    assert "idle" in idle.lower()
    for view in ("active", "versions", "builder", "evaluation", "simulation"):
        text = _print(
            PolicyStudioPanel(
                policies=policies,
                results=results,
                impact=impact,
                selected=studio.registry.get_policy("battery-saver"),
                view=view,
            )
        )
        assert "POLICY STUDIO" in text
    empty_eval = _print(
        PolicyStudioPanel(policies=policies, results=(), view="evaluation")
    )
    assert "no matches" in empty_eval.lower()
    empty_sim = _print(
        PolicyStudioPanel(policies=policies, results=results, view="simulation")
    )
    assert "Simulation" in empty_sim or "simulation" in empty_sim.lower()


def test_seed_idempotent(tmp_path: Path) -> None:
    reg = PolicyRegistry(root=tmp_path / "ps")
    seed_demo_policies(reg)
    seed_demo_policies(reg)
    assert len(reg.list_policies()) >= 3


def test_rule_from_list_permissions_style() -> None:
    data = {
        "field": "region",
        "operator": "IN",
        "value": ["Hyderabad"],
        "action": "Stay",
    }
    rule = Rule.from_dict(data)
    assert rule.value == ("Hyderabad",)


def test_parser_edge_literals() -> None:
    assert parse_expression("n == null").value.value is None
    assert parse_expression("t == true").value.value is True
    assert parse_expression("s == 'quoted'").value.value == "quoted"
    assert parse_expression('s == "dquoted"').value.value == "dquoted"
    assert parse_expression("solo IN Hyderabad").value.value == ("Hyderabad",)
    with pytest.raises(ValueError):
        parse_expression("x IN [@]")
    expr = rule_to_expression(Rule(field="cpu", operator=">=", value=1.5, action="Cap"))
    assert "cpu >=" in expr


def test_constraints_research_and_simulation_kinds() -> None:
    policy = _policy(id="res", name="Research")
    results = (
        EvaluationResult(
            matched=True,
            policy=policy,
            explanation="e",
            confidence=0.5,
            action="Limit research experiment batch",
        ),
        EvaluationResult(
            matched=True,
            policy=_policy(id="twin", name="Twin"),
            explanation="e",
            confidence=0.5,
            action="Annotate twin simulation",
        ),
        EvaluationResult(
            matched=True,
            policy=_policy(id="other", name="Other"),
            explanation="e",
            confidence=0.5,
            action="Apply governance hint",
        ),
    )
    cons = constraints_from_results(results)
    kinds = {c.kind for c in cons}
    assert "research" in kinds
    assert "simulation" in kinds
    # no rejects → passthrough
    assert filter_recommendations(("A", "B"), results) == ("A", "B")
    # empty reject target branch
    empty_reject = (
        EvaluationResult(
            matched=True,
            policy=policy,
            explanation="e",
            confidence=0.5,
            action="reject ",
        ),
    )
    assert filter_recommendations(("A",), empty_reject) == ("A",)


def test_evaluator_numeric_equality_and_coercion() -> None:
    ok, _ = evaluate_rule(parse_rule("cpu == 90", action="a"), {"cpu": 90.0})
    assert ok is True
    ok, _ = evaluate_rule(parse_rule("cpu != 90", action="a"), {"cpu": 90.0})
    assert ok is False
    from aetheros.policy.evaluator import _coerce_number

    assert _coerce_number(True) is None
    assert _coerce_number("nope") is None
    assert _coerce_number(object()) is None


def test_formatter_fallback_branches(tmp_path: Path) -> None:
    policies = (_policy(rules=()),)
    text = _print(
        PolicyStudioPanel(
            policies=policies, results=(), selected=policies[0], view="active"
        )
    )
    assert "POLICY STUDIO" in text
    text2 = _print(
        PolicyStudioPanel(
            policies=(_policy(),),
            results=(),
            view="versions",
        )
    )
    assert "battery-saver" in text2 or "Battery" in text2
    # empty versions list path when policies provided but we want (none) — use published empty via custom
    text2b = _print(
        PolicyStudioPanel(
            policies=(),
            results=(
                EvaluationResult(
                    matched=False,
                    policy=_policy(),
                    explanation="x",
                    confidence=1.0,
                ),
            ),
            view="versions",
        )
    )
    assert "none" in text2b.lower()
    # simulation with empty constraints/filtered
    impact = SimulationImpact(
        matched=(),
        filtered_recommendations=(),
        constraints=(),
        explanations=(),
    )
    text3 = _print(
        PolicyStudioPanel(
            policies=policies, results=(), impact=impact, view="simulation"
        )
    )
    assert "none" in text3.lower()


def test_registry_corrupt_and_new_version_missing(tmp_path: Path) -> None:
    reg = PolicyRegistry(root=tmp_path / "ps")
    with pytest.raises(KeyError):
        reg.new_version("missing")
    with pytest.raises(KeyError):
        reg.archive("missing")
    reg.store_path.parent.mkdir(parents=True, exist_ok=True)
    reg.store_path.write_text(
        json.dumps(
            {
                "policies": [
                    "bad",
                    {
                        "id": "x",
                        "name": "X",
                        "version": 1,
                        "description": "d",
                        "priority": 1,
                        "enabled": True,
                        "created_at": datetime.now(UTC).isoformat(),
                        "status": "published",
                        "rules": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    reg.reload()
    # empty rules policy loads
    assert reg.get_policy("x") is not None


def test_engine_validate_rule_operator_branch() -> None:
    studio = PolicyStudio(PolicyRegistry())
    policy = _policy(
        rules=(Rule(field="a", operator="IN", value=("x",), action="Stay"),)
    )
    ok, _ = studio.validate(policy)
    assert ok is True
    # empty id/name branches via frozen setattr
    p2 = _policy()
    object.__setattr__(p2, "id", "")
    object.__setattr__(p2, "name", "  ")
    ok, reasons = studio.validate(p2)
    assert ok is False
    assert any("id" in r for r in reasons)
