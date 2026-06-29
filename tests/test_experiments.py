from __future__ import annotations

from pathlib import Path

from maoe.compiler import WorkflowCompiler
from maoe.experiments import (
    CandidateEvaluation,
    CandidateLab,
    EarlyStopper,
    ParetoSelector,
)
from maoe.models.capsule import RiskLevel
from maoe.models.workflow import GoalConstraints, GoalQuality, WorkflowVariant

ROOT = Path(__file__).resolve().parent.parent


def _evaluation(
    workflow_id: str,
    variant: WorkflowVariant,
    *,
    quality: float,
    cost: float,
    latency: float,
) -> CandidateEvaluation:
    return CandidateEvaluation(
        workflow_id=workflow_id,
        variant=variant,
        quality=quality,
        reliability=quality,
        cost=cost,
        latency_seconds=latency,
        risk=RiskLevel.LOW,
        passed=True,
    )


def test_pareto_selector_removes_dominated_candidate() -> None:
    economy = _evaluation(
        "economy",
        WorkflowVariant.ECONOMY,
        quality=0.80,
        cost=0.01,
        latency=10,
    )
    dominated = _evaluation(
        "dominated",
        WorkflowVariant.BALANCED,
        quality=0.75,
        cost=0.02,
        latency=12,
    )
    selection = ParetoSelector().select(
        [economy, dominated],
        GoalConstraints(),
        GoalQuality(minimum_score=0.7),
    )
    assert selection.frontier_workflow_ids == ["economy"]
    assert selection.recommended_workflow_id == "economy"


def test_candidate_lab_runs_two_variants_and_reuses_shared_prefix() -> None:
    compiled = WorkflowCompiler(ROOT).compile("实现 Python 登录功能并通过测试")
    result = CandidateLab().run(compiled)

    assert len(result.evaluations) == 2
    assert result.stopped_early
    assert result.selection.recommended_workflow_id.startswith("wf-balanced-")
    assert "planning.task-decomposition" in result.reused_node_ids
    assert result.evaluations[1].reused_node_ids == ["planning.task-decomposition"]


def test_early_stopper_enforces_three_candidate_limit() -> None:
    stopper = EarlyStopper(maximum_candidates=3)
    compiled = WorkflowCompiler(ROOT).compile("实现 Python 功能并通过测试")
    completed = [
        _evaluation(str(index), WorkflowVariant.ECONOMY, quality=0.8, cost=0.01, latency=1)
        for index in range(3)
    ]
    decision = stopper.decide(compiled.goal_ir, completed, compiled.candidates)
    assert decision.stop
    assert decision.reason == "candidate limit reached"
