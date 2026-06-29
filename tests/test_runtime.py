"""runtime 包的最小冒烟测试 —— 保护包导出不会因死引用再次崩。"""
from __future__ import annotations

from pathlib import Path

import pytest

from maoe.models.capsule import RiskLevel
from maoe.models.workflow import (
    CandidateWorkflow,
    CompileResult,
    GoalIR,
    WorkflowDAG,
    WorkflowNode,
    WorkflowVariant,
)
from maoe.runtime import (
    DecisionRecord,
    EventRecord,
    NodePhase,
    NodeRunState,
    RunPhase,
    RunState,
    RunStore,
)


def _make_compiled() -> tuple[CompileResult, CandidateWorkflow]:
    goal = GoalIR(goal="demo", deliverables=["x"])
    node = WorkflowNode(
        id="n1",
        skill_id="dummy",
        skill_version="1.0.0",
        agent="code-agent",
        model_tier="economy",
    )
    dag = WorkflowDAG(nodes=[node])
    candidate = CandidateWorkflow(
        variant=WorkflowVariant.ECONOMY,
        workflow_id="wf-1",
        dag=dag,
        estimated_cost=0.0,
        estimated_tokens=0,
        estimated_seconds=0.0,
        predicted_quality=1.0,
        predicted_reliability=1.0,
        risk=RiskLevel.LOW,
    )
    compiled = CompileResult(
        goal_ir=goal,
        capability_graph={"nodes": [], "edges": [], "required_outputs": []},  # type: ignore[arg-type]
        candidates=[candidate],
        recommendation=WorkflowVariant.ECONOMY,
        lock_digest="x" * 16,
    )
    return compiled, candidate


def test_runtime_exports_resolve() -> None:
    """死引用 regression：从 maoe.runtime 导入核心符号必须成功。"""
    assert RunStore is not None
    assert RunState is not None
    assert NodePhase.PENDING.value == "pending"
    assert RunPhase.CREATED.value == "created"


def test_run_store_create_and_persist(tmp_path: Path) -> None:
    store = RunStore(root=tmp_path)
    compiled, candidate = _make_compiled()

    state = store.create(compiled, candidate, context={"foo": "bar"})
    assert state.run_id.startswith("run-")
    assert state.nodes["n1"].phase == NodePhase.PENDING

    # 改一下节点状态并 checkpoint，验证文件落盘
    state.nodes["n1"] = NodeRunState(node_id="n1", phase=NodePhase.COMPLETED, tokens=42, cost=0.001)
    state.phase = RunPhase.COMPLETED
    state.total_tokens = 42
    state.total_cost = 0.001
    store.checkpoint(state)

    reloaded = store.load_state(state.run_id)
    assert reloaded.phase == RunPhase.COMPLETED
    assert reloaded.nodes["n1"].phase == NodePhase.COMPLETED
    assert reloaded.nodes["n1"].tokens == 42


def test_run_store_events_and_decisions(tmp_path: Path) -> None:
    store = RunStore(root=tmp_path)
    compiled, candidate = _make_compiled()
    state = store.create(compiled, candidate)

    store.append_event(
        EventRecord(event_id="e1", sequence=1, run_id=state.run_id, event_type="node_started")
    )
    store.append_decision(
        DecisionRecord(
            decision_id="d1",
            sequence=1,
            run_id=state.run_id,
            action="route",
            reason="economy variant chosen",
        )
    )

    events = store.read_events(state.run_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "node_started"


def test_run_store_redacts_secrets(tmp_path: Path) -> None:
    """写盘前必须 redact API key —— 不能把 sk- 明文留在 .maoe/runs。"""
    store = RunStore(root=tmp_path)
    compiled, candidate = _make_compiled()
    state = store.create(
        compiled,
        candidate,
        context={"api_key": "sk-1234567890abcdef", "note": "Bearer abcdefghijkl"},
    )
    context_file = tmp_path / ".maoe" / "runs" / state.run_id / "context.json"
    text = context_file.read_text()
    assert "sk-1234567890abcdef" not in text
    assert "[REDACTED]" in text


def test_run_store_rejects_path_traversal(tmp_path: Path) -> None:
    store = RunStore(root=tmp_path)
    with pytest.raises(ValueError):
        store.load_state("../etc/passwd")
    with pytest.raises(ValueError):
        store.load_state("run-../escape")
