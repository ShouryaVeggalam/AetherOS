"""Hierarchical objective decomposition into a DAG task graph.

Levels: Strategic → Tactical → Operational → Execution.
Deterministic templates driven by objective cues and max_depth.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha1
from uuid import uuid4

from labs.aether.models.types import Goal, Task, TaskGraph, TaskType

_LEVELS: tuple[TaskType, ...] = (
    "strategic",
    "tactical",
    "operational",
    "execution",
)

_TACTICAL_TEMPLATES: tuple[str, ...] = (
    "Clarify success criteria and constraints for: {objective}",
    "Identify evidence sources and unknowns for: {objective}",
    "Draft hierarchical approach for: {objective}",
)

_OPERATIONAL_TEMPLATES: tuple[str, ...] = (
    "Enumerate workstreams under: {parent}",
    "Map dependencies and risks for: {parent}",
    "Define verification checkpoints for: {parent}",
)

_EXECUTION_TEMPLATES: tuple[str, ...] = (
    "Produce artifact for: {parent}",
    "Validate evidence against: {parent}",
)


def decompose_objective(
    goal: Goal,
    *,
    max_depth: int = 3,
    now: datetime | None = None,
    graph_id: str | None = None,
) -> TaskGraph:
    """Convert one objective into a hierarchical DAG of tasks.

    ``max_depth`` maps to levels:
    1 → strategic only
    2 → + tactical
    3 → + operational
    4+ → + execution
    """

    if max_depth < 1:
        raise ValueError("max_depth must be >= 1")
    depth_cap = min(max_depth, len(_LEVELS))
    stamp = now or datetime.now(UTC)
    tasks: list[Task] = []

    root_id = _task_id(goal.id, 0, 0, goal.objective)
    root = Task(
        id=root_id,
        parent_task=None,
        type="strategic",
        dependencies=(),
        status="ready",
        statement=f"Strategic objective: {goal.objective.strip()}",
        depth=0,
    )
    tasks.append(root)

    if depth_cap >= 2:
        tactical = _spawn(
            parent=root,
            templates=_select_tactical(goal),
            task_type="tactical",
            goal_id=goal.id,
            depth=1,
        )
        tasks.extend(tactical)
        if depth_cap >= 3:
            for tac in tactical:
                ops = _spawn(
                    parent=tac,
                    templates=_OPERATIONAL_TEMPLATES,
                    task_type="operational",
                    goal_id=goal.id,
                    depth=2,
                )
                tasks.extend(ops)
                if depth_cap >= 4:
                    for op in ops:
                        # First operational child gets execution leaves;
                        # keep DAG bounded and deterministic.
                        if op is not ops[0] and op is not ops[-1]:
                            continue
                        execs = _spawn(
                            parent=op,
                            templates=_EXECUTION_TEMPLATES,
                            task_type="execution",
                            goal_id=goal.id,
                            depth=3,
                        )
                        tasks.extend(execs)

    # Mark leaves without unmet deps as ready; others pending.
    finalized = _finalize_status(tuple(tasks))
    return TaskGraph(
        id=graph_id or f"tg_{uuid4().hex[:12]}",
        goal_id=goal.id,
        objective=goal.objective.strip(),
        tasks=finalized,
        roots=(root_id,),
        max_depth=depth_cap - 1,
        created_at=stamp,
    )


def topological_order(graph: TaskGraph) -> tuple[Task, ...]:
    """Return tasks in dependency-respecting order (Kahn)."""

    by_id = {t.id: t for t in graph.tasks}
    indegree = {t.id: 0 for t in graph.tasks}
    children: dict[str, list[str]] = {t.id: [] for t in graph.tasks}
    for task in graph.tasks:
        for dep in task.dependencies:
            indegree[task.id] += 1
            children[dep].append(task.id)
        if task.parent_task and task.parent_task not in task.dependencies:
            # Parent is an implicit sequencing edge for hierarchy.
            indegree[task.id] += 1
            children[task.parent_task].append(task.id)

    queue = sorted(tid for tid, deg in indegree.items() if deg == 0)
    ordered: list[Task] = []
    while queue:
        current = queue.pop(0)
        ordered.append(by_id[current])
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
                queue.sort()
    if len(ordered) != len(graph.tasks):
        raise ValueError("task graph contains a cycle")
    return tuple(ordered)


def validate_dag(graph: TaskGraph) -> tuple[str, ...]:
    """Return warning factors; raises on hard cycle errors via topo."""

    factors: list[str] = [
        f"tasks={len(graph.tasks)}",
        f"max_depth={graph.max_depth}",
        f"roots={len(graph.roots)}",
    ]
    by_type: dict[str, int] = {}
    for task in graph.tasks:
        by_type[task.type] = by_type.get(task.type, 0) + 1
    for level, count in sorted(by_type.items()):
        factors.append(f"{level}={count}")
    # Force cycle detection.
    topological_order(graph)
    return tuple(factors)


def _select_tactical(goal: Goal) -> tuple[str, ...]:
    templates = list(_TACTICAL_TEMPLATES)
    corpus = " ".join(
        [goal.objective.lower(), *[c.lower() for c in goal.constraints]]
    )
    if any(k in corpus for k in ("research", "evidence", "experiment")):
        templates.append("Design evidence protocol for: {objective}")
    if any(k in corpus for k in ("system", "architecture", "platform")):
        templates.append("Specify architecture boundaries for: {objective}")
    if goal.priority >= 70:
        templates.append("Prioritize risk controls for: {objective}")
    # Deterministic bound.
    return tuple(templates[:5])


def _spawn(
    *,
    parent: Task,
    templates: Sequence[str],
    task_type: TaskType,
    goal_id: str,
    depth: int,
) -> list[Task]:
    children: list[Task] = []
    for index, template in enumerate(templates):
        statement = template.format(
            objective=parent.statement.replace("Strategic objective: ", ""),
            parent=parent.statement,
        )
        tid = _task_id(goal_id, depth, index, statement)
        deps: tuple[str, ...] = (parent.id,)
        if index > 0:
            # Sequential dependency among siblings for stable DAG.
            deps = (parent.id, children[-1].id)
        children.append(
            Task(
                id=tid,
                parent_task=parent.id,
                type=task_type,
                dependencies=deps,
                status="pending",
                statement=statement,
                depth=depth,
            )
        )
    return children


def _finalize_status(tasks: tuple[Task, ...]) -> tuple[Task, ...]:
    out: list[Task] = []
    for task in tasks:
        status = task.status
        if task.depth == 0:
            status = "ready"
        elif not task.dependencies:
            status = "ready"
        else:
            status = "pending"
        if status != task.status:
            task = Task(
                id=task.id,
                parent_task=task.parent_task,
                type=task.type,
                dependencies=task.dependencies,
                status=status,
                statement=task.statement,
                depth=task.depth,
            )
        out.append(task)
    return tuple(out)


def _task_id(goal_id: str, depth: int, index: int, statement: str) -> str:
    digest = sha1(
        f"{goal_id}|{depth}|{index}|{statement}".encode(),
        usedforsecurity=False,
    ).hexdigest()[:10]
    return f"task_{depth}_{index}_{digest}"
