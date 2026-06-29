from __future__ import annotations

import pytest

from maoe.llm.client import LLMResponse
from maoe.orchestrator.agent_orchestrator import EngineResult, MAOEEngine


def test_engine_result_model() -> None:
    r = EngineResult(
        task_id="t1",
        description="test",
        subtask_count=2,
        completed_count=1,
        failed_count=1,
        total_cost=0.005,
        total_tokens=5000,
        status="completed",
        subtask_results=[
            {"id": "st-1", "status": "completed", "model": "gpt-4o-mini"},
            {"id": "st-2", "status": "failed", "model": "gpt-4o"},
        ],
    )
    assert r.completed_count == 1
    assert r.failed_count == 1
    assert len(r.subtask_results) == 2
    assert '"task_id":"t1"' in r.model_dump_json()


class _FakeLLMClient:
    def __init__(self) -> None:
        self._input_tokens = 0
        self._output_tokens = 0
        self._cost = 0.0

    def _record(self, input_tokens: int, output_tokens: int, cost: float) -> None:
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._cost += cost

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        prompt = messages[-1]["content"]
        if "Break the user request" in prompt:
            content = (
                '{"subtasks":[{"id":"st-1","description":"Build the MAOE core",'
                '"dependencies":[]}]}'
            )
            self._record(100, 50, 0.005)
        elif "Analyze the complexity" in prompt:
            content = (
                '{"level":3,"score":0.6,"reasoning":"moderate",'
                '"factors":{"scope":0.5,"difficulty":0.5,'
                '"dependencies":0.5,"domain_knowledge":0.5}}'
            )
            self._record(30, 12, 0.0012)
        elif "Execute the following sub-task" in prompt:
            content = "Implemented the MAOE core with bootstrap loading and cost tracking."
            self._record(200, 120, 0.008)
        elif "Evaluate whether the sub-task output meets requirements" in prompt:
            content = '{"pass":true,"score":0.95,"reasoning":"meets requirements","issues":[]}'
            self._record(20, 10, 0.0008)
        else:
            content = "{}"
            self._record(10, 5, 0.0001)

        return LLMResponse(
            content=content,
            model=model,
            usage_input_tokens=0,
            usage_output_tokens=0,
            cost=0.0,
            finish_reason="stop",
        )

    async def chat_json(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        return await self.chat(model=model, messages=messages, temperature=temperature)

    def usage_snapshot(self) -> dict[str, float | int]:
        return {
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "total_tokens": self._input_tokens + self._output_tokens,
            "cost": self._cost,
        }

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_engine_tracks_usage_and_serializes(monkeypatch: pytest.MonkeyPatch) -> None:
    from maoe.orchestrator import agent_orchestrator as orchestrator_module

    monkeypatch.setattr(orchestrator_module, "LLMClient", _FakeLLMClient)

    engine = MAOEEngine()
    try:
        result = await engine.run("Build the MAOE core")
    finally:
        await engine.close()

    assert result.status == "completed"
    assert result.completed_count == 1
    assert result.failed_count == 0
    assert result.total_tokens == 542
    assert result.total_cost == pytest.approx(0.015, rel=1e-6)
