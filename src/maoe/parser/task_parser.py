from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from loguru import logger

from maoe.llm import LLMClient
from maoe.models.task import SubTask, Task

DECOMPOSE_PROMPT = """Break the user request into concrete, actionable sub-tasks.

Each sub-task must:
1. Be self-contained and independently executable
2. Have clear dependencies on other sub-tasks (use exact sub-task IDs)
3. Be specific enough for a developer to implement
4. Produce at most {max_subtasks} sub-tasks total — do NOT exceed this limit

Respond in JSON format:
{{"subtasks": [
  {{"id": "st-1", "description": "...", "dependencies": []}}
]}}

User request: {description}"""


@dataclass
class ParseResult:
    task: Task
    subtask_count: int
    dependency_count: int


class TaskParser:
    def __init__(self, llm: LLMClient, model: str = "gpt-4o-mini") -> None:
        self._llm = llm
        self._model = model

    async def parse(self, description: str, max_subtasks: int = 8) -> ParseResult:
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task = Task(id=task_id, description=description)

        subtasks = await self._decompose_with_llm(description, max_subtasks)
        subtasks = subtasks[:max_subtasks]
        for s in subtasks:
            task.subtasks.append(s)

        dep_count = sum(len(s.dependencies) for s in subtasks)
        logger.info(
            "Parsed task: {} subtasks, {} dependencies",
            len(subtasks),
            dep_count,
        )
        return ParseResult(task=task, subtask_count=len(subtasks), dependency_count=dep_count)

    async def _decompose_with_llm(self, description: str, max_subtasks: int = 8) -> list[SubTask]:
        prompt = DECOMPOSE_PROMPT.format(description=description, max_subtasks=max_subtasks)
        resp = await self._llm.chat_json(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a precise task decomposition engine."},
                {"role": "user", "content": prompt},
            ],
        )

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse LLM response as JSON: {}", e)
            return [SubTask(id="st-1", description=description)]

        results: list[SubTask] = []
        for item in data.get("subtasks", []):
            results.append(
                SubTask(
                    id=item.get("id", f"st-{len(results) + 1}"),
                    description=item.get("description", ""),
                    dependencies=item.get("dependencies", []),
                )
            )

        if not results:
            results.append(SubTask(id="st-1", description=description))

        return results
