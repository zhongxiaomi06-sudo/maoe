from __future__ import annotations

from maoe.models.complexity import ComplexityLevel, ComplexityScore
from maoe.models.routing import TIER_ORDER, ModelTier, RoutingDecision
from maoe.models.task import SubTask, Task, TaskGraph, TaskStatus


def test_subtask_defaults() -> None:
    s = SubTask(id="st-1", description="test")
    assert s.status == TaskStatus.PENDING
    assert s.attempts == 0
    assert s.max_attempts == 3
    assert s.dependencies == []


def test_task_graph_execution_order_simple() -> None:
    t = Task(id="t1", description="test")
    graph = TaskGraph(task=t)
    graph.add_subtask(SubTask(id="st-1", description="first"))
    graph.add_subtask(SubTask(id="st-2", description="second", dependencies=["st-1"]))
    graph.add_subtask(SubTask(id="st-3", description="third", dependencies=["st-1"]))

    layers = graph.get_execution_order()
    assert len(layers) == 2
    assert {s.id for s in layers[0]} == {"st-1"}
    assert {s.id for s in layers[1]} == {"st-2", "st-3"}


def test_task_graph_execution_order_parallel() -> None:
    t = Task(id="t1", description="test")
    graph = TaskGraph(task=t)
    graph.add_subtask(SubTask(id="st-1", description="a"))
    graph.add_subtask(SubTask(id="st-2", description="b"))
    graph.add_subtask(SubTask(id="st-3", description="c"))

    layers = graph.get_execution_order()
    assert len(layers) == 1
    assert len(layers[0]) == 3


def test_task_graph_circular_dependency() -> None:
    t = Task(id="t1", description="test")
    graph = TaskGraph(task=t)
    graph.add_subtask(SubTask(id="st-1", description="a", dependencies=["st-2"]))
    graph.add_subtask(SubTask(id="st-2", description="b", dependencies=["st-1"]))

    try:
        graph.get_execution_order()
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_task_graph_dependents() -> None:
    t = Task(id="t1", description="test")
    graph = TaskGraph(task=t)
    graph.add_subtask(SubTask(id="st-1", description="a"))
    graph.add_subtask(SubTask(id="st-2", description="b", dependencies=["st-1"]))
    graph.add_subtask(SubTask(id="st-3", description="c", dependencies=["st-1"]))

    deps = graph.get_dependents("st-1")
    assert set(deps) == {"st-2", "st-3"}


def test_complexity_level_enum() -> None:
    assert ComplexityLevel.TRIVIAL.value == 1
    assert ComplexityLevel.CRITICAL.value == 5
    assert ComplexityLevel.MODERATE > ComplexityLevel.SIMPLE


def test_complexity_score_label() -> None:
    s = ComplexityScore(level=ComplexityLevel.COMPLEX, score=0.8, reasoning="test")
    assert s.label == "complex"
    assert s.score == 0.8


def test_model_tier_order() -> None:
    assert TIER_ORDER == [
        ModelTier.FAST,
        ModelTier.BALANCED,
        ModelTier.POWERFUL,
        ModelTier.CRITICAL,
    ]


def test_default_model_capabilities() -> None:
    from maoe.models.routing import DEFAULT_MODELS
    assert len(DEFAULT_MODELS) == 4
    assert DEFAULT_MODELS[0].tier == ModelTier.FAST
    assert DEFAULT_MODELS[1].tier == ModelTier.BALANCED
    assert DEFAULT_MODELS[2].tier == ModelTier.POWERFUL
    assert DEFAULT_MODELS[3].tier == ModelTier.CRITICAL


def test_routing_decision() -> None:
    d = RoutingDecision(
        subtask_id="st-1",
        assigned_model="gpt-4o-mini",
        assigned_tier=ModelTier.FAST,
        estimated_cost=0.001,
    )
    assert d.assigned_tier == ModelTier.FAST
    assert d.estimated_cost == 0.001
