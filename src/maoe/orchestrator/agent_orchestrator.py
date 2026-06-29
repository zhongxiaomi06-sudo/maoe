from __future__ import annotations

import asyncio

from loguru import logger
from pydantic import BaseModel, Field

from maoe.config import settings
from maoe.economist import TokenEconomist
from maoe.evaluator import ComplexityEval
from maoe.llm import LLMClient
from maoe.models.complexity import ComplexityLevel
from maoe.models.routing import ModelTier
from maoe.models.task import SubTask, TaskGraph, TaskStatus
from maoe.parser import TaskParser
from maoe.quality import QualityGate, SubtaskExecutor
from maoe.router import ModelRouter


class EngineResult(BaseModel):
    task_id: str
    description: str
    subtask_count: int
    completed_count: int
    failed_count: int
    total_cost: float
    total_tokens: int
    status: str
    subtask_results: list[dict] = Field(default_factory=list)


class MAOEEngine:
    def __init__(self) -> None:
        self._llm = LLMClient()
        self._parser = TaskParser(self._llm)
        self._evaluator = ComplexityEval(self._llm)
        self._router = ModelRouter()
        self._economist = TokenEconomist()
        self._quality = QualityGate(self._llm)
        self._executor = SubtaskExecutor(self._llm)
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)

    async def run(self, description: str) -> EngineResult:
        logger.info("MAOE Engine starting for: {}", description)
        usage_before = self._llm.usage_snapshot()

        parse_result = await self._parser.parse(description)
        graph_task = parse_result.task.model_copy(deep=True)
        graph_task.subtasks = []
        graph = TaskGraph(task=graph_task)
        for s in parse_result.task.subtasks:
            graph.add_subtask(s.model_copy(deep=True))

        logger.info("Evaluating complexity for {} sub-tasks", parse_result.subtask_count)

        complexity_data: list[tuple[str, int, ModelTier]] = []
        for subtask in graph.task.subtasks:
            score = await self._evaluator.evaluate(subtask.description)
            subtask.complexity_score = score.score
            subtask.complexity_level = score.label
            routing = self._router.route(subtask.id, score.level)
            subtask.assigned_model = routing.assigned_model
            subtask.assigned_tier = routing.assigned_tier.value
            complexity_data.append(
                (subtask.id, score.level.value, routing.assigned_tier)
            )

        budget_report = self._economist.allocate(complexity_data)
        for alloc in budget_report.allocations:
            for s in graph.task.subtasks:
                if s.id == alloc.subtask_id:
                    s.token_budget = alloc.token_budget

        if budget_report.warnings:
            for w in budget_report.warnings:
                logger.warning(w)

        try:
            layers = graph.get_execution_order()
        except ValueError as e:
            graph.task.status = TaskStatus.FAILED
            return EngineResult(
                task_id=graph.task.id,
                description=description,
                subtask_count=0,
                completed_count=0,
                failed_count=0,
                total_cost=0.0,
                total_tokens=0,
                status="failed",
                subtask_results=[{"error": str(e)}],
            )

        layer_ids = [[s.id for s in layer] for layer in layers]
        logger.info("Execution layers: {}", layer_ids)
        completed_map: dict[str, str] = {}
        results: list[dict] = []

        for layer_idx, layer in enumerate(layers):
            logger.info("Executing layer {} with {} sub-tasks", layer_idx + 1, len(layer))
            tasks = [self._execute_subtask(s, completed_map) for s in layer]
            outcomes = await asyncio.gather(*tasks)

            for subtask, dep_context in outcomes:
                completed_map[subtask.id] = dep_context
                results.append({
                    "id": subtask.id,
                    "description": subtask.description,
                    "status": subtask.status.value,
                    "model": subtask.assigned_model,
                    "tier": subtask.assigned_tier,
                    "attempts": subtask.attempts,
                    "complexity": subtask.complexity_level,
                    "quality_score": (
                        subtask.quality_pass
                        if subtask.quality_pass is None
                        else (1.0 if subtask.quality_pass else 0.0)
                    ),
                    "quality_passed": subtask.quality_pass,
                    "escalation_count": subtask.escalation_count,
                })

        usage_after = self._llm.usage_snapshot()
        total_cost = float(usage_after["cost"] - usage_before["cost"])
        total_tokens = int(usage_after["total_tokens"] - usage_before["total_tokens"])
        graph.task.total_cost = total_cost
        graph.task.total_tokens = total_tokens
        failed = [s for s in graph.task.subtasks if s.status == TaskStatus.FAILED]
        completed = [s for s in graph.task.subtasks if s.status == TaskStatus.COMPLETED]
        graph.task.status = TaskStatus.COMPLETED if not failed else TaskStatus.FAILED

        logger.info(
            "MAOE Engine completed: {}/{} sub-tasks done, cost=${:.6f}",
            len(completed),
            len(graph.task.subtasks),
            total_cost,
        )

        return EngineResult(
            task_id=graph.task.id,
            description=description,
            subtask_count=len(graph.task.subtasks),
            completed_count=len(completed),
            failed_count=len(failed),
            total_cost=total_cost,
            total_tokens=graph.task.total_tokens,
            status=graph.task.status.value,
            subtask_results=results,
        )

    async def _execute_subtask(
        self,
        subtask: SubTask,
        completed_map: dict[str, str],
    ) -> tuple[SubTask, str]:
        async with self._semaphore:
            dep_context = "\n".join(
                f"[{dep}]: {completed_map.get(dep, '')}"
                for dep in subtask.dependencies
                if dep in completed_map
            )

            for attempt in range(subtask.max_attempts):
                subtask.status = TaskStatus.RUNNING
                subtask.attempts = attempt + 1

                logger.info(
                    "Executing {} '{}' on {} (attempt {}/{})",
                    subtask.id,
                    subtask.description[:50],
                    subtask.assigned_model,
                    attempt + 1,
                    subtask.max_attempts,
                )

                output = await self._executor.execute(
                    description=subtask.description,
                    model=subtask.assigned_model or settings.default_model,
                    dep_context=dep_context,
                    max_tokens=subtask.token_budget or 16000,
                )

                verdict = await self._quality.check(subtask.description, output)
                subtask.quality_pass = verdict.passed

                if verdict.passed:
                    subtask.output = output
                    subtask.status = TaskStatus.COMPLETED
                    logger.info("{} passed quality gate (score={})", subtask.id, verdict.score)
                    return subtask, output

                logger.warning(
                    "{} failed quality gate: {} (score={})",
                    subtask.id,
                    verdict.reasoning,
                    verdict.score,
                )

                can_escalate = attempt < subtask.max_attempts - 1
                escalation = None
                if can_escalate and subtask.assigned_tier:
                    current = self._router.route(
                        subtask.id,
                        ComplexityLevel.MODERATE,
                        force_tier=ModelTier(subtask.assigned_tier),
                    )
                    escalation = self._router.escalate(current)

                if escalation:
                    subtask.assigned_model = escalation.assigned_model
                    subtask.assigned_tier = escalation.assigned_tier.value
                    subtask.status = TaskStatus.ESCALATED
                    subtask.escalation_count += 1
                    logger.info(
                        "Escalating {} to {} (tier {})",
                        subtask.id,
                        escalation.assigned_model,
                        escalation.assigned_tier,
                    )

            subtask.status = TaskStatus.FAILED
            subtask.error = f"Failed after {subtask.max_attempts} attempts"
            logger.error("{} failed after {} attempts", subtask.id, subtask.max_attempts)
            return subtask, ""

    async def close(self) -> None:
        await self._llm.close()
