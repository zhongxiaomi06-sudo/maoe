from __future__ import annotations

from pathlib import Path

import pytest

from maoe.compiler import StaticValidationError, WorkflowCompiler, WorkflowTypeChecker
from maoe.models.capsule import (
    CapabilityContract,
    CertificationLevel,
    EffectSpec,
    QualitySpec,
    SkillCapsule,
)
from maoe.models.workflow import GoalIR, WorkflowDAG, WorkflowNode, WorkflowVariant
from maoe.registry import SkillRegistry

ROOT = Path(__file__).resolve().parent.parent


def _capsule(
    skill_id: str,
    provides: list[str],
    requires: list[str] | None = None,
    schemas: dict[str, str] | None = None,
    writes: list[str] | None = None,
) -> SkillCapsule:
    return SkillCapsule(
        id=skill_id,
        version="1.0.0",
        description=f"Capsule {skill_id}",
        capabilities=CapabilityContract(
            provides=provides,
            requires=requires or [],
            schemas=schemas or {},
        ),
        effects=EffectSpec(writes=writes or []),
        quality=QualitySpec(validators=["valid"]),
        certification=CertificationLevel.VERIFIED,
    )


def _node(capsule: SkillCapsule, dependencies: list[str] | None = None) -> WorkflowNode:
    return WorkflowNode(
        id=capsule.id,
        skill_id=capsule.id,
        skill_version=capsule.version,
        agent="code-agent",
        model_tier="fast",
        dependencies=dependencies or [],
        requires=capsule.capabilities.requires,
        provides=capsule.capabilities.provides,
        validators=capsule.quality.validators,
        writes=capsule.effects.writes,
    )


def test_compiler_emits_three_distinct_deterministic_candidates() -> None:
    compiler = WorkflowCompiler(ROOT)
    first = compiler.compile("为 FastAPI 项目增加 JWT 登录并通过测试")
    second = compiler.compile("为 FastAPI 项目增加 JWT 登录并通过测试")

    assert len(first.candidates) == 3
    assert {candidate.variant for candidate in first.candidates} == set(WorkflowVariant)
    assert first.lock_digest == second.lock_digest
    assert [candidate.workflow_id for candidate in first.candidates] == [
        candidate.workflow_id for candidate in second.candidates
    ]
    assert first.recommendation == WorkflowVariant.BALANCED
    assert all(
        "planning.task-decomposition" in candidate.shared_node_ids
        for candidate in first.candidates
    )
    assert len({len(candidate.dag.nodes) for candidate in first.candidates}) == 3


def test_compiler_rejects_missing_capability() -> None:
    registry = SkillRegistry(ROOT)
    compiler = WorkflowCompiler(ROOT, registry=registry)
    with pytest.raises(StaticValidationError, match="no verified skill"):
        compiler.compile("实现一个 Python 功能")


def test_type_checker_detects_schema_mismatch() -> None:
    registry = SkillRegistry(ROOT)
    producer = _capsule("test.producer", ["data.value"], schemas={"data.value": "data/v1"})
    consumer = _capsule(
        "test.consumer",
        ["result.value"],
        ["data.value"],
        schemas={"data.value": "data/v2", "result.value": "result/v1"},
    )
    registry.register(producer)
    registry.register(consumer)
    dag = WorkflowDAG(nodes=[_node(producer), _node(consumer, [producer.id])])
    goal = GoalIR(goal="test", deliverables=["result.value"])

    issues = WorkflowTypeChecker(registry).validate(goal, dag)
    assert "schema_mismatch" in {issue.code for issue in issues}


def test_type_checker_detects_parallel_resource_conflict() -> None:
    registry = SkillRegistry(ROOT)
    left = _capsule("test.left", ["left.out"], writes=["src/shared.py"])
    right = _capsule("test.right", ["right.out"], writes=["src/shared.py"])
    registry.register(left)
    registry.register(right)
    dag = WorkflowDAG(nodes=[_node(left), _node(right)])
    goal = GoalIR(goal="test", deliverables=["left.out", "right.out"])

    issues = WorkflowTypeChecker(registry).validate(goal, dag)
    assert "resource_conflict" in {issue.code for issue in issues}


def test_type_checker_detects_cycle() -> None:
    registry = SkillRegistry(ROOT)
    left = _capsule("test.left", ["left.out"])
    right = _capsule("test.right", ["right.out"])
    registry.register(left)
    registry.register(right)
    dag = WorkflowDAG(nodes=[_node(left, [right.id]), _node(right, [left.id])])
    goal = GoalIR(goal="test", deliverables=["left.out"])

    issues = WorkflowTypeChecker(registry).validate(goal, dag)
    assert [issue.code for issue in issues] == ["cycle"]
